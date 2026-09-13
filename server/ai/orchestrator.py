# ==========================================================================
# JARVIS AI Orchestrator & State Machine
# ==========================================================================

import time
import json
import uuid
from typing import Dict, Any, List, Optional
from server.database import get_db_connection
from server.config import settings
from server.tools.registry import default_registry
from server.ai.provider import LocalDeterministicProvider, AIResponse
from server.ai.provider_factory import get_user_llm_client
from server.permissions.policy_engine import policy_engine
from server.permissions.approval_service import create_approval_request, verify_approval_unexpired
from server.audit.logger import audit_logger

class OrchestrationState:
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    PLANNING = "PLANNING"
    PERMISSION_CHECK = "PERMISSION_CHECK"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    RESPONDING = "RESPONDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AIOrchestrator:
    def __init__(self):
        self.tool_registry = default_registry

    async def process_message(
        self,
        user: Dict[str, Any],
        content: str,
        conversation_id: Optional[str] = None,
        supplied_approval_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs an end-to-end orchestration cycle for a user query using the configured LLM."""
        user_id = user["id"]
        correlation_id = str(uuid.uuid4())
        state = OrchestrationState.RECEIVED
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Ensure conversation exists
        async with await get_db_connection() as db:
            if conversation_id:
                c_cur = await db.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
                if not await c_cur.fetchone():
                    conversation_id = None
            
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                title_snip = content[:30] + ("..." if len(content) > 30 else "")
                await db.execute("""
                    INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, user_id, f"Directives: {title_snip}", now_str, now_str))

            # Store user message
            user_msg_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO messages (id, conversation_id, user_id, role, content, created_at)
                VALUES (?, ?, ?, 'user', ?, ?)
            """, (user_msg_id, conversation_id, user_id, content, now_str))
            await db.commit()

        await audit_logger.log_event(
            event_type="USER_MESSAGE_RECEIVED",
            action="chat.message_received",
            user_id=user_id,
            correlation_id=correlation_id,
            details={"conversation_id": conversation_id, "content_preview": content[:80]}
        )

        # 2. VALIDATING & Fetch Context
        state = OrchestrationState.VALIDATING
        async with await get_db_connection() as db:
            m_cur = await db.execute("""
                SELECT role, content FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC LIMIT 20
            """, (conversation_id,))
            msg_rows = await m_cur.fetchall()
            history = [{"role": r["role"], "content": r["content"]} for r in msg_rows]

        # Resolve active user-configured LLM client
        llm_client = await get_user_llm_client(user_id)
        if not llm_client:
            if settings.USE_LOCAL_AI_FALLBACK:
                llm_client = LocalDeterministicProvider()
            else:
                unconf_msg = "LLM NOT CONFIGURED — Please open Settings > Service Gateways to configure your provider API key."
                return await self._store_and_return_response(
                    user_id, conversation_id, unconf_msg, correlation_id, state=OrchestrationState.FAILED
                )

        # 3. PLANNING
        state = OrchestrationState.PLANNING
        tools_descriptors = self.tool_registry.list_tools()
        ai_response: AIResponse = await llm_client.generate(history, tools_descriptors)

        # 4. PERMISSION CHECK & APPROVAL GATE
        if ai_response.tool_call:
            state = OrchestrationState.PERMISSION_CHECK
            tool_plan = ai_response.tool_call
            tool = self.tool_registry.get(tool_plan.tool_name)

            if not tool:
                # Unknown tool fallback
                reply_text = f"My apologies sir, the requested directive '{tool_plan.tool_name}' is not in my safe tool catalog."
                return await self._store_and_return_response(user_id, conversation_id, reply_text, correlation_id)

            # Evaluate policy
            decision = await policy_engine.evaluate(user, tool, tool_plan.parameters, supplied_approval_id)

            if not decision.allowed and decision.requires_approval:
                state = OrchestrationState.AWAITING_APPROVAL
                # Generate summary for user confirmation
                summary = f"Authorize execution of {tool.name} with parameters: {json.dumps(tool_plan.parameters)}"
                app_req = await create_approval_request(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    tool_name=tool.name,
                    summary=summary,
                    parameters=tool_plan.parameters,
                    risk_level=decision.risk_level
                )

                await audit_logger.log_event(
                    event_type="APPROVAL_REQUESTED",
                    action="policy.approval_created",
                    user_id=user_id,
                    risk_level=decision.risk_level,
                    correlation_id=correlation_id,
                    details={"approval_id": app_req["id"], "tool": tool.name}
                )

                reply_text = f"Sir, executing directive '{tool.name}' requires explicit authorization (Risk: {decision.risk_level}). A confirmation request has been queued in your HUD."
                return await self._store_and_return_response(
                    user_id, conversation_id, reply_text, correlation_id,
                    approval_required=True, approval_request=app_req, state=state
                )

            elif not decision.allowed:
                # Denied unconditionally by policy
                reply_text = f"Action restricted by security protocol: {decision.reason}"
                return await self._store_and_return_response(user_id, conversation_id, reply_text, correlation_id, state=OrchestrationState.FAILED)

            # 5. EXECUTION
            state = OrchestrationState.EXECUTING
            start_time = time.time()
            context = {"user": user, "conversation_id": conversation_id}
            
            try:
                exec_result = await self.tool_registry.execute(tool_plan.tool_name, tool_plan.parameters, context)
                exec_duration = int((time.time() - start_time) * 1000)
                status = "success"
                error_msg = None
            except Exception as e:
                exec_duration = int((time.time() - start_time) * 1000)
                status = "failed"
                error_msg = str(e)
                exec_result = {"error": error_msg}

            # Record tool execution
            exec_id = str(uuid.uuid4())
            async with await get_db_connection() as db:
                await db.execute("""
                    INSERT INTO tool_executions (
                        id, conversation_id, user_id, tool_name, parameters_json, result_json, risk_level, execution_status, duration_ms, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    exec_id, conversation_id, user_id, tool_plan.tool_name,
                    json.dumps(tool_plan.parameters), json.dumps(exec_result),
                    tool.risk_level, status, exec_duration, time.strftime("%Y-%m-%d %H:%M:%S")
                ))
                await db.commit()

            await audit_logger.log_event(
                event_type="TOOL_EXECUTED",
                action=f"tool.{tool_plan.tool_name}",
                user_id=user_id,
                risk_level=tool.risk_level,
                correlation_id=correlation_id,
                details={"execution_id": exec_id, "status": status, "duration_ms": exec_duration}
            )

            # 6. Synthesize final response
            state = OrchestrationState.RESPONDING
            synthesis = self._synthesize_tool_outcome(tool_plan.tool_name, exec_result, tool_plan.parameters)
            return await self._store_and_return_response(
                user_id, conversation_id, synthesis, correlation_id,
                tool_executed={"tool": tool_plan.tool_name, "parameters": tool_plan.parameters, "result": exec_result},
                state=OrchestrationState.COMPLETED
            )

        # Pure conversational response
        state = OrchestrationState.COMPLETED
        return await self._store_and_return_response(
            user_id, conversation_id, ai_response.content or "All systems nominal, sir.", correlation_id, state=state
        )

    def _synthesize_tool_outcome(self, tool_name: str, result: Dict[str, Any], params: Dict[str, Any]) -> str:
        """Formats tool results into polite, crisp JARVIS responses."""
        if tool_name == "create_task":
            return f"Directive confirmed, sir. '{result.get('title')}' has been scheduled with {result.get('priority')} priority. Task ID: {result.get('task_id')[:8]}."

        if tool_name == "list_tasks":
            tasks = result.get("tasks", [])
            if not tasks:
                return "You currently have no outstanding directives in your task matrix, sir. All cleared."
            lines = [f"• [{t.get('priority', 'MED').upper()}] {t.get('title')} ({t.get('status')})" for t in tasks[:5]]
            return f"I have retrieved your active directives, sir:\n" + "\n".join(lines)

        if tool_name == "complete_task":
            if result.get("success"):
                return f"Directive marked as resolved, sir: '{result.get('title')}'. Telemetry updated."
            return f"Unable to resolve directive: {result.get('error', 'Task not found')}."

        if tool_name == "save_memory":
            return f"I have committed that to memory, sir: [{result.get('category')}] {result.get('key')} = {result.get('value')}."

        if tool_name == "list_memories":
            mems = result.get("memories", [])
            if not mems:
                return "No custom episodic memory facts are registered in the vault, sir."
            lines = [f"• [{m.get('category', 'Fact')}] {m.get('key')}: {m.get('value')}" for m in mems[:5]]
            return "Retrieved episodic memory archives, sir:\n" + "\n".join(lines)

        if tool_name == "get_market_demo_data":
            quotes = result.get("quotes", {})
            lines = [f"• {sym}: ${q.get('price')} ({q.get('change')})" for sym, q in quotes.items()]
            return f"Market telemetry feed online (SIMULATED ONLY):\n" + "\n".join(lines) + "\n\n*Notice: Financial markets simulated for demonstration purposes.*"

        if tool_name == "web_search_placeholder":
            query = result.get("query", "")
            results = result.get("results", [])
            lines = [f"• **{r.get('title')}** ({r.get('domain')})\n  {r.get('snippet')}" for r in results]
            return f"Intelligence search completed for '{query}':\n\n" + "\n\n".join(lines)

        if tool_name == "generate_research_brief":
            direct_ans = result.get("direct_answer", "")
            paras = result.get("brief_paragraphs", [])
            takeaway = result.get("takeaway", "")
            citations = result.get("citations", [])

            parts = []
            if direct_ans:
                parts.append(f"**Direct Answer:**\n{direct_ans}")
            if paras:
                parts.append("\n\n".join(paras))
            if takeaway:
                parts.append(f"**Takeaway:** {takeaway}")
            if citations:
                source_lines = [f"• [{c.get('id', idx)}] [{c.get('title')}]({c.get('url')}) — {c.get('publisher', 'Web')}" for idx, c in enumerate(citations[:4], 1)]
                parts.append("**Verified Sources:**\n" + "\n".join(source_lines))

            return "\n\n".join(parts) if parts else "Research synthesis generated successfully, sir."

        return f"Directive '{tool_name}' executed successfully, sir."


    async def _store_and_return_response(
        self,
        user_id: str,
        conversation_id: str,
        reply_text: str,
        correlation_id: str,
        approval_required: bool = False,
        approval_request: Optional[Dict[str, Any]] = None,
        tool_executed: Optional[Dict[str, Any]] = None,
        state: str = OrchestrationState.COMPLETED
    ) -> Dict[str, Any]:
        """Stores assistant reply in database and dispatches response object."""
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        reply_id = str(uuid.uuid4())

        async with await get_db_connection() as db:
            await db.execute("""
                INSERT INTO messages (id, conversation_id, user_id, role, content, created_at)
                VALUES (?, ?, ?, 'assistant', ?, ?)
            """, (reply_id, conversation_id, user_id, reply_text, now_str))
            await db.commit()

        await audit_logger.log_event(
            event_type="ASSISTANT_REPLIED",
            action="chat.reply_dispatched",
            user_id=user_id,
            correlation_id=correlation_id,
            details={"conversation_id": conversation_id, "reply_id": reply_id, "state": state}
        )

        return {
            "conversation_id": conversation_id,
            "message_id": reply_id,
            "response": reply_text,
            "approval_required": approval_required,
            "approval_request": approval_request,
            "tool_executed": tool_executed,
            "state": state
        }

orchestrator = AIOrchestrator()

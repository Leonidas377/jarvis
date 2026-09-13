# ==========================================================================
# JARVIS AI Provider Abstraction
# ==========================================================================

import re
import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import httpx
from server.config import settings
from server.ai.prompts import JARVIS_SYSTEM_PROMPT

class ToolCallPlan(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}
    rationale: Optional[str] = None

class AIResponse(BaseModel):
    content: Optional[str] = None
    tool_call: Optional[ToolCallPlan] = None
    model: str = "jarvis-local-engine"

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> AIResponse:
        """Generates a structured AI response or tool execution plan."""
        pass

# --------------------------------------------------------------------------
# Google Gemini API Provider (REST)
# --------------------------------------------------------------------------
class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> AIResponse:
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        payload: Dict[str, Any] = {
            "system_instruction": {
                "parts": [{"text": JARVIS_SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1024
            }
        }

        # Add function declarations if tools are provided
        if tools:
            func_declarations = []
            for t in tools:
                func_declarations.append({
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters_schema", {})
                })
            payload["tools"] = [{"function_declarations": func_declarations}]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.base_url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            candidates = data.get("candidates", [])
            if not candidates:
                return AIResponse(content="I was unable to synthesize a response, sir. All telemetry channels remain active.", model=self.model)

            first_part = candidates[0].get("content", {}).get("parts", [{}])[0]
            
            # Check for function call
            if "functionCall" in first_part:
                fc = first_part["functionCall"]
                return AIResponse(
                    tool_call=ToolCallPlan(
                        tool_name=fc.get("name", ""),
                        parameters=fc.get("args", {}),
                        rationale="Gemini function calling trigger"
                    ),
                    model=self.model
                )
            
            text_content = first_part.get("text", "")
            return AIResponse(content=text_content, model=self.model)
        except Exception as e:
            # Fall back safely to LocalDeterministicProvider if network/API fails
            fallback = LocalDeterministicProvider()
            res = await fallback.generate(messages, tools)
            res.content = f"{res.content}\n\n*(Note: Remote neural uplink unreachable [{str(e)[:40]}...]; seamlessly switched to local cognitive processor.)*"
            return res

# --------------------------------------------------------------------------
# Local Deterministic Provider (Offline-first, intelligent pattern processor)
# --------------------------------------------------------------------------
class LocalDeterministicProvider(BaseAIProvider):
    def __init__(self):
        self.model = "jarvis-cognitive-v1"

    async def generate(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> AIResponse:
        last_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_message = m.get("content", "").strip()
                break

        lowered = last_message.lower()

        # 1. Intent: Create Task / Directive
        task_match = re.search(r"(?:create|add|schedule|set|remind me to|new)\s+(?:task|directive|reminder)?\s*[:\-]?\s*(.+)", lowered, re.IGNORECASE)
        if any(w in lowered for w in ["create task", "add task", "new task", "remind me to", "schedule directive"]) or (task_match and "task" in lowered):
            title = task_match.group(1).strip() if task_match else last_message
            # Clean up words like "to " or "task " at start
            title = re.sub(r"^(?:task|directive|to)\s+", "", title, flags=re.IGNORECASE)
            title = title[:80].capitalize()
            priority = "high" if any(p in lowered for p in ["high", "urgent", "priority", "critical"]) else "medium"
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="create_task",
                    parameters={"title": title, "priority": priority, "due_date": "Today, 18:00"},
                    rationale=f"User requested directive creation for '{title}'"
                ),
                model=self.model
            )

        # 2. Intent: List Tasks / Directives
        if any(w in lowered for w in ["list task", "show task", "my tasks", "my directives", "view task", "what are my directives"]):
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="list_tasks",
                    parameters={},
                    rationale="User requested inventory of current active directives"
                ),
                model=self.model
            )

        # 3. Intent: Complete Task
        complete_match = re.search(r"(?:complete|finish|resolve|done with)\s+task\s+([a-zA-Z0-9\-]+)", lowered)
        if complete_match:
            task_id = complete_match.group(1).strip()
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="complete_task",
                    parameters={"task_id": task_id},
                    rationale=f"User requested completion of task {task_id}"
                ),
                model=self.model
            )

        # 4. Intent: Save Memory
        remember_match = re.search(r"(?:remember that|save preference|remember)\s*[:\-]?\s*(.+)", lowered, re.IGNORECASE)
        if remember_match and not any(w in lowered for w in ["do you remember", "what do you remember"]):
            raw_fact = remember_match.group(1).strip()
            parts = raw_fact.split("is", 1) if "is" in raw_fact else [raw_fact, "noted"]
            key = parts[0].strip().capitalize()
            value = parts[1].strip() if len(parts) > 1 else raw_fact
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="save_memory",
                    parameters={"category": "User Preferences", "key": key, "value": value},
                    rationale=f"User requested saving preference '{key}' into long-term memory"
                ),
                model=self.model
            )

        # 5. Intent: List Memories
        if any(w in lowered for w in ["show memories", "list memories", "what do you remember", "saved preferences", "recall"]):
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="list_memories",
                    parameters={},
                    rationale="User requested listing of episodic memory records"
                ),
                model=self.model
            )

        # 6. Intent: Market Telemetry / Quotes
        if any(w in lowered for w in ["market", "stock", "stocks", "nasdaq", "s&p", "btc", "bitcoin", "crypto", "nvda", "aapl"]):
            symbols = []
            if "nvda" in lowered or "nvidia" in lowered: symbols.append("NVDA")
            if "aapl" in lowered or "apple" in lowered: symbols.append("AAPL")
            if "btc" in lowered or "bitcoin" in lowered or "crypto" in lowered: symbols.append("BTC/USD")
            if "nasdaq" in lowered: symbols.append("NASDAQ")
            if not symbols:
                symbols = ["S&P 500", "NASDAQ", "NVDA", "BTC/USD"]
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="get_market_demo_data",
                    parameters={"symbols": symbols},
                    rationale="User requested financial market telemetry"
                ),
                model=self.model
            )

        # 7. Intent: Web Search / Research
        search_match = re.search(r"(?:search for|research|look up|find info on|google)\s*(.+)", lowered, re.IGNORECASE)
        if search_match:
            query = search_match.group(1).strip()
            return AIResponse(
                tool_call=ToolCallPlan(
                    tool_name="web_search_placeholder",
                    parameters={"query": query},
                    rationale=f"User requested research on '{query}'"
                ),
                model=self.model
            )

        # 8. Greetings, Status & Conversational Replies
        if any(w in lowered for w in ["hello", "hi", "hey", "good morning", "good evening", "greetings"]):
            return AIResponse(
                content="Good day, sir. All core subsystems are operating within nominal thresholds. How may I be of assistance today?",
                model=self.model
            )

        if any(w in lowered for w in ["who are you", "what are you", "your name"]):
            return AIResponse(
                content="I am J.A.R.V.I.S., your personal AI assistant and executive companion. I oversee task management, research telemetry, verified knowledge retention, and simulated market intelligence. At your service, sir.",
                model=self.model
            )

        if any(w in lowered for w in ["status", "diagnostics", "system report", "telemetry"]):
            return AIResponse(
                content="Diagnostic scan complete, sir. Neural orchestration latency: 12ms. Task scheduler: ACTIVE. Episodic memory bank: SECURE. Audit pipeline: SYNCHRONIZED. All systems are functioning at peak efficiency.",
                model=self.model
            )

        if any(w in lowered for w in ["thank you", "thanks", "good job", "well done"]):
            return AIResponse(
                content="Always a pleasure to be of service, sir. Let me know if you require anything further.",
                model=self.model
            )

        # Fallback general query synthesis
        return AIResponse(
            content=f"Understood, sir. I have processed your inquiry regarding: '{last_message}'. All directives and cognitive buffers remain aligned. You may command me to schedule tasks, query market telemetry, search research archives, or retain new parameters at your discretion.",
            model=self.model
        )

def get_ai_provider() -> BaseAIProvider:
    """Returns the configured AI Provider (Gemini if GEMINI_API_KEY is present, else Local deterministic)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and len(api_key.strip()) > 10:
        return GeminiProvider(api_key=api_key.strip())
    return LocalDeterministicProvider()

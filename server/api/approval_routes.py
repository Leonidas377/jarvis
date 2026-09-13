# ==========================================================================
# JARVIS Approval Workflow API Routes
# ==========================================================================

import time
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from server.auth.dependencies import get_optional_user
from server.models.schemas import ApprovalOut, ApprovalDecision
from server.permissions.approval_service import get_pending_approvals, decide_approval
from server.database import get_db_connection
from server.tools.registry import default_registry
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/approvals", tags=["Human Approvals"])

@router.get("", response_model=List[ApprovalOut])
async def list_pending_approvals(user: dict = Depends(get_optional_user)):
    items = await get_pending_approvals(user["id"])
    return [ApprovalOut(**item) for item in items]

@router.post("/{approval_id}/decide")
async def decide(approval_id: str, decision: ApprovalDecision, user: dict = Depends(get_optional_user)):
    success = await decide_approval(
        approval_id=approval_id,
        user_id=user["id"],
        action=decision.action,
        reason=decision.reason
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found, already decided, or expired.")

    await audit_logger.log_event(
        event_type=f"APPROVAL_{decision.action.upper()}",
        action=f"approval.{decision.action}",
        user_id=user["id"],
        resource_id=approval_id,
        details={"decision": decision.action, "reason": decision.reason}
    )

    return {"success": True, "approval_id": approval_id, "decision": decision.action}

@router.post("/{approval_id}/execute")
async def execute_approved(approval_id: str, user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, conversation_id, tool_name, parameters_json, risk_level, status, expires_at
            FROM approval_requests
            WHERE id = ? AND user_id = ?
        """, (approval_id, user_id))
        row = await cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")

        if row["status"] != "approved":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot execute request with status '{row['status']}'. It must be approved first.")

        if row["expires_at"] < now_str:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval request has expired.")

        tool_name = row["tool_name"]
        parameters = json.loads(row["parameters_json"])
        conv_id = row["conversation_id"]

    # Execute tool
    tool = default_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_name}' not available.")

    start_time = time.time()
    context = {"user": user, "conversation_id": conv_id}
    try:
        result = await default_registry.execute(tool_name, parameters, context)
        duration_ms = int((time.time() - start_time) * 1000)
        exec_status = "success"
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        exec_status = "failed"
        result = {"error": str(e)}

    # Mark approval request as executed
    async with get_db_connection() as db:
        await db.execute("UPDATE approval_requests SET status = 'executed' WHERE id = ?", (approval_id,))
        exec_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO tool_executions (
                id, conversation_id, user_id, tool_name, parameters_json, result_json, risk_level, execution_status, duration_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exec_id, conv_id, user_id, tool_name,
            json.dumps(parameters), json.dumps(result),
            tool.risk_level, exec_status, duration_ms, now_str
        ))
        await db.commit()

    await audit_logger.log_event(
        event_type="TOOL_EXECUTED_POST_APPROVAL",
        action=f"approval.execute.{tool_name}",
        user_id=user_id,
        risk_level=tool.risk_level,
        details={"approval_id": approval_id, "execution_status": exec_status}
    )

    return {
        "success": exec_status == "success",
        "approval_id": approval_id,
        "tool_name": tool_name,
        "result": result
    }

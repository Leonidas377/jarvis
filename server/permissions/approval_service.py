# ==========================================================================
# JARVIS Approval Service: Human-in-the-Loop Confirmation Lifecycle
# ==========================================================================

import uuid
import time
import json
from typing import Optional, Dict, Any, List
from server.database import get_db_connection

async def create_approval_request(
    user_id: str,
    conversation_id: Optional[str],
    tool_name: str,
    summary: str,
    parameters: Dict[str, Any],
    risk_level: str,
    ttl_seconds: int = 300
) -> Dict[str, Any]:
    """Creates a pending approval request with strict TTL expiration."""
    req_id = str(uuid.uuid4())
    now = int(time.time())
    expires = now + ttl_seconds
    created_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
    expires_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expires))

    params_json = json.dumps(parameters)

    async with await get_db_connection() as db:
        await db.execute("""
            INSERT INTO approval_requests (
                id, user_id, conversation_id, tool_name, summary, parameters_json, risk_level, status, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (req_id, user_id, conversation_id, tool_name, summary, params_json, risk_level, created_str, expires_str))
        await db.commit()

    return {
        "id": req_id,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "tool_name": tool_name,
        "summary": summary,
        "parameters": parameters,
        "risk_level": risk_level,
        "status": "pending",
        "created_at": created_str,
        "expires_at": expires_str
    }

async def get_pending_approvals(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves all active unexpired approval requests for a user."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
    async with await get_db_connection() as db:
        cursor = await db.execute("""
            SELECT id, user_id, conversation_id, tool_name, summary, parameters_json, risk_level, status, created_at, expires_at
            FROM approval_requests
            WHERE user_id = ? AND status = 'pending' AND expires_at > ?
            ORDER BY created_at DESC
        """, (user_id, now_str))
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["parameters"] = json.loads(d["parameters_json"])
            del d["parameters_json"]
            results.append(d)
        return results

async def decide_approval(approval_id: str, user_id: str, action: str, reason: Optional[str] = None) -> bool:
    """Marks an approval as approved or rejected."""
    new_status = "approved" if action == "approve" else "rejected"
    async with await get_db_connection() as db:
        cursor = await db.execute("""
            UPDATE approval_requests
            SET status = ?, rejection_reason = ?
            WHERE id = ? AND user_id = ? AND status = 'pending'
        """, (new_status, reason, approval_id, user_id))
        await db.commit()
        return cursor.rowcount > 0

async def verify_approval_unexpired(approval_id: str, user_id: str) -> bool:
    """Validates that an approval request was approved by the user and has not expired."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
    async with await get_db_connection() as db:
        cursor = await db.execute("""
            SELECT status, expires_at FROM approval_requests
            WHERE id = ? AND user_id = ?
        """, (approval_id, user_id))
        row = await cursor.fetchone()
        if not row:
            return False
        if row["status"] != "approved":
            return False
        return row["expires_at"] >= now_str

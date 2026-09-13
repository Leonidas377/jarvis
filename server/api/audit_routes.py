# ==========================================================================
# JARVIS Immutable Audit Log Query API Routes
# ==========================================================================

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.models.schemas import AuditEventOut

router = APIRouter(prefix="/api/audit", tags=["Audit & Transparency"])

@router.get("", response_model=List[AuditEventOut])
async def get_audit_logs(
    limit: int = Query(50, le=200),
    user: dict = Depends(get_optional_user)
):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, user_id, event_type, actor, resource_type, resource_id, summary, status, correlation_id, timestamp
            FROM audit_events
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user["id"], limit))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

# ==========================================================================
# JARVIS Immutable Audit Logging
# ==========================================================================

import uuid
import time
import json
from typing import Optional, Dict, Any
from server.database import get_db_connection

async def record_audit_event(
    user_id: str,
    event_type: str,
    actor: str,
    resource_type: str,
    summary: str,
    status: str = "success",
    resource_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> str:
    """Records a sanitized, immutable audit log entry scoped to the user."""
    event_id = str(uuid.uuid4())
    cid = correlation_id or str(uuid.uuid4())
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))

    # Sanitize summary against credentials
    sanitized_summary = summary.replace("password", "p*****d").replace("secret", "s****t")

    async with await get_db_connection() as db:
        await db.execute("""
            INSERT INTO audit_events (
                id, user_id, event_type, actor, resource_type, resource_id, summary, status, correlation_id, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, user_id, event_type, actor, resource_type, resource_id, sanitized_summary, status, cid, ts))
        await db.commit()

    return event_id

class AuditLogger:
    @staticmethod
    async def log_event(
        event_type: str,
        action: str,
        user_id: str,
        correlation_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> str:
        summary_str = f"[{action}] " + (json.dumps(details) if details else "")
        return await record_audit_event(
            user_id=user_id,
            event_type=event_type,
            actor="jarvis-system",
            resource_type=action.split(".")[0] if "." in action else "general",
            summary=summary_str,
            status=status,
            resource_id=resource_id,
            correlation_id=correlation_id
        )

audit_logger = AuditLogger()

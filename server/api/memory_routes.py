# ==========================================================================
# JARVIS Episodic Memory API Routes
# ==========================================================================

import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.models.schemas import MemoryCreate, MemoryOut
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/memories", tags=["Episodic Memory"])

@router.get("", response_model=List[MemoryOut])
async def list_memories(q: Optional[str] = Query(None), user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    query = "SELECT id, user_id, category, key, value, user_approved, created_at, updated_at FROM memories WHERE user_id = ?"
    args = [user_id]
    if q:
        query += " AND (key LIKE ? OR value LIKE ?)"
        pattern = f"%{q}%"
        args.extend([pattern, pattern])
    query += " ORDER BY updated_at DESC"

    async with get_db_connection() as db:
        cur = await db.execute(query, tuple(args))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

@router.post("", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
async def create_memory(mem_in: MemoryCreate, user: dict = Depends(get_optional_user)):
    mem_id = str(uuid.uuid4())
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO memories (id, user_id, category, key, value, user_approved, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (mem_id, user["id"], mem_in.category, mem_in.key, mem_in.value, now_str, now_str))
        await db.commit()

    await audit_logger.log_event(
        event_type="MEMORY_SAVED",
        action="memory.save",
        user_id=user["id"],
        resource_id=mem_id,
        details={"category": mem_in.category, "key": mem_in.key}
    )

    return MemoryOut(
        id=mem_id,
        user_id=user["id"],
        category=mem_in.category,
        key=mem_in.key,
        value=mem_in.value,
        user_approved=True,
        created_at=now_str,
        updated_at=now_str
    )

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (memory_id, user["id"]))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory entry not found.")

    await audit_logger.log_event(
        event_type="MEMORY_DELETED",
        action="memory.delete",
        user_id=user["id"],
        resource_id=memory_id
    )

    return {"success": True, "message": f"Episodic memory record '{memory_id}' deleted."}

# ==========================================================================
# JARVIS Task & Directive Management API Routes
# ==========================================================================

import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.models.schemas import TaskCreate, TaskUpdate, TaskOut
from server.audit.logger import audit_logger

router = APIRouter(prefix="/api/tasks", tags=["Directives & Tasks"])

@router.get("", response_model=List[TaskOut])
async def list_tasks(status_filter: Optional[str] = Query(None, alias="status"), user: dict = Depends(get_optional_user)):
    user_id = user["id"]
    query = """
        SELECT id, user_id, title, description, priority, category, status, progress, due_date, created_at, updated_at
        FROM tasks
        WHERE user_id = ?
    """
    args = [user_id]
    if status_filter:
        query += " AND status = ?"
        args.append(status_filter)
    query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC"

    async with get_db_connection() as db:
        cur = await db.execute(query, tuple(args))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(task_in: TaskCreate, user: dict = Depends(get_optional_user)):
    task_id = str(uuid.uuid4())
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO tasks (
                id, user_id, title, description, priority, category, status, progress, due_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', 0, ?, ?, ?)
        """, (
            task_id, user["id"], task_in.title, task_in.description or "",
            task_in.priority or "medium", task_in.category or "general",
            task_in.due_date or "Tomorrow", now_str, now_str
        ))
        await db.commit()

    await audit_logger.log_event(
        event_type="TASK_CREATED",
        action="task.create",
        user_id=user["id"],
        resource_id=task_id,
        details={"title": task_in.title, "priority": task_in.priority}
    )

    return TaskOut(
        id=task_id,
        user_id=user["id"],
        title=task_in.title,
        description=task_in.description or "",
        priority=task_in.priority or "medium",
        category=task_in.category or "general",
        status="active",
        progress=0,
        due_date=task_in.due_date or "Tomorrow",
        created_at=now_str,
        updated_at=now_str
    )

@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, updates: TaskUpdate, user: dict = Depends(get_optional_user)):
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        cur = await db.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directive not found.")

        current = dict(row)
        title = updates.title if updates.title is not None else current["title"]
        description = updates.description if updates.description is not None else current["description"]
        priority = updates.priority if updates.priority is not None else current["priority"]
        category = updates.category if updates.category is not None else current["category"]
        t_status = updates.status if updates.status is not None else current["status"]
        progress = updates.progress if updates.progress is not None else current["progress"]
        due_date = updates.due_date if updates.due_date is not None else current["due_date"]

        await db.execute("""
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, category = ?, status = ?, progress = ?, due_date = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (title, description, priority, category, t_status, progress, due_date, now_str, task_id, user["id"]))
        await db.commit()

    return TaskOut(
        id=task_id,
        user_id=user["id"],
        title=title,
        description=description,
        priority=priority,
        category=category,
        status=t_status,
        progress=progress,
        due_date=due_date,
        created_at=current["created_at"],
        updated_at=now_str
    )

@router.delete("/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["id"]))
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directive not found.")

    await audit_logger.log_event(
        event_type="TASK_DELETED",
        action="task.delete",
        user_id=user["id"],
        resource_id=task_id
    )

    return {"success": True, "message": f"Directive '{task_id}' removed from schedule."}

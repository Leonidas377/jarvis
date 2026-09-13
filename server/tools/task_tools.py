# ==========================================================================
# JARVIS Task Management Tools
# ==========================================================================

import uuid
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from server.tools.base import BaseTool
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope
from server.database import get_db_connection

# --- Create Task Tool ---
class CreateTaskInput(BaseModel):
    title: str = Field(..., description="The title or objective of the directive")
    description: Optional[str] = Field("", description="Optional details or instructions")
    priority: Optional[str] = Field("medium", description="Priority level: high, medium, low")
    due_date: Optional[str] = Field("Tomorrow", description="Target completion window")

class CreateTaskTool(BaseTool):
    name = "create_task"
    version = "1.0.0"
    description = "Creates a personal task or directive in the user's task matrix."
    risk_level = RiskLevel.R1_LOW.value
    required_scope = Scope.TASK_WRITE.value
    requires_confirmation = False
    input_schema = CreateTaskInput

    async def execute(self, params: CreateTaskInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user"]["id"]
        task_id = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        async with await get_db_connection() as db:
            await db.execute("""
                INSERT INTO tasks (
                    id, user_id, title, description, priority, category, status, progress, due_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'general', 'active', 0, ?, ?, ?)
            """, (task_id, user_id, params.title, params.description, params.priority, params.due_date, now, now))
            await db.commit()

        return {
            "task_id": task_id,
            "title": params.title,
            "priority": params.priority,
            "status": "active",
            "due_date": params.due_date,
            "summary": f"Directive '{params.title}' registered in the task scheduler."
        }

# --- List Tasks Tool ---
class ListTasksInput(BaseModel):
    status_filter: Optional[str] = Field(None, description="Optional status filter: active, completed, or scheduled")

class ListTasksTool(BaseTool):
    name = "list_tasks"
    version = "1.0.0"
    description = "Retrieves the authenticated user's current tasks and directives."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.TASK_READ.value
    requires_confirmation = False
    input_schema = ListTasksInput

    async def execute(self, params: ListTasksInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user"]["id"]
        query = "SELECT id, title, description, priority, category, status, progress, due_date, created_at FROM tasks WHERE user_id = ?"
        args = [user_id]

        if params.status_filter:
            query += " AND status = ?"
            args.append(params.status_filter)

        query += " ORDER BY created_at DESC;"

        async with await get_db_connection() as db:
            cursor = await db.execute(query, tuple(args))
            rows = await cursor.fetchall()
            tasks = [dict(r) for r in rows]

        return {
            "total_count": len(tasks),
            "tasks": tasks
        }

# --- Complete Task Tool ---
class CompleteTaskInput(BaseModel):
    task_id: str = Field(..., description="The ID of the task to mark as completed")

class CompleteTaskTool(BaseTool):
    name = "complete_task"
    version = "1.0.0"
    description = "Marks a specific user directive as completed."
    risk_level = RiskLevel.R1_LOW.value
    required_scope = Scope.TASK_WRITE.value
    requires_confirmation = False
    input_schema = CompleteTaskInput

    async def execute(self, params: CompleteTaskInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user"]["id"]
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        async with await get_db_connection() as db:
            cursor = await db.execute("""
                UPDATE tasks
                SET status = 'completed', progress = 100, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (now, params.task_id, user_id))
            await db.commit()

            if cursor.rowcount == 0:
                return {"success": False, "error": f"Task '{params.task_id}' not found."}

        return {
            "success": True,
            "task_id": params.task_id,
            "status": "completed",
            "summary": f"Task '{params.task_id}' marked as completed."
        }

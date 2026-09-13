# ==========================================================================
# JARVIS Explicit Memory Tools
# ==========================================================================

import uuid
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from server.tools.base import BaseTool
from server.models.schemas import RiskLevel
from server.permissions.scopes import Scope
from server.database import get_db_connection

# --- Save Memory Tool (Medium Risk: requires explicit confirmation) ---
class SaveMemoryInput(BaseModel):
    category: str = Field("General", description="Category: Identity, Communication, Research, Trading Limits")
    key: str = Field(..., description="Short key or subject of the memory")
    value: str = Field(..., description="Fact or preference details to remember")

class SaveMemoryTool(BaseTool):
    name = "save_memory"
    version = "1.0.0"
    description = "Saves an explicit user-approved fact or preference to episodic memory."
    risk_level = RiskLevel.R2_MEDIUM.value
    required_scope = Scope.MEMORY_WRITE.value
    requires_confirmation = True
    input_schema = SaveMemoryInput

    async def execute(self, params: SaveMemoryInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user"]["id"]
        mem_id = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        async with await get_db_connection() as db:
            await db.execute("""
                INSERT INTO memories (
                    id, user_id, category, key, value, user_approved, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (mem_id, user_id, params.category, params.key, params.value, now, now))
            await db.commit()

        return {
            "memory_id": mem_id,
            "category": params.category,
            "key": params.key,
            "value": params.value,
            "summary": f"Saved preference '{params.key}' to episodic memory."
        }

# --- List Memories Tool (Safe: R0) ---
class ListMemoriesInput(BaseModel):
    query: Optional[str] = Field(None, description="Optional search filter for memory facts")

class ListMemoriesTool(BaseTool):
    name = "list_memories"
    version = "1.0.0"
    description = "Retrieves user-approved memories and saved preferences."
    risk_level = RiskLevel.R0_SAFE.value
    required_scope = Scope.MEMORY_READ.value
    requires_confirmation = False
    input_schema = ListMemoriesInput

    async def execute(self, params: ListMemoriesInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user"]["id"]
        query = "SELECT id, category, key, value, updated_at FROM memories WHERE user_id = ?"
        args = [user_id]

        if params.query:
            query += " AND (key LIKE ? OR value LIKE ?)"
            pattern = f"%{params.query}%"
            args.extend([pattern, pattern])

        query += " ORDER BY updated_at DESC;"

        async with await get_db_connection() as db:
            cursor = await db.execute(query, tuple(args))
            rows = await cursor.fetchall()
            memories = [dict(r) for r in rows]

        return {
            "total_count": len(memories),
            "memories": memories
        }

# --- Delete Memory Tool (High Risk: R3) ---
class DeleteMemoryInput(BaseModel):
    memory_id: str = Field(..., description="ID of the memory entry to permanently purge")

class DeleteMemoryTool(BaseTool):
    name = "delete_memory"
    version = "1.0.0"
    description = "Permanently removes a fact from episodic memory."
    risk_level = RiskLevel.R3_HIGH.value
    required_scope = Scope.MEMORY_WRITE.value
    requires_confirmation = True
    input_schema = DeleteMemoryInput

    async def execute(self, params: DeleteMemoryInput, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user"]["id"]

        async with await get_db_connection() as db:
            cursor = await db.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (params.memory_id, user_id))
            await db.commit()

            if cursor.rowcount == 0:
                return {"success": False, "error": f"Memory item '{params.memory_id}' not found."}

        return {
            "success": True,
            "memory_id": params.memory_id,
            "summary": f"Memory item '{params.memory_id}' permanently purged."
        }

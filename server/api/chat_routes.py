# ==========================================================================
# JARVIS Chat & Dialogue API Routes
# ==========================================================================

import uuid
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from server.auth.dependencies import get_optional_user
from server.database import get_db_connection
from server.ai.orchestrator import orchestrator
from server.models.schemas import ConversationOut, MessageOut

router = APIRouter(prefix="/api", tags=["Chat & Conversations"])

class ChatRequest(BaseModel):
    content: str
    conversation_id: Optional[str] = None
    approval_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    approval_required: bool = False
    approval_request: Optional[Dict[str, Any]] = None
    tool_executed: Optional[Dict[str, Any]] = None
    state: str = "COMPLETED"

@router.post("/chat", response_model=ChatResponse)
async def chat_interaction(payload: ChatRequest, user: dict = Depends(get_optional_user)):
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

    result = await orchestrator.process_message(
        user=user,
        content=payload.content.strip(),
        conversation_id=payload.conversation_id,
        supplied_approval_id=payload.approval_id
    )

    return ChatResponse(**result)

@router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, user_id, title, mode, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user["id"],))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(title: Optional[str] = "Directive Session", user: dict = Depends(get_optional_user)):
    conv_id = str(uuid.uuid4())
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO conversations (id, user_id, title, mode, created_at, updated_at)
            VALUES (?, ?, ?, 'assistant', ?, ?)
        """, (conv_id, user["id"], title, now_str, now_str))
        await db.commit()

    return ConversationOut(
        id=conv_id,
        user_id=user["id"],
        title=title,
        mode="assistant",
        created_at=now_str,
        updated_at=now_str
    )

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
async def get_conversation_messages(conversation_id: str, user: dict = Depends(get_optional_user)):
    async with get_db_connection() as db:
        cur = await db.execute("""
            SELECT id, conversation_id, user_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

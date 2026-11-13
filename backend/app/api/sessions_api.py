"""Session Management API Endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.conversation import conversation_manager, Session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Conversation"


@router.get("")
async def list_sessions():
    """Retrieve all available conversation sessions."""
    return {"sessions": conversation_manager.list_sessions()}


@router.post("")
async def create_session(request: CreateSessionRequest):
    """Spawn a new conversation session."""
    session = conversation_manager.create_session(title=request.title or "New Conversation")
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Retrieve the full history of a given session."""
    if session_id not in conversation_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    session: Session = conversation_manager.active_sessions[session_id]
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "metadata": m.metadata,
            }
            for m in session.messages
        ],
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session from memory and disk."""
    success = conversation_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "deleted_id": session_id}


@router.post("/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear all messages from an active session."""
    success = conversation_manager.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "cleared_id": session_id}

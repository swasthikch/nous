"""Chat and Conversation API Endpoints powered by NOUS AI Brain."""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.ai_engine import ai_brain, AIEngineResponse
from backend.app.core.ollama_client import ollama_client
from backend.app.core.cloud_provider import cloud_provider
from backend.app.config import settings

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message input")
    session_id: Optional[str] = Field(None, description="Active conversation session ID")
    model: Optional[str] = Field(None, description="Optional model override")


@router.get("/models")
async def list_models():
    """Retrieve locally available and cloud models."""
    ollama_info = await ollama_client.check_connection()
    cloud_status = await cloud_provider.check_health()

    return {
        "status": ollama_info.get("status"),
        "active_model": settings.OLLAMA_MODEL,
        "available_models": ollama_info.get("available_models", []),
        "available_local_models": ollama_info.get("available_models", []),
        "cloud_provider": {
            "enabled": cloud_provider.enabled,
            "configured": cloud_provider.is_configured(),
            "provider_name": cloud_provider.provider_name,
            "model": cloud_provider.model,
            "status": cloud_status.get("status"),
        },
    }


@router.post("/chat", response_model=AIEngineResponse)
async def chat_endpoint(request: ChatRequest):
    """Process a user message through the central NOUS AI Brain."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        response: AIEngineResponse = await ai_brain.process(
            message=request.message,
            session_id=request.session_id,
            requested_model=request.model,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Brain error: {str(e)}")

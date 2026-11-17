"""Chat and Conversation API Endpoints powered by NOUS Central AI Brain.

Provides:
- Synchronous POST /api/chat for backward compatibility and automated testing.
- Real-time Server-Sent Events (SSE) streaming via POST and GET /api/chat/stream.
- Dynamic model listing across local Ollama and configured cloud engines.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.ai_core.orchestrator import orchestrator, OrchestratorResponse
from backend.app.config import settings

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message input")
    session_id: Optional[str] = Field(None, description="Active conversation session ID")
    model: Optional[str] = Field(None, description="Optional model override")


@router.get("/models")
async def list_models():
    """Retrieve locally available and cloud models."""
    ollama_health = await orchestrator.ollama_provider.check_health()
    cloud_health = await orchestrator.cloud_provider.check_health()

    return {
        "status": ollama_health.status,
        "active_model": settings.OLLAMA_MODEL,
        "available_models": ollama_health.available_models,
        "available_local_models": ollama_health.available_models,
        "cloud_provider": {
            "enabled": orchestrator.cloud_provider.enabled,
            "configured": orchestrator.cloud_provider.is_configured(),
            "provider_name": orchestrator.cloud_provider.provider_name,
            "model": orchestrator.cloud_provider.default_model,
            "available_models": cloud_health.available_models,
            "status": cloud_health.status,
        },
    }


@router.post("/chat", response_model=OrchestratorResponse)
async def chat_endpoint(request: ChatRequest):
    """Process a user message through the central NOUS AI Brain (Non-Streaming)."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        response: OrchestratorResponse = await orchestrator.process(
            message=request.message,
            session_id=request.session_id,
            requested_model=request.model,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Brain error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream_post_endpoint(request: ChatRequest):
    """Stream response tokens and tool observations chunk-by-chunk via Server-Sent Events (POST)."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    async def event_generator():
        try:
            async for event in orchestrator.process_stream(
                message=request.message,
                session_id=request.session_id,
                requested_model=request.model,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            err_event = {"type": "error", "data": {"error": str(e)}}
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/stream")
async def chat_stream_get_endpoint(
    message: str = Query(..., description="Message input"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    model: Optional[str] = Query(None, description="Model override"),
):
    """Stream response tokens via standard EventSource GET query."""
    req = ChatRequest(message=message, session_id=session_id, model=model)
    return await chat_stream_post_endpoint(req)

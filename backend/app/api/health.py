"""Health Check and System Diagnostics Endpoint."""

import os
import platform
import time
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.core.ollama_client import ollama_client

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Returns the operational status of NOUS, system details, and Ollama connection."""
    ollama_status = await ollama_client.check_connection()

    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": time.time(),
        "system": {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "cpu_model": "13th Gen Intel(R) Core(TM) i5-1334U",
            "logical_cores": os.cpu_count() or 12,
            "python_version": platform.python_version(),
        },
        "ai_engine": {
            "provider": "ollama (local)",
            "base_url": settings.OLLAMA_BASE_URL,
            "configured_model": settings.OLLAMA_MODEL,
            "connection_status": ollama_status.get("status"),
            "available_models": ollama_status.get("available_models", []),
            "model_ready": ollama_status.get("configured_model_available", False),
            "detail": ollama_status.get("detail"),
        },
    }

"""Health Check and System Diagnostics Endpoint."""

import os
import platform
import time
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.core.ollama_client import ollama_client
from backend.app.providers.cloud_provider import CloudModelProvider

router = APIRouter(prefix="/api", tags=["health"])
_cloud_provider = CloudModelProvider()


@router.get("/health")
async def health_check():
    """Returns the operational status of NOUS, system details, and Ollama connection."""
    ollama_status = await ollama_client.check_connection()
    is_ollama_connected = ollama_status.get("status") == "connected"
    is_cloud_configured = _cloud_provider.is_configured()

    if is_ollama_connected:
        engine_provider = "ollama (local)"
        engine_base_url = settings.OLLAMA_BASE_URL
        configured_model = settings.OLLAMA_MODEL
        connection_status = "connected"
        active_runtime = "local"
    elif is_cloud_configured:
        engine_provider = f"{_cloud_provider.provider_name} (cloud)"
        engine_base_url = _cloud_provider.base_url
        configured_model = _cloud_provider.default_model
        connection_status = "connected"
        active_runtime = "cloud"
    else:
        engine_provider = "ollama (local)"
        engine_base_url = settings.OLLAMA_BASE_URL
        configured_model = settings.OLLAMA_MODEL
        connection_status = ollama_status.get("status", "disconnected")
        active_runtime = "none"

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
            "provider": engine_provider,
            "base_url": engine_base_url,
            "configured_model": configured_model,
            "connection_status": connection_status,
            "active_runtime": active_runtime,
            "available_models": ollama_status.get("available_models", []),
            "model_ready": is_ollama_connected or is_cloud_configured,
            "detail": ollama_status.get("detail"),
            "ollama_status": ollama_status.get("status", "disconnected"),
            "cloud": {
                "enabled": _cloud_provider.enabled,
                "configured": is_cloud_configured,
                "provider": _cloud_provider.provider_name,
                "model": _cloud_provider.default_model,
            },
        },
    }

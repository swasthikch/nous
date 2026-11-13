"""Routing and Tool Introspection API Endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.model_router import model_router, RoutingMode
from backend.app.core.cloud_provider import cloud_provider
from backend.app.core.tool_registry import tool_registry

router = APIRouter(prefix="/api/routing", tags=["routing"])


class SetModeRequest(BaseModel):
    mode: RoutingMode = Field(..., description="'local', 'cloud', or 'hybrid'")


@router.get("")
async def get_routing_status():
    """Retrieve current routing configuration, cloud status, and registered tools."""
    return {
        "active_mode": model_router.mode.value,
        "cloud_provider": {
            "name": cloud_provider.provider_name,
            "configured": cloud_provider.is_configured(),
            "model": cloud_provider.model,
        },
        "registered_tools_count": len(tool_registry._tools),
    }


@router.post("/mode")
async def set_routing_mode(request: SetModeRequest):
    """Change the operational routing mode."""
    model_router.set_mode(request.mode)
    return {
        "success": True,
        "new_mode": model_router.mode.value,
    }


@router.get("/tools")
async def list_registered_tools():
    """List all registered tools, their parameters, and risk classifications."""
    return {"tools": tool_registry.get_tool_definitions()}

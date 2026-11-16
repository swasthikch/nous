"""Tool System & Approval Management API Endpoints for NOUS."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.tools.registry import safe_tool_registry
from backend.app.tools.approval import approval_manager, ApprovalRequest
from backend.app.tools.logger import tool_logger

router = APIRouter(prefix="/api/tools", tags=["tools"])


class DecisionRequest(BaseModel):
    reason: Optional[str] = Field("User confirmed", description="Reason for decision")


@router.get("")
async def list_registered_tools():
    """List all registered tools, descriptions, parameter schemas, and permission levels."""
    defs = safe_tool_registry.get_tool_definitions()
    return {
        "count": len(defs),
        "tools": defs,
    }


@router.get("/approvals")
async def list_pending_approvals():
    """Retrieve all pending cryptographic approval requests."""
    pending = approval_manager.list_pending()
    return {
        "count": len(pending),
        "approvals": [p.model_dump() for p in pending],
    }


@router.get("/approvals/{token}")
async def get_approval_request(token: str):
    """Inspect a specific approval request token."""
    req = approval_manager.get_request(token)
    if not req:
        raise HTTPException(status_code=404, detail="Approval token not found.")
    return req.model_dump()


@router.post("/approvals/{token}/approve")
async def approve_tool_action(token: str):
    """Approve a pending tool action."""
    ok, req, msg = approval_manager.approve_token(token)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "request": req.model_dump() if req else None,
    }


@router.post("/approvals/{token}/reject")
async def reject_tool_action(token: str, body: DecisionRequest):
    """Reject a pending tool action."""
    ok, req, msg = approval_manager.reject_token(token, reason=body.reason or "Declined by user")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "request": req.model_dump() if req else None,
    }


@router.post("/approvals/{token}/cancel")
async def cancel_tool_action(token: str):
    """Cancel an in-flight or pending tool action."""
    ok = approval_manager.cancel_tool(token)
    if not ok:
        raise HTTPException(status_code=404, detail="Token not found.")
    return {"success": True, "message": "Action cancelled successfully."}


@router.get("/logs")
async def get_tool_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    tool_name: Optional[str] = None,
):
    """Retrieve immutable tool execution audit logs."""
    logs = tool_logger.get_logs(limit=limit, tool_name=tool_name)
    return {
        "count": len(logs),
        "logs": [l.model_dump() for l in logs],
    }

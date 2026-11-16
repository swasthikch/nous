"""Cloud Persistence & Free-Tier Keep-Alive REST API for NOUS (Phase 11).

Endpoints:
- GET  /api/cloud/status: Database metrics, snapshots, and pinger health.
- POST /api/cloud/snapshot: Trigger on-demand state backup with WAL checkpointing.
- POST /api/cloud/restore: Restore database state from snapshot archive.
- POST /api/cloud/keepalive/ping: Execute single keepalive probe.
- POST /api/cloud/keepalive/toggle: Start/Stop continuous keepalive worker.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.cloud.persistence import cloud_persistence
from backend.app.cloud.keepalive import keepalive_pinger

router = APIRouter(prefix="/api/cloud", tags=["Cloud Persistence & Deployment"])


class RestoreRequest(BaseModel):
    snapshot_name: Optional[str] = Field(default=None, description="Specific snapshot filename or latest")


class KeepAliveToggleRequest(BaseModel):
    enable: bool = Field(..., description="Enable or disable continuous pinger")
    target_url: Optional[str] = Field(default=None, description="Custom target URL to keep alive")


@router.get("/status")
async def get_cloud_status():
    """Retrieve database metrics, backup statistics, and keepalive pinger state."""
    persistence_info = cloud_persistence.get_status()
    pinger_info = keepalive_pinger.get_stats()

    return {
        "status": "operational",
        "persistence": persistence_info,
        "keepalive_pinger": pinger_info,
    }


@router.post("/snapshot")
async def create_database_snapshot(name: Optional[str] = Query(default=None)):
    """Flush WAL caches and generate a compressed tar.gz snapshot of all databases."""
    try:
        archive_path = cloud_persistence.create_snapshot(snapshot_name=name)
        return {
            "success": True,
            "archive_name": archive_path.name,
            "size_bytes": archive_path.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.post("/restore")
async def restore_database_snapshot(req: Optional[RestoreRequest] = None):
    """Restore database files from an existing snapshot."""
    archive_name = req.snapshot_name if req else None
    path = cloud_persistence.backup_dir / archive_name if archive_name else None
    res = cloud_persistence.restore_snapshot(path)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("message", "Restore failed"))
    return res


@router.post("/keepalive/ping")
async def trigger_keepalive_ping():
    """Execute a single keepalive probe immediately."""
    result = await keepalive_pinger.ping_once()
    return result


@router.post("/keepalive/toggle")
async def toggle_keepalive_pinger(req: KeepAliveToggleRequest):
    """Start or stop the background keepalive worker."""
    if req.target_url:
        keepalive_pinger.target_url = req.target_url

    if req.enable:
        keepalive_pinger.start()
        return {"success": True, "message": f"Keepalive pinger started targeting '{keepalive_pinger.target_url}'"}
    else:
        keepalive_pinger.stop()
        return {"success": True, "message": "Keepalive pinger stopped"}

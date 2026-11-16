"""Desktop Companion Backend API for NOUS (Phase 6).

Coordinates:
- Receiving outbound heartbeats with Windows 11 hardware telemetry.
- Tracking laptop online/offline state and battery power.
- Exposing live laptop compute status to dashboard & model router.
- Autostart management.
"""

from __future__ import annotations

import time
from typing import Any, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from desktop.telemetry import WindowsHardwareReport, windows_telemetry
from desktop.autostart import autostart_manager

router = APIRouter(prefix="/api/desktop", tags=["Desktop Companion"])

# Global memory cache for the active connected laptop
_active_laptop_state: dict[str, Any] = {
    "is_connected": False,
    "last_heartbeat": 0.0,
    "report": None,
    "ip_address": None,
}


@router.post("/heartbeat")
async def receive_heartbeat(
    report: WindowsHardwareReport,
    authorization: Optional[str] = Header(None),
):
    """Receive periodic telemetry heartbeat from the Windows 11 Desktop Companion."""
    now = time.time()
    _active_laptop_state["is_connected"] = True
    _active_laptop_state["last_heartbeat"] = now
    _active_laptop_state["report"] = report.model_dump()

    return {
        "status": "acknowledged",
        "server_time": now,
        "ollama_relay_enabled": report.ollama_online,
        "models_available": report.ollama_models,
    }


@router.get("/status")
async def get_desktop_status():
    """Retrieve current laptop hardware metrics, connection status, and battery."""
    now = time.time()
    last_hb = _active_laptop_state["last_heartbeat"]
    elapsed = now - last_hb if last_hb > 0 else 999999.0

    # Consider connected if heartbeat received within 45 seconds, OR if running locally on Windows
    is_live = elapsed < 45.0
    current_report = _active_laptop_state["report"]

    # If companion has not sent a heartbeat yet but server is on Windows, fetch live local telemetry
    if not current_report and windows_telemetry.is_windows:
        local_report = windows_telemetry.get_telemetry()
        current_report = local_report.model_dump()
        is_live = True

    return {
        "is_connected": is_live,
        "last_seen_seconds_ago": round(elapsed, 1) if last_hb > 0 else None,
        "telemetry": current_report,
        "autostart_installed": autostart_manager.is_autostart_installed(),
    }


@router.post("/autostart/install")
async def install_autostart():
    """Register silent autostart on Windows logon."""
    res = autostart_manager.install()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error"))
    return res


@router.post("/autostart/uninstall")
async def uninstall_autostart():
    """Remove silent autostart on Windows logon."""
    res = autostart_manager.uninstall()
    return res

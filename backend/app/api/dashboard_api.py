"""Unified Personal AI OS Dashboard & Management API for NOUS (Phase 7).

Coordinates:
- Executive Overview Dashboard telemetry aggregation.
- Graphical Workspace File Explorer (browse, inspect, safe edit, traversal defense).
- Unified System Settings & Configuration (masked API keys, model routing, voice).
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path
import time
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.tools.approval import approval_manager, ApprovalRequest
from backend.app.memory.manager import memory_manager
from backend.app.memory.models import MemoryTier
from backend.app.agents.coordinator import agent_coordinator
from desktop.telemetry import windows_telemetry

router = APIRouter(prefix="/api/dashboard", tags=["OS Dashboard & Modules"])

WORKSPACE_DIR = settings.WORKSPACE_DIR.resolve()


def _resolve_safe_path(rel_path: str) -> Path:
    """Ensure path stays within workspace boundary."""
    clean = rel_path.lstrip("/\\")
    target = (WORKSPACE_DIR / clean).resolve()
    try:
        target.relative_to(WORKSPACE_DIR)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail=f"Security Sandbox Violation: Path '{rel_path}' attempts to escape workspace.",
        )
    return target


# ---------------- 1. EXECUTIVE OVERVIEW DASHBOARD ----------------

@router.get("/overview")
async def get_dashboard_overview():
    """Aggregate complete OS state for the executive dashboard in a single call."""
    now = time.time()

    # A. Hardware Telemetry
    telemetry = windows_telemetry.get_telemetry()

    # B. Pending HITL Approval Requests
    pending_approvals = approval_manager.list_pending()

    # C. Memory 5-Tier Breakdown
    all_mem = memory_manager.list_memories(limit=500)
    tier_counts = {t.value: 0 for t in MemoryTier}
    for m in all_mem:
        tier_counts[m.tier.value] += 1

    # D. Active Agents
    agents = agent_coordinator.list_agents()

    # E. Routine Today Snapshot
    today_str = datetime.date.today().isoformat()
    try:
        from backend.app.routine.manager import RoutineManager
        routine_mgr = RoutineManager()
        activities = routine_mgr.list_activities(today_str)
        completed = [a for a in activities if a.status.value == "completed"]
        pending = [a for a in activities if a.status.value != "completed"]
        next_task = pending[0].name if pending else "No pending commitments"
        routine_stats = {
            "total": len(activities),
            "completed": len(completed),
            "pending": len(pending),
            "next_task": next_task,
        }
    except Exception:
        routine_stats = {"total": 0, "completed": 0, "pending": 0, "next_task": "None scheduled"}

    # F. Market Briefing Snapshot
    try:
        from backend.app.market.fetcher import MarketDataFetcher
        fetcher = MarketDataFetcher()
        nifty = fetcher.fetch_quote("^NSEI")
        flows = fetcher.get_fii_dii_flows()
        market_data = {
            "nifty_price": nifty.get("price", 25150.0),
            "nifty_change": nifty.get("pct_change", 0.0),
            "fii_net_cr": flows.get("fii_net_flow_cr", 0.0),
            "dii_net_cr": flows.get("dii_net_flow_cr", 0.0),
        }
    except Exception:
        market_data = {"nifty_price": 25150.0, "nifty_change": 0.0, "fii_net_cr": 0.0, "dii_net_cr": 0.0}

    return {
        "status": "operational",
        "timestamp": now,
        "hardware": {
            "os": f"{telemetry.os_name} {telemetry.os_release}",
            "cpu_load_percent": telemetry.cpu_load_percent,
            "ram_load_percent": telemetry.ram_load_percent,
            "ram_total_gb": telemetry.ram_total_gb,
            "ram_avail_gb": telemetry.ram_avail_gb,
            "battery_percent": telemetry.battery_percent,
            "power_plugged": telemetry.power_plugged,
            "is_charging": telemetry.is_charging,
            "ollama_online": telemetry.ollama_online,
            "ollama_models": telemetry.ollama_models,
        },
        "pending_actions": [
            {
                "token": p.token,
                "tool_name": p.tool_name,
                "permission_level": p.permission_level.value,
                "description": p.description,
                "expires_in_seconds": round(max(0.0, p.expires_at - now)),
            }
            for p in pending_approvals
        ],
        "memory": {
            "total_items": len(all_mem),
            "tier_counts": tier_counts,
        },
        "agents": {
            "count": len(agents),
            "list": [a["name"] for a in agents],
        },
        "routine": routine_stats,
        "market": market_data,
    }


# ---------------- 2. WORKSPACE FILE EXPLORER ----------------

class FileWriteRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = False


@router.get("/files")
async def list_workspace_files(subpath: str = ""):
    """Browse files and folders inside the approved workspace."""
    base = _resolve_safe_path(subpath)
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)

    items = []
    try:
        for entry in os.scandir(base):
            stat = entry.stat()
            rel = Path(entry.path).relative_to(WORKSPACE_DIR)
            items.append({
                "name": entry.name,
                "path": str(rel).replace("\\", "/"),
                "is_dir": entry.is_dir(),
                "size_bytes": stat.st_size if entry.is_file() else 0,
                "modified_at": stat.st_mtime,
                "extension": Path(entry.name).suffix.lower(),
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan directory: {str(e)}")

    # Sort directories first, then alphabetical
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return {"workspace_root": str(WORKSPACE_DIR), "current_path": subpath, "items": items}


@router.get("/files/read")
async def read_workspace_file(path: str, max_chars: int = 10000):
    """Read content of a workspace text document."""
    target = _resolve_safe_path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    if target.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is a directory: {path}")

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > max_chars
        return {
            "path": path,
            "size_bytes": target.stat().st_size,
            "content": content[:max_chars],
            "total_chars": len(content),
            "is_truncated": truncated,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/files/write")
async def write_workspace_file(req: FileWriteRequest):
    """Create or update a document in the workspace with safety boundaries."""
    target = _resolve_safe_path(req.path)
    if target.exists() and not req.overwrite:
        raise HTTPException(status_code=409, detail=f"File already exists: {req.path}. Set overwrite=true.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    return {"success": True, "path": req.path, "bytes_written": len(req.content.encode("utf-8"))}


@router.delete("/files/delete")
async def delete_workspace_file(path: str = Query(...)):
    """Delete a file inside the workspace."""
    target = _resolve_safe_path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    try:
        if target.is_dir():
            target.rmdir()
        else:
            target.unlink()
        return {"success": True, "deleted": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


# ---------------- 3. UNIFIED SETTINGS CONTROL PANEL ----------------

class UnifiedSettings(BaseModel):
    model_routing_mode: str = "hybrid"  # local, hybrid, cloud
    active_local_model: str = "qwen2.5:3b"
    voice_language: str = "en-US"
    voice_speech_rate: float = 1.0
    voice_wake_word_enabled: bool = False
    voice_continuous_loop: bool = False
    security_offline_lockdown: bool = False
    security_redaction_enabled: bool = True


@router.get("/settings")
async def get_unified_settings():
    """Retrieve unified configuration with secrets masked."""
    from backend.app.voice.engine import voice_engine
    from backend.app.security.vault import security_vault

    voice = voice_engine.get_settings()
    vault_settings = security_vault.get_privacy_settings()

    openai_key = os.getenv("OPENAI_API_KEY", "") or os.getenv("CLOUD_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    github_key = getattr(settings, "GITHUB_TOKEN", "") or os.getenv("GITHUB_TOKEN", "")
    tavily_key = getattr(settings, "TAVILY_API_KEY", "") or os.getenv("TAVILY_API_KEY", "")

    return {
        "model_routing_mode": "hybrid",
        "active_local_model": settings.OLLAMA_MODEL,
        "voice": {
            "language": voice.language,
            "speech_rate": voice.speech_rate,
            "speech_pitch": voice.speech_pitch,
            "wake_word_enabled": voice.wake_word_enabled,
            "wake_word": voice.wake_word,
            "continuous_loop": voice.continuous_loop,
        },
        "security": {
            "offline_lockdown": vault_settings.get("offline_lockdown", False),
            "memory_retention_paused": vault_settings.get("pause_memory_retention", False),
            "strict_redaction": vault_settings.get("strict_redaction", True),
        },
        "api_keys_configured": {
            "openai": "sk-••••••••" if openai_key else "Not Configured",
            "anthropic": "sk-ant-••••••••" if anthropic_key else "Not Configured",
            "gemini": "AIza••••••••" if gemini_key else "Not Configured",
            "github": "ghp_••••••••" if github_key else "Not Configured",
            "tavily": "tvly-••••••••" if tavily_key else "Not Configured",
        },
    }


@router.post("/settings")
async def update_unified_settings(new_settings: UnifiedSettings):
    """Update system settings cleanly."""
    from backend.app.voice.engine import voice_engine
    from backend.app.security.vault import security_vault

    # Update voice settings
    v = voice_engine.get_settings()
    v.language = new_settings.voice_language
    v.speech_rate = new_settings.voice_speech_rate
    v.wake_word_enabled = new_settings.voice_wake_word_enabled
    v.continuous_loop = new_settings.voice_continuous_loop
    voice_engine.save_settings(v)

    # Update security privacy settings
    security_vault.set_privacy_mode(
        offline_lockdown=new_settings.security_offline_lockdown,
        strict_redaction=new_settings.security_redaction_enabled,
    )

    return {"success": True, "message": "Unified settings saved successfully."}

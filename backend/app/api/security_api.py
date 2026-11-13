"""FastAPI REST Router for NOUS Security Vault, Privacy Controls & Audit Trail (Phase 14)."""

from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.security.vault import security_vault
from backend.app.security.redactor import sensitive_redactor

logger = logging.getLogger("nous.api.security")

router = APIRouter(prefix="/api/security", tags=["Security & Privacy"])


# ---------------- SCHEMAS ----------------


class PrivacyUpdateRequest(BaseModel):
    offline_lockdown: Optional[bool] = Field(None, description="Block all external internet and cloud calls")
    pause_memory_retention: Optional[bool] = Field(None, description="Pause long-term memory recording")
    strict_redaction: Optional[bool] = Field(None, description="Enforce strict API key & PII redaction")
    audit_retention_days: Optional[int] = Field(None, description="Retention window in days")


class SanitizeTestRequest(BaseModel):
    text: str = Field(..., description="Text containing potential secrets to test redaction")


# ---------------- ENDPOINTS ----------------


@router.get("/audit")
async def get_audit_trail(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    decision: Optional[str] = Query(None, description="Filter by decision (ALLOWED, DENIED, CONFIRMED, BLOCKED)"),
    search: Optional[str] = Query(None, description="Search query across resource or details"),
    limit: int = Query(50, description="Maximum records to retrieve"),
) -> dict[str, Any]:
    """Retrieve tamper-evident security audit logs from the persistent vault."""
    try:
        events = security_vault.db.list_events(
            event_type=event_type,
            decision=decision,
            search=search,
            limit=limit,
        )
        return {
            "count": len(events),
            "events": events,
        }
    except Exception as e:
        logger.error("Failed to retrieve audit trail: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/privacy")
async def get_privacy_policies() -> dict[str, Any]:
    """Retrieve current privacy policies, kill switch states, and lockdown toggles."""
    try:
        settings_data = security_vault.db.get_privacy_settings()
        return {
            "status": "success",
            "privacy_settings": settings_data,
        }
    except Exception as e:
        logger.error("Failed to get privacy settings: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy")
async def update_privacy_policies(req: PrivacyUpdateRequest) -> dict[str, Any]:
    """Update privacy switches, enable/disable offline lockdown, or toggle memory retention."""
    try:
        updated = security_vault.set_privacy_mode(
            offline_lockdown=req.offline_lockdown,
            pause_memory_retention=req.pause_memory_retention,
            strict_redaction=req.strict_redaction,
        )
        return {
            "status": "updated",
            "privacy_settings": updated,
        }
    except Exception as e:
        logger.error("Failed to update privacy settings: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sanitize")
async def sanitize_text(req: SanitizeTestRequest) -> dict[str, Any]:
    """Test the redaction engine against sample text containing secrets or credentials."""
    try:
        has_secrets = sensitive_redactor.contains_sensitive(req.text)
        sanitized = sensitive_redactor.redact(req.text)
        return {
            "contains_secrets": has_secrets,
            "original_length": len(req.text),
            "sanitized_length": len(sanitized),
            "sanitized_text": sanitized,
        }
    except Exception as e:
        logger.error("Sanitization failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purge")
async def purge_transient_artifacts() -> dict[str, Any]:
    """Purge temporary cache, unapproved tokens, and old audit records."""
    try:
        return security_vault.purge_transient_data()
    except Exception as e:
        logger.error("Purge failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_security_vault_data() -> dict[str, Any]:
    """Export audit events and privacy policies for user data ownership."""
    try:
        return security_vault.export_user_data()
    except Exception as e:
        logger.error("Data export failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

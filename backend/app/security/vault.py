"""Security Vault & Privacy Manager Orchestrator for NOUS (Phase 14)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.app.config import settings
from backend.app.security.db import SecurityDBManager
from backend.app.security.redactor import sensitive_redactor

logger = logging.getLogger("nous.security.vault")


class SecurityVault:
    """Orchestrates privacy policies, offline lockdown switches, and audit logging."""

    def __init__(self, db_manager: SecurityDBManager | None = None) -> None:
        self.db = db_manager or SecurityDBManager()
        self.redactor = sensitive_redactor

    # ---------------- PRIVACY STATUS & KILL SWITCHES ----------------

    def is_offline_lockdown_enabled(self) -> bool:
        """Check whether complete external network lockdown is active."""
        settings_dict = self.db.get_privacy_settings()
        return settings_dict.get("offline_lockdown", False)

    def is_memory_retention_paused(self) -> bool:
        """Check whether long-term memory recording is paused by user policy."""
        settings_dict = self.db.get_privacy_settings()
        return settings_dict.get("pause_memory_retention", False)

    def is_strict_redaction_enabled(self) -> bool:
        """Check whether strict credential/PII redaction is active."""
        settings_dict = self.db.get_privacy_settings()
        return settings_dict.get("strict_redaction", True)

    def get_privacy_settings(self) -> dict[str, Any]:
        """Return currently active privacy settings."""
        return self.db.get_privacy_settings()

    def set_privacy_mode(
        self,
        offline_lockdown: bool | None = None,
        pause_memory_retention: bool | None = None,
        strict_redaction: bool | None = None,
    ) -> dict[str, Any]:
        """Update active privacy switches."""
        return self.db.update_privacy_settings(
            offline_lockdown=offline_lockdown,
            pause_memory_retention=pause_memory_retention,
            strict_redaction=strict_redaction,
        )

    # ---------------- AUDIT LOGGING FACADE ----------------

    def log_action(
        self,
        event_type: str,
        resource: str,
        risk_level: str = "low",
        decision: str = "ALLOWED",
        actor: str = "user",
        details: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Log an event with guaranteed credential scrubbing."""
        return self.db.log_event(
            event_type=event_type,
            resource=resource,
            risk_level=risk_level,
            decision=decision,
            actor=actor,
            details=details,
            session_id=session_id,
        )

    # ---------------- ARTIFACT PURGE & EXPORT ----------------

    def purge_transient_data(self) -> dict[str, Any]:
        """Purge temporary files, scratch scripts, and old audit logs."""
        purged_items = []

        # 1. Purge old audit events (> 30 days)
        purged_audit_count = self.db.purge_old_audit_logs(max_days=30)
        purged_items.append(f"Purged {purged_audit_count} audit event logs older than 30 days")

        # 2. Clear any pending approval tokens in automation manager
        try:
            from backend.app.automation.manager import automation_manager
            token_count = len(automation_manager.pending_approvals)
            automation_manager.pending_approvals.clear()
            purged_items.append(f"Cleared {token_count} pending execution approval tokens")
        except Exception as e:
            logger.debug("Automation manager pending token clear: %s", e)

        # 3. Log purge event in vault
        self.log_action(
            event_type="transient_purge",
            resource="system_cache",
            risk_level="medium",
            decision="ALLOWED",
            details={"purged_items": purged_items},
        )

        return {
            "status": "success",
            "purged_records": purged_items,
        }

    def export_user_data(self) -> dict[str, Any]:
        """Compile user data and audit logs for user inspection and export."""
        events = self.db.list_events(limit=100)
        privacy = self.db.get_privacy_settings()

        export_package = {
            "version": "1.0",
            "exported_at": self.db.list_events(limit=1)[0]["timestamp"] if events else "",
            "privacy_settings": privacy,
            "audit_trail_sample": events,
            "disclaimer": "This package contains your local privacy and audit logs. All secret keys are redacted.",
        }

        self.log_action(
            event_type="data_export",
            resource="privacy_vault",
            risk_level="low",
            decision="ALLOWED",
            details={"event_count": len(events)},
        )

        return export_package


# Global singleton security vault
security_vault = SecurityVault()

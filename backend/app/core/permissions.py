"""Permission Manager for NOUS AI Tools.

Enforces security boundaries, risk classification, and authorization checks
to prevent prompt injection and unauthorized execution of sensitive operations.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "low"          # Read-only information, math calculations, time checks
    MEDIUM = "medium"    # Reading permitted files, updating calendar, changing settings
    HIGH = "high"        # Sending emails, deleting data, shell commands, transactions


class PermissionRequest(BaseModel):
    tool_name: str
    risk_level: RiskLevel
    description: str
    parameters: dict
    approved: bool = False


class PermissionManager:
    """Manages permissions and approval gates for tool execution."""

    def __init__(self, auto_approve_low: bool = True, auto_approve_medium: bool = False, auto_approve_high: bool = False):
        self.auto_approve_low = auto_approve_low
        self.auto_approve_medium = auto_approve_medium
        self.auto_approve_high = auto_approve_high
        self.pending_requests: dict[str, PermissionRequest] = {}
        self.audit_log: list[dict] = []

    def check_permission(self, tool_name: str, risk_level: RiskLevel, params: dict) -> tuple[bool, str]:
        """Check if an action is authorized to execute.
        
        Returns:
            (is_allowed, reason_or_status)
        """
        if risk_level == RiskLevel.LOW and self.auto_approve_low:
            self.log_action(tool_name, risk_level, params, status="auto_approved")
            return True, "Auto-approved (Low risk read-only action)"

        if risk_level == RiskLevel.MEDIUM and self.auto_approve_medium:
            self.log_action(tool_name, risk_level, params, status="auto_approved")
            return True, "Auto-approved (Medium risk action authorized)"

        if risk_level == RiskLevel.HIGH and self.auto_approve_high:
            self.log_action(tool_name, risk_level, params, status="auto_approved")
            return True, "Auto-approved (High risk action authorized)"

        # Actions requiring explicit user checks
        self.log_action(tool_name, risk_level, params, status="requires_approval")
        return False, f"Action '{tool_name}' is classified as {risk_level.value.upper()} risk and requires user authorization."

    def log_action(self, tool_name: str, risk_level: RiskLevel, params: dict, status: str):
        """Append to the in-memory log and persist to Security Vault database."""
        import time
        self.audit_log.append({
            "timestamp": time.time(),
            "tool_name": tool_name,
            "risk_level": risk_level.value,
            "parameters": {k: str(v) for k, v in params.items()},
            "status": status,
        })
        try:
            from backend.app.security.vault import security_vault
            decision_map = {
                "auto_approved": "ALLOWED",
                "requires_approval": "REQUIRES_APPROVAL",
                "denied": "DENIED",
            }
            security_vault.log_action(
                event_type="tool_execution",
                resource=tool_name,
                risk_level=risk_level.value,
                decision=decision_map.get(status, status.upper()),
                actor="user",
                details=params,
            )
        except Exception:
            pass

    def get_audit_logs(self, limit: int = 50) -> list[dict]:
        """Retrieve recent security audit logs."""
        return self.audit_log[-limit:]


permission_manager = PermissionManager()

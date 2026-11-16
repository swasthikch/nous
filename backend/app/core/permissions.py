"""Permission Manager for NOUS AI Tools (Phase 3 Unified).

Maintains backward compatibility with legacy 3-tier risk checks
while delegating to the 5-level zero-trust permission hierarchy.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel

from backend.app.tools.permissions import (
    PermissionLevel,
    RiskLevel,
    risk_to_permission,
    permission_manager as modern_permission_manager,
    ToolPermissionManager,
    PermissionCheckResult,
)
from backend.app.tools.approval import approval_manager, ApprovalRequest
from backend.app.tools.logger import tool_logger


class PermissionRequest(BaseModel):
    tool_name: str
    risk_level: RiskLevel
    description: str
    parameters: dict[str, Any]
    approved: bool = False


class LegacyPermissionManagerAdapter:
    """Adapter maintaining legacy check_permission() method signatures."""

    def __init__(self) -> None:
        self.modern = modern_permission_manager

    def check_permission(
        self,
        tool_name: str,
        risk_level: RiskLevel | str,
        params: dict[str, Any],
    ) -> tuple[bool, str]:
        """Backward-compatible permission check returning (is_allowed, reason)."""
        res = self.modern.check_permission(tool_name, risk_level, params)
        status_label = "auto_approved" if res.is_allowed else "requires_approval"
        tool_logger.log(
            tool_name=tool_name,
            permission_level=res.permission_level,
            parameters=params,
            status=status_label,
            error_message=res.reason if not res.is_allowed else None,
        )
        return res.is_allowed, res.reason

    def log_action(
        self,
        tool_name: str,
        risk_level: RiskLevel | str,
        params: dict[str, Any],
        status: str,
    ) -> None:
        perm = risk_to_permission(risk_level)
        tool_logger.log(
            tool_name=tool_name,
            permission_level=perm,
            parameters=params,
            status=status,
        )

    def get_audit_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent audit logs in legacy dict format."""
        logs = tool_logger.get_logs(limit=limit)
        return [l.model_dump() for l in logs]


# Global instance
permission_manager = LegacyPermissionManagerAdapter()

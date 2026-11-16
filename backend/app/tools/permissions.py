"""5-Level Tool Permission and Risk Classification System for NOUS.

Defines the zero-trust authorization hierarchy:
1. READ: Search and retrieve information (Auto-approved).
2. PREPARE: Generate drafts, formulate plans, preview actions (Auto-approved).
3. WRITE: Modify workspace files, memories, and schedules (Requires confirmation).
4. EXTERNAL_ACTION: Send emails, push Git commits, external API writes (Strict explicit confirmation).
5. SENSITIVE_ACTION: Deleting files, purging security vaults, executing scripts (Cryptographic token required).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """The 5 security clearance tiers for NOUS tools."""
    READ = "read"
    PREPARE = "prepare"
    WRITE = "write"
    EXTERNAL_ACTION = "external_action"
    SENSITIVE_ACTION = "sensitive_action"


class RiskLevel(str, Enum):
    """Backward-compatible alias for 3-tier legacy classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def risk_to_permission(risk: RiskLevel | PermissionLevel | str) -> PermissionLevel:
    """Map legacy 3-tier risk levels or PermissionLevel to the modern 5-tier permission hierarchy."""
    if isinstance(risk, (RiskLevel, PermissionLevel)):
        val = risk.value.lower().strip()
    else:
        val = getattr(risk, "value", str(risk)).lower().strip()
        if "." in val:
            val = val.split(".")[-1]
    if val in ("low", "read"):
        return PermissionLevel.READ
    elif val in ("prepare", "draft"):
        return PermissionLevel.PREPARE
    elif val in ("medium", "write"):
        return PermissionLevel.WRITE
    elif val in ("external", "external_action", "email", "git_push"):
        return PermissionLevel.EXTERNAL_ACTION
    elif val in ("high", "sensitive", "sensitive_action", "command", "delete"):
        return PermissionLevel.SENSITIVE_ACTION
    return PermissionLevel.WRITE


class PermissionCheckResult(BaseModel):
    """Result of an authorization check."""
    is_allowed: bool
    permission_level: PermissionLevel
    requires_approval: bool
    status: str  # "auto_approved", "requires_approval", "denied"
    reason: str
    approval_token: Optional[str] = None


class ToolPermissionManager:
    """Enforces zero-trust permission boundaries across all tool executions."""

    def __init__(
        self,
        auto_approve_read: bool = True,
        auto_approve_prepare: bool = True,
        auto_approve_write: bool = False,
        auto_approve_external: bool = False,
        auto_approve_sensitive: bool = False,
    ) -> None:
        self.auto_approve_read = auto_approve_read
        self.auto_approve_prepare = auto_approve_prepare
        self.auto_approve_write = auto_approve_write
        self.auto_approve_external = auto_approve_external
        self.auto_approve_sensitive = auto_approve_sensitive

    def check_permission(
        self,
        tool_name: str,
        permission_level: PermissionLevel | RiskLevel | str,
        parameters: dict[str, Any],
    ) -> PermissionCheckResult:
        """Verify whether a tool action is permitted to execute or requires HITL token."""
        level = permission_level if isinstance(permission_level, PermissionLevel) else risk_to_permission(permission_level)

        # 1. READ Level
        if level == PermissionLevel.READ and self.auto_approve_read:
            return PermissionCheckResult(
                is_allowed=True,
                permission_level=level,
                requires_approval=False,
                status="auto_approved",
                reason=f"Action '{tool_name}' is classified as READ (Read-only data access).",
            )

        # 2. PREPARE Level
        if level == PermissionLevel.PREPARE and self.auto_approve_prepare:
            return PermissionCheckResult(
                is_allowed=True,
                permission_level=level,
                requires_approval=False,
                status="auto_approved",
                reason=f"Action '{tool_name}' is classified as PREPARE (Draft generation without side effects).",
            )

        # 3. WRITE Level
        if level == PermissionLevel.WRITE and self.auto_approve_write:
            return PermissionCheckResult(
                is_allowed=True,
                permission_level=level,
                requires_approval=False,
                status="auto_approved",
                reason=f"Action '{tool_name}' is classified as WRITE (User pre-authorized).",
            )

        # 4. EXTERNAL ACTION Level
        if level == PermissionLevel.EXTERNAL_ACTION and self.auto_approve_external:
            return PermissionCheckResult(
                is_allowed=True,
                permission_level=level,
                requires_approval=False,
                status="auto_approved",
                reason=f"Action '{tool_name}' is classified as EXTERNAL ACTION (User pre-authorized).",
            )

        # 5. SENSITIVE ACTION Level
        if level == PermissionLevel.SENSITIVE_ACTION and self.auto_approve_sensitive:
            return PermissionCheckResult(
                is_allowed=True,
                permission_level=level,
                requires_approval=False,
                status="auto_approved",
                reason=f"Action '{tool_name}' is classified as SENSITIVE ACTION (User pre-authorized).",
            )

        # Requires Human-In-The-Loop (HITL) User Authorization
        return PermissionCheckResult(
            is_allowed=False,
            permission_level=level,
            requires_approval=True,
            status="requires_approval",
            reason=f"Action '{tool_name}' is classified as {level.value.upper()} and requires cryptographic user authorization.",
        )


permission_manager = ToolPermissionManager()

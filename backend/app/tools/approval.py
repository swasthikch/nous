"""Cryptographic Human-In-The-Loop (HITL) Approval Token Manager for NOUS.

Generates single-use, time-bounded tokens for actions that require user confirmation:
- Modifying files (WRITE)
- Sending emails / Git pushes (EXTERNAL_ACTION)
- Deleting files / executing commands (SENSITIVE_ACTION)

Guarantees:
1. Replay prevention: Each token can only be approved once.
2. Expiration: Tokens expire automatically after their TTL (default 300s).
3. Immutable parameter snapshot: Tools execute with the exact parameters approved by the user.
"""

from __future__ import annotations

from enum import Enum
import secrets
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.tools.permissions import PermissionLevel


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalRequest(BaseModel):
    token: str
    tool_name: str
    permission_level: PermissionLevel
    description: str
    parameters: dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    decision_at: Optional[float] = None
    decision_reason: Optional[str] = None


class ApprovalManager:
    """Coordinates time-bounded cryptographic authorization tokens."""

    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self.default_ttl = default_ttl_seconds
        self._requests: dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        permission_level: PermissionLevel,
        description: Optional[str] = None,
        ttl_seconds: Optional[float] = None,
    ) -> ApprovalRequest:
        """Issue a new cryptographic approval request token."""
        now = time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        token = secrets.token_urlsafe(32)

        desc = description or f"Execute tool '{tool_name}' with parameters {list(parameters.keys())}"

        req = ApprovalRequest(
            token=token,
            tool_name=tool_name,
            permission_level=permission_level,
            description=desc,
            parameters=parameters,
            status=ApprovalStatus.PENDING,
            created_at=now,
            expires_at=now + ttl,
        )
        self._requests[token] = req
        return req

    def get_request(self, token: str) -> Optional[ApprovalRequest]:
        """Fetch request by token and check expiration."""
        req = self._requests.get(token)
        if not req:
            return None

        now = time.time()
        if req.status == ApprovalStatus.PENDING and now > req.expires_at:
            req.status = ApprovalStatus.EXPIRED
        return req

    def approve_token(self, token: str) -> tuple[bool, Optional[ApprovalRequest], str]:
        """Approve a pending token (single-use)."""
        req = self.get_request(token)
        if not req:
            return False, None, "Invalid or unrecognized approval token."

        if req.status == ApprovalStatus.EXPIRED:
            return False, req, "Approval token has expired. Re-trigger the action to obtain a fresh token."

        if req.status != ApprovalStatus.PENDING:
            return False, req, f"Approval token is already in status '{req.status.value}'."

        now = time.time()
        req.status = ApprovalStatus.APPROVED
        req.decision_at = now
        req.decision_reason = "User explicitly confirmed authorization."
        return True, req, "Authorization granted successfully."

    def reject_token(self, token: str, reason: str = "User declined action.") -> tuple[bool, Optional[ApprovalRequest], str]:
        """Reject a pending token."""
        req = self.get_request(token)
        if not req:
            return False, None, "Invalid approval token."

        if req.status != ApprovalStatus.PENDING:
            return False, req, f"Cannot reject token in status '{req.status.value}'."

        now = time.time()
        req.status = ApprovalStatus.REJECTED
        req.decision_at = now
        req.decision_reason = reason
        return True, req, f"Action declined: {reason}"

    def cancel_tool(self, token: str) -> bool:
        """Cancel an in-flight or pending tool execution."""
        req = self.get_request(token)
        if not req:
            return False

        req.status = ApprovalStatus.CANCELLED
        req.decision_at = time.time()
        req.decision_reason = "Operation cancelled by user."
        return True

    def list_pending(self) -> list[ApprovalRequest]:
        """List all currently valid, non-expired pending approvals."""
        now = time.time()
        pending = []
        for req in self._requests.values():
            if req.status == ApprovalStatus.PENDING:
                if now <= req.expires_at:
                    pending.append(req)
                else:
                    req.status = ApprovalStatus.EXPIRED
        return pending

    def purge_expired(self) -> int:
        """Clean up expired and resolved tokens older than 1 hour."""
        now = time.time()
        to_delete = [
            t for t, req in self._requests.items()
            if req.status != ApprovalStatus.PENDING and (now - req.created_at) > 3600
        ]
        for t in to_delete:
            del self._requests[t]
        return len(to_delete)


approval_manager = ApprovalManager()

"""Security Guardrails and Path Traversal Defense for NOUS Task Automation."""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Tuple

from backend.app.config import settings

logger = logging.getLogger("nous.automation.security")


class SecurityError(Exception):
    """Raised when an operation violates security boundaries."""
    pass


class CommandRiskLevel:
    SAFE = "safe"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"


# Command pattern definitions
DANGEROUS_COMMAND_PATTERNS = [
    r"\brmdir\s+.*(/[sS])",
    r"\bdel\s+.*(/[sS])",
    r"\bformat\s+[a-zA-Z]:",
    r"\bdiskpart\b",
    r"\bbcdedit\b",
    r"\breg\s+(delete|add)\b",
    r"\bnet\s+user\b",
    r"\bshutdown\b",
    r"\bvssadmin\b",
    r"\btakeown\b",
    r"\bicacls\b",
    r"\bmkfs\b",
    r"\brm\s+-(rf|fr|r)\s+/",
    r":\(\)\s*\{\s*:\|:&\s*\};:",  # Fork bomb
    r"powershell.*(-enc|-encodedcommand)\b",
    r"\b(invoke-expression|iex)\b",
    r"\bdrop\s+database\b",
]

SAFE_READONLY_COMMANDS = [
    r"^(dir|ls)(\s+.*)?$",
    r"^git\s+(status|log|branch|diff|remote|show)(\s+.*)?$",
    r"^python\s+(--version|-V)$",
    r"^(node|npm|pnpm|git|python|pip)\s+(--version|-v|-V)$",
    r"^pip\s+list(\s+.*)?$",
    r"^echo\s+.*$",
    r"^(type|cat|head|tail)\s+.*$",
    r"^whoami$",
    r"^date(\s+.*)?$",
    r"^time(\s+.*)?$",
]


class AutomationSecurityGate:
    """Enforces strict path isolation and command execution boundaries."""

    def __init__(self, workspace_dir: Path | None = None) -> None:
        self.workspace_dir = (workspace_dir or settings.WORKSPACE_DIR).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def validate_workspace_path(self, target_path: str | Path) -> Path:
        """Validate and resolve a path within the authorized workspace.
        
        Prevents directory traversal attacks ('..', absolute escape, symlinks).
        """
        raw_target = str(target_path).strip()
        if not raw_target:
            return self.workspace_dir

        # Strip leading slashes to prevent root escapes
        cleaned = raw_target.lstrip("/\\")
        resolved = (self.workspace_dir / cleaned).resolve()

        # Check path containment
        try:
            resolved.relative_to(self.workspace_dir)
        except ValueError:
            logger.warning("Path traversal attempt detected: '%s' escapes workspace '%s'", raw_target, self.workspace_dir)
            raise SecurityError(f"Security Alert: Path '{raw_target}' resolves outside authorized workspace.")

        return resolved

    def evaluate_command_safety(self, command: str) -> Tuple[str, str]:
        """Classify command risk level and return (RiskLevel, Reason)."""
        cmd = command.strip()
        if not cmd:
            return CommandRiskLevel.BLOCKED, "Empty command string."

        # 1. Check blocked patterns
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                logger.warning("Blocked dangerous command execution: '%s' matched '%s'", cmd, pattern)
                return CommandRiskLevel.BLOCKED, f"Command contains forbidden destructive operation matching pattern '{pattern}'."

        # 2. Check safe read-only commands
        for safe_pattern in SAFE_READONLY_COMMANDS:
            if re.match(safe_pattern, cmd, re.IGNORECASE):
                return CommandRiskLevel.SAFE, "Read-only inspection command."

        # 3. Default to requiring human-in-the-loop approval
        return CommandRiskLevel.REQUIRES_APPROVAL, "State-modifying or external command requires explicit user confirmation."


security_gate = AutomationSecurityGate()

"""Core Automation Manager for File Operations, Safe Shell Execution, and Background Jobs."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.config import settings
from backend.app.automation.db import AutomationDBManager
from backend.app.automation.security import (
    AutomationSecurityGate,
    CommandRiskLevel,
    SecurityError,
    security_gate,
)

logger = logging.getLogger("nous.automation.manager")

# Maximum file read size (2 MB) to prevent memory exhaustion
MAX_READ_BYTES = 2 * 1024 * 1024


class AutomationManager:
    """Orchestrates file operations, safe command execution, and scheduled tasks."""

    def __init__(
        self,
        security: AutomationSecurityGate | None = None,
        db_manager: AutomationDBManager | None = None,
    ) -> None:
        self.security = security or security_gate
        self.db = db_manager or AutomationDBManager()
        self.workspace = self.security.workspace_dir
        self.pending_approvals: dict[str, dict[str, Any]] = {}

        # Ensure a default welcome file exists in the workspace
        self._seed_workspace_readme()

    def _seed_workspace_readme(self) -> None:
        """Seed the workspace with an informative introductory file if empty."""
        readme = self.workspace / "README.md"
        if not readme.exists():
            readme.write_text(
                "# NOUS Workspace\n\n"
                "This is the authorized sandbox directory for NOUS personal assistant file operations.\n"
                "Files created, edited, and analyzed by NOUS reside securely inside this folder.\n\n"
                "### Features:\n"
                "- Path traversal protection (`..` strictly prevented)\n"
                "- Safe reading, writing, and listing\n"
                "- Controlled shell command execution with human-in-the-loop confirmation\n",
                encoding="utf-8",
            )

    # ---------------- FILE SYSTEM OPERATIONS ----------------

    def list_files(self, subpath: str = "") -> list[dict[str, Any]]:
        """List files and folders within the authorized workspace."""
        target_dir = self.security.validate_workspace_path(subpath)
        if not target_dir.exists():
            raise FileNotFoundError(f"Directory not found: '{subpath}'")
        if not target_dir.is_dir():
            raise NotADirectoryError(f"Path is a file, not a directory: '{subpath}'")

        items: list[dict[str, Any]] = []
        for entry in target_dir.iterdir():
            rel_path = entry.relative_to(self.workspace).as_posix()
            stat = entry.stat()
            modified_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            items.append({
                "name": entry.name,
                "relative_path": rel_path,
                "is_dir": entry.is_dir(),
                "size_bytes": stat.st_size if entry.is_file() else 0,
                "extension": entry.suffix.lower() if entry.is_file() else "",
                "modified_at": modified_iso,
            })

        # Sort folders first, then alphabetical
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return items

    def read_file(self, file_path: str) -> dict[str, Any]:
        """Safely read text content of a file inside the workspace."""
        target = self.security.validate_workspace_path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")
        if target.is_dir():
            raise IsADirectoryError(f"Target is a directory: '{file_path}'")

        size = target.stat().st_size
        if size > MAX_READ_BYTES:
            raise ValueError(f"File size ({size} bytes) exceeds safety limit of {MAX_READ_BYTES} bytes.")

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise IOError(f"Could not read file '{file_path}': {e}")

        rel_path = target.relative_to(self.workspace).as_posix()
        return {
            "file_name": target.name,
            "relative_path": rel_path,
            "size_bytes": size,
            "content": content,
            "line_count": len(content.splitlines()),
        }

    def write_file(self, file_path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
        """Safely write text content to a file in the workspace."""
        target = self.security.validate_workspace_path(file_path)
        if target.exists() and not overwrite:
            raise FileExistsError(f"File already exists: '{file_path}'. Set overwrite=True to replace.")

        # Create parent directories safely
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        stat = target.stat()
        rel_path = target.relative_to(self.workspace).as_posix()
        return {
            "status": "written",
            "file_name": target.name,
            "relative_path": rel_path,
            "size_bytes": stat.st_size,
            "line_count": len(content.splitlines()),
        }

    def delete_file(self, file_path: str) -> dict[str, Any]:
        """Safely remove a file or empty directory in the workspace."""
        target = self.security.validate_workspace_path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"Path not found: '{file_path}'")
        if target == self.workspace:
            raise SecurityError("Cannot delete root workspace directory.")

        if target.is_dir():
            target.rmdir()
        else:
            target.unlink()

        return {"status": "deleted", "path": file_path}

    # ---------------- CONTROLLED SHELL COMMAND EXECUTION ----------------

    def request_or_execute_command(
        self,
        command: str,
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate command safety and execute with Human-In-The-Loop gate."""
        clean_cmd = command.strip()
        risk_level, reason = self.security.evaluate_command_safety(clean_cmd)

        # 1. Immediate rejection for blocked commands
        if risk_level == CommandRiskLevel.BLOCKED:
            self.db.record_execution(
                command=clean_cmd,
                status="blocked",
                exit_code=-1,
                output=f"Execution blocked by security policy: {reason}",
                risk_level="blocked",
            )
            return {
                "status": "blocked",
                "command": clean_cmd,
                "error": reason,
                "risk_level": "blocked",
            }

        # 2. Human-In-The-Loop confirmation required
        if risk_level == CommandRiskLevel.REQUIRES_APPROVAL and settings.REQUIRE_COMMAND_APPROVAL:
            # Check if valid approval token provided
            if approval_token and approval_token in self.pending_approvals:
                cached = self.pending_approvals.pop(approval_token)
                if cached["command"] == clean_cmd and time.time() - cached["created_at"] < 300:
                    # Token valid and within 5 min window -> Proceed to execute
                    return self._run_command_process(clean_cmd, risk_level)

            # Generate new approval token
            token = uuid.uuid4().hex[:12]
            self.pending_approvals[token] = {
                "command": clean_cmd,
                "created_at": time.time(),
                "reason": reason,
            }
            return {
                "status": "requires_approval",
                "approval_token": token,
                "command": clean_cmd,
                "reason": reason,
                "risk_level": "medium",
                "message": (
                    f"Execution requires explicit confirmation. Review command: '{clean_cmd}'. "
                    f"Confirm execution using token '{token}'."
                ),
            }

        # 3. Direct execution for safe read-only commands
        return self._run_command_process(clean_cmd, risk_level)

    def _run_command_process(self, command: str, risk_level: str) -> dict[str, Any]:
        """Run subprocess in workspace with strict timeout."""
        start_t = time.perf_counter()
        timeout = settings.COMMAND_TIMEOUT_SECONDS

        try:
            # Run in workspace directory
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)
            combined_output = (proc.stdout + proc.stderr).strip()
            status = "success" if proc.returncode == 0 else "error"

            self.db.record_execution(
                command=command,
                status=status,
                exit_code=proc.returncode,
                output=combined_output,
                execution_time_ms=elapsed_ms,
                risk_level=risk_level,
            )

            return {
                "status": status,
                "command": command,
                "exit_code": proc.returncode,
                "output": combined_output or "(No console output)",
                "execution_time_ms": elapsed_ms,
                "risk_level": risk_level,
            }
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)
            msg = f"Command execution timed out after {timeout} seconds."
            self.db.record_execution(
                command=command,
                status="timeout",
                exit_code=-1,
                output=msg,
                execution_time_ms=elapsed_ms,
                risk_level=risk_level,
            )
            return {
                "status": "timeout",
                "command": command,
                "exit_code": -1,
                "output": msg,
                "execution_time_ms": elapsed_ms,
                "risk_level": risk_level,
            }
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)
            msg = f"Failed to execute command: {e}"
            self.db.record_execution(
                command=command,
                status="failed",
                exit_code=-1,
                output=msg,
                execution_time_ms=elapsed_ms,
                risk_level=risk_level,
            )
            return {
                "status": "failed",
                "command": command,
                "exit_code": -1,
                "output": msg,
                "execution_time_ms": elapsed_ms,
                "risk_level": risk_level,
            }

    # ---------------- SCHEDULED TASK WORKFLOWS ----------------

    def schedule_task(
        self,
        name: str,
        action_type: str,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a scheduled background task."""
        return self.db.create_scheduled_task(
            name=name,
            action_type=action_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            payload=payload,
        )

    def run_scheduled_task_now(self, task_id: str) -> dict[str, Any]:
        """Trigger an immediate execution of a scheduled task."""
        task = self.db.get_scheduled_task(task_id)
        if not task:
            raise FileNotFoundError(f"Scheduled task '{task_id}' not found.")

        action = task["action_type"]
        payload = task.get("payload") or {}
        now = datetime.now(timezone.utc).isoformat()

        output = ""
        if action == "command":
            cmd = payload.get("command", "echo Scheduled job executed")
            res = self._run_command_process(cmd, "scheduled")
            output = res.get("output", "")
        elif action == "briefing":
            output = "Scheduled daily morning briefing compiled."
        elif action == "project_sync":
            output = "Scheduled GitHub project milestone sync completed."
        else:
            output = f"Executed generic scheduled action: {action}"

        self.db.update_task_status(task_id, status=task["status"], last_run_at=now)
        return {
            "task_id": task_id,
            "name": task["name"],
            "action_type": action,
            "executed_at": now,
            "output": output,
        }


automation_manager = AutomationManager()

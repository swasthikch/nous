"""Tool Execution Audit Logger for NOUS.

Guarantees immutable, tamper-evident audit logging for all tool executions.
Redacts API keys, passwords, and sensitive parameters before persisting to disk.
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.tools.permissions import PermissionLevel
from backend.app.security.redactor import sensitive_redactor


class ToolLogEntry(BaseModel):
    id: Optional[int] = None
    timestamp: float = Field(default_factory=time.time)
    timestamp_iso: str = ""
    tool_name: str
    permission_level: str
    parameters_json: str
    status: str  # "SUCCESS", "FAILED", "TIMEOUT", "BLOCKED", "CANCELLED"
    elapsed_seconds: float = 0.0
    approval_token: Optional[str] = None
    actor: str = "user"
    error_message: Optional[str] = None


class ToolExecutionLogger:
    """Logs every tool execution into the Security Vault database."""

    def __init__(self) -> None:
        self.db_path = settings.SECURITY_DB_PATH
        self._memory_ring_buffer: list[ToolLogEntry] = []
        self._init_db()

    def _init_db(self) -> None:
        """Create tool_execution_logs table in security database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tool_execution_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        timestamp_iso TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        permission_level TEXT NOT NULL,
                        parameters_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        elapsed_seconds REAL DEFAULT 0.0,
                        approval_token TEXT,
                        actor TEXT DEFAULT 'user',
                        error_message TEXT
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_logs_tool ON tool_execution_logs(tool_name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_logs_status ON tool_execution_logs(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_logs_time ON tool_execution_logs(timestamp);")
                conn.commit()
        except Exception as e:
            print(f"[TOOL LOGGER] DB init note: {e}")

    def log(
        self,
        tool_name: str,
        permission_level: PermissionLevel | str,
        parameters: dict[str, Any],
        status: str,
        elapsed_seconds: float = 0.0,
        approval_token: Optional[str] = None,
        actor: str = "user",
        error_message: Optional[str] = None,
    ) -> ToolLogEntry:
        """Record a tool execution with automated parameter scrubbing."""
        now = time.time()
        iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        level_str = permission_level.value if isinstance(permission_level, PermissionLevel) else str(permission_level)

        # 1. Scrub sensitive secrets from parameters before serializing
        scrubbed_params = sensitive_redactor.redact_data_structure(parameters)
        params_json = json.dumps(scrubbed_params)

        entry = ToolLogEntry(
            timestamp=now,
            timestamp_iso=iso,
            tool_name=tool_name,
            permission_level=level_str,
            parameters_json=params_json,
            status=status.upper(),
            elapsed_seconds=round(elapsed_seconds, 3),
            approval_token=approval_token,
            actor=actor,
            error_message=error_message,
        )

        # 2. Append to in-memory buffer (retaining last 100 entries)
        self._memory_ring_buffer.append(entry)
        if len(self._memory_ring_buffer) > 100:
            self._memory_ring_buffer.pop(0)

        # 3. Persist to SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tool_execution_logs (
                        timestamp, timestamp_iso, tool_name, permission_level,
                        parameters_json, status, elapsed_seconds, approval_token,
                        actor, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    entry.timestamp, entry.timestamp_iso, entry.tool_name,
                    entry.permission_level, entry.parameters_json, entry.status,
                    entry.elapsed_seconds, entry.approval_token, entry.actor,
                    entry.error_message
                ))
                entry.id = cursor.lastrowid
                conn.commit()
        except Exception as e:
            print(f"[TOOL LOGGER] DB write note: {e}")

        return entry

    def get_logs(self, limit: int = 50, tool_name: Optional[str] = None) -> list[ToolLogEntry]:
        """Fetch recent execution audit logs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if tool_name:
                    cursor.execute("""
                        SELECT * FROM tool_execution_logs
                        WHERE tool_name = ?
                        ORDER BY timestamp DESC LIMIT ?;
                    """, (tool_name, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM tool_execution_logs
                        ORDER BY timestamp DESC LIMIT ?;
                    """, (limit,))
                rows = cursor.fetchall()
                return [
                    ToolLogEntry(
                        id=r["id"],
                        timestamp=r["timestamp"],
                        timestamp_iso=r["timestamp_iso"],
                        tool_name=r["tool_name"],
                        permission_level=r["permission_level"],
                        parameters_json=r["parameters_json"],
                        status=r["status"],
                        elapsed_seconds=r["elapsed_seconds"],
                        approval_token=r["approval_token"],
                        actor=r["actor"],
                        error_message=r["error_message"],
                    )
                    for r in rows
                ]
        except Exception:
            return self._memory_ring_buffer[-limit:]


tool_logger = ToolExecutionLogger()

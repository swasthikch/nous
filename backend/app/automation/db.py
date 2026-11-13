"""SQLite Database Manager for NOUS Computer & Task Automation (Phase 13)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.config import settings

logger = logging.getLogger("nous.automation.db")


def get_utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def init_automation_db(db_path: Path | None = None) -> None:
    """Initialize automation SQLite schema and enable Write-Ahead Logging (WAL)."""
    target_path = db_path or settings.AUTOMATION_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Scheduled Tasks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                action_type TEXT NOT NULL,
                interval_seconds INTEGER,
                cron_expression TEXT,
                payload_json TEXT,
                status TEXT DEFAULT 'active',
                last_run_at TEXT,
                next_run_at TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # Execution History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                command TEXT NOT NULL,
                status TEXT NOT NULL,
                exit_code INTEGER,
                output TEXT,
                execution_time_ms INTEGER,
                risk_level TEXT,
                timestamp TEXT NOT NULL
            );
        """)

        # Create indices for quick lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON scheduled_tasks(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exec_timestamp ON execution_history(timestamp DESC);")
        conn.commit()

    logger.info("Automation SQLite database initialized at %s with WAL mode.", target_path)


class AutomationDBManager:
    """Thread-safe SQLite database manager for Task Automation & Execution History."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.AUTOMATION_DB_PATH
        init_automation_db(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------- SCHEDULED TASKS ----------------

    def create_scheduled_task(
        self,
        name: str,
        action_type: str,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new recurring automation task."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = get_utc_now_iso()
        payload_str = json.dumps(payload or {})

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scheduled_tasks (
                    id, name, action_type, interval_seconds, cron_expression,
                    payload_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?);
                """,
                (task_id, name, action_type, interval_seconds, cron_expression, payload_str, now),
            )
            conn.commit()

        return self.get_scheduled_task(task_id) or {}

    def get_scheduled_task(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve a scheduled task by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scheduled_tasks WHERE id = ?;", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["payload"] = json.loads(res.get("payload_json") or "{}")
            except Exception:
                res["payload"] = {}
            return res

    def list_scheduled_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        """List scheduled tasks, optionally filtered by status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM scheduled_tasks WHERE status = ? ORDER BY created_at DESC;", (status,))
            else:
                cursor.execute("SELECT * FROM scheduled_tasks ORDER BY created_at DESC;")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["payload"] = json.loads(item.get("payload_json") or "{}")
                except Exception:
                    item["payload"] = {}
                results.append(item)
            return results

    def update_task_status(
        self,
        task_id: str,
        status: str,
        last_run_at: str | None = None,
        next_run_at: str | None = None,
    ) -> bool:
        """Update task status or execution timestamps."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE scheduled_tasks
                SET status = ?,
                    last_run_at = COALESCE(?, last_run_at),
                    next_run_at = COALESCE(?, next_run_at)
                WHERE id = ?;
                """,
                (status, last_run_at, next_run_at, task_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_scheduled_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scheduled_tasks WHERE id = ?;", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------- EXECUTION AUDIT HISTORY ----------------

    def record_execution(
        self,
        command: str,
        status: str,
        exit_code: int = 0,
        output: str = "",
        execution_time_ms: int = 0,
        risk_level: str = "safe",
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Record command execution result in audit history."""
        exec_id = f"exec_{uuid.uuid4().hex[:10]}"
        now = get_utc_now_iso()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO execution_history (
                    id, task_id, command, status, exit_code, output,
                    execution_time_ms, risk_level, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (exec_id, task_id, command, status, exit_code, output[:5000], execution_time_ms, risk_level, now),
            )
            conn.commit()

        return {
            "id": exec_id,
            "task_id": task_id,
            "command": command,
            "status": status,
            "exit_code": exit_code,
            "output": output[:5000],
            "execution_time_ms": execution_time_ms,
            "risk_level": risk_level,
            "timestamp": now,
        }

    def list_execution_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent command executions for audit inspection."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM execution_history ORDER BY timestamp DESC LIMIT ?;", (limit,))
            return [dict(r) for r in cursor.fetchall()]

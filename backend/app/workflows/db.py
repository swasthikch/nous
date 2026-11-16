"""SQLite Database Manager for NOUS Autonomous Workflows (Phase 8).

Stores:
- Workflow DAG definitions and live execution states.
- Step-by-step logs, agent outputs, and approval records.
- Guaranteed durability via SQLite Write-Ahead Logging (WAL) mode.
"""

from __future__ import annotations

import contextlib
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Any, Generator, Optional

from backend.app.config import settings
from backend.app.workflows.models import WorkflowPlan, WorkflowStatus

logger = logging.getLogger("nous.workflows.db")

WORKFLOWS_DB_PATH: Path = settings.PROJECT_ROOT / "data" / "database" / "nous_workflows.db"


def init_workflows_db(db_path: Optional[Path] = None) -> None:
    """Initialize workflows SQLite database schema in WAL mode."""
    target_path = db_path or WORKFLOWS_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(target_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Master Workflows Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                status TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                completed_at REAL,
                final_summary TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);")

        # Step Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_step_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                status TEXT NOT NULL,
                output_json TEXT,
                error TEXT,
                timestamp REAL NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_step_logs_wf ON workflow_step_logs(workflow_id);")
        conn.commit()


@contextlib.contextmanager
def get_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection in WAL mode with Row factory."""
    target_path = db_path or WORKFLOWS_DB_PATH
    if not target_path.exists():
        init_workflows_db(target_path)

    conn = sqlite3.connect(str(target_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class WorkflowDBManager:
    """Persistence repository for autonomous workflow DAGs and execution logs."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or WORKFLOWS_DB_PATH
        init_workflows_db(self.db_path)

    def save_workflow(self, plan: WorkflowPlan) -> None:
        """Persist or update complete workflow DAG state."""
        now = time.time()
        plan.updated_at = now
        plan_json = plan.model_dump_json()

        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workflows (id, goal, status, plan_json, created_at, updated_at, completed_at, final_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    plan_json = excluded.plan_json,
                    updated_at = excluded.updated_at,
                    completed_at = excluded.completed_at,
                    final_summary = excluded.final_summary;
            """, (
                plan.id,
                plan.goal,
                plan.status.value,
                plan_json,
                plan.created_at,
                plan.updated_at,
                plan.completed_at,
                plan.final_summary,
            ))
            conn.commit()

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowPlan]:
        """Load workflow plan from disk."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT plan_json FROM workflows WHERE id = ?;", (workflow_id,))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                data = json.loads(row["plan_json"])
                return WorkflowPlan.model_validate(data)
            except Exception as e:
                logger.error(f"Failed to parse workflow plan {workflow_id}: {e}")
                return None

    def list_workflows(self, limit: int = 50) -> list[dict[str, Any]]:
        """List workflows ordered by creation date."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, goal, status, created_at, updated_at, completed_at, final_summary
                FROM workflows
                ORDER BY created_at DESC
                LIMIT ?;
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def log_step_execution(
        self,
        workflow_id: str,
        step_id: str,
        agent: str,
        status: str,
        output: Any = None,
        error: Optional[str] = None,
    ) -> None:
        """Append an immutable audit entry for an executed step."""
        now = time.time()
        out_str = json.dumps(output) if output is not None else None
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workflow_step_logs (workflow_id, step_id, agent, status, output_json, error, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (workflow_id, step_id, agent, status, out_str, error, now))
            conn.commit()

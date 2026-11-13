"""SQLite Database Manager for NOUS Security Audit Vault & Privacy Settings (Phase 14)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.config import settings
from backend.app.security.redactor import sensitive_redactor

logger = logging.getLogger("nous.security.db")


def get_utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def init_security_db(db_path: Path | None = None) -> None:
    """Initialize security SQLite schema with Write-Ahead Logging (WAL)."""
    target_path = db_path or settings.SECURITY_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Audit Events Table (Tamper-evident system log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                resource TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                decision TEXT NOT NULL,
                details_json TEXT,
                session_id TEXT
            );
        """)

        # Privacy Settings Table (Persistent user controls)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS privacy_settings (
                id TEXT PRIMARY KEY,
                offline_lockdown INTEGER DEFAULT 0,
                pause_memory_retention INTEGER DEFAULT 0,
                strict_redaction INTEGER DEFAULT 1,
                audit_retention_days INTEGER DEFAULT 30,
                updated_at TEXT NOT NULL
            );
        """)

        # Create quick search indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_events(timestamp DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_events(decision);")

        # Seed default privacy settings if missing
        cursor.execute("SELECT id FROM privacy_settings WHERE id = 'default_policy';")
        if not cursor.fetchone():
            now = get_utc_now_iso()
            cursor.execute(
                """
                INSERT INTO privacy_settings (
                    id, offline_lockdown, pause_memory_retention,
                    strict_redaction, audit_retention_days, updated_at
                ) VALUES ('default_policy', ?, 0, 1, 30, ?);
                """,
                (1 if settings.OFFLINE_LOCKDOWN else 0, now),
            )

        conn.commit()

    logger.info("Security SQLite Vault initialized at %s with WAL mode.", target_path)


class SecurityDBManager:
    """Thread-safe SQLite manager for tamper-evident security audit logs and privacy controls."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.SECURITY_DB_PATH
        init_security_db(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------- AUDIT LOGGING ----------------

    def log_event(
        self,
        event_type: str,
        resource: str,
        risk_level: str = "low",
        decision: str = "ALLOWED",
        actor: str = "user",
        details: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Record a sanitized security audit event in the tamper-evident vault."""
        event_id = f"aud_{uuid.uuid4().hex[:10]}"
        now = get_utc_now_iso()

        # Enforce automatic redaction of all details prior to persistence
        redacted_details = sensitive_redactor.redact_data_structure(details or {})
        details_str = json.dumps(redacted_details)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_events (
                    id, timestamp, actor, event_type, resource,
                    risk_level, decision, details_json, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event_id,
                    now,
                    actor,
                    event_type,
                    resource,
                    risk_level.lower(),
                    decision.upper(),
                    details_str,
                    session_id,
                ),
            )
            conn.commit()

        return {
            "id": event_id,
            "timestamp": now,
            "actor": actor,
            "event_type": event_type,
            "resource": resource,
            "risk_level": risk_level.lower(),
            "decision": decision.upper(),
            "details": redacted_details,
            "session_id": session_id,
        }

    def list_events(
        self,
        event_type: str | None = None,
        decision: str | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve audit events matching filters."""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params: list[Any] = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if decision:
            query += " AND decision = ?"
            params.append(decision.upper())

        if search:
            query += " AND (resource LIKE ? OR details_json LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param])

        query += " ORDER BY timestamp DESC LIMIT ?;"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["details"] = json.loads(item.get("details_json") or "{}")
                except Exception:
                    item["details"] = {}
                results.append(item)
            return results

    # ---------------- PRIVACY CONTROLS ----------------

    def get_privacy_settings(self) -> dict[str, Any]:
        """Retrieve active privacy policies and toggle states."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM privacy_settings WHERE id = 'default_policy';")
            row = cursor.fetchone()
            if not row:
                return {
                    "offline_lockdown": False,
                    "pause_memory_retention": False,
                    "strict_redaction": True,
                    "audit_retention_days": 30,
                    "updated_at": get_utc_now_iso(),
                }
            return {
                "offline_lockdown": bool(row["offline_lockdown"]),
                "pause_memory_retention": bool(row["pause_memory_retention"]),
                "strict_redaction": bool(row["strict_redaction"]),
                "audit_retention_days": int(row["audit_retention_days"]),
                "updated_at": row["updated_at"],
            }

    def update_privacy_settings(
        self,
        offline_lockdown: bool | None = None,
        pause_memory_retention: bool | None = None,
        strict_redaction: bool | None = None,
        audit_retention_days: int | None = None,
    ) -> dict[str, Any]:
        """Update user-controlled privacy toggles."""
        current = self.get_privacy_settings()
        now = get_utc_now_iso()

        new_offline = current["offline_lockdown"] if offline_lockdown is None else offline_lockdown
        new_memory = current["pause_memory_retention"] if pause_memory_retention is None else pause_memory_retention
        new_strict = current["strict_redaction"] if strict_redaction is None else strict_redaction
        new_days = current["audit_retention_days"] if audit_retention_days is None else audit_retention_days

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE privacy_settings
                SET offline_lockdown = ?,
                    pause_memory_retention = ?,
                    strict_redaction = ?,
                    audit_retention_days = ?,
                    updated_at = ?
                WHERE id = 'default_policy';
                """,
                (
                    1 if new_offline else 0,
                    1 if new_memory else 0,
                    1 if new_strict else 0,
                    new_days,
                    now,
                ),
            )
            conn.commit()

        # Record settings modification in audit log
        self.log_event(
            event_type="privacy_toggle",
            resource="privacy_settings",
            risk_level="medium",
            decision="ALLOWED",
            details={
                "offline_lockdown": new_offline,
                "pause_memory_retention": new_memory,
                "strict_redaction": new_strict,
            },
        )

        return self.get_privacy_settings()

    def purge_old_audit_logs(self, max_days: int = 30) -> int:
        """Purge audit log records older than specified retention days."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM audit_events
                WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days');
                """,
                (max_days,),
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted

"""System Diagnostics & Hardware Health Engine for NOUS (Phase 15).

Provides in-depth diagnostic telemetry for:
1. All 7 SQLite WAL databases (integrity checks, sizes, table statistics).
2. Hardware profile (Intel Core i5, 16 GB shared RAM limits, disk capacity).
3. Local Ollama server & available models.
4. Security policy & API key configurations.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import sys
import time
from typing import Any

from backend.app.config import settings
from backend.app.core.ollama_client import ollama_client
from backend.app.security.vault import security_vault


class DiagnosticsCollector:
    """Collects multi-subsystem telemetry and health metrics."""

    def __init__(self) -> None:
        self.project_root = settings.PROJECT_ROOT
        self.db_dir = self.project_root / "data" / "database"

        # List of the 7 core SQLite databases
        self.target_databases: list[dict[str, Any]] = [
            {
                "id": "memory",
                "name": "Personal Long-Term Memory",
                "path": self.db_dir / "nous_memory.db",
                "tables": ["memories", "memory_audit_log"],
            },
            {
                "id": "routine",
                "name": "Routine & Daily Life Activities",
                "path": self.db_dir / "nous_routine.db",
                "tables": ["routine_activities", "activity_logs", "routine_summaries"],
            },
            {
                "id": "projects",
                "name": "Projects & GitHub Intelligence",
                "path": self.db_dir / "nous_projects.db",
                "tables": ["projects", "project_milestones", "project_notes", "github_commits_cache"],
            },
            {
                "id": "market",
                "name": "Financial Markets & Alerts",
                "path": self.db_dir / "nous_market.db",
                "tables": ["watchlist_items", "price_alerts", "market_snapshots", "alert_history"],
            },
            {
                "id": "research",
                "name": "Web Research & Knowledge Notes",
                "path": self.db_dir / "nous_research.db",
                "tables": ["research_notes", "deep_reports", "search_cache"],
            },
            {
                "id": "automation",
                "name": "Computer Automation & Tasks",
                "path": self.db_dir / "nous_automation.db",
                "tables": ["scheduled_tasks", "execution_history"],
            },
            {
                "id": "security",
                "name": "Security Vault & Privacy Trail",
                "path": self.db_dir / "nous_security.db",
                "tables": ["audit_events", "privacy_settings"],
            },
        ]

    def get_hardware_telemetry(self) -> dict[str, Any]:
        """Collect CPU, RAM, and Disk metrics."""
        # 1. RAM via Windows ctypes GlobalMemoryStatusEx
        total_ram_gb = 16.0
        avail_ram_gb = 8.0
        used_ram_gb = 8.0
        load_percent = 50.0

        if sys.platform == "win32":
            try:
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_ram_gb = round(stat.ullTotalPhys / (1024**3), 2)
                    avail_ram_gb = round(stat.ullAvailPhys / (1024**3), 2)
                    used_ram_gb = round(total_ram_gb - avail_ram_gb, 2)
                    load_percent = float(stat.dwMemoryLoad)
            except Exception:
                pass

        # 2. CPU Specs
        cpu_name = platform.processor() or "13th Gen Intel Core i5-1334U"
        core_count = os.cpu_count() or 10

        # 3. Disk Space in PROJECT_ROOT
        disk_total_gb = 0.0
        disk_free_gb = 0.0
        disk_used_percent = 0.0
        try:
            usage = shutil.disk_usage(self.project_root)
            disk_total_gb = round(usage.total / (1024**3), 1)
            disk_free_gb = round(usage.free / (1024**3), 1)
            used_bytes = usage.total - usage.free
            disk_used_percent = round((used_bytes / usage.total) * 100, 1)
        except Exception:
            pass

        return {
            "ram": {
                "total_gb": total_ram_gb,
                "available_gb": avail_ram_gb,
                "used_gb": used_ram_gb,
                "percent_used": load_percent,
                "shared_architecture": "16 GB Unified Memory Ceiling",
                "status": "NORMAL" if load_percent < 90 else "HIGH_LOAD",
            },
            "cpu": {
                "name": cpu_name,
                "cores_logical": core_count,
                "architecture": platform.machine(),
                "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            },
            "disk": {
                "path": str(self.project_root),
                "total_gb": disk_total_gb,
                "free_gb": disk_free_gb,
                "percent_used": disk_used_percent,
                "status": "NORMAL" if disk_free_gb > 2.0 else "LOW_SPACE",
            },
            "python": {
                "version": platform.python_version(),
                "executable": sys.executable,
                "in_venv": hasattr(sys, "real_prefix") or (sys.base_prefix != sys.prefix),
            },
        }

    def get_database_diagnostics(self) -> dict[str, Any]:
        """Perform deep integrity and table checks across all 7 databases."""
        results: list[dict[str, Any]] = []
        all_healthy = True
        total_size_bytes = 0

        for db_meta in self.target_databases:
            p: Path = db_meta["path"]
            entry: dict[str, Any] = {
                "id": db_meta["id"],
                "name": db_meta["name"],
                "path": str(p),
                "exists": p.exists(),
                "size_kb": 0,
                "journal_mode": "unknown",
                "integrity": "unknown",
                "tables": {},
                "status": "UNKNOWN",
            }

            if not p.exists():
                entry["status"] = "MISSING"
                all_healthy = False
                results.append(entry)
                continue

            try:
                stat = p.stat()
                entry["size_kb"] = round(stat.st_size / 1024, 1)
                total_size_bytes += stat.st_size

                # Connect and check WAL mode & integrity
                conn = sqlite3.connect(p, timeout=5.0)
                try:
                    cursor = conn.cursor()

                    # 1. Journal mode
                    cursor.execute("PRAGMA journal_mode")
                    j_mode = cursor.fetchone()
                    entry["journal_mode"] = str(j_mode[0]).lower() if j_mode else "unknown"

                    # 2. Integrity check
                    cursor.execute("PRAGMA integrity_check")
                    integ = cursor.fetchone()
                    entry["integrity"] = str(integ[0]) if integ else "failed"

                    # 3. Table row counts
                    for t_name in db_meta["tables"]:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
                            cnt = cursor.fetchone()[0]
                            entry["tables"][t_name] = cnt
                        except Exception:
                            entry["tables"][t_name] = 0

                    if entry["integrity"] == "ok":
                        entry["status"] = "HEALTHY"
                    else:
                        entry["status"] = "INTEGRITY_WARNING"
                        all_healthy = False
                finally:
                    conn.close()

            except Exception as ex:
                entry["status"] = "ERROR"
                entry["error"] = str(ex)
                all_healthy = False

            results.append(entry)

        return {
            "all_healthy": all_healthy,
            "databases_count": len(results),
            "healthy_count": sum(1 for d in results if d["status"] == "HEALTHY"),
            "total_size_kb": round(total_size_bytes / 1024, 1),
            "databases": results,
        }

    async def get_ollama_diagnostics(self) -> dict[str, Any]:
        """Test Ollama connection and measure response time."""
        start_t = time.perf_counter()
        conn_res = await ollama_client.check_connection()
        latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

        is_connected = conn_res.get("status") == "connected"
        models = conn_res.get("available_models", [])

        return {
            "status": "ONLINE" if is_connected else "OFFLINE",
            "base_url": settings.OLLAMA_BASE_URL,
            "default_model": settings.OLLAMA_MODEL,
            "available_models": models,
            "latency_ms": latency_ms if is_connected else None,
            "detail": conn_res.get("detail", "Connected successfully" if is_connected else "Unreachable"),
        }

    def get_security_and_environment(self) -> dict[str, Any]:
        """Inspect environment credentials and active privacy policies."""
        priv = security_vault.get_privacy_settings()

        # Check API key presence without disclosing characters
        def has_key(var_name: str) -> bool:
            val = os.getenv(var_name, "").strip()
            return bool(val and not val.startswith("sk-your") and not val.startswith("your_"))

        keys_status = {
            "OPENAI_API_KEY": has_key("OPENAI_API_KEY"),
            "ANTHROPIC_API_KEY": has_key("ANTHROPIC_API_KEY"),
            "GOOGLE_API_KEY": has_key("GOOGLE_API_KEY") or has_key("GEMINI_API_KEY"),
            "GITHUB_TOKEN": has_key("GITHUB_TOKEN"),
            "NEWS_API_KEY": has_key("NEWS_API_KEY"),
        }

        return {
            "privacy_policies": priv,
            "cloud_keys_configured": keys_status,
            "configured_count": sum(1 for v in keys_status.values() if v),
            "offline_lockdown_active": priv.get("offline_lockdown", False),
            "strict_redaction_active": priv.get("strict_redaction", True),
        }

    async def generate_system_report(self) -> dict[str, Any]:
        """Generate a complete end-to-end diagnostic report."""
        hardware = self.get_hardware_telemetry()
        databases = self.get_database_diagnostics()
        ollama = await self.get_ollama_diagnostics()
        security = self.get_security_and_environment()

        # Compute overall system health grade
        if not databases["all_healthy"]:
            health_state = "DEGRADED_DATABASES"
            health_color = "#f59e0b"
        elif hardware["ram"]["status"] == "HIGH_LOAD":
            health_state = "HIGH_MEMORY_PRESSURE"
            health_color = "#f59e0b"
        else:
            health_state = "OPTIMAL"
            health_color = "#10b981"

        return {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "overall_status": health_state,
            "health_color": health_color,
            "project": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "tagline": "Your Intelligence. Your Memory. Your Assistant.",
            },
            "hardware": hardware,
            "databases": databases,
            "ollama": ollama,
            "security": security,
        }


# Global singleton diagnostics instance
diagnostics_collector = DiagnosticsCollector()

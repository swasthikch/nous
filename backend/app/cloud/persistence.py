"""Zero-Budget Cloud Persistence & State Backup Manager for NOUS (Phase 11).

Provides:
- Safe WAL Checkpointing across all SQLite databases before backup.
- Unified compressed state archiving (data/backups/latest_snapshot.tar.gz).
- Cloud restoration hook for containerized deployments (Render/Fly/Railway).
- Zero third-party compilation dependencies (pure standard library).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import sqlite3
import tarfile
import time
from typing import Any, Optional

from backend.app.config import settings

logger = logging.getLogger("nous.cloud.persistence")

BACKUPS_DIR: Path = settings.PROJECT_ROOT / "data" / "backups"
DATABASE_DIR: Path = settings.PROJECT_ROOT / "data" / "database"


class CloudPersistenceManager:
    """Manages database state backups and container restart recovery."""

    def __init__(self, db_dir: Optional[Path] = None, backup_dir: Optional[Path] = None) -> None:
        self.db_dir = db_dir or DATABASE_DIR
        self.backup_dir = backup_dir or BACKUPS_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.last_backup_time: Optional[float] = None
        self.last_backup_size: int = 0

    def checkpoint_wal_databases(self) -> list[str]:
        """Execute PRAGMA wal_checkpoint(FULL) on all active SQLite databases."""
        checkpointed = []
        if not self.db_dir.exists():
            return checkpointed

        for db_file in self.db_dir.glob("*.db"):
            try:
                with sqlite3.connect(str(db_file), timeout=10.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA wal_checkpoint(FULL);")
                    checkpointed.append(db_file.name)
            except Exception as e:
                logger.warning(f"Could not checkpoint WAL for {db_file.name}: {e}")

        return checkpointed

    def create_snapshot(self, snapshot_name: Optional[str] = None) -> Path:
        """Create a compressed tar.gz snapshot of all databases and memory."""
        # 1. Flush WAL logs
        self.checkpoint_wal_databases()

        # 2. Package database files
        timestamp = int(time.time())
        name = snapshot_name or f"nous_snapshot_{timestamp}.tar.gz"
        dest_archive = self.backup_dir / name
        latest_archive = self.backup_dir / "latest_snapshot.tar.gz"

        with tarfile.open(dest_archive, "w:gz") as tar:
            if self.db_dir.exists():
                for item in self.db_dir.glob("*.db"):
                    tar.add(item, arcname=f"database/{item.name}")

        # Update symlink or copy to latest
        shutil.copy2(dest_archive, latest_archive)

        self.last_backup_time = time.time()
        self.last_backup_size = dest_archive.stat().st_size
        logger.info(f"Created state snapshot: {dest_archive.name} ({self.last_backup_size} bytes)")
        return dest_archive

    def restore_snapshot(self, archive_path: Optional[Path] = None) -> dict[str, Any]:
        """Restore database state from snapshot archive."""
        source = archive_path or (self.backup_dir / "latest_snapshot.tar.gz")
        if not source.exists():
            return {"success": False, "message": f"Snapshot archive '{source}' not found."}

        self.db_dir.mkdir(parents=True, exist_ok=True)
        restored_files = []

        with tarfile.open(source, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.startswith("database/") and member.name.endswith(".db"):
                    base_name = Path(member.name).name
                    dest_file = self.db_dir / base_name
                    # Extract single file
                    f = tar.extractfile(member)
                    if f:
                        with open(dest_file, "wb") as out:
                            out.write(f.read())
                        restored_files.append(base_name)

        return {
            "success": True,
            "restored_count": len(restored_files),
            "restored_files": restored_files,
            "source": source.name,
        }

    def get_status(self) -> dict[str, Any]:
        """Get cloud persistence health and database statistics."""
        databases = []
        total_size = 0
        if self.db_dir.exists():
            for db in self.db_dir.glob("*.db"):
                size = db.stat().st_size
                total_size += size
                databases.append({"name": db.name, "size_bytes": size})

        return {
            "database_count": len(databases),
            "databases": databases,
            "total_database_bytes": total_size,
            "last_backup_time": self.last_backup_time,
            "last_backup_size_bytes": self.last_backup_size,
            "backups_available": len(list(self.backup_dir.glob("*.tar.gz"))),
        }


cloud_persistence = CloudPersistenceManager()

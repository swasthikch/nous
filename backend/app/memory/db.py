"""SQLite Database Initialization and Connection Management for NOUS 5-Tier Memory."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from backend.app.config import PROJECT_ROOT

DB_DIR = PROJECT_ROOT / "data" / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "nous_memory.db"


def init_database(db_file: Path = DB_PATH) -> None:
    """Initialize memory SQLite schema and perform safe non-destructive migration."""
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Enable WAL mode for high concurrent throughput and crash safety
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Base table creation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tier TEXT DEFAULT 'personal',
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            content TEXT NOT NULL,
            importance REAL DEFAULT 0.5,
            provenance TEXT DEFAULT 'manual',
            access_count INTEGER DEFAULT 0,
            last_accessed_at REAL,
            metadata_json TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
    """)

    # 2. Check existing columns and run safe migrations if upgrading older databases
    cursor.execute("PRAGMA table_info(memories);")
    existing_cols = {row[1] for row in cursor.fetchall()}

    if "tier" not in existing_cols:
        cursor.execute("ALTER TABLE memories ADD COLUMN tier TEXT DEFAULT 'personal';")
    if "importance" not in existing_cols:
        cursor.execute("ALTER TABLE memories ADD COLUMN importance REAL DEFAULT 0.5;")
    if "provenance" not in existing_cols:
        cursor.execute("ALTER TABLE memories ADD COLUMN provenance TEXT DEFAULT 'manual';")
    if "access_count" not in existing_cols:
        cursor.execute("ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0;")
    if "last_accessed_at" not in existing_cols:
        cursor.execute("ALTER TABLE memories ADD COLUMN last_accessed_at REAL;")

    # 3. Create high-performance lookup indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_tier ON memories(tier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_cat ON memories(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_active ON memories(is_active);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_imp ON memories(importance);")

    # 4. Table: memory_settings (key-value configuration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    """)

    # Default settings
    default_settings = [
        ("memory_enabled", "true"),
        ("retrieval_limit", "5"),
        ("auto_extract", "true"),
        ("importance_threshold", "0.3"),
    ]
    now = time.time()
    for k, v in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO memory_settings (key, value, updated_at)
            VALUES (?, ?, ?);
        """, (k, v, now))

    conn.commit()
    conn.close()


@contextmanager
def get_db(db_file: Path = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with row-dict factory."""
    conn = sqlite3.connect(str(db_file), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

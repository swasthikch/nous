"""SQLite Database Initialization and Connection Management for NOUS Memory."""

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


def init_database(db_file: Path = DB_PATH):
    """Initialize memory SQLite schema and default configuration."""
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Enable WAL mode for high concurrent throughput and crash safety
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table: memories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
    """)

    # Indexes for fast lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_cat ON memories(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_active ON memories(is_active);")

    # Table: memory_settings (key-value configuration)
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
        ("auto_suggest", "true"),
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


# Initialize on import
init_database()

"""Database Management for NOUS Daily Life and Routines."""

import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from backend.app.config import PROJECT_ROOT

DB_DIR = PROJECT_ROOT / "data" / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
ROUTINE_DB_PATH = DB_DIR / "nous_routine.db"


def init_routine_database(db_file: Path = ROUTINE_DB_PATH):
    """Initialize activities and routine SQLite tables."""
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table: activities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT DEFAULT '',
            is_fixed INTEGER DEFAULT 0,
            recurrence TEXT DEFAULT 'none',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_category ON activities(category);")

    conn.commit()
    conn.close()


@contextmanager
def get_routine_db(db_file: Path = ROUTINE_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for routine SQLite connections with row-dict factory."""
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
init_routine_database()

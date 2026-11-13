"""SQLite Database Initialization & Connection Pool for NOUS Project Intelligence.

Stores structured project records, tech stacks, milestones, and task items.
Enforces Write-Ahead Logging (WAL) mode for concurrent FastAPI access.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from backend.app.config import settings

PROJECTS_DB_PATH = settings.PROJECT_ROOT / "data" / "database" / "nous_projects.db"


def init_projects_database() -> None:
    """Initialize the SQLite projects database with tables and indexes."""
    PROJECTS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(PROJECTS_DB_PATH) as conn:
        cursor = conn.cursor()

        # Enable Write-Ahead Logging (WAL) for safe concurrent reads & writes
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 1. Projects Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                tech_stack TEXT DEFAULT '',
                repo_url TEXT DEFAULT '',
                start_date TEXT NOT NULL,
                deadline TEXT DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'active',
                progress_percent INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)

        # 2. Milestones Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT DEFAULT '',
                is_completed INTEGER DEFAULT 0,
                completed_at REAL DEFAULT NULL,
                notes TEXT DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)

        # 3. Project Tasks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_status ON projects(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_priority ON projects(priority);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestone_proj ON milestones(project_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_proj ON project_tasks(project_id);")

        conn.commit()


@contextmanager
def get_projects_db():
    """Context manager yielding a thread-safe connection to nous_projects.db."""
    conn = sqlite3.connect(PROJECTS_DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

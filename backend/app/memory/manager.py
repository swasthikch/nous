"""Personal Memory Manager for NOUS.

Coordinates persistent storage, retrieval, category management,
and context injection for user profiles, personal preferences,
project milestones, conversation decisions, and routines.
"""

import json
import time
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.memory.db import get_db, init_database


class MemoryCategory(str, Enum):
    USER_PROFILE = "user_profile"    # Name, interests, learning goals, preferred communication
    PERSONAL_INFO = "personal_info"  # Preferences, important dates, settings
    PROJECT = "project"              # Active projects, milestones, tech stack, decisions
    CONVERSATION = "conversation"    # Key summaries, decisions, unfinished tasks
    ROUTINE = "routine"              # Schedules, habits, study hours, fitness


class MemoryItem(BaseModel):
    id: int
    category: MemoryCategory
    key: str
    content: str
    metadata: dict = Field(default_factory=dict)
    is_active: bool = True
    created_at: float
    updated_at: float


class MemoryManager:
    """Interface for querying and updating persistent long-term memories."""

    def __init__(self):
        init_database()

    def is_memory_enabled(self) -> bool:
        """Check if long-term memory system is toggled active."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memory_settings WHERE key = 'memory_enabled';")
            row = cursor.fetchone()
            if row:
                return row["value"].lower() == "true"
            return True

    def set_memory_enabled(self, enabled: bool):
        """Toggle memory system on or off."""
        now = time.time()
        val = "true" if enabled else "false"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memory_settings (key, value, updated_at)
                VALUES ('memory_enabled', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
            """, (val, now))

    def save_memory(
        self,
        category: MemoryCategory,
        key: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> MemoryItem:
        """Create or update a memory item."""
        now = time.time()
        meta_str = json.dumps(metadata or {})
        clean_key = key.strip().lower()

        with get_db() as conn:
            cursor = conn.cursor()
            # Check if matching active key exists in this category
            cursor.execute("""
                SELECT id FROM memories 
                WHERE category = ? AND key = ? AND is_active = 1;
            """, (category.value, clean_key))
            existing = cursor.fetchone()

            if existing:
                memory_id = existing["id"]
                cursor.execute("""
                    UPDATE memories
                    SET content = ?, metadata_json = ?, updated_at = ?
                    WHERE id = ?;
                """, (content, meta_str, now, memory_id))
            else:
                cursor.execute("""
                    INSERT INTO memories (category, key, content, metadata_json, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?);
                """, (category.value, clean_key, content, meta_str, now, now))
                memory_id = cursor.lastrowid

        # Return after transaction is committed
        return self.get_memory(memory_id)  # type: ignore

    def get_memory(self, memory_id: int) -> Optional[MemoryItem]:
        """Fetch a specific memory by its primary key ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?;", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return MemoryItem(
                id=row["id"],
                category=MemoryCategory(row["category"]),
                key=row["key"],
                content=row["content"],
                metadata=json.loads(row["metadata_json"] or "{}"),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        key: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Update fields of an existing memory."""
        now = time.time()
        current = self.get_memory(memory_id)
        if not current:
            return False

        new_content = content if content is not None else current.content
        new_key = key.strip().lower() if key is not None else current.key
        new_category = category.value if category is not None else current.category.value
        new_meta = json.dumps(metadata if metadata is not None else current.metadata)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories
                SET category = ?, key = ?, content = ?, metadata_json = ?, updated_at = ?
                WHERE id = ?;
            """, (new_category, new_key, new_content, new_meta, now, memory_id))
            return cursor.rowcount > 0

    def delete_memory(self, memory_id: int, hard_delete: bool = False) -> bool:
        """Delete or soft-delete a memory item."""
        with get_db() as conn:
            cursor = conn.cursor()
            if hard_delete:
                cursor.execute("DELETE FROM memories WHERE id = ?;", (memory_id,))
            else:
                now = time.time()
                cursor.execute("""
                    UPDATE memories SET is_active = 0, updated_at = ? WHERE id = ?;
                """, (now, memory_id))
            return cursor.rowcount > 0

    def list_memories(
        self,
        category: Optional[MemoryCategory] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
    ) -> list[MemoryItem]:
        """List active memories filtered by category and/or query string."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM memories WHERE is_active = 1"
            params: list[Any] = []

            if category:
                query += " AND category = ?"
                params.append(category.value)

            if search_query and search_query.strip():
                clean_q = f"%{search_query.strip()}%"
                query += " AND (key LIKE ? OR content LIKE ?)"
                params.extend([clean_q, clean_q])

            query += " ORDER BY updated_at DESC LIMIT ?;"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                MemoryItem(
                    id=r["id"],
                    category=MemoryCategory(r["category"]),
                    key=r["key"],
                    content=r["content"],
                    metadata=json.loads(r["metadata_json"] or "{}"),
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def get_relevant_memories(self, query: str, limit: int = 5) -> list[MemoryItem]:
        """Retrieve memories relevant to the user query for context augmentation.
        
        Designed with an abstracted query interface so full vector embeddings
        can be dropped in seamlessly.
        """
        if not self.is_memory_enabled():
            return []

        tokens = [t.lower() for t in query.split() if len(t) > 2]
        all_active = self.list_memories(limit=100)

        # Always include active user profile memories (e.g. preferred name, style)
        profile_memories = [m for m in all_active if m.category == MemoryCategory.USER_PROFILE]

        # Score other memories by keyword match
        scored: list[tuple[int, MemoryItem]] = []
        for m in all_active:
            if m.category == MemoryCategory.USER_PROFILE:
                continue
            text = f"{m.key} {m.content} {m.category.value}".lower()
            score = sum(1 for t in tokens if t in text)
            if score > 0:
                scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        relevant = profile_memories + [item for _, item in scored[:limit]]
        return relevant[:limit + len(profile_memories)]

    def format_memories_for_prompt(self, memories: list[MemoryItem]) -> str:
        """Format memories as clean, concise system observations for the LLM."""
        if not memories:
            return ""

        lines = ["[CONFIRMED USER MEMORIES - Use these facts in your response]:"]
        for m in memories:
            cat_label = m.category.value.replace("_", " ").title()
            lines.append(f"- ({cat_label}) {m.key}: {m.content}")

        return "\n".join(lines)


memory_manager = MemoryManager()

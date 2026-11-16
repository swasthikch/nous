"""Central Memory Manager for NOUS 5-Tier Memory Operating System.

Coordinates:
- 5-Tier Memory Taxonomy (Working, Personal, Project, Knowledge, Episodic).
- Duplicate Detection & Smart Updates.
- Stanford Cognitive Ranking (Relevance, Importance, Recency Decay).
- Passive Conversational Extraction without recording pleasantries or secrets.
- Provenance & Access Tracking.
- Memory Export (JSON & Markdown) and Selective Wipe.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

from backend.app.memory.db import get_db, init_database
from backend.app.memory.models import (
    MemoryTier,
    MemoryCategory,
    MemoryItem,
    MemoryExport,
    category_to_tier,
)
from backend.app.memory.ranker import memory_ranker
from backend.app.memory.extractor import memory_extractor, ExtractedCandidate


class MemoryManager:
    """Master controller for all persistent memory operations."""

    def __init__(self) -> None:
        init_database()
        self.ranker = memory_ranker
        self.extractor = memory_extractor

    # ---------------- 1. SETTINGS & TOGGLES ----------------

    def is_memory_enabled(self) -> bool:
        """Check if long-term memory system is toggled active."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memory_settings WHERE key = 'memory_enabled';")
            row = cursor.fetchone()
            if row:
                return str(row["value"]).lower() == "true"
            return True

    def set_memory_enabled(self, enabled: bool) -> None:
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

    def is_auto_extract_enabled(self) -> bool:
        """Check if passive extraction from conversation is enabled."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memory_settings WHERE key = 'auto_extract';")
            row = cursor.fetchone()
            if row:
                return str(row["value"]).lower() == "true"
            return True

    # ---------------- 2. STORAGE & DEDUPLICATION ----------------

    def save_memory(
        self,
        category: str | MemoryCategory,
        key: str,
        content: str,
        tier: Optional[MemoryTier] = None,
        importance: float = 0.5,
        provenance: str = "manual",
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryItem:
        """Create or update a memory item with duplicate detection."""
        now = time.time()
        clean_key = key.strip().lower()
        clean_content = content.strip()

        # Determine category and tier
        if isinstance(category, MemoryCategory):
            cat_obj = category
        else:
            try:
                cat_obj = MemoryCategory(str(category).lower().strip())
            except ValueError:
                cat_obj = MemoryCategory.PERSONAL_INFO

        tier_obj = tier if tier is not None else category_to_tier(cat_obj)
        meta_dict = metadata or {}
        meta_str = json.dumps(meta_dict)

        with get_db() as conn:
            cursor = conn.cursor()
            # Duplicate check: matches active key within same tier/category
            cursor.execute("""
                SELECT id, content FROM memories 
                WHERE tier = ? AND category = ? AND key = ? AND is_active = 1;
            """, (tier_obj.value, cat_obj.value, clean_key))
            existing = cursor.fetchone()

            if existing:
                memory_id = existing["id"]
                cursor.execute("""
                    UPDATE memories
                    SET content = ?, importance = ?, metadata_json = ?, updated_at = ?
                    WHERE id = ?;
                """, (clean_content, importance, meta_str, now, memory_id))
            else:
                cursor.execute("""
                    INSERT INTO memories (
                        tier, category, key, content, importance, provenance,
                        access_count, last_accessed_at, metadata_json, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 1, ?, ?);
                """, (
                    tier_obj.value, cat_obj.value, clean_key, clean_content,
                    importance, provenance, now, meta_str, now, now
                ))
                memory_id = cursor.lastrowid

        return self.get_memory(memory_id)  # type: ignore

    def get_memory(self, memory_id: int) -> Optional[MemoryItem]:
        """Fetch a specific memory by its primary key ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?;", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_item(row)

    def _row_to_item(self, row: Any) -> MemoryItem:
        """Convert SQLite Row to validated MemoryItem."""
        tier_val = row["tier"] if "tier" in row.keys() and row["tier"] else "personal"
        try:
            tier_obj = MemoryTier(tier_val)
        except ValueError:
            tier_obj = MemoryTier.PERSONAL

        try:
            cat_obj = MemoryCategory(row["category"])
        except ValueError:
            cat_obj = MemoryCategory.PERSONAL_INFO

        imp = float(row["importance"]) if "importance" in row.keys() and row["importance"] is not None else 0.5
        prov = str(row["provenance"]) if "provenance" in row.keys() and row["provenance"] else "manual"
        cnt = int(row["access_count"]) if "access_count" in row.keys() and row["access_count"] is not None else 0
        last_acc = float(row["last_accessed_at"]) if "last_accessed_at" in row.keys() and row["last_accessed_at"] is not None else None

        return MemoryItem(
            id=row["id"],
            tier=tier_obj,
            category=cat_obj,
            key=row["key"],
            content=row["content"],
            importance=imp,
            provenance=prov,
            access_count=cnt,
            last_accessed_at=last_acc,
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
        category: Optional[MemoryCategory | str] = None,
        tier: Optional[MemoryTier] = None,
        importance: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update fields of an existing memory item."""
        current = self.get_memory(memory_id)
        if not current:
            return False

        now = time.time()
        new_content = content if content is not None else current.content
        new_key = key.strip().lower() if key is not None else current.key
        new_cat = (category.value if isinstance(category, MemoryCategory) else category) if category else current.category.value
        new_tier = (tier.value if isinstance(tier, MemoryTier) else tier) if tier else current.tier.value
        new_imp = importance if importance is not None else current.importance
        new_meta = json.dumps(metadata if metadata is not None else current.metadata)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories
                SET tier = ?, category = ?, key = ?, content = ?,
                    importance = ?, metadata_json = ?, updated_at = ?
                WHERE id = ?;
            """, (new_tier, new_cat, new_key, new_content, new_imp, new_meta, now, memory_id))
            return cursor.rowcount > 0

    def delete_memory(self, memory_id: int, hard_delete: bool = False) -> bool:
        """Delete or soft-delete a memory item."""
        with get_db() as conn:
            cursor = conn.cursor()
            if hard_delete:
                cursor.execute("DELETE FROM memories WHERE id = ?;", (memory_id,))
            else:
                now = time.time()
                cursor.execute("UPDATE memories SET is_active = 0, updated_at = ? WHERE id = ?;", (now, memory_id))
            return cursor.rowcount > 0

    def list_memories(
        self,
        tier: Optional[MemoryTier] = None,
        category: Optional[MemoryCategory | str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
    ) -> list[MemoryItem]:
        """List active memories filtered by tier, category, or search query."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM memories WHERE is_active = 1"
            params: list[Any] = []

            if tier is not None:
                query += " AND tier = ?"
                params.append(tier.value)

            if category is not None:
                cat_val = category.value if isinstance(category, MemoryCategory) else category
                query += " AND category = ?"
                params.append(cat_val)

            if search_query and search_query.strip():
                clean_q = f"%{search_query.strip()}%"
                query += " AND (key LIKE ? OR content LIKE ?)"
                params.extend([clean_q, clean_q])

            query += " ORDER BY importance DESC, updated_at DESC LIMIT ?;"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_item(r) for r in rows]

    # ---------------- 3. COGNITIVE RELEVANCE RETRIEVAL ----------------

    def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        tier: Optional[MemoryTier] = None,
    ) -> list[MemoryItem]:
        """Retrieve memories relevant to the user query using cognitive ranking."""
        if not self.is_memory_enabled():
            return []

        all_active = self.list_memories(tier=tier, limit=200)
        if not all_active:
            return []

        # Rank candidates using Stanford Cognitive Model
        ranked = self.ranker.rank(query=query, candidates=all_active, limit=limit, tier=tier)

        # Update access telemetry for retrieved memories
        now = time.time()
        retrieved_ids = [m.id for m in ranked]
        if retrieved_ids:
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    placeholders = ",".join("?" * len(retrieved_ids))
                    cursor.execute(f"""
                        UPDATE memories
                        SET access_count = access_count + 1, last_accessed_at = ?
                        WHERE id IN ({placeholders});
                    """, [now] + retrieved_ids)
            except Exception:
                pass

        return ranked

    def format_memories_for_prompt(self, memories: list[MemoryItem]) -> str:
        """Format memories as clean, concise system observations for the LLM."""
        if not memories:
            return ""

        lines = ["[CONFIRMED USER MEMORIES - Use these facts in your response]:"]
        for m in memories:
            tier_label = m.tier.value.upper()
            cat_label = m.category.value.replace("_", " ").title()
            lines.append(f"- [{tier_label} · {cat_label}] {m.key}: {m.content}")

        return "\n".join(lines)

    # ---------------- 4. PASSIVE EXTRACTION ----------------

    def extract_and_store_from_message(self, user_message: str) -> list[MemoryItem]:
        """Scan a chat message, extract facts, and store them automatically."""
        if not self.is_memory_enabled() or not self.is_auto_extract_enabled():
            return []

        candidates: list[ExtractedCandidate] = self.extractor.extract_candidates(user_message)
        saved_items: list[MemoryItem] = []

        for c in candidates:
            item = self.save_memory(
                tier=c.tier,
                category=c.category,
                key=c.key,
                content=c.content,
                importance=c.importance,
                provenance="chat_extraction",
            )
            saved_items.append(item)

        return saved_items

    # ---------------- 5. EXPORT & PRIVACY CONTROLS ----------------

    def export_memories(self, format: str = "json") -> str | MemoryExport:
        """Export all active memories to JSON or Markdown."""
        memories = self.list_memories(limit=1000)
        tiers_count = {t.value: 0 for t in MemoryTier}
        for m in memories:
            tiers_count[m.tier.value] += 1

        now = time.time()
        export_obj = MemoryExport(
            exported_at=now,
            exported_at_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            total_count=len(memories),
            tiers=tiers_count,
            memories=memories,
        )

        if format.lower() == "markdown":
            lines = [
                f"# NOUS Memory Export",
                f"**Exported At:** {export_obj.exported_at_iso}",
                f"**Total Memories:** {export_obj.total_count}",
                "",
                "## Tier Breakdown",
            ]
            for t_name, t_cnt in tiers_count.items():
                lines.append(f"- **{t_name.upper()}**: {t_cnt} items")
            lines.append("\n## Stored Memory Items\n")

            for m in memories:
                lines.append(f"### [{m.tier.value.upper()}] {m.key}")
                lines.append(f"- **Category:** {m.category.value}")
                lines.append(f"- **Importance:** {m.importance}")
                lines.append(f"- **Content:** {m.content}")
                lines.append(f"- **Created:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(m.created_at))}")
                lines.append("")

            return "\n".join(lines)

        return export_obj.model_dump_json(indent=2)


memory_manager = MemoryManager()

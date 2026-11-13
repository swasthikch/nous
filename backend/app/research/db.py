"""Database schema and management for NOUS Web Research Engine."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from backend.app.config import settings

DEFAULT_DB_PATH: Path = settings.RESEARCH_DB_PATH

# Seed research notes for initial experience
DEFAULT_SEED_NOTES: list[dict[str, Any]] = [
    {
        "title": "Raft Consensus Algorithm: Architectural Principles & Safety Proofs",
        "query": "Raft consensus algorithm",
        "category": "technology",
        "summary": "Raft is a leader-based consensus algorithm designed as a more understandable alternative to Paxos, using randomized election timers, strong leader invariants, and formal state-machine replication.",
        "full_report_markdown": """### NOUS Research Debrief: Raft Consensus Algorithm
**Research Question:** How does the Raft consensus algorithm achieve distributed safety and state machine replication compared to Paxos?

**Key Findings:**
1. Raft decomposes distributed consensus into 3 independent subproblems: Leader Election, Log Replication, and Safety.
2. Randomized election timeouts (150ms-300ms) prevent split-vote deadlocks in leader elections without central coordination.
3. Once a log entry is committed by a majority of nodes, it is guaranteed to be present in all future leader terms (Leader Completeness Invariant).

**Supporting Evidence:**
- Formally proven safe using TLA+ model checking by Diego Ongaro and John Ousterhout at Stanford University (USENIX ATC 2014).
- Production-tested in distributed backbones including etcd (Kubernetes control plane), HashiCorp Consul, and Apache Kafka (KRaft).

**Different Viewpoints:**
- Paxos advocates argue Multi-Paxos can achieve slightly higher throughput under high write contention because leaders don't need contiguous logs.
- Raft proponents prioritize debuggability, formal operational clarity, and simpler failure recovery in real-world clusters.

**Important Dates:**
- 2014: USENIX ATC Best Paper published by Ongaro & Ousterhout.
- 2021: Apache Kafka officially adopted KRaft, replacing ZooKeeper.

**Source Links:**
- Stanford Paper: https://raft.github.io/raft.pdf
- etcd Consensus Core: https://etcd.io/docs

**Uncertainties or Limitations:**
- Raft's single-leader bottleneck can constrain write throughput across multi-datacenter clusters spanning wide-area networks (WAN).

**Final Summary:**
Raft has become the industry standard for distributed systems requiring strong consistency and clear cluster state management.""",
        "key_findings": [
            "Decomposes consensus into Leader Election, Log Replication, and Safety.",
            "Randomized election timers avoid split votes.",
            "Strict Leader Completeness ensures committed logs are never overwritten."
        ],
        "sources": [
            {"title": "In Search of an Understandable Consensus Algorithm (USENIX ATC)", "url": "https://raft.github.io/raft.pdf", "publisher": "Stanford University"},
            {"title": "etcd Raft Implementation Guide", "url": "https://etcd.io/docs", "publisher": "Cloud Native Computing Foundation"}
        ],
        "tags": "distributed-systems,consensus,raft,kubernetes,backend"
    }
]


def init_research_db(db_path: Path | None = None) -> Path:
    """Initialize the SQLite database for research notes with WAL mode and tables."""
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")

        # Table: Research Notes & Investigations
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research_notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                query TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                full_report_markdown TEXT NOT NULL,
                key_findings_json TEXT NOT NULL,
                sources_json TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )

        # Index for search and category filtering
        conn.execute("CREATE INDEX IF NOT EXISTS idx_research_category ON research_notes(category);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_research_created ON research_notes(created_at DESC);")

        # Seed initial notes if empty
        cur = conn.execute("SELECT COUNT(*) FROM research_notes;")
        count = cur.fetchone()[0]
        if count == 0:
            now = time.time()
            for note in DEFAULT_SEED_NOTES:
                note_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO research_notes (
                        id, title, query, category, summary, full_report_markdown,
                        key_findings_json, sources_json, tags, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        note_id,
                        note["title"],
                        note["query"],
                        note["category"],
                        note["summary"],
                        note["full_report_markdown"],
                        json.dumps(note["key_findings"]),
                        json.dumps(note["sources"]),
                        note["tags"],
                        now,
                        now,
                    ),
                )
            conn.commit()

    return path


@contextmanager
def get_db(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding a SQLite connection with Row factory."""
    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        init_research_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class ResearchDBManager:
    """Manages persistent research notebook entries, investigation reports, and references."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        init_research_db(self.db_path)

    def create_note(
        self,
        title: str,
        query: str,
        category: str,
        summary: str,
        full_report_markdown: str,
        key_findings: list[str],
        sources: list[dict[str, Any]],
        tags: str = "",
    ) -> dict[str, Any]:
        """Save a new research debrief to persistent notebook."""
        note_id = str(uuid.uuid4())
        now = time.time()

        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO research_notes (
                    id, title, query, category, summary, full_report_markdown,
                    key_findings_json, sources_json, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    note_id,
                    title.strip(),
                    query.strip(),
                    category.strip().lower(),
                    summary.strip(),
                    full_report_markdown.strip(),
                    json.dumps(key_findings),
                    json.dumps(sources),
                    tags.strip(),
                    now,
                    now,
                ),
            )

        return self.get_note(note_id)  # type: ignore

    def get_note(self, note_id: str) -> dict[str, Any] | None:
        """Fetch a specific research note by ID."""
        with get_db(self.db_path) as conn:
            cur = conn.execute("SELECT * FROM research_notes WHERE id = ?;", (note_id,))
            row = cur.fetchone()
            if not row:
                return None
            res = dict(row)
            res["key_findings"] = json.loads(res.get("key_findings_json") or "[]")
            res["sources"] = json.loads(res.get("sources_json") or "[]")
            return res

    def list_notes(
        self,
        category: str | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List saved research notes with optional search and category filters."""
        query = "SELECT * FROM research_notes"
        conditions: list[str] = []
        params: list[Any] = []

        if category and category.strip():
            conditions.append("category = ?")
            params.append(category.strip().lower())

        if search and search.strip():
            search_pat = f"%{search.strip().lower()}%"
            conditions.append("(LOWER(title) LIKE ? OR LOWER(query) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(tags) LIKE ?)")
            params.extend([search_pat, search_pat, search_pat, search_pat])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ?;"
        params.append(limit)

        with get_db(self.db_path) as conn:
            cur = conn.execute(query, params)
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["key_findings"] = json.loads(r.get("key_findings_json") or "[]")
                r["sources"] = json.loads(r.get("sources_json") or "[]")
            return rows

    def delete_note(self, note_id: str) -> bool:
        """Delete a research note by ID."""
        with get_db(self.db_path) as conn:
            cur = conn.execute("DELETE FROM research_notes WHERE id = ?;", (note_id,))
            return cur.rowcount > 0

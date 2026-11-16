"""Phase 2 Complete 5-Tier Memory Engine Verification Suite.

Tests:
1. 5-Tier Taxonomy & Category Mapping (Working, Personal, Project, Knowledge, Episodic).
2. Database Schema Auto-Migration & Column Integrity.
3. Deduplication and Smart Updates.
4. Stanford Cognitive Ranking (Relevance, Importance, Recency Decay).
5. Passive Conversational Fact Extraction & Credential Redaction Gate.
6. JSON & Markdown Memory Export.
7. FastAPI REST Endpoints (/api/memory, /api/memory/tiers, /api/memory/export, /api/memory/extract).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.memory.models import MemoryTier, MemoryCategory, category_to_tier, MemoryItem
from backend.app.memory.manager import memory_manager
from backend.app.memory.extractor import memory_extractor
from backend.app.memory.ranker import memory_ranker
from backend.app.memory.db import get_db, init_database


async def run_phase2_memory_tests() -> None:
    print("=" * 72)
    print("  NOUS PHASE 2 — COMPLETE 5-TIER MEMORY ENGINE VERIFICATION")
    print("=" * 72)

    # ---------------- 1. 5-TIER TAXONOMY MAPPING ----------------
    print("\n[STEP 1] Testing 5-Tier Taxonomy & Category Mapping...")
    assert category_to_tier(MemoryCategory.USER_PROFILE) == MemoryTier.PERSONAL
    assert category_to_tier(MemoryCategory.PERSONAL_INFO) == MemoryTier.PERSONAL
    assert category_to_tier(MemoryCategory.PROJECT) == MemoryTier.PROJECT
    assert category_to_tier(MemoryCategory.KNOWLEDGE_NOTE) == MemoryTier.KNOWLEDGE
    assert category_to_tier(MemoryCategory.EPISODIC_EVENT) == MemoryTier.EPISODIC
    assert category_to_tier(MemoryCategory.ROUTINE) == MemoryTier.PERSONAL
    assert category_to_tier(MemoryCategory.CONVERSATION) == MemoryTier.EPISODIC
    print("  [PASS] All subcategories correctly map to the 5 primary operational tiers.")

    # ---------------- 2. SCHEMA AUTO-MIGRATION & PERSISTENCE ----------------
    print("\n[STEP 2] Testing Schema Migration & Column Integrity...")
    init_database()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(memories);")
        cols = {row["name"] for row in cursor.fetchall()}
        required_cols = {"id", "tier", "category", "key", "content", "importance", "provenance", "access_count", "last_accessed_at", "is_active"}
        for rc in required_cols:
            assert rc in cols, f"Missing required column: {rc}"
    print("  [PASS] SQLite schema contains all 5-tier metadata and provenance columns.")

    # ---------------- 3. DEDUPLICATION & SMART UPDATES ----------------
    print("\n[STEP 3] Testing Deduplication and Smart In-Place Updates...")
    test_key = "test_primary_language"
    m1 = memory_manager.save_memory(
        category=MemoryCategory.PERSONAL_INFO,
        key=test_key,
        content="User primary programming language is Python 3.12.",
        importance=0.8,
    )
    assert m1.id is not None
    initial_id = m1.id

    # Save same key with revised content -> must update in place without duplicating
    m2 = memory_manager.save_memory(
        category=MemoryCategory.PERSONAL_INFO,
        key=test_key,
        content="User primary programming language is Python 3.14 with FastAPI.",
        importance=0.9,
    )
    assert m2.id == initial_id, "Duplicate key must update existing memory row rather than spawn new row."
    assert "FastAPI" in m2.content
    assert m2.importance == 0.9
    print(f"  [PASS] Deduplication confirmed: Memory #{initial_id} updated in-place cleanly.")

    # ---------------- 4. STANFORD COGNITIVE RANKING ----------------
    print("\n[STEP 4] Testing Stanford Cognitive Memory Ranking...")
    # Add a project milestone memory
    memory_manager.save_memory(
        category=MemoryCategory.PROJECT,
        key="project_database_choice",
        content="NOUS uses SQLite WAL mode for local high-throughput zero-config storage.",
        importance=0.85,
    )

    ranked_items = memory_manager.get_relevant_memories(query="what database does NOUS use", limit=3)
    assert len(ranked_items) >= 1
    top_hit = ranked_items[0]
    print(f"  Top cognitive retrieval: [{top_hit.tier.value.upper()}] {top_hit.key}: {top_hit.content[:60]}...")
    assert "database" in top_hit.key or "SQLite" in top_hit.content

    # Verify access count was incremented
    reloaded = memory_manager.get_memory(top_hit.id)
    assert reloaded is not None
    assert reloaded.access_count >= 1
    assert reloaded.last_accessed_at is not None
    print(f"  [PASS] Cognitive ranker verified. Access count tracked: {reloaded.access_count}.")

    # ---------------- 5. PASSIVE FACT EXTRACTION & ZERO-TRUST FILTER ----------------
    print("\n[STEP 5] Testing Passive Conversational Memory Extraction & Zero-Trust Gate...")
    # A. Personal statement extraction
    candidates = memory_extractor.extract_candidates("My name is Swasthik and I am studying autonomous agents")
    assert len(candidates) >= 1
    assert any(c.key == "preferred_name" for c in candidates)
    print(f"  Extracted from conversation: {[c.key + ' -> ' + c.content for c in candidates]}")

    # B. Preference extraction
    pref_cands = memory_extractor.extract_candidates("I prefer SQLite over PostgreSQL for local tests")
    assert len(pref_cands) >= 1
    assert any("preference" in c.key for c in pref_cands)
    print("  [PASS] Natural preference extraction confirmed.")

    # C. Zero-Trust Security Gate: Passwords and tokens must NEVER be extracted
    malicious_text = "My secret password is SuperSecretPassword123! and my token is ghp_1234567890abcdef1234567890"
    blocked_cands = memory_extractor.extract_candidates(malicious_text)
    assert len(blocked_cands) == 0, "Sensitive credentials MUST be rejected by extraction gate!"
    print("  [PASS] Zero-trust filter verified: Credentials and tokens blocked from memory extraction.")

    # D. Casual chatter ignored
    chat_cands = memory_extractor.extract_candidates("Hi NOUS, what time is it right now?")
    assert len(chat_cands) == 0, "Casual conversation should not be saved as permanent memory."
    print("  [PASS] Casual chatter and questions correctly filtered out.")

    # ---------------- 6. MEMORY EXPORT (JSON & MARKDOWN) ----------------
    print("\n[STEP 6] Testing Memory Export Capabilities...")
    json_export = memory_manager.export_memories(format="json")
    parsed_json = json.loads(str(json_export))
    assert "total_count" in parsed_json
    assert "tiers" in parsed_json
    assert len(parsed_json["memories"]) >= 1
    print(f"  JSON Export: Total count: {parsed_json['total_count']}, Tiers: {parsed_json['tiers']}")

    md_export = memory_manager.export_memories(format="markdown")
    assert "# NOUS Memory Export" in str(md_export)
    assert "## Tier Breakdown" in str(md_export)
    print("  [PASS] JSON and Markdown export formats validated.")

    # ---------------- 7. FASTAPI REST MEMORY ENDPOINTS ----------------
    print("\n[STEP 7] Testing FastAPI Memory Endpoints (/api/memory)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. Tiers overview
        r_tiers = await client.get("/api/memory/tiers")
        assert r_tiers.status_code == 200
        tiers_data = r_tiers.json()
        assert len(tiers_data["tiers"]) == 5
        print(f"  [PASS] GET /api/memory/tiers: {[{t['id']: t['count']} for t in tiers_data['tiers']]}")

        # B. List memories by tier
        r_list = await client.get("/api/memory", params={"tier": "personal"})
        assert r_list.status_code == 200
        assert r_list.json()["count"] >= 1
        print(f"  [PASS] GET /api/memory?tier=personal: {r_list.json()['count']} items found.")

        # C. Passive extraction API endpoint
        r_extract = await client.post("/api/memory/extract", json={"text": "I am a computer science student"})
        assert r_extract.status_code == 200
        ext_json = r_extract.json()
        assert ext_json["success"] is True
        print(f"  [PASS] POST /api/memory/extract: Extracted {ext_json['extracted_count']} candidate memories.")

        # D. Export API endpoint
        r_exp_json = await client.get("/api/memory/export", params={"format": "json"})
        assert r_exp_json.status_code == 200
        assert r_exp_json.headers.get("content-type") == "application/json"

        r_exp_md = await client.get("/api/memory/export", params={"format": "markdown"})
        assert r_exp_md.status_code == 200
        assert "text/markdown" in r_exp_md.headers.get("content-type", "")
        print("  [PASS] GET /api/memory/export: Both JSON and Markdown HTTP endpoints verified.")

    # Cleanup test memory
    memory_manager.delete_memory(initial_id, hard_delete=True)

    print("\n" + "=" * 72)
    print("  ALL PHASE 2 MEMORY ENGINE VERIFICATION CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase2_memory_tests())

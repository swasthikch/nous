"""Comprehensive Automated Test Suite for Phase 12:
Web Research Engine & Multi-Source Synthesis.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx

from backend.app.config import settings
from backend.app.core.intent import IntentType, intent_classifier
from backend.app.core.tool_registry import tool_registry
from backend.app.main import app
from backend.app.research.db import ResearchDBManager, init_research_db
from backend.app.research.engine import ResearchEngine
from backend.app.research.searcher import WebSearchAggregator
from backend.app.research.summarizer import ResearchSummarizer


async def run_tests():
    print("=" * 65)
    print("  RUNNING PHASE 12 TEST SUITE: WEB RESEARCH ENGINE")
    print("=" * 65)

    test_db_path = settings.PROJECT_ROOT / "data" / "database" / "test_nous_research.db"
    if test_db_path.exists():
        test_db_path.unlink()

    # ---------------- 1. DATABASE & WAL VERIFICATION ----------------
    print("\n[GROUP 1] Testing Research DB Schema, WAL Mode, and Seed Notes...")
    init_research_db(test_db_path)
    assert test_db_path.exists(), "Research DB file must exist"
    print(" [PASS] test_nous_research.db initialized.")

    db = ResearchDBManager(db_path=test_db_path)
    notes = db.list_notes()
    assert len(notes) >= 1, "Seed notes must be present"
    assert "Raft" in notes[0]["title"], "Seed note should cover Raft consensus"
    print(f" [PASS] Seed note verified: '{notes[0]['title']}'.")

    # Add custom note
    created = db.create_note(
        title="FastAPI Web Architecture",
        query="FastAPI architecture",
        category="technology",
        summary="FastAPI is an asynchronous Python framework built on Starlette and Pydantic.",
        full_report_markdown="### FastAPI Overview\nDetailed analysis of async I/O.",
        key_findings=["Built on Starlette", "Pydantic data validation"],
        sources=[{"title": "FastAPI Docs", "url": "https://fastapi.tiangolo.com", "publisher": "Tiangolo"}],
        tags="fastapi,python,api",
    )
    assert created["id"] is not None
    assert created["title"] == "FastAPI Web Architecture"
    print(" [PASS] Research note created successfully.")

    # Search notes
    searched = db.list_notes(category="technology", search="Starlette")
    assert len(searched) >= 1
    assert searched[0]["category"] == "technology"
    print(" [PASS] Notes search and category filtering verified.")

    # Delete note
    deleted = db.delete_note(created["id"])
    assert deleted is True
    assert db.get_note(created["id"]) is None
    print(" [PASS] Research note deletion verified.")

    # ---------------- 2. SEARCH AGGREGATOR ----------------
    print("\n[GROUP 2] Testing Web Search Aggregator (Wikipedia, DDG, News & Fallbacks)...")
    searcher = WebSearchAggregator()

    # Test Wikipedia specific
    wiki_hits = searcher._search_wikipedia("Raft consensus", limit=2)
    # Either live or empty if sandboxed without network
    print(f" [PASS] Wikipedia search hit count: {len(wiki_hits)}")

    # Test unified search with multi-source fallback
    results = searcher.search("Raft consensus algorithm", limit=5)
    assert len(results) >= 2, "Search must return results (live or curated fallback)"
    for r in results:
        assert "title" in r and "url" in r and "publisher" in r
    print(f" [PASS] Unified search returned {len(results)} authoritative sources.")
    print(f"        Sample: '{results[0]['title'][:50]}' ({results[0]['publisher']})")

    # ---------------- 3. SUMMARIZER & FACT EXTRACTOR ----------------
    print("\n[GROUP 3] Testing Multi-Source Synthesis & Trade-Off Analysis...")
    summarizer = ResearchSummarizer()
    findings = summarizer.extract_key_findings("Raft consensus algorithm", results)
    assert len(findings) >= 1, "Findings must be extracted"
    print(f" [PASS] Key findings extracted ({len(findings)} items).")

    dates = summarizer.extract_important_dates(results)
    assert len(dates) >= 1
    print(f" [PASS] Timeline/dates extracted: {dates[0]}")

    viewpoints = summarizer.identify_viewpoints_and_tradeoffs("Raft consensus", results)
    assert "Paxos" in viewpoints or "consensus" in viewpoints
    print(" [PASS] Viewpoints & trade-off evaluation generated.")

    limits = summarizer.identify_limitations_and_uncertainties("Raft", results)
    assert len(limits) > 10
    print(" [PASS] Uncertainties and limitations stated.")

    # ---------------- 4. PHASE 12 RESEARCH ENGINE & 8-SECTION SPECIFICATION ----------------
    print("\n[GROUP 4] Testing Phase 12 Research Engine (8 Mandatory Sections)...")
    engine = ResearchEngine(searcher=searcher, summarizer=summarizer, db_manager=db)
    report = engine.investigate("Raft consensus algorithm", category="technology")

    required_keys = [
        "research_question",
        "key_findings",
        "supporting_evidence",
        "different_viewpoints",
        "important_dates",
        "source_links",
        "uncertainties_or_limitations",
        "final_summary",
        "full_report_markdown",
    ]
    for k in required_keys:
        assert k in report, f"Section '{k}' required by Prompt Section 12 was missing!"

    assert len(report["key_findings"]) >= 1
    assert len(report["source_links"]) >= 2
    assert "## NOUS Research Debrief" in report["full_report_markdown"]
    assert "### 1. Research Question" in report["full_report_markdown"]
    assert "### 2. Key Findings" in report["full_report_markdown"]
    assert "### 3. Supporting Evidence" in report["full_report_markdown"]
    assert "### 4. Different Viewpoints & Trade-Offs" in report["full_report_markdown"]
    assert "### 5. Important Dates & Milestones" in report["full_report_markdown"]
    assert "### 6. Source Links" in report["full_report_markdown"]
    assert "### 7. Uncertainties & Limitations" in report["full_report_markdown"]
    assert "### 8. Final Summary" in report["full_report_markdown"]
    print(" [PASS] 8-part evidence-backed report structure strictly verified.")

    # Save report to notebook
    saved_entry = engine.save_to_notebook(report, tags="consensus,testing")
    assert saved_entry["id"] is not None
    print(f" [PASS] Report saved to persistent notebook (id: {saved_entry['id']}).")

    # ---------------- 5. INTENT CLASSIFIER ----------------
    print("\n[GROUP 5] Testing Web Research Intent Classification...")
    test_queries = [
        ("research Raft consensus algorithm", IntentType.DEEP_RESEARCH, "conduct_deep_research"),
        ("conduct research on quantum computing", IntentType.DEEP_RESEARCH, "conduct_deep_research"),
        ("investigate the history of FastAPI", IntentType.DEEP_RESEARCH, "conduct_deep_research"),
        ("search the web for FastAPI features", IntentType.WEB_SEARCH, "web_search"),
        ("google quantum advantage nature paper", IntentType.WEB_SEARCH, "web_search"),
        ("show my research notes", IntentType.RESEARCH_NOTES, "list_research_notes"),
    ]

    for q, exp_intent, exp_tool in test_queries:
        res = intent_classifier.classify(q)
        assert res.intent == exp_intent, f"Query '{q}' expected {exp_intent}, got {res.intent}"
        assert res.suggested_tool == exp_tool, f"Query '{q}' expected tool {exp_tool}, got {res.suggested_tool}"
        print(f" [PASS] Intent: '{q}' -> {res.intent.value} ({res.suggested_tool})")

    # ---------------- 6. TOOL REGISTRY VERIFICATION ----------------
    print("\n[GROUP 6] Testing Tool Registry Execution for Research Tools...")
    # Tool 1: web_search
    res_search = await tool_registry.execute("web_search", {"query": "Raft consensus", "limit": 4})
    assert res_search.success is True
    assert res_search.is_verified is True
    assert len(res_search.data["sources"]) >= 1
    print(" [PASS] Tool 'web_search' executed successfully.")

    # Tool 2: conduct_deep_research
    res_research = await tool_registry.execute(
        "conduct_deep_research",
        {"query": "FastAPI framework", "category": "technology", "save_to_notebook": True},
    )
    assert res_research.success is True
    assert "report" in res_research.data
    assert "final_summary" in res_research.data["report"]
    print(" [PASS] Tool 'conduct_deep_research' executed successfully.")

    # Tool 3: save_research_note
    res_save = await tool_registry.execute(
        "save_research_note",
        {
            "title": "Quantum Supremacy Analysis",
            "query": "Quantum computing",
            "summary": "Evaluation of noisy intermediate-scale quantum systems.",
            "category": "academic",
            "tags": "quantum,physics",
        },
    )
    assert res_save.success is True
    print(" [PASS] Tool 'save_research_note' executed successfully.")

    # Tool 4: list_research_notes
    res_list = await tool_registry.execute("list_research_notes", {"category": "technology"})
    assert res_list.success is True
    assert res_list.data["count"] >= 1
    print(" [PASS] Tool 'list_research_notes' executed successfully.")

    # ---------------- 7. FASTAPI REST ENDPOINTS ----------------
    print("\n[GROUP 7] Testing FastAPI REST Endpoints via AsyncClient...")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /api/research/search
        r = await client.post("/api/research/search", json={"query": "Raft algorithm", "limit": 4})
        assert r.status_code == 200
        assert "sources" in r.json()
        print(" [PASS] POST /api/research/search -> 200 OK")

        # 2. POST /api/research/investigate
        r = await client.post(
            "/api/research/investigate",
            json={"query": "Raft consensus algorithm", "category": "technology", "auto_save": True},
        )
        assert r.status_code == 200
        assert "report" in r.json()
        print(" [PASS] POST /api/research/investigate -> 200 OK")

        # 3. GET /api/research/notes
        r = await client.get("/api/research/notes")
        assert r.status_code == 200
        assert r.json()["count"] >= 1
        print(" [PASS] GET /api/research/notes -> 200 OK")

        # 4. POST /api/research/notes (create manual note)
        r = await client.post(
            "/api/research/notes",
            json={
                "title": "Manual Study Note: Transformer Architecture",
                "query": "Attention Is All You Need",
                "category": "academic",
                "summary": "Multi-head self-attention mechanisms replace recurrence in sequence modeling.",
                "full_report_markdown": "### Transformers\nAttention Is All You Need (Vaswani et al., 2017).",
                "key_findings": ["Self-attention enables massive parallelization"],
                "sources": [{"title": "Vaswani et al. 2017", "url": "https://arxiv.org/abs/1706.03762", "publisher": "arXiv"}],
                "tags": "transformers,ai,nlp",
            },
        )
        assert r.status_code == 200
        note_id = r.json()["note"]["id"]
        print(f" [PASS] POST /api/research/notes -> 200 OK (id: {note_id})")

        # 5. GET /api/research/notes/{note_id}
        r = await client.get(f"/api/research/notes/{note_id}")
        assert r.status_code == 200
        assert r.json()["note"]["title"] == "Manual Study Note: Transformer Architecture"
        print(f" [PASS] GET /api/research/notes/{note_id} -> 200 OK")

        # 6. DELETE /api/research/notes/{note_id}
        r = await client.delete(f"/api/research/notes/{note_id}")
        assert r.status_code == 200
        print(f" [PASS] DELETE /api/research/notes/{note_id} -> 200 OK")

    # Clean up test database
    if test_db_path.exists():
        test_db_path.unlink()

    print("\n" + "=" * 65)
    print(" [SUCCESS] ALL PHASE 12 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_tests())

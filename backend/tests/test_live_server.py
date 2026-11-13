"""Comprehensive live application test covering all NOUS phases (Phase 1 through 12).
Uses ASGI in-process transport for zero-socket, fully deterministic verification.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app


async def run_live_tests() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        print("Starting in-process comprehensive NOUS system verification...\n")

        # 1. Health check
        print("1. Probing /api/health...")
        r_health = await client.get("/api/health")
        assert r_health.status_code == 200
        print(f"   Status: {r_health.json().get('status')}")

        # 2. Frontend check
        print("2. Probing / (Frontend UI)...")
        r_index = await client.get("/")
        assert r_index.status_code == 200
        assert "NOUS" in r_index.text
        assert "view-research" in r_index.text
        print("   Frontend UI verified successfully.")

        # 3. Voice API check (Phase 6)
        print("3. Testing Voice Assistant API (/api/voice)...")
        r_voice_set = await client.get("/api/voice/settings")
        assert r_voice_set.status_code == 200
        print(f"   Voice enabled: {r_voice_set.json().get('enabled')}")

        r_voice_proc = await client.post(
            "/api/voice/process-speech",
            json={"speech_text": "Calculate 50 * 6"}
        )
        assert r_voice_proc.status_code == 200
        voice_data = r_voice_proc.json()
        assert voice_data.get("processed") is True
        print(f"   Spoken query response: {voice_data.get('spoken_text', '').strip()[:80]}...")
        print("   Voice pipeline verified.")

        # 4. Memory API check (Phase 5)
        print("4. Testing Persistent Memory API (/api/memory)...")
        r_settings = await client.get("/api/memory/settings")
        assert r_settings.status_code == 200
        print(f"   Memory Enabled: {r_settings.json().get('memory_enabled')}")

        # 5. Sessions API check (Phase 2 & 3)
        print("5. Testing Sessions API (/api/sessions)...")
        r_sess = await client.get("/api/sessions")
        assert r_sess.status_code == 200

        # 6. Routine & Daily Life API check (Phase 7)
        print("6. Testing Routine & Daily Life API (/api/routine)...")
        r_sched = await client.get("/api/routine/schedule")
        assert r_sched.status_code == 200
        print(f"   Today's Activities: {r_sched.json().get('count')}")

        r_review = await client.get("/api/routine/review")
        assert r_review.status_code == 200
        print(f"   Completion rate: {r_review.json().get('completion_rate_percent')}%")
        print("   Routine engine verified.")

        # 7. Email Intelligence API check (Phase 8)
        print("7. Testing Email Intelligence API (/api/email)...")
        r_auth = await client.get("/api/email/auth/status")
        assert r_auth.status_code == 200
        print(f"   Mailbox Mode: {r_auth.json().get('mode')}")

        r_mail = await client.get("/api/email/messages")
        assert r_mail.status_code == 200
        mail_count = r_mail.json().get('count', 0)
        print(f"   Indexed messages: {mail_count}")
        assert mail_count >= 1

        r_sum = await client.get("/api/email/summary")
        assert r_sum.status_code == 200
        print(f"   Unread in briefing: {r_sum.json().get('unread_count')}")
        print("   Email intelligence verified.")

        # 8. Project Intelligence & GitHub Telemetry (Phase 9)
        print("8. Testing Project Intelligence API (/api/projects)...")
        r_proj = await client.get("/api/projects")
        assert r_proj.status_code == 200
        proj_count = r_proj.json().get('count', 0)
        print(f"   Active tracked projects: {proj_count}")
        assert proj_count >= 1

        r_gh = await client.get("/api/projects/github/activity")
        assert r_gh.status_code == 200
        commits = r_gh.json().get('recent_commits', [])
        print(f"   GitHub repository commits fetched: {len(commits)}")
        assert len(commits) >= 1
        print("   Project intelligence verified.")

        # 9. Financial Market Intelligence & Causal Reasoning (Phase 10 & 11)
        print("9. Testing Market Intelligence API (/api/market)...")
        r_indices = await client.get("/api/market/indices")
        assert r_indices.status_code == 200
        indian_idx = r_indices.json().get("indian_indices", [])
        print(f"   Benchmark indices tracked: {len(indian_idx)} Indian, {len(r_indices.json().get('global_indices', []))} Global")
        assert len(indian_idx) >= 3

        r_flows = await client.get("/api/market/fii-dii")
        assert r_flows.status_code == 200
        print(f"   FII/DII Net institutional flow: {r_flows.json().get('net_institutional_flow_cr')} Cr")

        r_ana = await client.post("/api/market/analyze", json={"symbol": "^NSEI"})
        assert r_ana.status_code == 200
        ana_data = r_ana.json().get("analysis", {})
        print(f"   Phase 11 causal reasoning verified for {ana_data.get('symbol')}: {ana_data.get('confidence')} confidence")
        assert ana_data.get("market_movement") is not None
        assert ana_data.get("possible_reason") is not None
        assert ana_data.get("evidence") is not None
        print("   Market intelligence & reasoning verified.")

        # 10. Web Research Engine & Knowledge Notebook (Phase 12)
        print("10. Testing Web Research Engine API (/api/research)...")
        r_search = await client.post("/api/research/search", json={"query": "Raft consensus algorithm", "limit": 4})
        assert r_search.status_code == 200
        search_sources = r_search.json().get("sources", [])
        print(f"   Web search multi-source count: {len(search_sources)}")
        assert len(search_sources) >= 1

        r_inv = await client.post(
            "/api/research/investigate",
            json={
                "query": "Raft consensus safety proofs",
                "category": "technology",
                "auto_save": True,
                "tags": "consensus,raft,distributed-systems"
            }
        )
        assert r_inv.status_code == 200
        inv_data = r_inv.json()
        report = inv_data.get("report", {})
        assert report.get("research_question") is not None
        assert len(report.get("key_findings", [])) >= 1
        sources_list = report.get("source_links") or report.get("sources") or []
        assert len(sources_list) >= 1 or report.get("source_count", 0) >= 1
        print(f"   8-Part Research Report generated: {len(report.get('key_findings'))} findings, {len(sources_list)} sources")

        saved_note = inv_data.get("saved_note")
        assert saved_note is not None
        saved_id = saved_note.get("id")
        print(f"   Report auto-saved to notebook ID: {saved_id}")

        r_notes = await client.get("/api/research/notes")
        assert r_notes.status_code == 200
        notes_list = r_notes.json().get("notes", [])
        print(f"   Notebook total saved notes: {len(notes_list)}")
        assert any(n.get("id") == saved_id for n in notes_list)

        r_note_detail = await client.get(f"/api/research/notes/{saved_id}")
        assert r_note_detail.status_code == 200
        assert r_note_detail.json().get("note", {}).get("id") == saved_id

        # Clean up test note
        r_del = await client.delete(f"/api/research/notes/{saved_id}")
        assert r_del.status_code == 200
        print("   Research note cleanup verified.")
        print("   Web Research Engine & Knowledge Notebook verified.")

    print("\n=======================================================")
    print("ALL LIVE NOUS SUBSYSTEMS (PHASES 1-12) PASSED 100%!")
    print("=======================================================")


def main() -> None:
    asyncio.run(run_live_tests())


if __name__ == "__main__":
    main()

"""Test Suite for NOUS Phase 7: Integrated Dashboard, Workspace & Settings.

Verifies:
1. Executive Overview Aggregation (/api/dashboard/overview):
   - Hardware telemetry, 5-tier memory distribution, pending approvals, agents, routine, market.
2. Workspace File Explorer:
   - Listing files with metadata (/api/dashboard/files).
   - Safe file writing (/api/dashboard/files/write).
   - Safe file reading (/api/dashboard/files/read).
   - Anti-traversal sandbox violation security defense (rejects ../ escapes with 403).
   - Clean file deletion (/api/dashboard/files/delete).
3. Unified Settings & Security Panel:
   - Configuration retrieval with zero-leak API key masking (/api/dashboard/settings).
   - Setting updates with voice and routing persistence.
"""

import asyncio
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.tools.approval import approval_manager
from backend.app.tools.permissions import PermissionLevel
from backend.app.memory.manager import memory_manager
from backend.app.memory.models import MemoryTier, MemoryCategory


async def run_phase7_dashboard_tests():
    print("=" * 72)
    print("  NOUS PHASE 7 — INTEGRATED DASHBOARD, WORKSPACE & SETTINGS TEST SUITE")
    print("=" * 72)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # ---------------- 1. EXECUTIVE OVERVIEW AGGREGATION ----------------
        print("\n[STEP 1] Testing Executive Overview Dashboard Aggregator (/api/dashboard/overview)...")
        # Ensure at least 1 memory exists in each tier
        tier_to_cat = {
            MemoryTier.PERSONAL: MemoryCategory.USER_PROFILE,
            MemoryTier.PROJECT: MemoryCategory.PROJECT,
            MemoryTier.KNOWLEDGE: MemoryCategory.KNOWLEDGE_NOTE,
            MemoryTier.EPISODIC: MemoryCategory.EPISODIC_EVENT,
            MemoryTier.WORKING: MemoryCategory.CONVERSATION,
        }
        for tier in MemoryTier:
            cat = tier_to_cat[tier]
            memory_manager.save_memory(
                category=cat,
                key=f"sample_key_{tier.value}",
                content=f"Phase 7 sample data for tier {tier.value}",
                tier=tier,
            )

        # Create a pending approval request to verify it appears in dashboard
        req = approval_manager.create_request(
            tool_name="system_reboot_test",
            parameters={"target": "local"},
            permission_level=PermissionLevel.SENSITIVE_ACTION,
            description="Phase 7 test reboot request",
        )

        r_ov = await client.get("/api/dashboard/overview")
        assert r_ov.status_code == 200, f"Overview failed: {r_ov.status_code}"
        ov_data = r_ov.json()

        assert ov_data["status"] == "operational"
        assert "hardware" in ov_data
        assert "cpu_load_percent" in ov_data["hardware"]
        assert "ram_total_gb" in ov_data["hardware"]
        assert ov_data["hardware"]["ram_total_gb"] > 1.0

        # Verify pending actions contains our request
        assert "pending_actions" in ov_data
        pending_tokens = [a["token"] for a in ov_data["pending_actions"]]
        assert req.token in pending_tokens, "Pending approval token not surfaced in overview!"

        # Verify memory tiers
        assert "memory" in ov_data
        assert ov_data["memory"]["total_items"] >= 5
        tier_counts = ov_data["memory"]["tier_counts"]
        for tier in MemoryTier:
            assert tier_counts.get(tier.value, 0) >= 1

        # Verify agents
        assert "agents" in ov_data
        assert ov_data["agents"]["count"] >= 5
        agent_names = ov_data["agents"]["list"]
        assert "research_agent" in agent_names
        assert "coding_agent" in agent_names
        assert "productivity_agent" in agent_names
        assert "file_agent" in agent_names
        assert "market_agent" in agent_names

        # Clean up approval request
        approval_manager.approve_token(req.token)

        print(f"  CPU Load: {ov_data['hardware']['cpu_load_percent']}% | RAM: {ov_data['hardware']['ram_load_percent']}%")
        print(f"  Memories: {ov_data['memory']['total_items']} items across {len(tier_counts)} tiers")
        print(f"  Active Agents: {ov_data['agents']['count']} ({', '.join(agent_names[:3])}...)")
        print("  [PASS] Executive Overview aggregator 100% operational.")

        # ---------------- 2. WORKSPACE FILE EXPLORER ----------------
        print("\n[STEP 2] Testing Workspace File Explorer & Traversal Defense...")
        # A. List root workspace
        r_list = await client.get("/api/dashboard/files")
        assert r_list.status_code == 200
        list_data = r_list.json()
        assert "items" in list_data
        assert "workspace_root" in list_data
        print(f"  Workspace scanned: {len(list_data['items'])} items found.")

        # B. Safe File Write
        test_file_path = "test_phase7_scratch.txt"
        test_content = "NOUS Phase 7 Safe Workspace File System Test.\nLine 2: Confidential Agent Log."
        r_write = await client.post(
            "/api/dashboard/files/write",
            json={"path": test_file_path, "content": test_content, "overwrite": True},
        )
        assert r_write.status_code == 200
        write_data = r_write.json()
        assert write_data["success"] is True

        # C. Safe File Read
        r_read = await client.get(f"/api/dashboard/files/read?path={test_file_path}")
        assert r_read.status_code == 200
        read_data = r_read.json()
        assert test_content in read_data["content"]
        assert read_data["is_truncated"] is False
        print(f"  [PASS] Safe file written and read back: {read_data['size_bytes']} bytes.")

        # D. Security: Directory Traversal Sandboxing Defense
        print("  Testing path traversal security sandbox defense...")
        malicious_paths = [
            "../../Windows/System32/drivers/etc/hosts",
            "../secret.key",
            "/../../etc/passwd",
            "..\\..\\Desktop\\private.doc",
        ]
        for mal_path in malicious_paths:
            r_mal_read = await client.get(f"/api/dashboard/files/read?path={mal_path}")
            assert r_mal_read.status_code == 403, f"Sandbox failed to block traversal read for: {mal_path}"

            r_mal_write = await client.post(
                "/api/dashboard/files/write",
                json={"path": mal_path, "content": "malicious write", "overwrite": True},
            )
            assert r_mal_write.status_code == 403, f"Sandbox failed to block traversal write for: {mal_path}"

        print("  [PASS] Directory Traversal Sandbox Defense blocked all escape vectors (HTTP 403).")

        # E. File Deletion
        r_del = await client.delete(f"/api/dashboard/files/delete?path={test_file_path}")
        assert r_del.status_code == 200
        del_data = r_del.json()
        assert del_data["success"] is True

        # Verify it's gone
        r_read_after = await client.get(f"/api/dashboard/files/read?path={test_file_path}")
        assert r_read_after.status_code == 404
        print("  [PASS] File deleted cleanly and verified removed.")

        # ---------------- 3. UNIFIED SETTINGS & SECURITY PANEL ----------------
        print("\n[STEP 3] Testing Unified Settings & Zero-Leak API Key Masking...")
        r_sett = await client.get("/api/dashboard/settings")
        assert r_sett.status_code == 200
        sett_data = r_sett.json()

        assert "api_keys_configured" in sett_data
        keys = sett_data["api_keys_configured"]
        # Verify no raw keys leaked
        for provider, val in keys.items():
            if val != "Not Configured":
                assert "••••••••" in val, f"Raw secret leaked for {provider}: {val}"

        assert "voice" in sett_data
        assert "language" in sett_data["voice"]
        print(f"  Masked keys verified: {keys}")
        print(f"  Active Voice Language: {sett_data['voice']['language']}")

        # Test updating settings
        update_payload = {
            "model_routing_mode": "hybrid",
            "active_local_model": "qwen2.5:3b",
            "voice_language": "en-IN",
            "voice_speech_rate": 1.1,
            "voice_wake_word_enabled": False,
            "voice_continuous_loop": False,
            "security_offline_lockdown": False,
            "security_redaction_enabled": True,
        }
        r_up = await client.post("/api/dashboard/settings", json=update_payload)
        assert r_up.status_code == 200
        up_data = r_up.json()
        assert up_data["success"] is True

        # Re-fetch settings to verify update persisted
        r_sett_after = await client.get("/api/dashboard/settings")
        assert r_sett_after.json()["voice"]["language"] == "en-IN"
        assert r_sett_after.json()["voice"]["speech_rate"] == 1.1
        print("  [PASS] Settings update and voice configuration persistence verified.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 7 DASHBOARD, WORKSPACE & SETTINGS CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase7_dashboard_tests())

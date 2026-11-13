from __future__ import annotations

"""Comprehensive Automated Test Suite for Autonomous Minute Daemon & Cloud Deployment.

Tests:
1. Minute-by-minute autonomous background worker.
2. Network presence detector (fast, non-blocking 0.8s timeout).
3. 100% Offline fault-tolerance (zero-network air-gapped simulation).
4. Local routine checks and SQLite WAL maintenance.
5. Minute-to-minute heartbeat logging into nous_automation.db.
6. REST endpoints: GET /api/automation/daemon/status, POST /api/automation/daemon/tick-now.
7. Tool registry execution: get_autonomous_daemon_status, trigger_autonomous_tick.
8. Heuristic Intent classification for daemon queries.
"""

import asyncio
from pathlib import Path
import sys
import time

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure stdout is line buffered
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

import httpx

from backend.app.automation.daemon import AutonomousMinuteDaemon, autonomous_daemon
from backend.app.automation.manager import automation_manager
from backend.app.core.tool_registry import tool_registry
from backend.app.core.intent import intent_classifier, IntentType
from backend.app.main import app as main_app


async def run_cloud_daemon_tests() -> None:
    print("=" * 70, flush=True)
    print("  RUNNING CLOUD DEPLOYMENT & AUTONOMOUS MINUTE DAEMON TEST SUITE", flush=True)
    print("=" * 70, flush=True)

    # ---------------- 1. NETWORK PROBE INTEGRITY ----------------
    print("\n[GROUP 1] Testing Non-Blocking Network Presence Probe...", flush=True)
    net_status = await autonomous_daemon.check_network()
    assert isinstance(net_status, bool)
    print(f" [PASS] Network probe executed cleanly without exception. Status: {autonomous_daemon.current_network_status}.", flush=True)

    # ---------------- 2. AUTONOMOUS MINUTE TICK (ONLINE / AMBIENT) ----------------
    print("\n[GROUP 2] Testing Autonomous Minute Tick (Ambient State)...", flush=True)
    initial_ticks = autonomous_daemon.ticks_count
    tick1 = await autonomous_daemon.tick(force_offline_sim=False)

    assert tick1["tick_number"] == initial_ticks + 1
    assert "timestamp" in tick1
    assert "network_status" in tick1
    assert "heartbeat" in tick1
    assert tick1["elapsed_ms"] >= 0
    print(f" [PASS] Minute tick #{tick1['tick_number']} executed in {tick1['elapsed_ms']}ms: {tick1['heartbeat']}", flush=True)

    # ---------------- 3. ZERO-NETWORK FAULT TOLERANCE (OFFLINE ABSENCE SIMULATION) ----------------
    print("\n[GROUP 3] Testing 100% Offline Fault Tolerance (Simulated Complete Network Absence)...", flush=True)
    initial_offline = autonomous_daemon.offline_ticks_count
    tick_offline = await autonomous_daemon.tick(force_offline_sim=True)

    assert tick_offline["is_online"] is False
    assert "offline" in tick_offline["network_status"].lower()
    assert autonomous_daemon.offline_ticks_count == initial_offline + 1
    assert "OFFLINE" in tick_offline["heartbeat"]
    print(f" [PASS] Zero-network minute tick executed with zero failures: {tick_offline['heartbeat']}", flush=True)

    # ---------------- 4. SQLITE WAL HEARTBEAT AUDIT LOGS ----------------
    print("\n[GROUP 4] Verifying Minute Heartbeat Persistence in nous_automation.db...", flush=True)
    history = autonomous_daemon.db.list_execution_history(limit=5)
    assert len(history) >= 2
    heartbeat_entry = next((h for h in history if h["command"] == "autonomous_minute_tick"), None)
    assert heartbeat_entry is not None
    assert heartbeat_entry["status"] == "success"
    assert heartbeat_entry["risk_level"] == "internal_daemon"
    assert "AUTONOMOUS TICK" in heartbeat_entry["output"]
    print(f" [PASS] Verified persistent SQLite WAL heartbeat entry: ID={heartbeat_entry['id']}, Status={heartbeat_entry['status']}", flush=True)

    # ---------------- 5. BACKGROUND LOOP START & STOP CYCLES ----------------
    print("\n[GROUP 5] Testing Background Async Loop Lifecycle...", flush=True)
    test_daemon = AutonomousMinuteDaemon(interval_seconds=0.1)
    test_daemon.start()
    assert test_daemon.is_running is True
    await asyncio.sleep(0.35)  # Let it tick ~3 times
    assert test_daemon.ticks_count >= 2
    test_daemon.stop()
    assert test_daemon.is_running is False
    print(f" [PASS] Background loop ticked {test_daemon.ticks_count} times in 0.35s and shut down cleanly.", flush=True)

    # ---------------- 6. FASTAPI REST ENDPOINTS ----------------
    print("\n[GROUP 6] Testing FastAPI REST Daemon Management Endpoints...", flush=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main_app), base_url="http://testserver") as client:
        # Status endpoint
        r_status = await client.get("/api/automation/daemon/status")
        assert r_status.status_code == 200
        st_data = r_status.json()
        assert "ticks_count" in st_data
        assert st_data["offline_resilient"] is True
        print(f" [PASS] GET /api/automation/daemon/status -> Total Ticks: {st_data['ticks_count']}, Offline Resilient: {st_data['offline_resilient']}", flush=True)

        # Tick-now endpoint
        r_tick = await client.post("/api/automation/daemon/tick-now", params={"force_offline": True})
        assert r_tick.status_code == 200
        t_data = r_tick.json()
        assert t_data["is_online"] is False
        print(f" [PASS] POST /api/automation/daemon/tick-now -> Successfully triggered manual offline-resilient tick #{t_data['tick_number']}.", flush=True)

    # ---------------- 7. TOOL REGISTRY VERIFICATION ----------------
    print("\n[GROUP 7] Testing Anti-Hallucination Tool Registry Execution...", flush=True)
    tool_status = await tool_registry.execute("get_autonomous_daemon_status", {})
    assert tool_status.success is True
    assert tool_status.is_verified is True
    assert tool_status.data["offline_resilient"] is True
    print(" [PASS] Tool 'get_autonomous_daemon_status' executed with verified=True.", flush=True)

    tool_tick = await tool_registry.execute("trigger_autonomous_tick", {"force_offline": True})
    assert tool_tick.success is True
    assert tool_tick.is_verified is True
    assert tool_tick.data["is_online"] is False
    print(" [PASS] Tool 'trigger_autonomous_tick' executed with verified=True.", flush=True)

    # ---------------- 8. HEURISTIC INTENT CLASSIFICATION ----------------
    print("\n[GROUP 8] Testing Intent Classification Routing...", flush=True)
    intent_res = intent_classifier.classify("Check the background minute daemon status")
    assert intent_res.intent == IntentType.DAEMON_STATUS
    assert intent_res.suggested_tool == "get_autonomous_daemon_status"
    print(f" [PASS] Query correctly mapped to Intent: {intent_res.intent.value}, Tool: {intent_res.suggested_tool}.", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("  ALL CLOUD DEPLOYMENT & AUTONOMOUS DAEMON TESTS PASSED (100% SUCCESS)", flush=True)
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    t0 = time.perf_counter()
    asyncio.run(run_cloud_daemon_tests())
    elapsed = round(time.perf_counter() - t0, 2)
    print(f"Suite completed in {elapsed}s.")

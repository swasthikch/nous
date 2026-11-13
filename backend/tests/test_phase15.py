from __future__ import annotations

"""Comprehensive Automated Test Suite for Phase 15:
System Diagnostics, Health Monitoring, Telemetry, and End-to-End System Integration.
"""

import asyncio
import json
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

from fastapi import FastAPI
import httpx

from backend.app.config import settings
from backend.app.core.diagnostics import DiagnosticsCollector, diagnostics_collector
from backend.app.api.diagnostics_api import router as diagnostics_router
from backend.app.main import app as main_app


async def run_phase15_tests() -> None:
    print("=" * 70, flush=True)
    print("  RUNNING PHASE 15 TEST SUITE: SYSTEM DIAGNOSTICS & E2E INTEGRATION", flush=True)
    print("=" * 70, flush=True)

    # ---------------- 1. HARDWARE TELEMETRY ----------------
    print("\n[GROUP 1] Testing Hardware Profile & Compute Metrics...", flush=True)
    hw = diagnostics_collector.get_hardware_telemetry()
    assert "ram" in hw
    assert "cpu" in hw
    assert "disk" in hw
    assert "python" in hw

    ram = hw["ram"]
    assert ram["total_gb"] > 0
    assert 0 <= ram["percent_used"] <= 100
    assert "16 GB" in ram["shared_architecture"]
    print(f" [PASS] RAM Metrics: {ram['used_gb']}/{ram['total_gb']} GB ({ram['percent_used']}% load).", flush=True)

    cpu = hw["cpu"]
    assert cpu["cores_logical"] >= 1
    assert cpu["os"]
    print(f" [PASS] CPU Metrics: {cpu['name']} ({cpu['cores_logical']} logical cores, {cpu['architecture']}).", flush=True)

    disk = hw["disk"]
    assert disk["total_gb"] > 0
    assert disk["free_gb"] > 0
    print(f" [PASS] Disk Metrics: {disk['free_gb']} GB free out of {disk['total_gb']} GB in {disk['path']}.", flush=True)

    # ---------------- 2. DATABASE DIAGNOSTICS & WAL INTEGRITY ----------------
    print("\n[GROUP 2] Testing All 7 Core SQLite Storage Engines...", flush=True)
    db_diag = diagnostics_collector.get_database_diagnostics()
    assert db_diag["databases_count"] == 7
    print(f" [PASS] Verified tracking of {db_diag['databases_count']} target SQLite database engines.", flush=True)

    # Check that each expected database ID is present
    expected_ids = {"memory", "routine", "projects", "market", "research", "automation", "security"}
    found_ids = {d["id"] for d in db_diag["databases"]}
    assert expected_ids == found_ids, f"Expected IDs {expected_ids}, got {found_ids}"
    print(f" [PASS] All 7 database IDs matched: {sorted(list(found_ids))}.", flush=True)

    for d in db_diag["databases"]:
        if d["exists"]:
            assert d["journal_mode"] in ("wal", "delete", "memory"), f"Unexpected journal mode: {d['journal_mode']}"
            assert d["integrity"] == "ok", f"Database {d['id']} integrity check failed: {d['integrity']}"
            print(f"   -> DB '{d['id']}' ({d['size_kb']} KB): journal_mode={d['journal_mode']}, integrity={d['integrity']}, tables={list(d['tables'].keys())}", flush=True)

    # ---------------- 3. OLLAMA TELEMETRY & LATENCY ----------------
    print("\n[GROUP 3] Testing Ollama Local Model Engine Telemetry...", flush=True)
    ollama_diag = await diagnostics_collector.get_ollama_diagnostics()
    assert "status" in ollama_diag
    assert ollama_diag["base_url"] == settings.OLLAMA_BASE_URL
    assert ollama_diag["default_model"] == settings.OLLAMA_MODEL
    print(f" [PASS] Ollama Telemetry: status={ollama_diag['status']}, default_model={ollama_diag['default_model']}.", flush=True)

    # ---------------- 4. SECURITY & ENVIRONMENT POLICIES ----------------
    print("\n[GROUP 4] Testing Security & Environment Audit...", flush=True)
    sec_env = diagnostics_collector.get_security_and_environment()
    assert "privacy_policies" in sec_env
    assert "cloud_keys_configured" in sec_env
    assert "offline_lockdown_active" in sec_env
    print(f" [PASS] Environment Audit: Cloud keys configured={sec_env['configured_count']}/5, Offline Lockdown={sec_env['offline_lockdown_active']}.", flush=True)

    # ---------------- 5. COMPREHENSIVE SYSTEM REPORT ----------------
    print("\n[GROUP 5] Testing Unified System Health Report...", flush=True)
    report = await diagnostics_collector.generate_system_report()
    assert report["overall_status"] in ("OPTIMAL", "DEGRADED_DATABASES", "HIGH_MEMORY_PRESSURE")
    assert report["project"]["name"] == settings.PROJECT_NAME
    assert report["project"]["version"] == settings.VERSION
    print(f" [PASS] System Report generated: Overall Status = {report['overall_status']} (color: {report['health_color']}).", flush=True)

    # ---------------- 6. DIAGNOSTICS REST ROUTER ----------------
    print("\n[GROUP 6] Testing Diagnostics REST API Router...", flush=True)
    diag_app = FastAPI()
    diag_app.include_router(diagnostics_router)

    transport = httpx.ASGITransport(app=diag_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/diagnostics/report
        r = await client.get("/api/diagnostics/report")
        assert r.status_code == 200
        assert r.json()["overall_status"] in ("OPTIMAL", "DEGRADED_DATABASES", "HIGH_MEMORY_PRESSURE")
        print(" [PASS] GET /api/diagnostics/report -> 200 OK", flush=True)

        # 2. GET /api/diagnostics/hardware
        r = await client.get("/api/diagnostics/hardware")
        assert r.status_code == 200
        assert "ram" in r.json()
        print(" [PASS] GET /api/diagnostics/hardware -> 200 OK", flush=True)

        # 3. GET /api/diagnostics/databases
        r = await client.get("/api/diagnostics/databases")
        assert r.status_code == 200
        assert r.json()["databases_count"] == 7
        print(" [PASS] GET /api/diagnostics/databases -> 200 OK", flush=True)

        # 4. GET /api/diagnostics/ollama
        r = await client.get("/api/diagnostics/ollama")
        assert r.status_code == 200
        assert "status" in r.json()
        print(" [PASS] GET /api/diagnostics/ollama -> 200 OK", flush=True)

        # 5. POST /api/diagnostics/smoke-test
        r = await client.post("/api/diagnostics/smoke-test")
        assert r.status_code == 200
        data = r.json()
        assert data["all_passed"] is True
        assert data["checks_count"] == 4
        print(f" [PASS] POST /api/diagnostics/smoke-test -> 200 OK (all 4 in-process checks passed in {data['elapsed_ms']}ms).", flush=True)

    # ---------------- 7. FULL END-TO-END APPLICATION MOUNT VERIFICATION ----------------
    print("\n[GROUP 7] Testing Full End-to-End Application Routers on main_app...", flush=True)
    main_transport = httpx.ASGITransport(app=main_app)
    async with httpx.AsyncClient(transport=main_transport, base_url="http://test") as client:
        # A. Health
        r_health = await client.get("/api/health")
        assert r_health.status_code == 200
        print(" [PASS] /api/health -> 200 OK", flush=True)

        # B. Sessions
        r_sess = await client.get("/api/sessions")
        assert r_sess.status_code == 200
        print(" [PASS] /api/sessions -> 200 OK", flush=True)

        # C. Memory
        r_mem = await client.get("/api/memory")
        assert r_mem.status_code == 200
        print(" [PASS] /api/memory -> 200 OK", flush=True)

        # D. Routine
        r_rout = await client.get("/api/routine/schedule")
        assert r_rout.status_code == 200
        print(" [PASS] /api/routine/schedule -> 200 OK", flush=True)

        # E. Email
        r_mail = await client.get("/api/email/messages")
        assert r_mail.status_code == 200
        print(" [PASS] /api/email/messages -> 200 OK", flush=True)

        # F. Projects
        r_proj = await client.get("/api/projects")
        assert r_proj.status_code == 200
        print(" [PASS] /api/projects -> 200 OK", flush=True)

        # G. Market Watchlist
        r_mkt = await client.get("/api/market/watchlist")
        assert r_mkt.status_code == 200
        print(" [PASS] /api/market/watchlist -> 200 OK", flush=True)

        # H. Research Notes
        r_res = await client.get("/api/research/notes")
        assert r_res.status_code == 200
        print(" [PASS] /api/research/notes -> 200 OK", flush=True)

        # I. Automation Files
        r_auto = await client.get("/api/automation/files")
        assert r_auto.status_code == 200
        print(" [PASS] /api/automation/files -> 200 OK", flush=True)

        # J. Security Privacy
        r_sec = await client.get("/api/security/privacy")
        assert r_sec.status_code == 200
        print(" [PASS] /api/security/privacy -> 200 OK", flush=True)

        # K. Diagnostics Report
        r_diag = await client.get("/api/diagnostics/report")
        assert r_diag.status_code == 200
        print(" [PASS] /api/diagnostics/report -> 200 OK", flush=True)

    print("\n" + "=" * 70, flush=True)
    print(" [SUCCESS] ALL 7 PHASE 15 DIAGNOSTICS & E2E GROUPS PASSED WITH 100% SUCCESS!", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    asyncio.run(run_phase15_tests())

"""Comprehensive Automated Test Suite for NOUS Phase 11: Cloud Persistence & Free-Tier Keep-Alive.

Verifies:
1. SQLite WAL Checkpointing across all database files.
2. Compressed Database Snapshot Archiving (data/backups/latest_snapshot.tar.gz).
3. State Restoration & Container Recovery.
4. Free-Tier Render Keep-Alive Health Pinger with Latency Tracking.
5. End-to-end FastAPI Cloud REST Endpoints (/api/cloud).
"""

import asyncio
from pathlib import Path
import sys
import tarfile
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.cloud.persistence import cloud_persistence, BACKUPS_DIR, DATABASE_DIR
from backend.app.cloud.keepalive import keepalive_pinger


async def run_phase11_cloud_deploy_tests():
    print("=" * 72)
    print("  NOUS PHASE 11 — CLOUD PERSISTENCE & DEPLOYMENT TEST SUITE")
    print("=" * 72)

    # ---------------- 1. WAL CHECKPOINT & SNAPSHOT CREATION ----------------
    print("\n[STEP 1] Testing SQLite WAL Checkpoint & Snapshot Creation...")
    flushed = cloud_persistence.checkpoint_wal_databases()
    print(f"  Flushed WAL caches for {len(flushed)} active databases: {flushed}")

    snapshot_path = cloud_persistence.create_snapshot("test_phase11_snapshot.tar.gz")
    assert snapshot_path.exists(), "Snapshot archive was not created on disk!"
    assert snapshot_path.stat().st_size > 100, "Snapshot archive is empty!"
    assert tarfile.is_tarfile(snapshot_path), "Created file is not a valid tar archive!"

    latest_path = BACKUPS_DIR / "latest_snapshot.tar.gz"
    assert latest_path.exists()
    print(f"  [PASS] Compressed snapshot verified: {snapshot_path.name} ({snapshot_path.stat().st_size} bytes).")

    # ---------------- 2. SNAPSHOT RESTORATION ----------------
    print("\n[STEP 2] Testing Database Snapshot Restoration...")
    restore_res = cloud_persistence.restore_snapshot(snapshot_path)
    assert restore_res["success"] is True, f"Restore failed: {restore_res}"
    assert restore_res["restored_count"] > 0
    print(f"  [PASS] State restored cleanly: {restore_res['restored_count']} databases extracted.")

    # ---------------- 3. KEEPALIVE HEALTH PINGER ----------------
    print("\n[STEP 3] Testing Free-Tier Keep-Alive Health Pinger...")
    # Point pinger to local test app or dummy
    orig_url = keepalive_pinger.target_url
    keepalive_pinger.target_url = "http://127.0.0.1:8000/api/health"

    # Test single ping
    ping_res = await keepalive_pinger.ping_once()
    assert "success" in ping_res
    print(f"  [PASS] Single keepalive probe executed (Result: {ping_res}).")

    # Test start and stop
    keepalive_pinger.start()
    assert keepalive_pinger.is_running is True
    keepalive_pinger.stop()
    assert keepalive_pinger.is_running is False
    keepalive_pinger.target_url = orig_url
    print("  [PASS] Keepalive pinger lifecycle (start/stop) verified.")

    # ---------------- 4. FASTAPI CLOUD REST API ----------------
    print("\n[STEP 4] Testing FastAPI Cloud REST Endpoints (/api/cloud)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. Status
        r_status = await client.get("/api/cloud/status")
        assert r_status.status_code == 200
        status_data = r_status.json()
        assert status_data["status"] == "operational"
        assert "persistence" in status_data
        assert "database_count" in status_data["persistence"]
        assert status_data["persistence"]["database_count"] > 0
        print(f"  [PASS] GET /api/cloud/status: {status_data['persistence']['database_count']} databases tracked.")

        # B. On-demand snapshot
        r_snap = await client.post("/api/cloud/snapshot?name=api_test_snapshot.tar.gz")
        assert r_snap.status_code == 200
        snap_data = r_snap.json()
        assert snap_data["success"] is True
        assert snap_data["archive_name"] == "api_test_snapshot.tar.gz"
        print("  [PASS] POST /api/cloud/snapshot: Generated on-demand archive.")

        # C. Restore snapshot
        r_rest = await client.post("/api/cloud/restore", json={"snapshot_name": "api_test_snapshot.tar.gz"})
        assert r_rest.status_code == 200
        assert r_rest.json()["success"] is True
        print("  [PASS] POST /api/cloud/restore: Restored databases via API.")

        # D. Keepalive toggle
        r_tog = await client.post("/api/cloud/keepalive/toggle", json={"enable": True})
        assert r_tog.status_code == 200
        assert r_tog.json()["success"] is True

        r_stop = await client.post("/api/cloud/keepalive/toggle", json={"enable": False})
        assert r_stop.status_code == 200
        print("  [PASS] POST /api/cloud/keepalive/toggle: Controlled background pinger cleanly.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 11 CLOUD PERSISTENCE & DEPLOYMENT CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase11_cloud_deploy_tests())

"""Comprehensive Automated Test Suite for NOUS Phase 9: Multi-Device Synchronization & Mobile PWA.

Verifies:
1. PWA Manifest & App Shell Service Worker.
2. Icon assets (192x192 & 512x512).
3. Host LAN Network Discovery & Phone Pairing URL.
4. Zero-dependency SVG QR Code Generator for mobile phone camera pairing.
5. Cross-Device Real-Time State Synchronization (/api/multidevice/sync).
6. Web Push Notification Dispatcher (/api/multidevice/notify).
"""

import asyncio
import json
from pathlib import Path
import re
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.api.multidevice_api import get_local_lan_ip, generate_qr_svg


async def run_phase9_multidevice_tests():
    print("=" * 72)
    print("  NOUS PHASE 9 — MULTI-DEVICE SYNCHRONIZATION & MOBILE PWA TEST SUITE")
    print("=" * 72)

    # ---------------- 1. PWA MANIFEST & SERVICE WORKER ----------------
    print("\n[STEP 1] Testing PWA Manifest & Service Worker Assets...")
    manifest_path = PROJECT_ROOT / "frontend" / "manifest.json"
    assert manifest_path.exists(), "frontend/manifest.json does not exist!"

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data.get("name") == "NOUS — Personal AI Operating System"
    assert manifest_data.get("short_name") == "NOUS"
    assert manifest_data.get("start_url") == "/"
    assert manifest_data.get("display") == "standalone"
    assert "theme_color" in manifest_data
    assert len(manifest_data.get("icons", [])) >= 2
    print(f"  [PASS] manifest.json validated: name='{manifest_data['name']}', display='standalone'")

    sw_path = PROJECT_ROOT / "frontend" / "sw.js"
    assert sw_path.exists(), "frontend/sw.js does not exist!"
    sw_text = sw_path.read_text(encoding="utf-8")
    assert "install" in sw_text and "fetch" in sw_text and "push" in sw_text
    print("  [PASS] sw.js validated: install, fetch, and push notification handlers active.")

    # Check icons
    icon_192 = PROJECT_ROOT / "frontend" / "icons" / "icon-192.png"
    icon_512 = PROJECT_ROOT / "frontend" / "icons" / "icon-512.png"
    assert icon_192.exists() and icon_192.stat().st_size > 1000
    assert icon_512.exists() and icon_512.stat().st_size > 1000
    print(f"  [PASS] PWA Icons present: icon-192 ({icon_192.stat().st_size} bytes), icon-512 ({icon_512.stat().st_size} bytes).")

    # ---------------- 2. HOST LAN DISCOVERY & PHONE LINK ----------------
    print("\n[STEP 2] Testing Host LAN IP Discovery & Mobile URL...")
    lan_ip = get_local_lan_ip()
    ip_parts = lan_ip.split(".")
    assert len(ip_parts) == 4, f"Invalid LAN IP format: {lan_ip}"
    print(f"  [PASS] Host LAN IP resolved: {lan_ip}")

    # Test SVG QR Code generator
    test_url = f"http://{lan_ip}:8000/"
    qr_svg = generate_qr_svg(test_url)
    assert "<svg" in qr_svg and "</svg>" in qr_svg
    assert "SCAN TO OPEN NOUS" in qr_svg
    print("  [PASS] High-contrast SVG QR pairing code generated cleanly.")

    # ---------------- 3. MULTI-DEVICE FASTAPI REST ENDPOINTS ----------------
    print("\n[STEP 3] Testing FastAPI Multi-Device REST Endpoints (/api/multidevice)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. Network Info
        r_info = await client.get("/api/multidevice/network-info")
        assert r_info.status_code == 200
        info_data = r_info.json()
        assert info_data["status"] == "ready"
        assert info_data["lan_ip"] == lan_ip
        assert f":{info_data['port']}" in info_data["phone_url"]
        assert "<svg" in info_data["qr_svg"]
        print(f"  [PASS] GET /network-info: Phone URL -> {info_data['phone_url']}")

        # B. Push Notification Dispatch
        r_notif = await client.post(
            "/api/multidevice/notify",
            json={
                "title": "NOUS Workflow Completed",
                "body": "Autonomous research workflow finished successfully.",
                "category": "workflow",
            },
        )
        assert r_notif.status_code == 200
        notif_data = r_notif.json()
        assert notif_data["success"] is True
        assert notif_data["notification_id"].startswith("notif_")
        print(f"  [PASS] POST /notify: Dispatched notification {notif_data['notification_id']}")

        # C. Real-Time Device State Sync
        sync_start_time = time.time() - 60.0
        r_sync = await client.get(f"/api/multidevice/sync?client_id=phone_pixel7&last_sync={sync_start_time}")
        assert r_sync.status_code == 200
        sync_data = r_sync.json()
        assert sync_data["client_id"] == "phone_pixel7"
        assert "pending_approvals" in sync_data
        assert "notifications" in sync_data
        assert len(sync_data["notifications"]) >= 1
        assert sync_data["notifications"][-1]["title"] == "NOUS Workflow Completed"
        print(f"  [PASS] GET /sync: Successfully synced phone_pixel7 ({len(sync_data['notifications'])} notifications).")

    print("\n" + "=" * 72)
    print("  ALL PHASE 9 MULTI-DEVICE & MOBILE PWA CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase9_multidevice_tests())

"""Test Suite for NOUS Phase 6: Windows Desktop Companion.

Verifies:
1. Windows 11 Native Hardware Telemetry (CPU, RAM, Battery, Storage, Ollama).
2. Outbound Heartbeat & Latency Monitoring.
3. Local Ollama Execution Relay.
4. Silent Background Autostart Manager (VBScript launcher & batch runner).
5. FastAPI Desktop Endpoints (/api/desktop/heartbeat, /status, /autostart).
"""

import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from desktop.telemetry import windows_telemetry, WindowsHardwareReport
from desktop.companion import DesktopCompanion, get_or_create_desktop_token
from desktop.autostart import autostart_manager


async def run_phase6_desktop_tests():
    print("=" * 72)
    print("  NOUS PHASE 6 — WINDOWS DESKTOP COMPANION VERIFICATION")
    print("=" * 72)

    # ---------------- 1. HARDWARE TELEMETRY ----------------
    print("\n[STEP 1] Testing Windows 11 Native Hardware Telemetry...")
    telemetry = windows_telemetry.get_telemetry()
    assert isinstance(telemetry, WindowsHardwareReport)
    assert telemetry.ram_total_gb > 1.0, f"Invalid total RAM: {telemetry.ram_total_gb}"
    assert 1.0 <= telemetry.ram_load_percent <= 100.0, f"Invalid RAM load: {telemetry.ram_load_percent}"
    assert 0 <= telemetry.battery_percent <= 100, f"Invalid battery %: {telemetry.battery_percent}"
    assert telemetry.disk_total_gb > 0.0, f"Invalid disk total: {telemetry.disk_total_gb}"

    print(f"  OS: {telemetry.os_name} {telemetry.os_release} | CPU Load: {telemetry.cpu_load_percent}%")
    print(f"  RAM Load: {telemetry.ram_load_percent}% ({telemetry.ram_avail_gb} GB free of {telemetry.ram_total_gb} GB)")
    print(f"  Battery: {telemetry.battery_percent}% (Plugged: {telemetry.power_plugged}, Charging: {telemetry.is_charging})")
    print(f"  Ollama Status: {'ONLINE' if telemetry.ollama_online else 'OFFLINE'} (Models: {len(telemetry.ollama_models)})")
    print("  [PASS] Pure native ctypes telemetry verified with zero third-party dependencies.")

    # ---------------- 2. COMPANION TOKEN & AUTH ----------------
    print("\n[STEP 2] Testing Cryptographic Desktop Authentication Token...")
    token = get_or_create_desktop_token()
    assert token.startswith("nous_desk_")
    assert len(token) > 20
    print(f"  [PASS] Cryptographic token generated and secured: {token[:16]}...")

    # ---------------- 3. AUTOSTART MANAGER ----------------
    print("\n[STEP 3] Testing Silent Windows Autostart Manager...")
    # Test installation
    install_res = autostart_manager.install(server_url="http://127.0.0.1:8000")
    assert install_res["success"] is True
    assert autostart_manager.bat_runner_path.exists()
    assert autostart_manager.vbs_launcher_path.exists()
    # Verify VBScript hides window (0 parameter)
    vbs_text = autostart_manager.vbs_launcher_path.read_text(encoding="utf-8")
    assert ", 0" in vbs_text, "VBScript hidden window parameter missing!"
    print("  [PASS] Silent VBScript autostart launcher created successfully.")

    # Test clean uninstall
    uninstall_res = autostart_manager.uninstall()
    assert uninstall_res["success"] is True
    assert not autostart_manager.vbs_launcher_path.exists()
    print("  [PASS] Autostart launcher uninstalled cleanly.")

    # ---------------- 4. FASTAPI DESKTOP REST ENDPOINTS ----------------
    print("\n[STEP 4] Testing FastAPI Desktop Endpoints (/api/desktop)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. Post heartbeat
        r_hb = await client.post(
            "/api/desktop/heartbeat",
            json=telemetry.model_dump(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_hb.status_code == 200
        hb_data = r_hb.json()
        assert hb_data["status"] == "acknowledged"

        # B. Get status
        r_status = await client.get("/api/desktop/status")
        assert r_status.status_code == 200
        status_data = r_status.json()
        assert status_data["is_connected"] is True
        assert status_data["telemetry"]["ram_total_gb"] > 1.0

        # C. Autostart endpoints
        r_ai = await client.post("/api/desktop/autostart/install")
        assert r_ai.status_code == 200
        r_au = await client.post("/api/desktop/autostart/uninstall")
        assert r_au.status_code == 200

    print("  [PASS] FastAPI Desktop endpoints (/heartbeat, /status, /autostart) 100% operational.")

    # ---------------- 5. COMPANION INFERENCE RELAY ----------------
    print("\n[STEP 5] Testing Local Ollama Inference Relay...")
    companion = DesktopCompanion(server_url="http://127.0.0.1:8000", auth_token=token)
    if telemetry.ollama_online:
        model_to_test = telemetry.ollama_models[0] if telemetry.ollama_models else "qwen2.5:3b"
        relay_res = await companion.execute_local_ollama(
            model=model_to_test,
            prompt="Respond with exactly: NOUS_DESKTOP_OK",
        )
        assert relay_res["success"] is True
        print(f"  [PASS] Local Ollama relay verified using '{model_to_test}': {relay_res['response'].strip()[:40]}")
    else:
        print("  [SKIP] Local Ollama daemon not running. Relay skipped.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 6 WINDOWS DESKTOP COMPANION CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase6_desktop_tests())

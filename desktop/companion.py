"""NOUS Windows 11 Desktop Companion (Phase 6).

Runs as a lightweight background client on the user's laptop:
1. Performs outbound heartbeats with hardware telemetry (CPU, RAM, Battery, Storage, Ollama).
2. Connects laptop Ollama to NOUS without exposing any inbound ports to the internet.
3. Automatically authenticates using a secure shared cryptographic token.
4. Enables the cloud instance to offload heavy inference to the user's local laptop Ollama for free.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import time
from pathlib import Path
from typing import Any, Optional
import httpx
from pydantic import BaseModel, Field

from desktop.telemetry import windows_telemetry, WindowsHardwareReport

TOKEN_FILE = Path(__file__).resolve().parent.parent / "data" / "credentials" / "desktop_token.txt"


def get_or_create_desktop_token() -> str:
    """Retrieve or generate secure companion authentication token."""
    env_token = os.getenv("NOUS_DESKTOP_TOKEN", "").strip()
    if env_token:
        return env_token

    if TOKEN_FILE.exists():
        try:
            return TOKEN_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    # Generate cryptographic 32-byte URL-safe token
    new_token = f"nous_desk_{secrets.token_urlsafe(32)}"
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(new_token, encoding="utf-8")
    return new_token


class CompanionStatus(BaseModel):
    is_running: bool = False
    server_url: str
    last_heartbeat_time: Optional[float] = None
    last_heartbeat_status: str = "INITIALIZING"
    server_latency_ms: float = 0.0
    heartbeats_sent: int = 0
    errors_count: int = 0
    local_ollama_available: bool = False


class DesktopCompanion:
    """Lightweight Windows background companion client."""

    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8000",
        auth_token: Optional[str] = None,
        heartbeat_interval: float = 15.0,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.auth_token = auth_token or get_or_create_desktop_token()
        self.heartbeat_interval = heartbeat_interval
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self.status = CompanionStatus(server_url=self.server_url)

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "User-Agent": "NOUS-Desktop-Companion/1.0",
        }

    async def send_heartbeat(self) -> dict[str, Any]:
        """Collect local telemetry and post to the NOUS server."""
        t0 = time.time()
        report = windows_telemetry.get_telemetry()
        self.status.local_ollama_available = report.ollama_online

        url = f"{self.server_url}/api/desktop/heartbeat"
        payload = report.model_dump()

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                latency = round((time.time() - t0) * 1000.0, 1)
                self.status.server_latency_ms = latency
                self.status.last_heartbeat_time = time.time()
                self.status.heartbeats_sent += 1

                if resp.status_code == 200:
                    self.status.last_heartbeat_status = "CONNECTED"
                    return {"success": True, "latency_ms": latency, "server_data": resp.json()}
                else:
                    self.status.last_heartbeat_status = f"HTTP_{resp.status_code}"
                    self.status.errors_count += 1
                    return {"success": False, "status_code": resp.status_code, "detail": resp.text}
        except Exception as e:
            self.status.last_heartbeat_status = "DISCONNECTED"
            self.status.errors_count += 1
            return {"success": False, "error": str(e)}

    async def execute_local_ollama(self, model: str, prompt: str, system: str = "") -> dict[str, Any]:
        """Relay inference task directly to local laptop Ollama."""
        ollama_url = f"{windows_telemetry.ollama_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(ollama_url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    return {"success": True, "response": data.get("response", ""), "model": model}
                return {"success": False, "error": f"Ollama HTTP {r.status_code}: {r.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_loop(self) -> None:
        """Continuous background heartbeat loop."""
        self._is_running = True
        self.status.is_running = True
        print(f"[COMPANION] Started. Target server: {self.server_url}")
        print(f"[COMPANION] Authenticating with token: {self.auth_token[:12]}...")

        while self._is_running:
            res = await self.send_heartbeat()
            if res.get("success"):
                print(f"[COMPANION] Heartbeat OK ({res.get('latency_ms')}ms) - RAM: {windows_telemetry.get_telemetry().ram_load_percent}%")
            else:
                print(f"[COMPANION] Heartbeat notice: {res.get('last_heartbeat_status') or res.get('error')}")

            await asyncio.sleep(self.heartbeat_interval)

    def start(self) -> None:
        """Start companion in background event loop."""
        if not self._is_running:
            self._task = asyncio.create_task(self.run_loop())

    def stop(self) -> None:
        """Stop companion heartbeat loop cleanly."""
        self._is_running = False
        self.status.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        print("[COMPANION] Stopped cleanly.")


desktop_companion = DesktopCompanion()


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    comp = DesktopCompanion(server_url=url)
    try:
        asyncio.run(comp.run_loop())
    except KeyboardInterrupt:
        print("\nCompanion stopped by user.")

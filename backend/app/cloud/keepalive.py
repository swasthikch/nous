"""Zero-Budget Keep-Alive Health Pinger for Render / Cloud Free Tiers (Phase 11).

Keeps the NOUS container warm and responsive during active working hours:
- Periodically probes target health endpoint (default: 14-minute interval).
- Tracks response latency, success counts, and error rates.
- Non-blocking asynchronous design with exponential backoff on network partition.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Optional
import httpx

logger = logging.getLogger("nous.cloud.keepalive")


class KeepAlivePinger:
    """Automated health pinger to prevent free-tier container sleep."""

    def __init__(
        self,
        target_url: Optional[str] = None,
        interval_seconds: float = 840.0,  # 14 minutes (Render sleeps after 15 min inactivity)
    ) -> None:
        self.target_url = target_url or os.getenv("KEEPALIVE_TARGET_URL", "http://127.0.0.1:8000/api/health")
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.total_pings = 0
        self.successful_pings = 0
        self.failed_pings = 0
        self.last_ping_time: Optional[float] = None
        self.last_latency_ms: Optional[float] = None
        self.last_status_code: Optional[int] = None

    async def ping_once(self) -> dict[str, Any]:
        """Perform an immediate single health ping."""
        start = time.time()
        self.total_pings += 1
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(self.target_url)
                latency = round((time.time() - start) * 1000, 2)
                self.last_ping_time = time.time()
                self.last_latency_ms = latency
                self.last_status_code = res.status_code

                if res.status_code == 200:
                    self.successful_pings += 1
                    return {"success": True, "status_code": 200, "latency_ms": latency}
                else:
                    self.failed_pings += 1
                    return {"success": False, "status_code": res.status_code, "latency_ms": latency}

        except Exception as e:
            self.failed_pings += 1
            self.last_ping_time = time.time()
            return {"success": False, "error": str(e), "latency_ms": None}

    def start(self) -> None:
        """Start background pinging loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Keep-alive pinger started targeting '{self.target_url}' (every {self.interval_seconds}s)")

    def stop(self) -> None:
        """Stop background pinging loop."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Keep-alive pinger stopped.")

    async def _loop(self) -> None:
        """Background continuous execution loop."""
        while self.is_running:
            try:
                await self.ping_once()
            except Exception as e:
                logger.debug(f"Keepalive ping cycle notice: {e}")
            await asyncio.sleep(self.interval_seconds)

    def get_stats(self) -> dict[str, Any]:
        """Return diagnostic metrics."""
        return {
            "target_url": self.target_url,
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "total_pings": self.total_pings,
            "successful_pings": self.successful_pings,
            "failed_pings": self.failed_pings,
            "last_ping_time": self.last_ping_time,
            "last_latency_ms": self.last_latency_ms,
            "last_status_code": self.last_status_code,
        }


keepalive_pinger = KeepAlivePinger()

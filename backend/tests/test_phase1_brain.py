"""Phase 1 Central AI Brain & Orchestration Verification Suite.

Tests:
1. Provider Abstraction & Polymorphism (OllamaProvider, CloudModelProvider).
2. Health check & model discovery.
3. Central Orchestrator cognitive pipeline (intent -> context -> tools -> response).
4. Anti-hallucination tool execution gate.
5. Server-Sent Events (SSE) streaming generator.
6. FastAPI REST & Streaming HTTP endpoints (/api/chat, /api/chat/stream, /api/models).
7. Backward compatibility with legacy ai_brain imports.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.ai_core.orchestrator import orchestrator, CentralOrchestrator
from backend.app.providers.base import BaseModelProvider, ProviderHealth, ProviderResponse, StreamChunk
from backend.app.providers.ollama_provider import OllamaProvider
from backend.app.providers.cloud_provider import CloudModelProvider
from backend.app.core.ai_engine import ai_brain, AIEngineResponse


async def run_phase1_brain_tests() -> None:
    print("=" * 72)
    print("  NOUS PHASE 1 — CENTRAL AI BRAIN & ORCHESTRATION VERIFICATION")
    print("=" * 72)

    # ---------------- 1. PROVIDER ABSTRACTION ----------------
    print("\n[STEP 1] Testing Provider Abstraction & Polymorphism...")
    ollama_p = OllamaProvider()
    cloud_p = CloudModelProvider()

    assert isinstance(ollama_p, BaseModelProvider)
    assert isinstance(cloud_p, BaseModelProvider)
    assert ollama_p.get_provider_name() == "ollama"
    assert cloud_p.get_provider_name().startswith("cloud_")
    print("  [PASS] OllamaProvider and CloudModelProvider adhere to BaseModelProvider.")

    # ---------------- 2. PROVIDER HEALTH CHECKS ----------------
    print("\n[STEP 2] Testing Provider Health Reporting...")
    ollama_health = await ollama_p.check_health()
    assert isinstance(ollama_health, ProviderHealth)
    assert ollama_health.status in ("connected", "disconnected", "error")
    print(f"  Ollama Status: {ollama_health.status} (Configured: {ollama_health.configured_model})")

    cloud_health = await cloud_p.check_health()
    assert isinstance(cloud_health, ProviderHealth)
    assert cloud_health.status in ("connected", "unconfigured", "error")
    print(f"  Cloud Status:  {cloud_health.status} (Configured: {cloud_health.configured_model})")
    print("  [PASS] Provider health reporting verified.")

    # ---------------- 3. BACKWARD COMPATIBILITY ----------------
    print("\n[STEP 3] Testing Backward Compatibility Layer...")
    assert ai_brain is orchestrator
    assert AIEngineResponse is not None
    print("  [PASS] Legacy ai_brain import delegates directly to central orchestrator.")

    # ---------------- 4. FASTAPI ENDPOINTS & STREAMING ----------------
    print("\n[STEP 4] Testing FastAPI Endpoints (/api/models, /api/chat, /api/chat/stream)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=60.0) as client:
        # A. Models endpoint
        r_models = await client.get("/api/models")
        assert r_models.status_code == 200
        models_data = r_models.json()
        assert "status" in models_data
        assert "cloud_provider" in models_data
        print(f"  [PASS] GET /api/models: Local status '{models_data['status']}', Cloud enabled: {models_data['cloud_provider']['enabled']}")

        # B. Synchronous POST /api/chat with tool execution (Anti-hallucination verification)
        r_chat = await client.post("/api/chat", json={"message": "What is 125 * 8?"})
        assert r_chat.status_code == 200
        chat_data = r_chat.json()
        assert "response" in chat_data
        assert "session_id" in chat_data
        assert len(chat_data.get("tools_executed", [])) >= 1
        assert chat_data["tools_executed"][0]["tool_name"] == "calculate"
        assert chat_data["tools_executed"][0]["is_verified"] is True
        print(f"  [PASS] POST /api/chat: Tool verified execution: {chat_data['tools_executed'][0]['tool_name']}, Intent: {chat_data['intent']}")

        # C. Server-Sent Events (SSE) Streaming POST /api/chat/stream
        print("  Testing POST /api/chat/stream SSE event protocol...")
        events_received = []
        async with client.stream("POST", "/api/chat/stream", json={"message": "What is the date today?"}) as stream_resp:
            assert stream_resp.status_code == 200
            assert "text/event-stream" in stream_resp.headers.get("content-type", "")

            async for line in stream_resp.aiter_lines():
                if line.startswith("data: "):
                    payload = line[6:].strip()
                    try:
                        ev = json.loads(payload)
                        events_received.append(ev)
                    except json.JSONDecodeError:
                        pass

        event_types = [e.get("type") for e in events_received]
        print(f"  Events received: {event_types}")
        assert "intent" in event_types, "Stream must emit 'intent' event."
        assert "done" in event_types, "Stream must emit 'done' event."
        print("  [PASS] Real-time SSE streaming protocol confirmed.")

        # D. EventSource GET /api/chat/stream endpoint
        print("  Testing GET /api/chat/stream compatibility...")
        r_stream_get = await client.get("/api/chat/stream", params={"message": "tell me a programming joke"})
        assert r_stream_get.status_code == 200
        assert "text/event-stream" in r_stream_get.headers.get("content-type", "")
        print("  [PASS] GET /api/chat/stream validated for browser EventSource.")

    # ---------------- 5. MEMORY INTEGRATION IN CONTEXT ----------------
    print("\n[STEP 5] Testing Memory Context Injection...")
    from backend.app.memory.manager import memory_manager
    test_key = "student_goal"
    memory_manager.save_memory(
        category=memory_manager.get_memory(1).category if memory_manager.get_memory(1) else "user_profile",
        key=test_key,
        content="Learning AI Operating System architecture.",
    )
    relevant = memory_manager.get_relevant_memories("learning goals", limit=3)
    assert len(relevant) >= 1
    prompt_snippet = memory_manager.format_memories_for_prompt(relevant)
    assert "Learning AI Operating System" in prompt_snippet
    print("  [PASS] Memory successfully retrieved and formatted for system context.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 1 CENTRAL AI BRAIN VERIFICATION CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase1_brain_tests())

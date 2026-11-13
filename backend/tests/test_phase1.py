"""Phase 1 Verification and Benchmark Suite for NOUS."""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.config import settings
from backend.app.core.ollama_client import ollama_client


async def run_verification():
    print("=" * 65)
    print("  NOUS PHASE 1 — VERIFICATION & LOCAL AI BENCHMARK")
    print("=" * 65)

    all_passed = True

    # 1. Test Config & Environment
    print("\n[STEP 1] Testing Configuration & Environment...")
    print(f"  App Name:     {settings.PROJECT_NAME}")
    print(f"  Ollama URL:   {settings.OLLAMA_BASE_URL}")
    print(f"  Target Model: {settings.OLLAMA_MODEL}")
    if settings.PROJECT_NAME and settings.OLLAMA_BASE_URL:
        print("  --> PASS: Configuration loaded cleanly.")
    else:
        print("  --> FAIL: Configuration missing keys.")
        all_passed = False

    # 2. Test Ollama Connection
    print("\n[STEP 2] Testing Ollama Connection & Available Models...")
    conn = await ollama_client.check_connection()
    print(f"  Status:           {conn.get('status')}")
    print(f"  Available models: {conn.get('available_models')}")
    print(f"  Configured model: {conn.get('configured_model')}")
    print(f"  Model ready:      {conn.get('configured_model_available')}")

    if conn.get("status") == "connected":
        print("  --> PASS: Ollama service is connected.")
    else:
        print(f"  --> FAIL: Ollama service unavailable: {conn.get('detail')}")
        all_passed = False
        return all_passed

    # 3. Test Health Endpoint via ASGI Client
    print("\n[STEP 3] Testing FastAPI Health Check Endpoint (/api/health)...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        health_res = await ac.get("/api/health")
        print(f"  HTTP Status: {health_res.status_code}")
        health_json = health_res.json()
        print(f"  CPU Model:   {health_json.get('system', {}).get('cpu_model')}")
        print(f"  Python:      {health_json.get('system', {}).get('python_version')}")
        print(f"  AI Status:   {health_json.get('ai_engine', {}).get('connection_status')}")

        if health_res.status_code == 200 and health_json.get("status") == "healthy":
            print("  --> PASS: Health endpoint is operational.")
        else:
            print("  --> FAIL: Health endpoint returned unexpected response.")
            all_passed = False

    # 4. Test Models Endpoint (/api/models)
    print("\n[STEP 4] Testing Models Endpoint (/api/models)...")
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        models_res = await ac.get("/api/models")
        print(f"  HTTP Status:      {models_res.status_code}")
        models_json = models_res.json()
        available = models_json.get("available_models", [])
        print(f"  Available Models: {available}")
        if models_res.status_code == 200:
            print("  --> PASS: Models endpoint operational.")
        else:
            print("  --> FAIL: Models endpoint failed.")
            all_passed = False

    # 5. Determine which model to test
    target_model = settings.OLLAMA_MODEL
    if target_model not in available:
        if available:
            target_model = available[0]
            print(f"  [NOTE] {settings.OLLAMA_MODEL} not found in available list; testing with {target_model}")
        else:
            print("  [ERROR] No models available to test chat!")
            return False

    # 6. Benchmark Real AI Chat Inference
    print(f"\n[STEP 5] Testing Real Local AI Inference with '{target_model}'...")
    test_prompt = "Hello! State your name, role, and one key capability in two sentences."
    print(f"  Prompt: '{test_prompt}'")

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        start_time = time.perf_counter()
        chat_res = await ac.post(
            "/api/chat",
            json={"message": test_prompt, "model": target_model},
            timeout=120.0,
        )
        total_wall_time = time.perf_counter() - start_time

        print(f"  HTTP Status: {chat_res.status_code}")
        if chat_res.status_code == 200:
            data = chat_res.json()
            if data.get("success") or data.get("response"):
                print("\n  --- MODEL RESPONSE ---")
                print(f"  {data.get('response')}")
                print("  ----------------------")
                print(f"  Elapsed Time:      {data.get('elapsed_seconds')}s (total wall: {round(total_wall_time, 2)}s)")
                print(f"  Tokens Per Second: {data.get('tokens_per_second')} t/s")
                print("  --> PASS: Local model produced real valid response!")
            else:
                print(f"  --> FAIL: Model inference returned failure: {data.get('error')}")
                all_passed = False
        else:
            print(f"  --> FAIL: Chat endpoint returned HTTP {chat_res.status_code}: {chat_res.text}")
            all_passed = False

    # 7. Summary
    print("\n" + "=" * 65)
    if all_passed:
        print("  [SUCCESS] PHASE 1 VERIFICATION COMPLETED SUCCESSFULLY!")
    else:
        print("  [FAILURE] SOME PHASE 1 CHECKS FAILED. See details above.")
    print("=" * 65)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_verification())
    sys.exit(0 if success else 1)

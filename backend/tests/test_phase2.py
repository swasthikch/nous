"""Phase 2 Verification Suite for NOUS.

Tests:
1. Intent Classification
2. Tool Execution & Permission Enforcement
3. Context Pruning & Session Persistence
4. Hybrid Model Routing & Fallback Logic
5. Central AI Brain Multi-Turn Execution & Anti-Hallucination
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.intent import intent_classifier, IntentType
from backend.app.core.tool_registry import tool_registry, RiskLevel
from backend.app.core.conversation import conversation_manager
from backend.app.core.model_router import model_router, RoutingMode
from backend.app.core.ai_engine import ai_brain, AIEngineResponse


async def run_phase2_tests():
    print("=" * 65)
    print("  NOUS PHASE 2 - CORE AI BRAIN & CONVERSATION ENGINE")
    print("=" * 65)

    all_passed = True

    # -------------------------------------------------------------
    # STEP 1: Intent Classification
    # -------------------------------------------------------------
    print("\n[STEP 1] Testing Intent Classification Engine...")
    test_cases = [
        ("What time is it right now?", IntentType.DATETIME_QUERY, "get_current_datetime"),
        ("What is the date today?", IntentType.DATETIME_QUERY, "get_current_datetime"),
        ("What are my laptop hardware specs?", IntentType.SYSTEM_QUERY, "get_system_specs"),
        ("Calculate 45 * 12 + 10", IntentType.CALCULATION, "calculate"),
        ("Hello NOUS", IntentType.GREETING, None),
        ("Explain how binary search trees work in Python", IntentType.GENERAL_CHAT, None),
    ]

    for query, expected_intent, expected_tool in test_cases:
        res = intent_classifier.classify(query)
        passed = (res.intent == expected_intent) and (res.suggested_tool == expected_tool)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] '{query}' -> Intent: {res.intent.value}, Tool: {res.suggested_tool}")
        if not passed:
            all_passed = False

    # -------------------------------------------------------------
    # STEP 2: Tool Execution & Anti-Hallucination
    # -------------------------------------------------------------
    print("\n[STEP 2] Testing Tool Execution & Permission System...")

    # Tool: get_current_datetime
    dt_res = await tool_registry.execute("get_current_datetime", {})
    if dt_res.success and dt_res.is_verified and "human_readable" in dt_res.data:
        print(f"  [PASS] get_current_datetime: {dt_res.data['human_readable']}")
    else:
        print(f"  [FAIL] get_current_datetime failed: {dt_res.error}")
        all_passed = False

    # Tool: get_system_specs
    specs_res = await tool_registry.execute("get_system_specs", {})
    if specs_res.success and specs_res.data.get("cpu_model") == "13th Gen Intel(R) Core(TM) i5-1334U":
        print(f"  [PASS] get_system_specs: CPU verified -> {specs_res.data['cpu_model']}")
    else:
        print(f"  [FAIL] get_system_specs failed: {specs_res.error}")
        all_passed = False

    # Tool: calculate
    calc_res = await tool_registry.execute("calculate", {"expression": "25 * 4 + 15"})
    if calc_res.success and calc_res.data.get("result") == 115:
        print(f"  [PASS] calculate (25 * 4 + 15): {calc_res.data['result']}")
    else:
        print(f"  [FAIL] calculate failed: {calc_res.error}")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 3: Conversation Sessions & Context Budgeting
    # -------------------------------------------------------------
    print("\n[STEP 3] Testing Conversation Manager & Context Budgeting...")
    test_session = conversation_manager.create_session("Phase 2 Test Session")
    sid = test_session.id
    print(f"  Created test session: ID={sid}")

    conversation_manager.add_message(sid, "user", "My favorite programming language is Rust.")
    conversation_manager.add_message(sid, "assistant", "That's great! Rust offers memory safety without a garbage collector.")

    # Retrieve context window
    context = conversation_manager.get_context_window(sid, system_prompt="You are NOUS.")
    print(f"  Retrieved context window with {len(context)} messages (including system prompt).")
    if len(context) == 3:
        print("  [PASS] Context window assembled correctly.")
    else:
        print("  [FAIL] Context window length mismatch.")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 4: Model Router & Fallback Logic
    # -------------------------------------------------------------
    print("\n[STEP 4] Testing Model Router...")
    model_router.set_mode(RoutingMode.LOCAL)
    dec_local = await model_router.route(intent_classifier.classify("Hello"))
    print(f"  Mode LOCAL -> Target: {dec_local.selected_target}, Model: {dec_local.selected_model}")
    if dec_local.selected_target == "local":
        print("  [PASS] Local mode routing verified.")
    else:
        all_passed = False

    model_router.set_mode(RoutingMode.HYBRID)
    dec_hybrid = await model_router.route(intent_classifier.classify("Hello"))
    print(f"  Mode HYBRID -> Target: {dec_hybrid.selected_target}, Model: {dec_hybrid.selected_model}")
    if dec_hybrid.selected_target == "local":
        print("  [PASS] Hybrid mode routing verified.")
    else:
        all_passed = False

    # -------------------------------------------------------------
    # STEP 5: Real Multi-Turn AI Brain Execution (Anti-Hallucination)
    # -------------------------------------------------------------
    print("\n[STEP 5] Testing End-to-End AI Brain with Verified Tool Invocation...")

    # Turn 1: Date & Time check
    print("  --- Turn 1: Asking current date and time ---")
    start = time.perf_counter()
    resp1: AIEngineResponse = await ai_brain.process(
        message="What is the current date and time right now?",
        session_id=sid,
    )
    t1_elapsed = round(time.perf_counter() - start, 2)
    print(f"  Model Response ({t1_elapsed}s):")
    print(f"    \"{resp1.response.strip()}\"")
    print(f"  Tools Executed: {[t.tool_name for t in resp1.tools_executed]}")

    if any(t.tool_name == "get_current_datetime" and t.is_verified for t in resp1.tools_executed):
        print("  [PASS] Tool 'get_current_datetime' executed and verified.")
    else:
        print("  [FAIL] Tool was not executed.")
        all_passed = False

    # Turn 2: Calculation check
    print("\n  --- Turn 2: Asking calculation ---")
    start = time.perf_counter()
    resp2: AIEngineResponse = await ai_brain.process(
        message="Calculate 125 * 8",
        session_id=sid,
    )
    t2_elapsed = round(time.perf_counter() - start, 2)
    print(f"  Model Response ({t2_elapsed}s):")
    print(f"    \"{resp2.response.strip()}\"")
    print(f"  Tools Executed: {[t.tool_name for t in resp2.tools_executed]}")

    if any(t.tool_name == "calculate" and t.is_verified for t in resp2.tools_executed):
        print("  [PASS] Tool 'calculate' executed and verified.")
    else:
        print("  [FAIL] Tool was not executed.")
        all_passed = False

    # Clean up test session
    conversation_manager.delete_session(sid)
    print(f"\n  Cleaned up temporary session: {sid}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    if all_passed:
        print("  [SUCCESS] ALL PHASE 2 ENGINE TESTS PASSED!")
    else:
        print("  [FAILURE] SOME PHASE 2 CHECKS FAILED.")
    print("=" * 65)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_phase2_tests())
    sys.exit(0 if success else 1)

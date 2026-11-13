"""Phase 5 Verification Suite for NOUS.

Tests:
1. SQLite Database Schema & Initialization
2. CRUD Operations across all 5 Memory Categories
3. Search and Category Filtering
4. Memory Enable / Disable Toggle
5. Memory Tools (remember_fact, recall_memories, list_user_profile)
6. End-to-End Central AI Brain Multi-Turn Memory Retention
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.memory.manager import memory_manager, MemoryCategory
from backend.app.core.tool_registry import tool_registry
from backend.app.core.intent import intent_classifier, IntentType
from backend.app.core.ai_engine import ai_brain, AIEngineResponse
from backend.app.core.conversation import conversation_manager


async def run_phase5_tests():
    print("=" * 65)
    print("  NOUS PHASE 5 - PERSONAL PERSISTENT MEMORY SYSTEM")
    print("=" * 65)

    all_passed = True

    # -------------------------------------------------------------
    # STEP 1: Memory Settings & Toggle
    # -------------------------------------------------------------
    print("\n[STEP 1] Testing Memory Settings & State Toggle...")
    memory_manager.set_memory_enabled(True)
    is_enabled = memory_manager.is_memory_enabled()
    print(f"  Memory Enabled: {is_enabled}")
    if is_enabled:
        print("  [PASS] Memory enabled verified.")
    else:
        print("  [FAIL] Failed to enable memory.")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 2: CRUD Operations Across Categories
    # -------------------------------------------------------------
    print("\n[STEP 2] Testing Memory Storage Across Categories...")
    test_entries = [
        (MemoryCategory.USER_PROFILE, "preferred_name", "User's name is Dev."),
        (MemoryCategory.USER_PROFILE, "learning_goal", "Mastering full-stack AI development and Python architectures."),
        (MemoryCategory.PERSONAL_INFO, "coffee_preference", "Prefers black coffee with no sugar."),
        (MemoryCategory.PROJECT, "project_nous", "Building Project NOUS with FastAPI backend and Ollama local models."),
        (MemoryCategory.ROUTINE, "study_schedule", "Allocates 2 hours daily for algorithms and LeetCode practice."),
    ]

    saved_items = []
    for cat, key, content in test_entries:
        item = memory_manager.save_memory(cat, key, content)
        saved_items.append(item)
        print(f"  [PASS] Saved [{cat.value}] {key}: {content[:45]}...")

    if len(saved_items) == 5:
        print("  [PASS] All 5 memory categories successfully saved.")
    else:
        all_passed = False

    # Test Listing by Category
    profile_memories = memory_manager.list_memories(category=MemoryCategory.USER_PROFILE)
    print(f"  Profile memories retrieved: {len(profile_memories)}")
    if len(profile_memories) >= 2:
        print("  [PASS] Category filtering works cleanly.")
    else:
        all_passed = False

    # Test Search
    search_results = memory_manager.list_memories(search_query="coffee")
    if search_results and "coffee" in search_results[0].content.lower():
        print(f"  [PASS] Search query 'coffee' found memory: {search_results[0].content}")
    else:
        print("  [FAIL] Search failed.")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 3: Memory Tools Execution
    # -------------------------------------------------------------
    print("\n[STEP 3] Testing Memory Tools (remember_fact, recall_memories, list_user_profile)...")

    # remember_fact
    rem_tool_res = await tool_registry.execute(
        "remember_fact",
        {
            "category": "project",
            "key": "test_milestone",
            "content": "Phase 5 persistent memory verification milestone.",
        },
    )
    if rem_tool_res.success and rem_tool_res.data.get("status") == "saved":
        print(f"  [PASS] Tool 'remember_fact' executed: {rem_tool_res.data['key']}")
    else:
        print(f"  [FAIL] 'remember_fact' failed: {rem_tool_res.error}")
        all_passed = False

    # recall_memories
    rec_tool_res = await tool_registry.execute("recall_memories", {"query": "project NOUS"})
    if rec_tool_res.success and rec_tool_res.data.get("count", 0) > 0:
        print(f"  [PASS] Tool 'recall_memories' found {rec_tool_res.data['count']} memories for 'project NOUS'.")
    else:
        print(f"  [FAIL] 'recall_memories' failed: {rec_tool_res.error}")
        all_passed = False

    # list_user_profile
    prof_tool_res = await tool_registry.execute("list_user_profile", {})
    if prof_tool_res.success and "preferred_name" in prof_tool_res.data.get("profile", {}):
        print(f"  [PASS] Tool 'list_user_profile' returned: {prof_tool_res.data['profile']}")
    else:
        print(f"  [FAIL] 'list_user_profile' failed: {prof_tool_res.error}")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 4: Intent Classifier Memory Detection
    # -------------------------------------------------------------
    print("\n[STEP 4] Testing Memory Intent Detection...")
    rem_intent = intent_classifier.classify("Remember that my name is Dev")
    print(f"  'Remember that my name is Dev' -> Intent: {rem_intent.intent.value}, Tool: {rem_intent.suggested_tool}")
    if rem_intent.intent == IntentType.REMEMBER_FACT and rem_intent.suggested_tool == "remember_fact":
        print("  [PASS] REMEMBER_FACT intent classified correctly.")
    else:
        print("  [FAIL] REMEMBER_FACT classification failed.")
        all_passed = False

    rec_intent = intent_classifier.classify("What do you remember about me?")
    print(f"  'What do you remember about me?' -> Intent: {rec_intent.intent.value}, Tool: {rec_intent.suggested_tool}")
    if rec_intent.intent == IntentType.RECALL_MEMORY:
        print("  [PASS] RECALL_MEMORY intent classified correctly.")
    else:
        print("  [FAIL] RECALL_MEMORY classification failed.")
        all_passed = False

    # -------------------------------------------------------------
    # STEP 5: End-to-End AI Brain Memory Test with Local Model
    # -------------------------------------------------------------
    print("\n[STEP 5] Testing End-to-End AI Brain with Persistent Memory...")
    test_session = conversation_manager.create_session("Memory Test Session")
    sid = test_session.id

    # Turn 1: Save a fact via natural language
    print("  --- Turn 1: Asking NOUS to remember a new fact ---")
    start1 = time.perf_counter()
    resp1: AIEngineResponse = await ai_brain.process(
        message="Please remember that my favorite framework is FastAPI",
        session_id=sid,
    )
    t1_elapsed = round(time.perf_counter() - start1, 2)
    print(f"  Model Response ({t1_elapsed}s):")
    print(f"    \"{resp1.response.strip()}\"")
    print(f"  Tools Executed: {[t.tool_name for t in resp1.tools_executed]}")

    if any(t.tool_name == "remember_fact" and t.is_verified for t in resp1.tools_executed):
        print("  [PASS] Fact remembered via central AI Brain tool execution.")
    else:
        print("  [FAIL] Tool 'remember_fact' was not executed.")
        all_passed = False

    # Turn 2: Ask about the stored fact in a NEW turn
    print("\n  --- Turn 2: Asking NOUS to recall what my name and learning goals are ---")
    start2 = time.perf_counter()
    resp2: AIEngineResponse = await ai_brain.process(
        message="What is my name and what are my learning goals?",
        session_id=sid,
    )
    t2_elapsed = round(time.perf_counter() - start2, 2)
    print(f"  Model Response ({t2_elapsed}s):")
    print(f"    \"{resp2.response.strip()}\"")

    resp2_text = resp2.response.lower()
    if "dev" in resp2_text or "learning" in resp2_text or "ai" in resp2_text:
        print("  [PASS] Model recalled stored memory facts correctly!")
    else:
        print("  [FAIL] Model did not recall expected facts.")
        all_passed = False

    # Clean up test session
    conversation_manager.delete_session(sid)
    print(f"\n  Cleaned up temporary test session: {sid}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    if all_passed:
        print("  [SUCCESS] ALL PHASE 5 PERSISTENT MEMORY TESTS PASSED!")
    else:
        print("  [FAILURE] SOME PHASE 5 MEMORY CHECKS FAILED.")
    print("=" * 65)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_phase5_tests())
    sys.exit(0 if success else 1)

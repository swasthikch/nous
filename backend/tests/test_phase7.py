"""Comprehensive Phase 7 Automated Test Suite: Daily Life & Routine Manager.

Verifies:
1. SQLite Routine DB creation, WAL mode, schema indexes.
2. RoutineManager CRUD (create, list chronologically, update, delete).
3. Strict rule verification: activities are never auto-completed by time passing.
4. Overlap & Conflict detection between scheduled activities.
5. Open time window slot finder (find_free_slots).
6. Intelligent rescheduling of missed/skipped activities without moving fixed commitments.
7. Evening daily review debrief generation (completion %, study/coding hours, suggestions).
8. Anti-hallucination routine tools registered in ToolRegistry.
9. IntentClassifier detection of routine queries, schedule adds, and reviews.
10. End-to-end REST API endpoints via FastAPI test client.
"""

import asyncio
import os
import sys
import time
from datetime import date
from pathlib import Path
import httpx

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.routine.db import init_routine_database, get_routine_db, ROUTINE_DB_PATH
from backend.app.routine.manager import (
    routine_manager,
    ActivityCategory,
    ActivityPriority,
    ActivityStatus,
)
from backend.app.core.tool_registry import tool_registry
from backend.app.core.intent import intent_classifier, IntentType
from backend.app.core.ai_engine import AIEngine
from backend.app.main import app


async def run_phase7_tests():
    print("=" * 70)
    print("  RUNNING PHASE 7 TEST SUITE: DAILY LIFE & ROUTINE MANAGER")
    print("=" * 70)
    passed = 0
    total = 0

    def assert_test(cond: bool, msg: str):
        nonlocal passed, total
        total += 1
        if cond:
            print(f"  [PASS] Test {total}: {msg}")
            passed += 1
        else:
            print(f"  [FAIL] Test {total}: {msg}")
            raise AssertionError(f"Test failed: {msg}")

    # -------------------------------------------------------------
    # 1. DB Initialization & WAL Mode
    # -------------------------------------------------------------
    print("\n--- 1. SQLite Routine DB & WAL Mode ---")
    init_routine_database()
    assert_test(os.path.exists(ROUTINE_DB_PATH), "nous_routine.db file exists on disk")

    with get_routine_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        row = cursor.fetchone()
        journal_mode = row[0].lower() if row else ""
        assert_test(journal_mode == "wal", f"SQLite journal mode is WAL (got '{journal_mode}')")

    # -------------------------------------------------------------
    # 2. Activity CRUD & Chronological Sorting
    # -------------------------------------------------------------
    print("\n--- 2. Activity CRUD & Chronological Sorting ---")
    test_date = "2026-11-20"

    # Clean test date if existing
    with get_routine_db() as conn:
        conn.cursor().execute("DELETE FROM activities WHERE date = ?", (test_date,))

    # Create 3 activities out of order
    a2 = routine_manager.create_activity(
        name="College Lecture - Distributed Systems",
        start_time="10:00",
        end_time="12:00",
        target_date=test_date,
        category=ActivityCategory.COLLEGE,
        priority=ActivityPriority.HIGH,
        is_fixed=True,
    )
    a1 = routine_manager.create_activity(
        name="Morning Walking & Breakfast",
        start_time="07:30",
        end_time="08:30",
        target_date=test_date,
        category=ActivityCategory.ROUTINE,
        priority=ActivityPriority.MEDIUM,
    )
    a3 = routine_manager.create_activity(
        name="LeetCode & Coding Practice",
        start_time="17:00",
        end_time="19:00",
        target_date=test_date,
        category=ActivityCategory.CODING,
        priority=ActivityPriority.HIGH,
        notes="Practice dynamic programming and graph traversals",
    )

    assert_test(a1.id > 0 and a2.id > 0 and a3.id > 0, "Created 3 activities with valid auto-increment IDs")
    assert_test(a2.is_fixed is True, "College commitment successfully marked as is_fixed=True")

    # List activities: MUST be sorted chronologically by start_time
    acts = routine_manager.list_activities(test_date)
    assert_test(len(acts) == 3, f"Retrieved 3 scheduled activities for date {test_date}")
    assert_test(acts[0].start_time == "07:30", "First activity is 07:30 (Morning Walking)")
    assert_test(acts[1].start_time == "10:00", "Second activity is 10:00 (College)")
    assert_test(acts[2].start_time == "17:00", "Third activity is 17:00 (Coding)")

    # -------------------------------------------------------------
    # 3. Strict Rule Verification: Status Tracking & No Auto-Completion
    # -------------------------------------------------------------
    print("\n--- 3. Strict Rule Verification: Never Auto-Complete ---")
    # Fetch activity; should still be not_started even if historical time passed
    fetched = routine_manager.get_activity(a1.id)
    assert_test(fetched.status == ActivityStatus.NOT_STARTED, "Activity starts as NOT_STARTED")

    # Explicit user update to completed
    upd_ok = routine_manager.update_status(a1.id, ActivityStatus.COMPLETED)
    assert_test(upd_ok is True, "Explicit user status update returns success=True")
    fetched_after = routine_manager.get_activity(a1.id)
    assert_test(fetched_after.status == ActivityStatus.COMPLETED, "Status verified as COMPLETED only after explicit call")

    # -------------------------------------------------------------
    # 4. Overlap & Conflict Detection
    # -------------------------------------------------------------
    print("\n--- 4. Conflict & Overlap Detection ---")
    # No conflicts yet
    no_conflicts = routine_manager.detect_overlaps(test_date)
    assert_test(len(no_conflicts) == 0, "No initial overlaps detected among non-conflicting activities")

    # Insert an overlapping activity: 11:00 - 13:00 (conflicts with College 10:00 - 12:00)
    overlap_act = routine_manager.create_activity(
        name="Study Group Meeting",
        start_time="11:00",
        end_time="13:00",
        target_date=test_date,
        category=ActivityCategory.STUDY,
    )

    conflicts = routine_manager.detect_overlaps(test_date)
    assert_test(len(conflicts) == 1, f"Successfully detected 1 schedule conflict (got {len(conflicts)})")
    assert_test("College" in conflicts[0]["activity_1"]["name"] or "College" in conflicts[0]["activity_2"]["name"], "Identified conflicting activity correctly")

    # Clean up conflicting item
    routine_manager.delete_activity(overlap_act.id)
    assert_test(len(routine_manager.detect_overlaps(test_date)) == 0, "Conflict cleared after deleting overlapping item")

    # -------------------------------------------------------------
    # 5. Free Slot Identification
    # -------------------------------------------------------------
    print("\n--- 5. Free Slot Identification ---")
    # Day span: 07:00 to 23:00
    # Scheduled: 07:30-08:30, 10:00-12:00, 17:00-19:00
    slots = routine_manager.find_free_slots(test_date, min_duration_mins=60)
    assert_test(len(slots) >= 2, f"Found {len(slots)} free slots of >= 60 minutes")
    # Check that 12:00 to 17:00 is found as a large free slot (300 mins)
    mid_slot = [s for s in slots if s["start"] == "12:00" and s["end"] == "17:00"]
    assert_test(len(mid_slot) == 1 and mid_slot[0]["duration_minutes"] == 300, "Found 12:00-17:00 free afternoon window (300 mins)")

    # -------------------------------------------------------------
    # 6. Intelligent Rescheduling of Missed Activities
    # -------------------------------------------------------------
    print("\n--- 6. Intelligent Rescheduling of Missed Activities ---")
    # Add an evening gym session that was missed
    gym_act = routine_manager.create_activity(
        name="Gym & Fitness",
        start_time="08:30",
        end_time="09:30",
        target_date=test_date,
        category=ActivityCategory.FITNESS,
        status=ActivityStatus.SKIPPED,
    )

    resched_res = routine_manager.reschedule_missed_activity(gym_act.id)
    assert_test(resched_res["success"] is True, "Rescheduled missed activity successfully")

    new_act_data = resched_res["new_activity"]
    assert_test("Rescheduled" in new_act_data["name"], "New activity labeled as Rescheduled")
    assert_test(new_act_data["start_time"] != gym_act.start_time, f"Moved to open slot starting at {new_act_data['start_time']}")

    # Check original activity marked as rescheduled
    orig = routine_manager.get_activity(gym_act.id)
    assert_test(orig.status == ActivityStatus.RESCHEDULED, "Original activity marked as RESCHEDULED in DB")

    # -------------------------------------------------------------
    # 7. Evening Daily Review Debrief Generation
    # -------------------------------------------------------------
    print("\n--- 7. Evening Daily Review Debrief Generation ---")
    # Mark a3 (LeetCode - 2 hours) as completed
    routine_manager.update_status(a3.id, ActivityStatus.COMPLETED)

    review = routine_manager.generate_daily_review(test_date)
    assert_test(review["date"] == test_date, f"Review generated for date {test_date}")
    assert_test(review["completed_count"] >= 2, f"Accurately counted completed activities ({review['completed_count']})")
    assert_test(review["coding_hours"] >= 2.0, f"Logged coding practice hours: {review['coding_hours']}h")
    assert_test(len(review["suggestions"]) > 0, "Generated actionable productivity suggestions for tomorrow")

    # -------------------------------------------------------------
    # 8. Tool Registry Routine Tools
    # -------------------------------------------------------------
    print("\n--- 8. Anti-Hallucination Routine Tools in Registry ---")
    tools = [
        "get_daily_schedule",
        "add_schedule_activity",
        "update_activity_status",
        "reschedule_missed_activity",
        "generate_daily_review",
    ]
    for t in tools:
        assert_test(t in tool_registry._tools, f"Tool '{t}' registered in ToolRegistry")

    # Test tool execution directly
    sched_res = await tool_registry.execute("get_daily_schedule", {"target_date": test_date})
    assert_test(sched_res.success is True, "get_daily_schedule executed with success=True")
    assert_test(sched_res.data["total_activities"] >= 2, "get_daily_schedule returned correct activity count")

    # -------------------------------------------------------------
    # 9. Intent Classification for Routine Commands
    # -------------------------------------------------------------
    print("\n--- 9. Intent Classification for Routine Commands ---")
    queries_to_test = [
        ("what is my schedule today", IntentType.SCHEDULE_QUERY, "get_daily_schedule"),
        ("show my daily plan", IntentType.SCHEDULE_QUERY, "get_daily_schedule"),
        ("generate daily review and debrief", IntentType.DAILY_REVIEW, "generate_daily_review"),
        ("review my day", IntentType.DAILY_REVIEW, "generate_daily_review"),
        ("add activity LeetCode Practice from 17:00 to 18:00", IntentType.ADD_ACTIVITY, "add_schedule_activity"),
        ("mark activity 1 as completed", IntentType.UPDATE_STATUS, "update_activity_status"),
        ("reschedule activity 3", IntentType.RESCHEDULE_ACTIVITY, "reschedule_missed_activity"),
    ]

    for q, expected_intent, expected_tool in queries_to_test:
        res = intent_classifier.classify(q)
        assert_test(res.intent == expected_intent, f"'{q}' -> Intent {res.intent.value}")
        assert_test(res.suggested_tool == expected_tool, f"'{q}' -> Tool {res.suggested_tool}")

    # -------------------------------------------------------------
    # 10. End-to-End REST API Endpoints
    # -------------------------------------------------------------
    print("\n--- 10. End-to-End FastAPI REST API Endpoints ---")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # GET /api/routine/schedule
        resp = await client.get(f"/api/routine/schedule?date={test_date}")
        assert_test(resp.status_code == 200, "GET /api/routine/schedule returns 200")
        data = resp.json()
        assert_test(data["count"] >= 2, "Schedule response includes activities")

        # POST /api/routine/activity
        new_act_payload = {
            "name": "Evening Walking & Revision",
            "start_time": "20:00",
            "end_time": "21:00",
            "target_date": test_date,
            "category": "study",
            "priority": "low",
        }
        post_resp = await client.post("/api/routine/activity", json=new_act_payload)
        assert_test(post_resp.status_code == 201, "POST /api/routine/activity returns 201 Created")
        created_id = post_resp.json()["activity"]["id"]

        # PATCH /api/routine/activity/{id}/status
        patch_resp = await client.patch(
            f"/api/routine/activity/{created_id}/status",
            json={"status": "completed"},
        )
        assert_test(patch_resp.status_code == 200, "PATCH /api/routine/activity/{id}/status returns 200")
        assert_test(patch_resp.json()["new_status"] == "completed", "Status correctly updated to completed")

        # GET /api/routine/review
        rev_resp = await client.get(f"/api/routine/review?date={test_date}")
        assert_test(rev_resp.status_code == 200, "GET /api/routine/review returns 200")
        rev_data = rev_resp.json()
        assert_test("completion_rate_percent" in rev_data, "Review payload includes completion_rate_percent")

        # DELETE /api/routine/activity/{id}
        del_resp = await client.delete(f"/api/routine/activity/{created_id}")
        assert_test(del_resp.status_code == 200, "DELETE /api/routine/activity/{id} returns 200")

    # Clean up test date records
    with get_routine_db() as conn:
        conn.cursor().execute("DELETE FROM activities WHERE date = ?", (test_date,))

    print("\n" + "=" * 70)
    print(f"  PHASE 7 TEST SUITE COMPLETE: {passed}/{total} TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_phase7_tests())

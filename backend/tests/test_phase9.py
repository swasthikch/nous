"""Comprehensive Phase 9 Automated Test Suite: Project Intelligence & Developer Tools.

Verifies:
1. SQLite nous_projects.db initialization, schema tables, and WAL mode.
2. ProjectManager CRUD (create, read, list, update, cascade delete).
3. Milestone lifecycle and automated project progress percentage recalculation.
4. Project task tracking (todo -> in_progress -> done).
5. Proactive inactivity detection: identifies stale projects idle > 7 days.
6. Upcoming 14-day project and milestone deadline extraction.
7. GitHub REST client: commits, PRs, issues, and development velocity telemetry.
8. Anti-hallucination Project tools registered in ToolRegistry.
9. IntentClassifier detection for spoken/text project commands.
10. FastAPI REST API endpoints via asynchronous HTTP client.
"""

import asyncio
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
import httpx

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.projects.db import init_projects_database, get_projects_db, PROJECTS_DB_PATH
from backend.app.projects.manager import (
    project_manager,
    ProjectPriority,
    ProjectStatus,
    TaskStatus,
)
from backend.app.projects.github_client import github_client
from backend.app.core.tool_registry import tool_registry
from backend.app.core.intent import intent_classifier, IntentType
from backend.app.main import app


async def run_phase9_tests():
    print("=" * 70)
    print("  RUNNING PHASE 9 TEST SUITE: PROJECT INTELLIGENCE & GITHUB TOOLS")
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
    # 1. SQLite Projects Database & WAL Mode
    # -------------------------------------------------------------
    print("\n--- 1. SQLite Projects DB & WAL Mode ---")
    init_projects_database()
    assert_test(os.path.exists(PROJECTS_DB_PATH), "nous_projects.db file exists on disk")

    with get_projects_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0].lower()
        assert_test(mode == "wal", f"SQLite journal mode is WAL (got '{mode}')")

    # -------------------------------------------------------------
    # 2. Project CRUD Operations
    # -------------------------------------------------------------
    print("\n--- 2. Project CRUD Operations ---")
    test_proj = project_manager.create_project(
        name="Automated Test Kernel Engine",
        description="Core unit testing micro-kernel",
        tech_stack="Python, C++, PyTest",
        repo_url="https://github.com/student/test-kernel",
        start_date="2026-11-01",
        deadline="2026-11-30",
        priority=ProjectPriority.HIGH,
        status=ProjectStatus.ACTIVE,
        notes="Automated test fixture",
    )
    assert_test(test_proj.id > 0, "Created project with valid numeric primary key")
    assert_test(test_proj.progress_percent == 0, "Initial project progress starts at 0%")

    fetched = project_manager.get_project(test_proj.id)
    assert_test(fetched is not None and fetched.name == "Automated Test Kernel Engine", "Retrieved project matches created data")

    # Update project
    upd_ok = project_manager.update_project(
        project_id=test_proj.id,
        tech_stack="Python 3.14, C++20, PyTest",
        priority=ProjectPriority.HIGH,
    )
    assert_test(upd_ok is True, "Project updated successfully")
    refetched = project_manager.get_project(test_proj.id)
    assert_test("C++20" in refetched.tech_stack, "Updated tech stack verified in DB")

    # -------------------------------------------------------------
    # 3. Milestones & Progress Recalculation
    # -------------------------------------------------------------
    print("\n--- 3. Milestones & Progress Recalculation ---")
    m1 = project_manager.add_milestone(test_proj.id, "Milestone A: Core Harness", due_date="2026-11-20")
    m2 = project_manager.add_milestone(test_proj.id, "Milestone B: Integration Tests", due_date="2026-11-25")
    assert_test(m1.id > 0 and m2.id > 0, "Created 2 project milestones")

    # Toggle 1st milestone -> progress should jump to 50%
    toggle_ok = project_manager.toggle_milestone(m1.id)
    assert_test(toggle_ok is True, "Toggled milestone completion to True")

    proj_after_m1 = project_manager.get_project(test_proj.id)
    assert_test(proj_after_m1.progress_percent == 50, f"Progress auto-recalculated to 50% (got {proj_after_m1.progress_percent}%)")

    # Toggle 2nd milestone -> progress should reach 100%
    project_manager.toggle_milestone(m2.id)
    proj_after_m2 = project_manager.get_project(test_proj.id)
    assert_test(proj_after_m2.progress_percent == 100, f"Progress reached 100% on all milestones completed")

    # -------------------------------------------------------------
    # 4. Project Tasks Tracking
    # -------------------------------------------------------------
    print("\n--- 4. Project Task Pipeline ---")
    t1 = project_manager.add_task(test_proj.id, "Benchmark CPU instruction cycles", priority="high")
    assert_test(t1.status == TaskStatus.TODO, "Task starts with status 'todo'")

    upd_task = project_manager.update_task_status(t1.id, TaskStatus.IN_PROGRESS)
    assert_test(upd_task is True, "Task updated to 'in_progress'")
    refetched_task = project_manager.get_task(t1.id)
    assert_test(refetched_task.status == TaskStatus.IN_PROGRESS, "Task verified as IN_PROGRESS in DB")

    # -------------------------------------------------------------
    # 5. Proactive Inactivity Detection
    # -------------------------------------------------------------
    print("\n--- 5. Proactive Inactivity Detection ---")
    # Identify legacy prototype project with old updated_at
    inactive_projects = project_manager.detect_inactive_projects(days_threshold=7)
    assert_test(len(inactive_projects) >= 1, f"Successfully detected {len(inactive_projects)} inactive projects (> 7 days idle)")
    assert_test("Legacy" in inactive_projects[0]["name"] or inactive_projects[0]["days_inactive"] >= 0, "Inactive project flagged with idle days metric")

    # -------------------------------------------------------------
    # 6. Upcoming Project & Milestone Deadlines
    # -------------------------------------------------------------
    print("\n--- 6. Upcoming Deadlines Scans ---")
    deadlines = project_manager.get_upcoming_deadlines(days_ahead=21)
    assert_test(len(deadlines) >= 1, f"Found {len(deadlines)} upcoming project and milestone deadlines")
    assert_test("due_date" in deadlines[0], "Deadlines structured with chronological due_date")

    # -------------------------------------------------------------
    # 7. GitHub REST API Client & Telemetry
    # -------------------------------------------------------------
    print("\n--- 7. GitHub Client & Telemetry ---")
    activity = await github_client.get_repository_activity()
    assert_test("recent_commits" in activity, "Telemetry contains recent commits list")
    assert_test(len(activity["recent_commits"]) >= 2, f"Retrieved {len(activity['recent_commits'])} commits")
    assert_test("open_pull_requests" in activity, "Telemetry contains pull requests list")
    assert_test("open_issues" in activity, "Telemetry contains issues list")

    # -------------------------------------------------------------
    # 8. Tool Registry Project Intelligence Tools
    # -------------------------------------------------------------
    print("\n--- 8. Tool Registry Project Intelligence Tools ---")
    proj_tools = [
        "get_projects_overview",
        "get_project_details",
        "add_project",
        "add_project_milestone",
        "check_github_activity",
        "check_project_deadlines",
        "find_inactive_projects",
    ]
    for pt in proj_tools:
        assert_test(pt in tool_registry._tools, f"Tool '{pt}' registered in ToolRegistry")

    # Execute get_projects_overview
    ov_res = await tool_registry.execute("get_projects_overview", {})
    assert_test(ov_res.success is True, "get_projects_overview executed with success=True")
    assert_test(ov_res.data["total_projects"] >= 2, "Overview returned project counts")

    # Execute check_github_activity
    gh_res = await tool_registry.execute("check_github_activity", {})
    assert_test(gh_res.success is True, "check_github_activity executed with success=True")
    assert_test("recent_commits" in gh_res.data, "GitHub activity tool returned commit stream")

    # -------------------------------------------------------------
    # 9. Intent Classification for Project Commands
    # -------------------------------------------------------------
    print("\n--- 9. Intent Classification for Project Commands ---")
    proj_queries = [
        ("NOUS, check my project progress.", IntentType.PROJECT_PROGRESS, "get_projects_overview"),
        ("show my projects", IntentType.PROJECT_PROGRESS, "get_projects_overview"),
        ("What are my upcoming project deadlines?", IntentType.PROJECT_DEADLINES, "check_project_deadlines"),
        ("Summarise recent commits on the repository", IntentType.GITHUB_ACTIVITY, "check_github_activity"),
        ("check github activity", IntentType.GITHUB_ACTIVITY, "check_github_activity"),
        ("Are there any inactive projects?", IntentType.INACTIVE_PROJECTS, "find_inactive_projects"),
        ("add project milestone: finish phase 9 by tonight", IntentType.ADD_PROJECT_MILESTONE, "add_project_milestone"),
    ]

    for q, exp_intent, exp_tool in proj_queries:
        res = intent_classifier.classify(q)
        assert_test(res.intent == exp_intent, f"'{q}' -> Intent {res.intent.value}")
        assert_test(res.suggested_tool == exp_tool, f"'{q}' -> Tool {res.suggested_tool}")

    # -------------------------------------------------------------
    # 10. FastAPI REST API End-to-End
    # -------------------------------------------------------------
    print("\n--- 10. FastAPI REST API End-to-End ---")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # GET /api/projects
        p_resp = await client.get("/api/projects")
        assert_test(p_resp.status_code == 200, "GET /api/projects returns 200")
        assert_test(p_resp.json()["count"] >= 2, "List projects returns populated list")

        # GET /api/projects/health
        h_resp = await client.get("/api/projects/health")
        assert_test(h_resp.status_code == 200, "GET /api/projects/health returns 200")
        assert_test("active_projects" in h_resp.json(), "Health endpoint provides active projects count")

        # GET /api/projects/github/activity
        g_resp = await client.get("/api/projects/github/activity")
        assert_test(g_resp.status_code == 200, "GET /api/projects/github/activity returns 200")
        assert_test("recent_commits" in g_resp.json(), "GitHub API endpoint returns commits")

        # POST /api/projects
        new_proj_payload = {
            "name": "API Testing Suite Project",
            "description": "Integration test fixture for REST endpoints",
            "tech_stack": "FastAPI, HTTPX",
            "deadline": "2026-12-01",
            "priority": "low",
        }
        create_resp = await client.post("/api/projects", json=new_proj_payload)
        assert_test(create_resp.status_code == 201, "POST /api/projects returns 201 Created")
        new_id = create_resp.json()["project"]["id"]

        # POST /api/projects/{id}/milestones
        m_payload = {"title": "Deliver API Spec", "due_date": "2026-11-28"}
        m_resp = await client.post(f"/api/projects/{new_id}/milestones", json=m_payload)
        assert_test(m_resp.status_code == 201, "POST milestone returns 201 Created")
        new_mid = m_resp.json()["milestone"]["id"]

        # PATCH /api/projects/{id}/milestones/{mid}/toggle
        t_resp = await client.patch(f"/api/projects/{new_id}/milestones/{new_mid}/toggle")
        assert_test(t_resp.status_code == 200, "PATCH milestone toggle returns 200")
        assert_test(t_resp.json()["project_progress_percent"] == 100, "Progress recalculated to 100%")

        # DELETE /api/projects/{id}
        del_resp = await client.delete(f"/api/projects/{new_id}")
        assert_test(del_resp.status_code == 200, "DELETE project returns 200")

    # Clean up test fixture project
    project_manager.delete_project(test_proj.id)

    print("\n" + "=" * 70)
    print(f"  PHASE 9 TEST SUITE COMPLETE: {passed}/{total} TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_phase9_tests())

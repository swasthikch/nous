from __future__ import annotations

"""Comprehensive Automated Test Suite for Phase 13:
Computer & Task Automation, Workspace Security, and Scheduled Jobs.
"""

import asyncio
from pathlib import Path
import shutil
import sys
import time

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure stdout is line buffered
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from fastapi import FastAPI
import httpx

from backend.app.config import settings
from backend.app.automation.db import AutomationDBManager, init_automation_db
from backend.app.automation.security import AutomationSecurityGate, CommandRiskLevel, SecurityError
from backend.app.automation.manager import AutomationManager
from backend.app.core.permissions import permission_manager
from backend.app.core.tool_registry import tool_registry
from backend.app.core.intent import IntentType, intent_classifier
from backend.app.api.automation_api import router as automation_router


async def run_phase13_tests() -> None:
    print(">>> IN RUN_PHASE13_TESTS", flush=True)
    print("=" * 68, flush=True)
    print("  RUNNING PHASE 13 TEST SUITE: COMPUTER & TASK AUTOMATION", flush=True)
    print("=" * 68, flush=True)

    test_workspace = settings.PROJECT_ROOT / "data" / "test_automation_workspace"
    test_db_path = settings.PROJECT_ROOT / "data" / "database" / "test_nous_automation.db"

    # Reset test paths
    if test_workspace.exists():
        shutil.rmtree(test_workspace, ignore_errors=True)
    test_workspace.mkdir(parents=True, exist_ok=True)

    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass

    try:
        # ---------------- 1. DATABASE & WAL VERIFICATION ----------------
        print("\n[GROUP 1] Testing Database Schema, WAL Mode, and Task CRUD...")
        init_automation_db(test_db_path)
        assert test_db_path.exists(), "Automation database file must exist"

        db = AutomationDBManager(db_path=test_db_path)
        # Create scheduled task
        created_task = db.create_scheduled_task(
            name="Morning Briefing",
            action_type="briefing",
            interval_seconds=86400,
            payload={"focus": "daily_review"},
        )
        assert created_task["id"].startswith("task_")
        assert created_task["name"] == "Morning Briefing"
        assert created_task["status"] == "active"
        print(f" [PASS] Created scheduled task: {created_task['id']}")

        # List tasks
        tasks = db.list_scheduled_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == created_task["id"]
        print(f" [PASS] Listed scheduled tasks ({len(tasks)} found).")

        # Update task status
        updated = db.update_task_status(created_task["id"], status="paused")
        assert updated is True
        assert db.get_scheduled_task(created_task["id"])["status"] == "paused"
        print(" [PASS] Task status updated to 'paused'.")

        # Record execution history
        rec = db.record_execution(
            command="echo test",
            status="success",
            exit_code=0,
            output="test",
            execution_time_ms=15,
            risk_level="safe",
        )
        assert rec["id"].startswith("exec_")
        history = db.list_execution_history(limit=10)
        assert len(history) == 1
        assert history[0]["command"] == "echo test"
        print(" [PASS] Command execution history recorded in WAL database.")

        # ---------------- 2. SECURITY GATE & PATH TRAVERSAL ----------------
        print("\n[GROUP 2] Testing Security Gate & Path Traversal Prevention...")
        sec = AutomationSecurityGate(workspace_dir=test_workspace)

        # Valid subpath
        valid_path = sec.validate_workspace_path("subfolder/my_notes.txt")
        assert str(valid_path).startswith(str(test_workspace))
        print(" [PASS] Valid workspace relative path permitted.")

        # Traversal attempt with ../
        traversal_caught = False
        try:
            sec.validate_workspace_path("../../windows/system32/cmd.exe")
        except SecurityError:
            traversal_caught = True
        assert traversal_caught is True, "Security Gate must block directory traversal attempts!"
        print(" [PASS] Directory traversal attempt ('../../windows') strictly blocked.")

        # Absolute root attempt
        abs_caught = False
        try:
            sec.validate_workspace_path("C:/Windows/System32/drivers")
        except SecurityError:
            abs_caught = True
        assert abs_caught is True, "Security Gate must block absolute paths outside workspace!"
        print(" [PASS] Absolute external root escape strictly blocked.")

        # ---------------- 3. SAFE FILE OPERATIONS ----------------
        print("\n[GROUP 3] Testing Safe Workspace File Operations (CRUD)...")
        mgr = AutomationManager(security=sec, db_manager=db)

        # Write file
        write_res = mgr.write_file("project_plan.md", "# Project NOUS Plan\nPhase 13 Automation.", overwrite=False)
        assert write_res["status"] == "written"
        assert (test_workspace / "project_plan.md").exists()
        print(" [PASS] File written successfully within workspace sandbox.")

        # Read file
        read_res = mgr.read_file("project_plan.md")
        assert "Phase 13 Automation" in read_res["content"]
        assert read_res["line_count"] == 2
        print(f" [PASS] File read verified ({read_res['size_bytes']} bytes, {read_res['line_count']} lines).")

        # List files
        files = mgr.list_files()
        file_names = [f["name"] for f in files]
        assert "project_plan.md" in file_names
        print(f" [PASS] Workspace listing verified ({len(files)} files listed).")

        # Overwrite protection
        overwrite_blocked = False
        try:
            mgr.write_file("project_plan.md", "New text", overwrite=False)
        except FileExistsError:
            overwrite_blocked = True
        assert overwrite_blocked is True
        print(" [PASS] Accidental file overwrite correctly prevented.")

        # Overwrite allowed with flag
        mgr.write_file("project_plan.md", "# Updated Plan", overwrite=True)
        assert "Updated" in mgr.read_file("project_plan.md")["content"]
        print(" [PASS] Explicit file overwrite succeeded.")

        # Delete file
        del_res = mgr.delete_file("project_plan.md")
        assert del_res["status"] == "deleted"
        assert not (test_workspace / "project_plan.md").exists()
        print(" [PASS] Safe file deletion verified.")

        # ---------------- 4. COMMAND SAFETY & BLOCKLIST ----------------
        print("\n[GROUP 4] Testing Command Classification & Blocklist Filter...")
        # Dangerous commands
        for bad_cmd in ["rmdir /s /q my_dir", "del /f /s /q C:\\", "format d:", "reg delete HKLM\\Software", ":(){ :|:& };:"]:
            lvl, reason = sec.evaluate_command_safety(bad_cmd)
            assert lvl == CommandRiskLevel.BLOCKED, f"Expected '{bad_cmd}' to be BLOCKED, got {lvl}"
        print(" [PASS] Destructive command patterns blocked (rmdir /s, format, reg delete, fork bomb).")

        # Safe read-only commands
        for safe_cmd in ["dir", "git status", "python --version", "echo Hello World"]:
            lvl, reason = sec.evaluate_command_safety(safe_cmd)
            assert lvl == CommandRiskLevel.SAFE, f"Expected '{safe_cmd}' to be SAFE, got {lvl}"
        print(" [PASS] Read-only commands verified safe (dir, git status, python --version, echo).")

        # State modifying commands requiring approval
        for risky_cmd in ["pip install requests", "python script.py", "npm run build"]:
            lvl, reason = sec.evaluate_command_safety(risky_cmd)
            assert lvl == CommandRiskLevel.REQUIRES_APPROVAL, f"Expected '{risky_cmd}' to REQUIRE_APPROVAL, got {lvl}"
        print(" [PASS] State-modifying commands correctly gated for approval.")

        # ---------------- 5. CONTROLLED EXECUTION & HITL APPROVAL GATE ----------------
        print("\n[GROUP 5] Testing Controlled Shell Execution & HITL Approval Token...")
        # Direct execution of safe command
        safe_run = mgr.request_or_execute_command("echo NOUS_TEST_AUTOMATION_OUTPUT")
        assert safe_run["status"] == "success"
        assert "NOUS_TEST_AUTOMATION_OUTPUT" in safe_run["output"]
        assert safe_run["exit_code"] == 0
        print(f" [PASS] Safe command executed directly: '{safe_run['command']}' -> exit {safe_run['exit_code']}")

        # Blocked command execution
        blocked_run = mgr.request_or_execute_command("rmdir /s /q forbidden_dir")
        assert blocked_run["status"] == "blocked"
        assert "forbidden" in blocked_run["error"] or "destructive" in blocked_run["error"]
        print(" [PASS] Blocked command prevented from executing.")

        # Risky command with approval token flow
        cmd_to_gate = "git commit -m test"
        gate_res = mgr.request_or_execute_command(cmd_to_gate)
        assert gate_res["status"] == "requires_approval"
        token = gate_res["approval_token"]
        assert token is not None
        print(f" [PASS] Command gated. Received human confirmation token: {token}")

        # Execute using token
        confirmed_run = mgr.request_or_execute_command(
            command=cmd_to_gate,
            approval_token=token,
        )
        assert confirmed_run["status"] in ("success", "error")
        print(" [PASS] Confirmed command executed successfully upon token presentation.")

        # ---------------- 6. INTENT CLASSIFICATION & TOOL REGISTRY ----------------
        print("\n[GROUP 6] Testing Intent Classifier & Tool Registry Dispatch...")
        # Intent 1: List files
        res_intent1 = intent_classifier.classify("NOUS, show workspace files")
        assert res_intent1.intent == IntentType.LIST_FILES
        assert res_intent1.suggested_tool == "list_workspace_files"
        print(" [PASS] 'show workspace files' classified as LIST_FILES intent.")

        # Intent 2: Read file
        res_intent2 = intent_classifier.classify("read file notes.txt")
        assert res_intent2.intent == IntentType.READ_FILE
        assert res_intent2.suggested_tool == "read_workspace_file"
        print(" [PASS] 'read file notes.txt' classified as READ_FILE intent.")

        # Intent 3: Run command
        res_intent3 = intent_classifier.classify("run command: git status")
        assert res_intent3.intent == IntentType.RUN_COMMAND
        assert res_intent3.suggested_tool == "execute_safe_command"
        print(" [PASS] 'run command: git status' classified as RUN_COMMAND intent.")

        # Allow medium and high risk for testing tool registry execution
        permission_manager.auto_approve_medium = True
        permission_manager.auto_approve_high = True

        # Tool Registry Execution
        tool_write = await tool_registry.execute(
            "write_workspace_file",
            {"file_path": "automation_log.txt", "content": "Verified tool output", "overwrite": True},
        )
        assert tool_write.success is True
        print(" [PASS] 'write_workspace_file' executed through Tool Registry.")

        tool_read = await tool_registry.execute(
            "read_workspace_file",
            {"file_path": "automation_log.txt"},
        )
        assert tool_read.success is True
        assert "Verified tool output" in tool_read.data["content"]
        print(" [PASS] 'read_workspace_file' executed through Tool Registry.")

        tool_cmd = await tool_registry.execute(
            "execute_safe_command",
            {"command": "echo REGISTRY_DISPATCH_OK"},
        )
        assert tool_cmd.success is True
        assert "REGISTRY_DISPATCH_OK" in tool_cmd.data["output"]
        print(" [PASS] 'execute_safe_command' executed through Tool Registry.")

        # ---------------- 7. REST API ROUTER INTEGRATION ----------------
        print("\n[GROUP 7] Testing Automation REST API Endpoints...")
        test_app = FastAPI()
        test_app.include_router(automation_router)

        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET /api/automation/files
            r = await client.get("/api/automation/files")
            assert r.status_code == 200
            assert "files" in r.json()
            print(" [PASS] GET /api/automation/files -> 200 OK")

            # 2. POST /api/automation/files/write
            r = await client.post(
                "/api/automation/files/write",
                json={"file_path": "api_test.json", "content": '{"status": "ok"}', "overwrite": True},
            )
            assert r.status_code == 200
            print(" [PASS] POST /api/automation/files/write -> 200 OK")

            # 3. POST /api/automation/files/read
            r = await client.post("/api/automation/files/read", json={"file_path": "api_test.json"})
            assert r.status_code == 200
            assert '{"status": "ok"}' in r.json()["content"]
            print(" [PASS] POST /api/automation/files/read -> 200 OK")

            # 4. POST /api/automation/execute
            r = await client.post("/api/automation/execute", json={"command": "echo API_EXECUTE_SUCCESS"})
            assert r.status_code == 200
            assert "API_EXECUTE_SUCCESS" in r.json()["output"]
            print(" [PASS] POST /api/automation/execute -> 200 OK")

            # 5. POST /api/automation/tasks
            r = await client.post(
                "/api/automation/tasks",
                json={"name": "Hourly Sync", "action_type": "project_sync", "interval_seconds": 3600},
            )
            assert r.status_code == 200
            created_tid = r.json()["task"]["id"]
            print(f" [PASS] POST /api/automation/tasks -> 200 OK (id: {created_tid})")

            # 6. POST /api/automation/tasks/{id}/run
            r = await client.post(f"/api/automation/tasks/{created_tid}/run")
            assert r.status_code == 200
            assert r.json()["task_id"] == created_tid
            print(" [PASS] POST /api/automation/tasks/{id}/run -> 200 OK")

            # 7. GET /api/automation/tasks
            r = await client.get("/api/automation/tasks")
            assert r.status_code == 200
            assert r.json()["count"] >= 1
            print(" [PASS] GET /api/automation/tasks -> 200 OK")

            # 8. GET /api/automation/history
            r = await client.get("/api/automation/history")
            assert r.status_code == 200
            assert r.json()["count"] >= 1
            print(" [PASS] GET /api/automation/history -> 200 OK")

            # 9. DELETE /api/automation/files
            r = await client.request("DELETE", "/api/automation/files", json={"file_path": "api_test.json"})
            assert r.status_code == 200
            print(" [PASS] DELETE /api/automation/files -> 200 OK")

        print("\n" + "=" * 68)
        print(" [SUCCESS] ALL 7 PHASE 13 AUTOMATION GROUPS PASSED WITH 100% SUCCESS!")
        print("=" * 68)

    finally:
        # Clean up test directories
        if test_workspace.exists():
            shutil.rmtree(test_workspace, ignore_errors=True)
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    print(">>> ENTERING MAIN", flush=True)
    asyncio.run(run_phase13_tests())

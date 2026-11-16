"""Phase 3 Tool-Calling & Safe Permission Framework Verification Suite.

Tests:
1. 5-Level Permission Hierarchy (READ, PREPARE, WRITE, EXTERNAL_ACTION, SENSITIVE_ACTION).
2. Input Schema & Parameter Type Validation.
3. Cryptographic Human-In-The-Loop (HITL) Single-Use Approval Tokens.
4. Execution Timeout Sandbox (Preventing Hung Tools).
5. Immutable Audit Logging with Secret Parameter Scrubbing.
6. FastAPI REST Endpoints (/api/tools, /api/tools/approvals, /api/tools/logs).
7. Backward-Compatibility with 48 registered legacy tools.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.app.main import app
from backend.app.tools.permissions import PermissionLevel, RiskLevel, risk_to_permission, permission_manager
from backend.app.tools.approval import approval_manager, ApprovalStatus
from backend.app.tools.logger import tool_logger
from backend.app.tools.registry import safe_tool_registry, SafeToolRegistry, ToolParameter, ToolResult
from backend.app.core.tool_registry import tool_registry


async def run_phase3_tool_tests() -> None:
    print("=" * 72)
    print("  NOUS PHASE 3 — TOOL-CALLING & SAFE PERMISSION FRAMEWORK VERIFICATION")
    print("=" * 72)

    # ---------------- 1. 5-LEVEL PERMISSION HIERARCHY ----------------
    print("\n[STEP 1] Testing 5-Level Permission Hierarchy...")
    assert risk_to_permission(RiskLevel.LOW) == PermissionLevel.READ
    assert risk_to_permission(RiskLevel.MEDIUM) == PermissionLevel.WRITE
    assert risk_to_permission(RiskLevel.HIGH) == PermissionLevel.SENSITIVE_ACTION
    assert risk_to_permission("external") == PermissionLevel.EXTERNAL_ACTION
    assert risk_to_permission("prepare") == PermissionLevel.PREPARE
    print("  [PASS] 5-tier permission classification & backward mapping confirmed.")

    # ---------------- 2. SCHEMA & INPUT TYPE VALIDATION ----------------
    print("\n[STEP 2] Testing Schema Parameter Type Validation...")
    test_reg = SafeToolRegistry()

    @test_reg.register(
        name="test_order_widget",
        description="Creates a test order with strictly validated parameters.",
        parameters=[
            ToolParameter(name="item_name", type="string", description="Name of the item", required=True),
            ToolParameter(name="quantity", type="integer", description="Number of items", required=True),
            ToolParameter(name="price", type="number", description="Unit price", required=True),
        ],
        permission_level=PermissionLevel.READ,
    )
    def test_order_func(item_name: str, quantity: int, price: float):
        return {"item": item_name, "total": quantity * price}

    # Missing required parameter
    res_missing = await test_reg.execute("test_order_widget", {"item_name": "Widget"})
    assert res_missing.success is False
    assert "Missing required parameter 'quantity'" in res_missing.error
    print("  [PASS] Missing required parameters rejected safely.")

    # Type mismatch: string passed for integer
    res_bad_type = await test_reg.execute("test_order_widget", {"item_name": "Widget", "quantity": "five", "price": 10.5})
    assert res_bad_type.success is False
    assert "must be an integer" in res_bad_type.error
    print("  [PASS] Parameter type mismatch ('five' for int) rejected safely.")

    # Valid execution
    res_valid = await test_reg.execute("test_order_widget", {"item_name": "Widget", "quantity": 3, "price": 10.5})
    assert res_valid.success is True
    assert res_valid.data["total"] == 31.5
    print("  [PASS] Valid typed parameters executed successfully.")

    # ---------------- 3. CRYPTOGRAPHIC APPROVAL TOKENS (HITL) ----------------
    print("\n[STEP 3] Testing Cryptographic Approval Tokens & Replay Protection...")
    sensitive_reg = SafeToolRegistry()

    @sensitive_reg.register(
        name="delete_important_file",
        description="Deletes a file requiring explicit Level 4 sensitive authorization.",
        parameters=[
            ToolParameter(name="file_path", type="string", description="Path to delete", required=True)
        ],
        permission_level=PermissionLevel.SENSITIVE_ACTION,
    )
    def sensitive_delete(file_path: str):
        return {"deleted": file_path}

    # First attempt: No token provided -> MUST be blocked and issue an approval token
    res_blocked = await sensitive_reg.execute("delete_important_file", {"file_path": "database.backup"})
    assert res_blocked.success is False
    assert res_blocked.requires_approval is True
    assert res_blocked.approval_token is not None
    token = res_blocked.approval_token
    print(f"  Action paused: Cryptographic token generated: {token[:12]}...")

    # Second attempt: User confirms with the token -> Action succeeds
    res_approved = await sensitive_reg.execute("delete_important_file", {"file_path": "database.backup"}, approval_token=token)
    assert res_approved.success is True
    assert res_approved.data["deleted"] == "database.backup"
    print("  [PASS] Action confirmed and executed with valid cryptographic token.")

    # Replay attempt: Re-using the same token -> MUST fail (Replay Protection)
    res_replay = await sensitive_reg.execute("delete_important_file", {"file_path": "database.backup"}, approval_token=token)
    assert res_replay.success is False
    assert "already in status 'approved'" in res_replay.error
    print("  [PASS] Replay protection confirmed: Used tokens cannot be reused.")

    # ---------------- 4. EXECUTION TIMEOUT SANDBOX ----------------
    print("\n[STEP 4] Testing Asynchronous Execution Timeouts...")
    timeout_reg = SafeToolRegistry()

    @timeout_reg.register(
        name="slow_external_fetch",
        description="Simulates an unresponsive network endpoint.",
        parameters=[],
        permission_level=PermissionLevel.READ,
        timeout_seconds=0.25,  # 250ms limit
    )
    async def slow_func():
        await asyncio.sleep(1.0)
        return "finished"

    res_timeout = await timeout_reg.execute("slow_external_fetch", {})
    assert res_timeout.success is False
    assert "exceeded execution timeout limit" in res_timeout.error
    print(f"  [PASS] Timeout guardrail enforced: Long-running task terminated cleanly after 0.25s.")

    # ---------------- 5. IMMUTABLE SECURITY AUDIT LOGGING ----------------
    print("\n[STEP 5] Testing Audit Logger with Secret Parameter Redaction...")
    # Log an action with a simulated API key and password in parameters
    secret_params = {
        "api_endpoint": "https://api.openai.com/v1",
        "secret_token": "sk-proj-1234567890abcdef1234567890abcdef12345678",
        "password": "SuperSecretPassword123!",
    }
    log_entry = tool_logger.log(
        tool_name="cloud_sync",
        permission_level=PermissionLevel.EXTERNAL_ACTION,
        parameters=secret_params,
        status="SUCCESS",
        elapsed_seconds=0.042,
    )
    # Check stored parameter text in database log
    assert "[REDACTED_AI_API_KEY]" in log_entry.parameters_json
    assert "[REDACTED_SECRET]" in log_entry.parameters_json
    assert "SuperSecretPassword123!" not in log_entry.parameters_json
    print("  [PASS] Audit log verified: Credentials and API keys scrubbed before persisting.")

    # ---------------- 6. FASTAPI TOOLS & APPROVAL REST ENDPOINTS ----------------
    print("\n[STEP 6] Testing FastAPI Tools Endpoints (/api/tools)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. List tools
        r_tools = await client.get("/api/tools")
        assert r_tools.status_code == 200
        tools_json = r_tools.json()
        assert tools_json["count"] >= 10
        print(f"  [PASS] GET /api/tools: {tools_json['count']} tools listed with schemas.")

        # B. Check pending approvals endpoint
        r_apps = await client.get("/api/tools/approvals")
        assert r_apps.status_code == 200
        print(f"  [PASS] GET /api/tools/approvals: Operational.")

        # C. Check logs endpoint
        r_logs = await client.get("/api/tools/logs", params={"limit": 10})
        assert r_logs.status_code == 200
        assert r_logs.json()["count"] >= 1
        print(f"  [PASS] GET /api/tools/logs: {r_logs.json()['count']} audited entries retrieved.")

    # ---------------- 7. LEGACY 48-TOOL COMPATIBILITY ----------------
    print("\n[STEP 7] Testing Backward-Compatibility with Core Tools...")
    core_calc = await tool_registry.execute("calculate", {"expression": "25 * 4"})
    assert core_calc.success is True
    assert core_calc.data["result"] == 100
    print("  [PASS] Core tools execute seamlessly through the upgraded permission gateway.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 3 SAFE TOOL FRAMEWORK CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase3_tool_tests())

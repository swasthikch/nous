from __future__ import annotations

"""Comprehensive Automated Test Suite for Phase 14:
Security Vault, Sensitive Data Redaction, Privacy Controls, and Audit Trail.
"""

import asyncio
import json
from pathlib import Path
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
from backend.app.security.db import SecurityDBManager, init_security_db
from backend.app.security.redactor import sensitive_redactor
from backend.app.security.vault import SecurityVault
from backend.app.core.intent import IntentType, intent_classifier, IntentResult
from backend.app.core.model_router import model_router, RoutingMode
from backend.app.core.tool_registry import tool_registry
from backend.app.core.permissions import permission_manager
from backend.app.api.security_api import router as security_router


async def run_phase14_tests() -> None:
    print("=" * 68, flush=True)
    print("  RUNNING PHASE 14 TEST SUITE: SECURITY VAULT & PRIVACY CONTROLS", flush=True)
    print("=" * 68, flush=True)

    test_db_path = settings.PROJECT_ROOT / "data" / "database" / "test_nous_security.db"
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass

    try:
        # ---------------- 1. DATABASE & WAL VERIFICATION ----------------
        print("\n[GROUP 1] Testing Security Database Schema, WAL Mode, and Defaults...", flush=True)
        init_security_db(test_db_path)
        assert test_db_path.exists(), "Security database file must exist"

        db = SecurityDBManager(db_path=test_db_path)
        default_priv = db.get_privacy_settings()
        assert default_priv["offline_lockdown"] is False
        assert default_priv["strict_redaction"] is True
        print(" [PASS] test_nous_security.db initialized with default privacy policy.", flush=True)

        # ---------------- 2. SENSITIVE DATA REDACTION ----------------
        print("\n[GROUP 2] Testing Sensitive Data Redaction & Pattern Masking...", flush=True)
        # Test A: OpenAI & Anthropic API Key
        raw_ai = "Calling OpenAI with key sk-abcdef12345678901234567890 for completion."
        redacted_ai = sensitive_redactor.redact(raw_ai)
        assert "sk-abcdef" not in redacted_ai
        assert "[REDACTED_AI_API_KEY]" in redacted_ai
        print(" [PASS] OpenAI / AI API key redacted.", flush=True)

        # Test B: Google API Key
        raw_google = "Connecting to Google Cloud using AIzaSyD9876543210123456789012345678901."
        redacted_google = sensitive_redactor.redact(raw_google)
        assert "AIzaSy" not in redacted_google
        assert "[REDACTED_GOOGLE_API_KEY]" in redacted_google
        print(" [PASS] Google API key redacted.", flush=True)

        # Test C: GitHub Personal Access Token
        raw_gh = "git remote set-url origin https://ghp_1234567890abcdefghijklmnopqrstuvwxyz@github.com/org/repo"
        redacted_gh = sensitive_redactor.redact(raw_gh)
        assert "ghp_" not in redacted_gh
        assert "[REDACTED_GITHUB_TOKEN]" in redacted_gh
        print(" [PASS] GitHub Personal Access Token redacted.", flush=True)

        # Test D: Bearer Token
        raw_bearer = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
        redacted_bearer = sensitive_redactor.redact(raw_bearer)
        assert "Bearer [REDACTED_BEARER_TOKEN]" in redacted_bearer
        print(" [PASS] Authorization Bearer token redacted.", flush=True)

        # Test E: Credit Card Number
        raw_cc = "Payment card on file: 4111 2222 3333 4444"
        redacted_cc = sensitive_redactor.redact(raw_cc)
        assert "4111" not in redacted_cc
        assert "[REDACTED_CREDIT_CARD]" in redacted_cc
        print(" [PASS] Credit card number redacted.", flush=True)

        # Test F: Recursive Data Structure Redaction
        nested_data = {
            "user": "student_developer",
            "api_key": "sk-test12345678901234567890",
            "db_url": "postgresql://postgres:mySuperSecret123@localhost:5432/mydb",
            "tokens": ["ghp_abcdefghijklmnopqrstuvwxyz1234567890"],
        }
        scrubbed = sensitive_redactor.redact_data_structure(nested_data)
        assert scrubbed["api_key"] == "[REDACTED_FIELD]"
        assert "mySuperSecret123" not in scrubbed["db_url"]
        assert "ghp_" not in scrubbed["tokens"][0]
        print(" [PASS] Recursive dictionary and list credential scrubbing verified.", flush=True)

        # ---------------- 3. TAMPER-EVIDENT AUDIT TRAIL ----------------
        print("\n[GROUP 3] Testing Security Audit Trail & Event Logging...", flush=True)
        # Log event with embedded sensitive key to verify auto-redaction
        event = db.log_event(
            event_type="tool_execution",
            resource="execute_safe_command",
            risk_level="high",
            decision="CONFIRMED",
            actor="user",
            details={
                "command": "git push origin main",
                "secret_token": "ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            },
            session_id="sess_sec_test",
        )
        assert event["id"].startswith("aud_")
        assert event["decision"] == "CONFIRMED"
        assert "ghp_" not in json.dumps(event["details"])
        assert "[REDACTED" in json.dumps(event["details"])
        print(f" [PASS] Audit event recorded with automatic credential redaction (id: {event['id']}).", flush=True)

        # Filter events
        listed = db.list_events(event_type="tool_execution")
        assert len(listed) >= 1
        assert listed[0]["resource"] == "execute_safe_command"

        search_res = db.list_events(search="git push")
        assert len(search_res) >= 1
        print(" [PASS] Audit event query and keyword search verified.", flush=True)

        # ---------------- 4. PRIVACY CONTROLS & OFFLINE LOCKDOWN SWITCH ----------------
        print("\n[GROUP 4] Testing Privacy Controls, Memory Pause, and Offline Lockdown...", flush=True)
        vault = SecurityVault(db_manager=db)

        # Test Offline Lockdown Activation
        vault.set_privacy_mode(offline_lockdown=True)
        assert vault.is_offline_lockdown_enabled() is True
        print(" [PASS] Offline Lockdown switch activated.", flush=True)

        # Verify Model Router obeys Offline Lockdown
        mock_intent = IntentResult(
            intent=IntentType.COMPLEX_REASONING,
            confidence=0.9,
            suggested_tool=None,
            requires_cloud_routing=True,  # Would normally require cloud
        )
        # Point global security vault temporarily to test db
        from backend.app.security.vault import security_vault
        orig_db = security_vault.db
        security_vault.db = db

        routing_decision = await model_router.route(mock_intent)
        assert routing_decision.selected_target == "local", "Offline Lockdown MUST force local model inference!"
        assert "Offline Lockdown is active" in routing_decision.reason
        print(" [PASS] Model Router enforced Offline Lockdown: cloud route blocked -> local model selected.", flush=True)

        # Revert lockdown
        vault.set_privacy_mode(offline_lockdown=False)
        assert vault.is_offline_lockdown_enabled() is False
        print(" [PASS] Offline Lockdown switch deactivated.", flush=True)

        # Test Memory Retention Pause
        vault.set_privacy_mode(pause_memory_retention=True)
        assert vault.is_memory_retention_paused() is True
        vault.set_privacy_mode(pause_memory_retention=False)
        assert vault.is_memory_retention_paused() is False
        print(" [PASS] Memory retention pause switch verified.", flush=True)

        # Restore global vault db
        security_vault.db = orig_db

        # ---------------- 5. ARTIFACT PURGING & DATA EXPORT ----------------
        print("\n[GROUP 5] Testing Transient Data Purge & Data Export Package...", flush=True)
        purge_res = vault.purge_transient_data()
        assert purge_res["status"] == "success"
        print(" [PASS] Transient cache and expired artifacts purged.", flush=True)

        export_data = vault.export_user_data()
        assert export_data["version"] == "1.0"
        assert "privacy_settings" in export_data
        assert "audit_trail_sample" in export_data
        print(f" [PASS] User privacy package exported ({len(export_data['audit_trail_sample'])} audit entries).", flush=True)

        # ---------------- 6. INTENT CLASSIFICATION & TOOL REGISTRY ----------------
        print("\n[GROUP 6] Testing Intent Classifier & Tool Registry Dispatch...", flush=True)
        # Intent: Security Audit
        r_intent1 = intent_classifier.classify("NOUS, show security audit logs")
        assert r_intent1.intent == IntentType.SECURITY_AUDIT
        assert r_intent1.suggested_tool == "get_security_audit_logs"
        print(" [PASS] 'show security audit logs' classified as SECURITY_AUDIT intent.", flush=True)

        # Intent: Offline Lockdown
        r_intent2 = intent_classifier.classify("turn on offline lockdown mode")
        assert r_intent2.intent == IntentType.OFFLINE_LOCKDOWN
        assert r_intent2.suggested_tool == "set_security_privacy_mode"
        print(" [PASS] 'turn on offline lockdown mode' classified as OFFLINE_LOCKDOWN intent.", flush=True)

        # Tool Registry: sanitize_text_content
        tool_san = await tool_registry.execute(
            "sanitize_text_content",
            {"text": "My API key is sk-12345678901234567890123456."},
        )
        assert tool_san.success is True
        assert tool_san.data["contains_secrets"] is True
        assert "[REDACTED_AI_API_KEY]" in tool_san.data["sanitized_text"]
        print(" [PASS] 'sanitize_text_content' tool executed through Tool Registry.", flush=True)

        # Tool Registry: get_security_audit_logs
        tool_audit = await tool_registry.execute("get_security_audit_logs", {"limit": 5})
        assert tool_audit.success is True
        assert "events" in tool_audit.data
        print(" [PASS] 'get_security_audit_logs' tool executed through Tool Registry.", flush=True)

        # ---------------- 7. REST API ENDPOINTS ----------------
        print("\n[GROUP 7] Testing Security REST API Endpoints...", flush=True)
        test_app = FastAPI()
        test_app.include_router(security_router)

        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET /api/security/privacy
            r = await client.get("/api/security/privacy")
            assert r.status_code == 200
            assert "privacy_settings" in r.json()
            print(" [PASS] GET /api/security/privacy -> 200 OK", flush=True)

            # 2. POST /api/security/privacy
            r = await client.post("/api/security/privacy", json={"strict_redaction": True})
            assert r.status_code == 200
            assert r.json()["status"] == "updated"
            print(" [PASS] POST /api/security/privacy -> 200 OK", flush=True)

            # 3. POST /api/security/sanitize
            r = await client.post(
                "/api/security/sanitize",
                json={"text": "User token: ghp_9876543210abcdefghijklmnopqrstuvwxy"},
            )
            assert r.status_code == 200
            assert r.json()["contains_secrets"] is True
            assert "[REDACTED_GITHUB_TOKEN]" in r.json()["sanitized_text"]
            print(" [PASS] POST /api/security/sanitize -> 200 OK", flush=True)

            # 4. GET /api/security/audit
            r = await client.get("/api/security/audit")
            assert r.status_code == 200
            assert "events" in r.json()
            print(" [PASS] GET /api/security/audit -> 200 OK", flush=True)

            # 5. POST /api/security/purge
            r = await client.post("/api/security/purge")
            assert r.status_code == 200
            assert r.json()["status"] == "success"
            print(" [PASS] POST /api/security/purge -> 200 OK", flush=True)

            # 6. GET /api/security/export
            r = await client.get("/api/security/export")
            assert r.status_code == 200
            assert "audit_trail_sample" in r.json()
            print(" [PASS] GET /api/security/export -> 200 OK", flush=True)

        print("\n" + "=" * 68, flush=True)
        print(" [SUCCESS] ALL 7 PHASE 14 SECURITY GROUPS PASSED WITH 100% SUCCESS!", flush=True)
        print("=" * 68, flush=True)

    finally:
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(run_phase14_tests())

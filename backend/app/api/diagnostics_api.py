"""System Diagnostics REST API Router for NOUS (Phase 15).

Exposes system diagnostics, hardware health, database verification,
and end-to-end smoke testing endpoints.
"""

from __future__ import annotations

import time
from typing import Any
from fastapi import APIRouter, HTTPException

from backend.app.core.diagnostics import diagnostics_collector
from backend.app.security.redactor import sensitive_redactor
from backend.app.core.intent import intent_classifier, IntentType
from backend.app.core.model_router import model_router

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("/report")
async def get_system_report() -> dict[str, Any]:
    """Retrieve complete multi-subsystem diagnostic report."""
    try:
        report = await diagnostics_collector.generate_system_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diagnostic report: {str(e)}")


@router.get("/hardware")
async def get_hardware() -> dict[str, Any]:
    """Retrieve CPU, RAM, and Disk telemetry."""
    return diagnostics_collector.get_hardware_telemetry()


@router.get("/databases")
async def get_databases() -> dict[str, Any]:
    """Retrieve status, sizes, and integrity of all 7 SQLite databases."""
    return diagnostics_collector.get_database_diagnostics()


@router.get("/ollama")
async def get_ollama() -> dict[str, Any]:
    """Check Ollama connectivity, latency, and available models."""
    return await diagnostics_collector.get_ollama_diagnostics()


@router.post("/smoke-test")
async def run_smoke_test() -> dict[str, Any]:
    """Execute rapid in-process smoke check across core components."""
    t0 = time.perf_counter()
    results: list[dict[str, Any]] = []

    # 1. Database Check
    db_diag = diagnostics_collector.get_database_diagnostics()
    results.append({
        "component": "Databases (7 SQLite Engines)",
        "passed": db_diag["all_healthy"],
        "detail": f"{db_diag['healthy_count']}/{db_diag['databases_count']} databases healthy and verified.",
    })

    # 2. Sensitive Redactor Check
    test_key = "sk-test1234567890abcdef1234567890"
    scrubbed = sensitive_redactor.redact(f"Key: {test_key}")
    redactor_passed = test_key not in scrubbed and "[REDACTED_AI_API_KEY]" in scrubbed
    results.append({
        "component": "Zero-Trust Credential Redactor",
        "passed": redactor_passed,
        "detail": "Credential masking correctly intercepted and substituted synthetic key.",
    })

    # 3. Intent Classifier Check
    intent_res = intent_classifier.classify("what is my schedule today?")
    intent_passed = intent_res.intent == IntentType.SCHEDULE_QUERY
    results.append({
        "component": "Intent Classifier & Semantic Engine",
        "passed": intent_passed,
        "detail": f"Classified 'schedule' query to IntentType.{intent_res.intent.name}.",
    })

    # 4. Model Router Check
    route_res = await model_router.route(intent_res)
    router_passed = route_res.selected_target in ("local", "cloud")
    results.append({
        "component": "Model Router & Hybrid Dispatch",
        "passed": router_passed,
        "detail": f"Target: {route_res.selected_target.upper()} (Reason: {route_res.reason}).",
    })

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    all_passed = all(r["passed"] for r in results)

    return {
        "status": "PASSED" if all_passed else "FAILED",
        "all_passed": all_passed,
        "elapsed_ms": elapsed_ms,
        "checks_count": len(results),
        "results": results,
    }

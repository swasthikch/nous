from __future__ import annotations

"""Master Test Runner for NOUS Personal AI Assistant.

Executes all 13 automated test suites across Phases 1 through 15,
verifies zero regression, and generates an executive validation report.
"""

from pathlib import Path
import subprocess
import sys
import time

TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent

TEST_SUITES = [
    {"phase": "Phase 1", "name": "Core Brain, Config & Calibration", "file": "test_phase1.py"},
    {"phase": "Phase 2", "name": "Anti-Hallucination Tool Verification", "file": "test_phase2.py"},
    {"phase": "Phase 5", "name": "Persistent SQLite Long-Term Memory", "file": "test_phase5.py"},
    {"phase": "Phase 6", "name": "Hands-Free Voice Engine & Visualizer", "file": "test_phase6.py"},
    {"phase": "Phase 7", "name": "Daily Life & Routine Management", "file": "test_phase7.py"},
    {"phase": "Phase 8", "name": "Email Intelligence & Injection Defense", "file": "test_phase8.py"},
    {"phase": "Phase 9", "name": "Project Intelligence & Milestones", "file": "test_phase9.py"},
    {"phase": "Phase 10 & 11", "name": "Financial Markets & 20-Factor Reasoning", "file": "test_phase10.py"},
    {"phase": "Phase 12", "name": "Web Research & Knowledge Notebook", "file": "test_phase12.py"},
    {"phase": "Phase 13", "name": "Computer Automation & Guardrails", "file": "test_phase13.py"},
    {"phase": "Phase 14", "name": "Security Vault, Privacy & Redaction", "file": "test_phase14.py"},
    {"phase": "Phase 15", "name": "System Diagnostics & E2E Integration", "file": "test_phase15.py"},
    {"phase": "Public APIs", "name": "Open-Meteo, Dictionary, Frankfurter & Jokes", "file": "test_public_apis.py"},
    {"phase": "Cloud Daemon", "name": "Minute-to-Minute Offline Autonomous Worker", "file": "test_cloud_daemon.py"},
    {"phase": "Live Server", "name": "ASGI Dispatch & Live Server Smoke", "file": "test_live_server.py"},
]


def run_master_suite() -> int:
    print("=" * 76)
    print("      NOUS PERSONAL AI ASSISTANT - MASTER TEST SUITE RUNNER")
    print("      'Your Intelligence. Your Memory. Your Assistant.'")
    print("=" * 76)
    print(f" Python: {sys.version.split()[0]} ({sys.executable})")
    print(f" Root:   {PROJECT_ROOT}")
    print(f" Total Suites: {len(TEST_SUITES)}")
    print("=" * 76 + "\n")

    overall_start = time.perf_counter()
    results = []
    failed_count = 0

    for idx, suite in enumerate(TEST_SUITES, 1):
        test_path = TEST_DIR / suite["file"]
        if not test_path.exists():
            print(f"[{idx:02d}/{len(TEST_SUITES):02d}] ⚠️  {suite['phase']}: {suite['name']} - File not found: {suite['file']}")
            results.append({**suite, "status": "MISSING", "elapsed": 0.0})
            failed_count += 1
            continue

        print(f"[{idx:02d}/{len(TEST_SUITES):02d}] Running {suite['phase']} ({suite['file']})...", end="", flush=True)
        t0 = time.perf_counter()

        proc = subprocess.run(
            [sys.executable, "-u", str(test_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        elapsed = round(time.perf_counter() - t0, 2)

        if proc.returncode == 0:
            print(f" [PASSED] ({elapsed}s)")
            results.append({**suite, "status": "PASSED", "elapsed": elapsed})
        else:
            print(f" [FAILED] ({elapsed}s, exit code: {proc.returncode})")
            results.append({**suite, "status": "FAILED", "elapsed": elapsed, "output": proc.stderr or proc.stdout})
            failed_count += 1

    total_time = round(time.perf_counter() - overall_start, 2)

    # Print Executive Summary Scorecard
    print("\n" + "=" * 76)
    print("                        EXECUTIVE VALIDATION REPORT CARD")
    print("=" * 76)
    print(f"{'PHASE':<14} | {'STATUS':<8} | {'TIME':<8} | {'SUBSYSTEM / TEST SUITE'}")
    print("-" * 76)
    for r in results:
        status_symbol = "[PASS]" if r["status"] == "PASSED" else "[FAIL]"
        print(f"{r['phase']:<14} | {status_symbol:<8} | {r['elapsed']:>5.2f}s  | {r['name']}")
    print("-" * 76)
    print(f"Total Test Time: {total_time}s | Passed: {len(results) - failed_count}/{len(results)} suites ({(len(results) - failed_count)/len(results)*100:.1f}%)")
    print("=" * 76)

    if failed_count > 0:
        print("\n[FAILURES DETECTED]:")
        for r in results:
            if r["status"] == "FAILED":
                print(f"\n--- {r['phase']} ({r['file']}) Error Output ---")
                err_text = r.get("output", "")
                # Print last 15 lines of error
                lines = err_text.strip().splitlines()
                print("\n".join(lines[-15:]))
        return 1

    print(f"\n [ALL {len(results)} MASTER TEST SUITES PASSED WITH 100% SUCCESS!]")
    return 0


if __name__ == "__main__":
    sys.exit(run_master_suite())

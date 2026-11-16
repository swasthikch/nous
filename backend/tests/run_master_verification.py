"""Master Verification Test Runner for NOUS Personal AI Operating System (Phases 1-10).

Executes the official test suites for all 10 architectural phases:
- Phase 1: Central AI Brain & SSE Stream
- Phase 2: 5-Tier Memory Engine
- Phase 3: Safe Tool Calling & HITL Approval
- Phase 4: Specialized AI Agents (Research, Coding, Productivity, File, Market)
- Phase 5: Voice Assistant & Speech Pipeline
- Phase 6: Windows Desktop Companion & Native Telemetry
- Phase 7: Integrated Dashboard, Workspace & Settings
- Phase 8: Autonomous Workflows & Execution Engine
- Phase 9: Multi-Device Synchronization & Mobile PWA
- Phase 10: Security Hardening & Production Authentication
"""

import asyncio
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.tests.test_phase1_brain import run_phase1_brain_tests
from backend.tests.test_phase2_memory import run_phase2_memory_tests
from backend.tests.test_phase3_tools import run_phase3_tool_tests
from backend.tests.test_phase4_agents import run_phase4_agents_tests
from backend.tests.test_phase5_voice import run_phase5_voice_tests
from backend.tests.test_phase6_desktop import run_phase6_desktop_tests
from backend.tests.test_phase7_dashboard import run_phase7_dashboard_tests
from backend.tests.test_phase8_workflows import run_phase8_workflows_tests
from backend.tests.test_phase9_multidevice import run_phase9_multidevice_tests
from backend.tests.test_phase10_security_auth import run_phase10_security_auth_tests
from backend.tests.test_phase11_cloud_deploy import run_phase11_cloud_deploy_tests


SUITES = [
    ("Phase 1: Central AI Brain & SSE Stream", run_phase1_brain_tests),
    ("Phase 2: 5-Tier Memory Engine", run_phase2_memory_tests),
    ("Phase 3: Safe Tool Calling & HITL Approval", run_phase3_tool_tests),
    ("Phase 4: Specialized AI Agents", run_phase4_agents_tests),
    ("Phase 5: Voice Assistant & Speech Pipeline", run_phase5_voice_tests),
    ("Phase 6: Windows Desktop Companion", run_phase6_desktop_tests),
    ("Phase 7: Integrated Dashboard & Workspace", run_phase7_dashboard_tests),
    ("Phase 8: Autonomous Workflows & Execution Engine", run_phase8_workflows_tests),
    ("Phase 9: Multi-Device Sync & Mobile PWA", run_phase9_multidevice_tests),
    ("Phase 10: Security Hardening & Production Auth", run_phase10_security_auth_tests),
    ("Phase 11: Cloud Persistence & Deployment", run_phase11_cloud_deploy_tests),
]


async def main():
    print("=" * 80)
    print("       NOUS PERSONAL AI OPERATING SYSTEM — MASTER SYSTEM VERIFICATION")
    print("=" * 80)

    start_total = time.time()
    results = []

    for name, suite_func in SUITES:
        print(f"\n>>> EXECUTING {name.upper()}...")
        suite_start = time.time()
        try:
            await suite_func()
            elapsed = time.time() - suite_start
            results.append((name, "PASS", elapsed))
        except Exception as e:
            elapsed = time.time() - suite_start
            results.append((name, f"FAIL: {e}", elapsed))
            print(f"FAILED: {e}")

    total_elapsed = time.time() - start_total
    passed_count = sum(1 for _, st, _ in results if st == "PASS")

    print("\n" + "=" * 80)
    print("                        EXECUTIVE VERIFICATION SUMMARY")
    print("=" * 80)
    for name, st, el in results:
        status_str = f"[\033[92mPASS\033[0m]" if st == "PASS" else f"[\033[91m{st}\033[0m]"
        print(f"  {status_str:<12} {name:<50} ({el:.2f}s)")

    print("-" * 80)
    print(f"  Total Suites: {len(results)} | Passed: {passed_count}/{len(results)} ({(passed_count/len(results))*100:.1f}%) | Time: {total_elapsed:.2f}s")
    print("=" * 80)

    if passed_count != len(results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

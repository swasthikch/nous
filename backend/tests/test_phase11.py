from __future__ import annotations

"""Phase 11 Test Suite: Financial Market Intelligence & Causal Reasoning.
Runs the market intelligence and 20-factor causal analysis test suite.
"""

import asyncio
from backend.tests.test_phase10 import run_tests

if __name__ == "__main__":
    asyncio.run(run_tests())

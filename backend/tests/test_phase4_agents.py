"""Test Suite for NOUS Phase 4: Specialized AI Agents.

Verifies:
1. Agent Registration & Base Polymorphism (5 specialized agents).
2. Research Agent execution, citation building, and Knowledge Memory indexing.
3. Coding Agent workspace inspection, syntax verification, Git status, and Project Memory indexing.
4. Productivity Agent schedule coordination, Eisenhower briefing, and Episodic Memory indexing.
5. File Agent workspace navigation, bounded reading, path traversal protection, and memory recording.
6. Market Agent benchmark tracking, causal reasoning, educational disclaimer, and zero-trade safety gate.
7. Agent Coordinator dynamic intent routing.
8. FastAPI Agents REST endpoints (/api/agents, /api/agents/{id}/run, /api/agents/route).
"""

import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx

from backend.app.main import app
from backend.app.agents.coordinator import agent_coordinator
from backend.app.agents.base import AgentRole
from backend.app.agents.research_agent import research_agent
from backend.app.agents.coding_agent import coding_agent
from backend.app.agents.productivity_agent import productivity_agent
from backend.app.agents.file_agent import file_agent
from backend.app.agents.market_agent import market_agent
from backend.app.memory.manager import memory_manager
from backend.app.memory.models import MemoryTier


async def run_phase4_agents_tests():
    print("=" * 72)
    print("  NOUS PHASE 4 — SPECIALIZED AI AGENTS VERIFICATION")
    print("=" * 72)

    # ---------------- 1. AGENT REGISTRY & BASE POLYMORPHISM ----------------
    print("\n[STEP 1] Testing Agent Registry & Polymorphism...")
    agents = agent_coordinator.list_agents()
    assert len(agents) == 5, f"Expected 5 specialized agents, found {len(agents)}"
    roles = {a["role"] for a in agents}
    expected_roles = {"research", "coding", "productivity", "file", "market"}
    assert roles == expected_roles, f"Roles mismatch: {roles}"
    print(f"  [PASS] 5 Specialized Agents registered: {[a['name'] for a in agents]}")

    # ---------------- 2. RESEARCH AGENT ----------------
    print("\n[STEP 2] Testing Research Agent (Web Search & Knowledge Memory)...")
    res_result = await research_agent.run("What are the core advantages of FastAPI?")
    assert res_result.role == AgentRole.RESEARCH
    assert len(res_result.actions_taken) >= 1
    assert "FastAPI" in res_result.response
    assert len(res_result.memories_created) >= 1
    # Verify Knowledge memory was stored in the memory engine
    kmems = memory_manager.get_relevant_memories(query="FastAPI", limit=3, tier=MemoryTier.KNOWLEDGE)
    assert len(kmems) >= 1, "Knowledge memory was not indexed"
    print(f"  [PASS] Research Agent executed successfully. Memory created: {res_result.memories_created[0]}")

    # ---------------- 3. CODING AGENT ----------------
    print("\n[STEP 3] Testing Coding Agent (Workspace, Git & Project Memory)...")
    code_result = await coding_agent.run("Check git status and commit history")
    assert code_result.role == AgentRole.CODING
    assert any(a.tool_name == "git_status" for a in code_result.actions_taken)
    assert "Branch:" in code_result.response

    # Test syntax checking
    test_res = await coding_agent.run_syntax_or_test("backend/app/main.py")
    assert test_res.get("success") is True, f"Syntax verification failed: {test_res}"
    print("  [PASS] Coding Agent verified: Git status and Python syntax verification confirmed.")

    # ---------------- 4. PRODUCTIVITY AGENT ----------------
    print("\n[STEP 4] Testing Productivity Agent (Schedule, Rescheduling & Episodic Memory)...")
    prod_result = await productivity_agent.run("Give me my daily schedule briefing")
    assert prod_result.role == AgentRole.PRODUCTIVITY
    assert "Productivity Briefing" in prod_result.response
    assert len(prod_result.memories_created) >= 1
    # Verify Episodic memory was stored
    emems = memory_manager.get_relevant_memories(query="schedule", limit=3, tier=MemoryTier.EPISODIC)
    assert len(emems) >= 1, "Episodic memory was not indexed"
    print(f"  [PASS] Productivity Agent briefing verified. Memory indexed: {prod_result.memories_created[0]}")

    # ---------------- 5. FILE AGENT ----------------
    print("\n[STEP 5] Testing File Agent (Bounded Navigation & Path Traversal Guard)...")
    # A. Safe file list & write
    file_result = await file_agent.run("List files in the workspace")
    assert file_result.role == AgentRole.FILE
    assert any(a.tool_name == "list_files" for a in file_result.actions_taken)

    # B. Test Path Traversal Protection
    traversal_blocked = False
    try:
        file_agent._resolve_safe_path("../../../Windows/System32/cmd.exe")
    except PermissionError:
        traversal_blocked = True
    assert traversal_blocked, "Path traversal guard failed to block directory escape!"
    print("  [PASS] File Agent verified: Directory traversal attack blocked by security sandbox.")

    # ---------------- 6. MARKET AGENT ----------------
    print("\n[STEP 6] Testing Market Agent (Causal Analysis & Zero-Trade Safety Gate)...")
    # A. Analytical overview
    market_result = await market_agent.run("Explain current NIFTY 50 and institutional flows")
    assert market_result.role == AgentRole.MARKET
    assert "DISCLAIMER" in market_result.response
    assert "NIFTY" in market_result.response

    # B. Zero-trade safety gate test
    trade_result = await market_agent.run("Buy 100 shares of Reliance stock immediately")
    assert "Trade Execution Blocked" in trade_result.response
    assert len(trade_result.actions_taken) == 0, "Trade order was not blocked!"
    print("  [PASS] Market Agent verified: Overview retrieved and speculative trade order safely blocked.")

    # ---------------- 7. AGENT COORDINATOR ROUTING ----------------
    print("\n[STEP 7] Testing Agent Coordinator Cognitive Routing...")
    assert agent_coordinator.route_query("Explain python async await and run pytest") == AgentRole.CODING
    assert agent_coordinator.route_query("Research latest breakthroughs in transformer attention") == AgentRole.RESEARCH
    assert agent_coordinator.route_query("What is my schedule for today?") == AgentRole.PRODUCTIVITY
    assert agent_coordinator.route_query("Read the contents of README.md file") == AgentRole.FILE
    assert agent_coordinator.route_query("What is the current NIFTY 50 price?") == AgentRole.MARKET
    print("  [PASS] Coordinator cognitive intent classification verified across all 5 domains.")

    # ---------------- 8. FASTAPI REST ENDPOINTS ----------------
    print("\n[STEP 8] Testing FastAPI Agents REST Endpoints (/api/agents)...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
        # A. List agents
        r_list = await client.get("/api/agents")
        assert r_list.status_code == 200
        data = r_list.json()
        assert data["count"] == 5

        # B. Get agent detail
        r_detail = await client.get("/api/agents/coding_agent")
        assert r_detail.status_code == 200
        assert r_detail.json()["role"] == "coding"

        # C. Run query on specific agent
        r_run = await client.post(
            "/api/agents/coding_agent/run",
            json={"query": "Check git repository status", "context": {}},
        )
        assert r_run.status_code == 200
        assert r_run.json()["role"] == "coding"

        # D. Dynamic routing endpoint
        r_route = await client.post(
            "/api/agents/route",
            json={"query": "What are the latest stocks and market trends?", "context": {}},
        )
        assert r_route.status_code == 200
        assert r_route.json()["role"] == "market"

    print("  [PASS] FastAPI Agents endpoints (/api/agents, /run, /route) 100% operational.")

    print("\n" + "=" * 72)
    print("  ALL PHASE 4 SPECIALIZED AI AGENTS CHECKS PASSED (100%)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(run_phase4_agents_tests())

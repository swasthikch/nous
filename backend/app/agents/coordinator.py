"""Agent Coordinator & Inter-Agent Router for NOUS (Phase 4).

Coordinates:
1. Registration of all specialized agents (Research, Coding, Productivity, File, Market).
2. Cognitive routing: Maps user query to the most capable domain agent.
3. Central Brain alignment: Ensures all agents communicate through the Central Brain and share Memory.
4. Inter-agent collaboration: Allows one agent to delegate specialized sub-tasks to another.
"""

from __future__ import annotations

import re
import time
from typing import Any, Optional

from backend.app.agents.base import BaseAgent, AgentRole, AgentResult
from backend.app.agents.research_agent import research_agent, ResearchAgent
from backend.app.agents.coding_agent import coding_agent, CodingAgent
from backend.app.agents.productivity_agent import productivity_agent, ProductivityAgent
from backend.app.agents.file_agent import file_agent, FileAgent
from backend.app.agents.market_agent import market_agent, MarketIntelligenceAgent


class AgentCoordinator:
    """Central registry and dispatch coordinator for specialized NOUS agents."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self.register_agent(research_agent)
        self.register_agent(coding_agent)
        self.register_agent(productivity_agent)
        self.register_agent(file_agent)
        self.register_agent(market_agent)

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a specialized agent."""
        self._agents[agent.name] = agent
        self._agents[agent.role.value] = agent

    def get_agent(self, name_or_role: str) -> Optional[BaseAgent]:
        """Retrieve an agent by name or role."""
        return self._agents.get(name_or_role.lower().strip())

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents and their capabilities."""
        unique_agents = {agent.name: agent for agent in self._agents.values()}.values()
        return [
            {
                "name": a.name,
                "role": a.role.value,
                "description": a.description,
                "allowed_tools": a.allowed_tools,
            }
            for a in unique_agents
        ]

    def route_query(self, query: str) -> AgentRole:
        """Determine the most appropriate specialized agent based on query intent."""
        q = query.lower()

        # 1. Market & Financial intelligence
        if re.search(r"\b(stock|stocks|nifty|sensex|market|nasdaq|shares|fii|dii|bull|bear)\b", q):
            return AgentRole.MARKET

        # 2. Coding, Git, and Engineering
        if re.search(r"\b(code|git|commit|branch|repo|repository|pytest|test|syntax|bug|debug|python|fastapi|function|class)\b", q):
            return AgentRole.CODING

        # 3. Productivity & Routine
        if re.search(r"\b(schedule|routine|today|briefing|calendar|task|tasks|reschedule|eisenhower|priority|daily review)\b", q):
            return AgentRole.PRODUCTIVITY

        # 4. File & Workspace Document operations
        if re.search(r"\b(file|files|workspace|directory|read file|write file|document|folder)\b", q):
            return AgentRole.FILE

        # 5. Research & Academic investigation
        if re.search(r"\b(research|investigate|search web|sources|arxiv|paper|study|wikipedia|findings)\b", q):
            return AgentRole.RESEARCH

        # Default: General Central Orchestrator
        return AgentRole.GENERAL

    async def execute(
        self,
        query: str,
        agent_name: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        """Route and execute a query via the specified or auto-detected agent."""
        target_agent: Optional[BaseAgent] = None

        if agent_name:
            target_agent = self.get_agent(agent_name)

        if not target_agent:
            role = self.route_query(query)
            target_agent = self.get_agent(role.value)

        # Fallback to research agent if query is general investigation or not found
        if not target_agent:
            target_agent = research_agent

        return await target_agent.run(query=query, context=context, session_id=session_id)


agent_coordinator = AgentCoordinator()

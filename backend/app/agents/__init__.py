"""Specialized AI Agents Package for NOUS (Phase 4)."""

from backend.app.agents.base import BaseAgent, AgentRole, AgentAction, AgentResult
from backend.app.agents.research_agent import research_agent, ResearchAgent
from backend.app.agents.coding_agent import coding_agent, CodingAgent
from backend.app.agents.productivity_agent import productivity_agent, ProductivityAgent
from backend.app.agents.file_agent import file_agent, FileAgent
from backend.app.agents.market_agent import market_agent, MarketIntelligenceAgent
from backend.app.agents.coordinator import agent_coordinator, AgentCoordinator

__all__ = [
    "BaseAgent",
    "AgentRole",
    "AgentAction",
    "AgentResult",
    "research_agent",
    "ResearchAgent",
    "coding_agent",
    "CodingAgent",
    "productivity_agent",
    "ProductivityAgent",
    "file_agent",
    "FileAgent",
    "market_agent",
    "MarketIntelligenceAgent",
    "agent_coordinator",
    "AgentCoordinator",
]

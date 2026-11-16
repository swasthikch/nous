"""Base Agent Abstraction for NOUS Specialized AI Agents (Phase 4).

Every specialized agent:
1. Communicates through the Central Brain and Provider Abstraction.
2. Shares the 5-Tier Memory Engine (reads & writes working, personal, project, knowledge, episodic).
3. Executes tools through the Safe Tool Framework (permission tiers, HITL approval, timeouts).
4. Never hallucinates tool actions or claims to perform operations that failed.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, Optional
from pydantic import BaseModel, Field

from backend.app.ai_core.orchestrator import CentralOrchestrator
from backend.app.memory.manager import memory_manager
from backend.app.memory.models import MemoryCategory, MemoryTier, MemoryItem
from backend.app.tools.permissions import PermissionLevel
from backend.app.tools.registry import safe_tool_registry, ToolResult


class AgentRole(str, Enum):
    RESEARCH = "research"
    CODING = "coding"
    PRODUCTIVITY = "productivity"
    FILE = "file"
    MARKET = "market"
    GENERAL = "general"


class AgentAction(BaseModel):
    tool_name: str
    parameters: dict[str, Any]
    result: Any
    is_verified: bool
    status: str = "SUCCESS"
    error: Optional[str] = None


class AgentResult(BaseModel):
    query: str
    agent_name: str
    role: AgentRole
    response: str
    actions_taken: list[AgentAction] = Field(default_factory=list)
    memories_created: list[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0


class BaseAgent(ABC):
    """Abstract base class for all specialized NOUS agents."""

    def __init__(
        self,
        name: str,
        role: AgentRole,
        description: str,
        system_prompt: str,
        allowed_tools: list[str] | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.description = description
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or []

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        approval_token: Optional[str] = None,
    ) -> ToolResult:
        """Safely execute a tool via the Safe Tool Registry with permission and timeout checks."""
        return await safe_tool_registry.execute(
            name=tool_name,
            parameters=parameters,
            approval_token=approval_token,
            actor=f"agent:{self.role.value}",
        )

    def retrieve_memories(self, query: str, limit: int = 4, tier: Optional[MemoryTier] = None) -> list[MemoryItem]:
        """Query the central 5-tier memory engine using Stanford cognitive ranking."""
        return memory_manager.get_relevant_memories(query=query, limit=limit, tier=tier)

    def remember(
        self,
        key: str,
        content: str,
        category: MemoryCategory = MemoryCategory.KNOWLEDGE_NOTE,
        importance: float = 0.7,
        provenance: Optional[str] = None,
    ) -> MemoryItem:
        """Store verified findings into the central shared memory."""
        source = provenance or f"agent:{self.name}"
        return memory_manager.save_memory(
            category=category,
            key=key,
            content=content,
            importance=importance,
            provenance=source,
        )

    @abstractmethod
    async def run(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        """Execute the agent's goal-directed workflow and return structured result."""
        pass

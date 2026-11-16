"""FastAPI Endpoints for NOUS Specialized AI Agents (Phase 4).

Provides:
- GET  /api/agents: List all registered agents and capabilities.
- GET  /api/agents/{agent_id}: Details for a specific agent.
- POST /api/agents/{agent_id}/run: Execute a query with a specific agent.
- POST /api/agents/route: Intelligent routing and execution.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.agents.coordinator import agent_coordinator
from backend.app.agents.base import AgentResult

router = APIRouter(prefix="/api/agents", tags=["Specialized Agents"])


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User instruction or query for the agent")
    context: Optional[dict[str, Any]] = Field(default_factory=dict, description="Optional execution context")
    session_id: Optional[str] = Field(default=None, description="Active session ID")


@router.get("")
async def list_agents():
    """List all available specialized NOUS agents."""
    return {"agents": agent_coordinator.list_agents(), "count": len(agent_coordinator.list_agents())}


@router.get("/{agent_id}")
async def get_agent_details(agent_id: str):
    """Retrieve details and tool permissions for a specific agent."""
    agent = agent_coordinator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    return {
        "name": agent.name,
        "role": agent.role.value,
        "description": agent.description,
        "allowed_tools": agent.allowed_tools,
        "system_prompt_preview": agent.system_prompt[:200] + "...",
    }


@router.post("/{agent_id}/run", response_model=AgentResult)
async def run_agent(agent_id: str, request: AgentQueryRequest):
    """Execute a query through a specific named agent."""
    agent = agent_coordinator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

    try:
        result = await agent.run(
            query=request.query,
            context=request.context,
            session_id=request.session_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/route", response_model=AgentResult)
async def route_and_execute(request: AgentQueryRequest):
    """Dynamically route the query to the most capable specialized agent."""
    try:
        result = await agent_coordinator.execute(
            query=request.query,
            context=request.context,
            session_id=request.session_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing execution failed: {str(e)}")

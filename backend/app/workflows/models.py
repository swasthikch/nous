"""Domain Models for NOUS Autonomous Workflows & Execution Engine (Phase 8).

Defines:
- Workflow & Step Execution States.
- Directed Acyclic Graph (DAG) Step Dependencies.
- Cryptographic Human-In-The-Loop Approval Interruption.
- Context data propagation between agent steps.
"""

from __future__ import annotations

from enum import Enum
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Overall status of a multi-step autonomous workflow."""
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED_APPROVAL = "paused_approval"
    PAUSED_USER = "paused_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Lifecycle status of an individual milestone/step."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED_APPROVAL = "paused_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    """An individual atomic task inside an autonomous workflow DAG."""
    step_id: str
    name: str
    description: str
    assigned_agent: str = "system"  # research_agent, coding_agent, productivity_agent, file_agent, market_agent, or system
    tool_name: Optional[str] = None
    tool_params: dict[str, Any] = Field(default_factory=dict)
    prompt: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)  # step_ids that must finish before this step
    status: StepStatus = StepStatus.PENDING
    output: Any = None
    error: Optional[str] = None
    requires_approval: bool = False
    approval_token: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class WorkflowPlan(BaseModel):
    """The master DAG workflow container coordinating multi-step autonomous execution."""
    id: str
    goal: str
    status: WorkflowStatus = WorkflowStatus.PLANNING
    steps: list[WorkflowStep] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    context_data: dict[str, Any] = Field(default_factory=dict)
    final_summary: Optional[str] = None
    pause_reason: Optional[str] = None

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

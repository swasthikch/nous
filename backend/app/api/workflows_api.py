"""REST API Endpoints for NOUS Autonomous Workflows & Execution Engine (Phase 8).

Endpoints:
- POST /api/workflows/plan: Decompose high-level goal into an executable DAG.
- GET  /api/workflows: List past and active workflows.
- GET  /api/workflows/{workflow_id}: Inspect status, steps, dependencies, and outputs.
- POST /api/workflows/{workflow_id}/start: Execute/advance runnable steps.
- POST /api/workflows/{workflow_id}/pause: Pause active execution.
- POST /api/workflows/{workflow_id}/resume: Resume paused workflow.
- POST /api/workflows/{workflow_id}/cancel: Cancel workflow.
- POST /api/workflows/{workflow_id}/retry: Retry a failed step.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.workflows.models import WorkflowPlan, WorkflowStatus
from backend.app.workflows.planner import workflow_planner
from backend.app.workflows.engine import workflow_engine

router = APIRouter(prefix="/api/workflows", tags=["Autonomous Workflows & Execution"])


class PlanGoalRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="High-level goal to plan and decompose")
    auto_start: bool = Field(default=False, description="Whether to automatically begin execution")


class PauseWorkflowRequest(BaseModel):
    reason: str = Field(default="User paused workflow", description="Reason for pausing execution")


class CancelWorkflowRequest(BaseModel):
    reason: str = Field(default="User cancelled workflow", description="Reason for cancellation")


class RetryStepRequest(BaseModel):
    step_id: str = Field(..., description="The step_id to reset and retry")


@router.post("/plan", response_model=WorkflowPlan)
async def plan_goal_workflow(req: PlanGoalRequest):
    """Decompose a high-level goal into an ordered DAG workflow."""
    plan = await workflow_planner.plan_goal(req.goal)
    workflow_engine.db.save_workflow(plan)

    if req.auto_start:
        plan = await workflow_engine.start_workflow(plan.id)

    return plan


@router.get("", response_model=list[dict[str, Any]])
async def list_workflows(limit: int = Query(default=50, ge=1, le=200)):
    """Retrieve history of planned and executed workflows."""
    return workflow_engine.list_workflows(limit=limit)


@router.get("/{workflow_id}", response_model=WorkflowPlan)
async def get_workflow_details(workflow_id: str):
    """Inspect detailed status, steps, logs, and outputs of a workflow."""
    plan = workflow_engine.get_workflow(workflow_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return plan


@router.post("/{workflow_id}/start", response_model=WorkflowPlan)
async def start_workflow(workflow_id: str):
    """Start or advance execution of an existing workflow plan."""
    try:
        return await workflow_engine.start_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.post("/{workflow_id}/pause", response_model=WorkflowPlan)
async def pause_workflow(workflow_id: str, req: Optional[PauseWorkflowRequest] = None):
    """Pause execution of a running workflow."""
    reason = req.reason if req else "User paused workflow"
    try:
        return await workflow_engine.pause_workflow(workflow_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workflow_id}/resume", response_model=WorkflowPlan)
async def resume_workflow(workflow_id: str):
    """Resume execution of a paused or approved workflow."""
    try:
        return await workflow_engine.resume_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume error: {str(e)}")


@router.post("/{workflow_id}/cancel", response_model=WorkflowPlan)
async def cancel_workflow(workflow_id: str, req: Optional[CancelWorkflowRequest] = None):
    """Cancel a workflow permanently."""
    reason = req.reason if req else "User cancelled workflow"
    try:
        return await workflow_engine.cancel_workflow(workflow_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workflow_id}/retry", response_model=WorkflowPlan)
async def retry_step(workflow_id: str, req: RetryStepRequest):
    """Retry a failed or skipped step in a workflow."""
    try:
        return await workflow_engine.retry_step(workflow_id, req.step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retry error: {str(e)}")

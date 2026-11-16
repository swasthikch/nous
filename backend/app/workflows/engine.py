"""Autonomous Workflow Execution Engine for NOUS (Phase 8).

Coordinates:
- Dependency-aware DAG step evaluation.
- Inter-Agent dispatch with context data propagation.
- Cryptographic Human-In-The-Loop approval pauses.
- Complete execution lifecycle: Start, Pause, Resume, Cancel, Retry.
- Persistent state logging in SQLite WAL mode.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from backend.app.workflows.models import (
    WorkflowPlan,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
)
from backend.app.workflows.db import WorkflowDBManager, get_db
from backend.app.agents.coordinator import agent_coordinator
from backend.app.tools.approval import approval_manager
from backend.app.tools.permissions import PermissionLevel

logger = logging.getLogger("nous.workflows.engine")


class WorkflowEngine:
    """Master runtime coordinator for multi-step autonomous workflows."""

    def __init__(self, db_manager: Optional[WorkflowDBManager] = None) -> None:
        self.db = db_manager or WorkflowDBManager()
        self._active_tasks: dict[str, asyncio.Task] = {}

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowPlan]:
        """Fetch current workflow plan from persistent storage."""
        return self.db.get_workflow(workflow_id)

    def list_workflows(self, limit: int = 50) -> list[dict[str, Any]]:
        """List workflows from storage."""
        return self.db.list_workflows(limit=limit)

    async def start_workflow(self, workflow_id: str) -> WorkflowPlan:
        """Begin or advance execution of an existing workflow plan."""
        plan = self.get_workflow(workflow_id)
        if not plan:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        if plan.status in (WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED):
            return plan

        plan.status = WorkflowStatus.RUNNING
        plan.pause_reason = None
        self.db.save_workflow(plan)

        # Run execution loop
        return await self._execute_runnable_steps(plan)

    async def pause_workflow(self, workflow_id: str, reason: str = "User requested pause") -> WorkflowPlan:
        """Pause a running workflow gracefully."""
        plan = self.get_workflow(workflow_id)
        if not plan:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        plan.status = WorkflowStatus.PAUSED_USER
        plan.pause_reason = reason
        self.db.save_workflow(plan)
        return plan

    async def resume_workflow(self, workflow_id: str) -> WorkflowPlan:
        """Resume a paused workflow (user pause or post-approval)."""
        plan = self.get_workflow(workflow_id)
        if not plan:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        # If a step was paused for approval, check if it was approved
        for step in plan.steps:
            if step.status == StepStatus.PAUSED_APPROVAL and step.approval_token:
                req = approval_manager.get_request(step.approval_token)
                if req and req.status.value == "approved":
                    step.status = StepStatus.PENDING

        plan.status = WorkflowStatus.RUNNING
        plan.pause_reason = None
        self.db.save_workflow(plan)

        return await self._execute_runnable_steps(plan)

    async def cancel_workflow(self, workflow_id: str, reason: str = "User cancelled workflow") -> WorkflowPlan:
        """Permanently cancel a workflow."""
        plan = self.get_workflow(workflow_id)
        if not plan:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        plan.status = WorkflowStatus.CANCELLED
        plan.pause_reason = reason
        plan.completed_at = time.time()
        for step in plan.steps:
            if step.status in (StepStatus.PENDING, StepStatus.RUNNING, StepStatus.PAUSED_APPROVAL):
                step.status = StepStatus.SKIPPED
        self.db.save_workflow(plan)
        return plan

    async def retry_step(self, workflow_id: str, step_id: str) -> WorkflowPlan:
        """Reset a failed step to PENDING and resume execution."""
        plan = self.get_workflow(workflow_id)
        if not plan:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        target_step = next((s for s in plan.steps if s.step_id == step_id), None)
        if not target_step:
            raise ValueError(f"Step '{step_id}' not found in workflow '{workflow_id}'.")

        target_step.status = StepStatus.PENDING
        target_step.error = None
        plan.status = WorkflowStatus.RUNNING
        self.db.save_workflow(plan)

        return await self._execute_runnable_steps(plan)

    async def _execute_runnable_steps(self, plan: WorkflowPlan) -> WorkflowPlan:
        """Iteratively execute steps whose dependencies have resolved."""
        max_iterations = len(plan.steps) * 2
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            if plan.status not in (WorkflowStatus.RUNNING,):
                break

            # Find runnable steps
            completed_step_ids = {s.step_id for s in plan.steps if s.status == StepStatus.COMPLETED}
            runnable_step = next(
                (
                    s for s in plan.steps
                    if s.status == StepStatus.PENDING and all(dep in completed_step_ids for dep in s.depends_on)
                ),
                None,
            )

            if not runnable_step:
                # No more pending steps that are runnable.
                # Check if all steps completed
                if all(s.status == StepStatus.COMPLETED for s in plan.steps):
                    plan.status = WorkflowStatus.COMPLETED
                    plan.completed_at = time.time()
                    plan.final_summary = self._generate_final_summary(plan)
                elif any(s.status == StepStatus.FAILED for s in plan.steps):
                    plan.status = WorkflowStatus.FAILED
                elif any(s.status == StepStatus.PAUSED_APPROVAL for s in plan.steps):
                    plan.status = WorkflowStatus.PAUSED_APPROVAL
                break

            # Check if this step requires HITL confirmation and has not yet been approved
            if runnable_step.requires_approval:
                has_approved_token = False
                if runnable_step.approval_token:
                    tok_req = approval_manager.get_request(runnable_step.approval_token)
                    if tok_req and tok_req.status.value == "approved":
                        has_approved_token = True

                if not has_approved_token:
                    req = approval_manager.create_request(
                        tool_name=f"workflow_step_{runnable_step.step_id}",
                        parameters={"step_name": runnable_step.name, "agent": runnable_step.assigned_agent},
                        permission_level=PermissionLevel.WRITE,
                        description=f"Autonomous workflow step '{runnable_step.name}': {runnable_step.description}",
                    )
                    runnable_step.status = StepStatus.PAUSED_APPROVAL
                    runnable_step.approval_token = req.token
                    plan.status = WorkflowStatus.PAUSED_APPROVAL
                    plan.pause_reason = f"Requires authorization: {runnable_step.description}"
                    self.db.save_workflow(plan)
                    self.db.log_step_execution(
                        workflow_id=plan.id,
                        step_id=runnable_step.step_id,
                        agent=runnable_step.assigned_agent,
                        status=runnable_step.status.value,
                        output={"approval_token": req.token},
                    )
                    return plan

            # Execute the runnable step
            await self._run_single_step(plan, runnable_step)
            self.db.save_workflow(plan)

        self.db.save_workflow(plan)
        return plan

    async def _run_single_step(self, plan: WorkflowPlan, step: WorkflowStep) -> None:
        """Dispatch a single step to its assigned agent with prior context."""
        step.status = StepStatus.RUNNING
        step.started_at = time.time()
        self.db.save_workflow(plan)

        logger.info(f"Executing step '{step.step_id}' ({step.name}) via agent '{step.assigned_agent}'")

        try:
            # Build context from previous step outputs
            prior_context: dict[str, Any] = {
                "workflow_id": plan.id,
                "goal": plan.goal,
                "completed_context": plan.context_data,
            }

            input_prompt = step.prompt or step.description
            # Enrich prompt with previous outputs if applicable
            if plan.context_data:
                context_summary = "\n".join(f"[{k}]: {str(v)[:200]}" for k, v in plan.context_data.items())
                input_prompt = f"{input_prompt}\n\nContext from previous steps:\n{context_summary}"

            agent = agent_coordinator.get_agent(step.assigned_agent)
            if agent:
                agent_res = await agent.run(query=input_prompt, context=prior_context)
                step.output = {
                    "text": agent_res.response,
                    "agent": agent.name,
                    "actions_taken": [a.model_dump() for a in agent_res.actions_taken],
                    "memories_created": agent_res.memories_created,
                }
            else:
                # System fallback execution
                step.output = {"text": f"Completed task '{step.name}': {input_prompt[:100]}", "agent": "system"}

            step.status = StepStatus.COMPLETED
            step.completed_at = time.time()
            plan.context_data[step.step_id] = step.output.get("text", "")

            self.db.log_step_execution(
                workflow_id=plan.id,
                step_id=step.step_id,
                agent=step.assigned_agent,
                status=step.status.value,
                output=step.output,
            )

        except Exception as e:
            logger.error(f"Error executing step '{step.step_id}': {e}")
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = time.time()
            self.db.log_step_execution(
                workflow_id=plan.id,
                step_id=step.step_id,
                agent=step.assigned_agent,
                status=step.status.value,
                error=str(e),
            )

    def _generate_final_summary(self, plan: WorkflowPlan) -> str:
        """Synthesize overall workflow completion summary."""
        lines = [f"Autonomous workflow '{plan.goal}' executed successfully:"]
        for s in plan.steps:
            lines.append(f"✓ [{s.name}]: {s.assigned_agent} completed.")
        return "\n".join(lines)


workflow_engine = WorkflowEngine()

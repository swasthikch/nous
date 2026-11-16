"""Plan-and-Solve Task Decomposition Planner for NOUS (Phase 8).

Decomposes high-level objectives into executable, dependency-aware
Directed Acyclic Graph (DAG) milestones assigned to specialized agents.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
import time
from typing import Any, Optional

from backend.app.workflows.models import (
    WorkflowPlan,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
)
from backend.app.core.ollama_client import ollama_client

logger = logging.getLogger("nous.workflows.planner")


class WorkflowPlanner:
    """Decomposes complex multi-turn goals into actionable workflow DAGs."""

    def __init__(self) -> None:
        pass

    async def plan_goal(self, goal: str, context: Optional[dict[str, Any]] = None) -> WorkflowPlan:
        """Decompose a high-level goal into an ordered DAG of steps."""
        wf_id = f"wf_{uuid.uuid4().hex[:12]}"
        clean_goal = goal.strip()

        # Step 1: Try AI model structured plan generation if Ollama is available
        ai_plan = await self._decompose_with_ai(clean_goal, wf_id)
        if ai_plan:
            return ai_plan

        # Step 2: Fallback to cognitive heuristic decomposition
        return self._decompose_with_heuristics(clean_goal, wf_id)

    async def _decompose_with_ai(self, goal: str, wf_id: str) -> Optional[WorkflowPlan]:
        """Ask the local AI model for structured JSON task decomposition."""
        system_prompt = (
            "You are the NOUS Master Task Planner. Decompose the user's high-level goal into "
            "a sequential or dependent Directed Acyclic Graph (DAG) of actionable steps.\n"
            "Available Agents:\n"
            "- research_agent: Web search, academic paper lookups, citations, knowledge synthesis.\n"
            "- coding_agent: Git inspection, Python syntax checking, code analysis.\n"
            "- productivity_agent: Schedule planning, daily review, routine management.\n"
            "- file_agent: Workspace file reading, writing documents, directory browsing.\n"
            "- market_agent: Benchmark market indices, institutional flows, causal financial reasoning.\n\n"
            "Respond ONLY with a valid JSON array of step objects with these exact keys:\n"
            "[\n"
            "  {\n"
            '    "step_id": "step_1",\n'
            '    "name": "Step title",\n'
            '    "description": "What to do",\n'
            '    "assigned_agent": "research_agent",\n'
            '    "prompt": "Specific instruction for the agent",\n'
            '    "depends_on": [],\n'
            '    "requires_approval": false\n'
            "  }\n"
            "]\n"
            "Mark requires_approval: true ONLY if the step modifies/deletes files or sends data externally."
        )

        try:
            res = await ollama_client.generate(
                prompt=f"Goal: {goal}",
                system=system_prompt,
                options={"temperature": 0.1},
            )
            raw = res.get("response", "").strip()
            # Extract JSON block
            json_match = re.search(r"\[\s*\{.*\}\s*\]", raw, re.DOTALL)
            if json_match:
                raw_json = json_match.group(0)
                step_dicts = json.loads(raw_json)
                steps: list[WorkflowStep] = []
                for s in step_dicts:
                    steps.append(
                        WorkflowStep(
                            step_id=s.get("step_id", f"step_{len(steps)+1}"),
                            name=s.get("name", "Task Step"),
                            description=s.get("description", ""),
                            assigned_agent=s.get("assigned_agent", "system"),
                            prompt=s.get("prompt", s.get("description", "")),
                            depends_on=s.get("depends_on", []),
                            requires_approval=bool(s.get("requires_approval", False)),
                            status=StepStatus.PENDING,
                        )
                    )
                if steps:
                    return WorkflowPlan(
                        id=wf_id,
                        goal=goal,
                        status=WorkflowStatus.PLANNING,
                        steps=steps,
                    )
        except Exception as e:
            logger.debug(f"AI decomposition skipped: {e}")

        return None

    def _decompose_with_heuristics(self, goal: str, wf_id: str) -> WorkflowPlan:
        """Deterministic heuristic decomposition based on intent recognition."""
        low = goal.lower()
        steps: list[WorkflowStep] = []

        # Pattern A: Research + Document / Workspace Report
        if any(w in low for w in ["research", "investigate", "study", "analyze", "explain"]) and any(w in low for w in ["report", "write", "document", "file", "save"]):
            steps.append(
                WorkflowStep(
                    step_id="step_1",
                    name="Conduct In-Depth Research",
                    description=f"Investigate core facts, sources, and literature for: {goal}",
                    assigned_agent="research_agent",
                    prompt=f"Research the following subject with sources and citations: {goal}",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStep(
                    step_id="step_2",
                    name="Synthesize and Draft Workspace Report",
                    description="Synthesize research output into a formatted markdown report.",
                    assigned_agent="file_agent",
                    prompt="Save the research synthesis into workspace as an executive briefing.",
                    depends_on=["step_1"],
                    requires_approval=True,  # Modifies workspace
                )
            )

        # Pattern B: Code analysis / check + Git status
        elif any(w in low for w in ["code", "syntax", "git", "repo", "commit", "build"]):
            steps.append(
                WorkflowStep(
                    step_id="step_1",
                    name="Inspect Codebase & Git Status",
                    description="Inspect active branch, modified files, and working tree cleanliness.",
                    assigned_agent="coding_agent",
                    prompt="Check git status and active branch in the repository.",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStep(
                    step_id="step_2",
                    name="Verify Python Syntax & Imports",
                    description="Run static syntax compilation checks across changed python files.",
                    assigned_agent="coding_agent",
                    prompt="Verify syntax across backend code files.",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )

        # Pattern C: Market research + Portfolio check
        elif any(w in low for w in ["market", "stock", "nifty", "fii", "invest"]):
            steps.append(
                WorkflowStep(
                    step_id="step_1",
                    name="Gather Market Telemetry & Indices",
                    description="Fetch latest benchmark price indices (NIFTY, SENSEX) and institutional flows.",
                    assigned_agent="market_agent",
                    prompt=f"Analyze market conditions and institutional flows for: {goal}",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStep(
                    step_id="step_2",
                    name="Formulate Causal Intelligence Briefing",
                    description="Apply 20-factor causal reasoning model to summarize market implications.",
                    assigned_agent="market_agent",
                    prompt="Synthesize market telemetry into an educational causal briefing.",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )

        # Pattern D: Productivity / Routine daily plan
        elif any(w in low for w in ["schedule", "routine", "planner", "briefing", "tasks"]):
            steps.append(
                WorkflowStep(
                    step_id="step_1",
                    name="Analyze Daily Schedule & Commitments",
                    description="List today's scheduled activities, fixed blocks, and identify open windows.",
                    assigned_agent="productivity_agent",
                    prompt="Review today's schedule and check for missed activities.",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStep(
                    step_id="step_2",
                    name="Generate Daily Briefing & Reschedule",
                    description="Create an executive briefing with Eisenhower prioritization.",
                    assigned_agent="productivity_agent",
                    prompt="Generate prioritized daily debrief and action list.",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )

        # Default Generic Two-Step Flow
        else:
            steps.append(
                WorkflowStep(
                    step_id="step_1",
                    name="Initial Analysis & Investigation",
                    description=f"Analyze context and determine requirements for: {goal}",
                    assigned_agent="research_agent",
                    prompt=f"Investigate: {goal}",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStep(
                    step_id="step_2",
                    name="Synthesize Final Deliverable",
                    description="Compile results into an actionable response.",
                    assigned_agent="system",
                    prompt=f"Synthesize conclusions for: {goal}",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )

        return WorkflowPlan(
            id=wf_id,
            goal=goal,
            status=WorkflowStatus.PLANNING,
            steps=steps,
        )


workflow_planner = WorkflowPlanner()

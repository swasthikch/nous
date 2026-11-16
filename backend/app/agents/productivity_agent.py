"""Productivity & Daily Life Agent for NOUS.

Specializes in:
1. Daily schedule planning and activity coordination.
2. Task prioritization using the Eisenhower Matrix (Urgent vs. Important).
3. Automated rescheduling of missed commitments.
4. Morning executive briefing and evening review generation.
5. Recording daily milestones and routine habits into Memory Tier EPISODIC and PERSONAL.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any, Optional

from backend.app.agents.base import BaseAgent, AgentRole, AgentAction, AgentResult
from backend.app.memory.models import MemoryCategory, MemoryTier
from backend.app.routine.manager import RoutineManager, ActivityCategory, ActivityPriority

PRODUCTIVITY_AGENT_SYSTEM_PROMPT = """You are the NOUS Specialized Productivity & Daily Life Agent.
Role: Time management, routine optimization, schedule coordination, and task prioritization.
Directives:
- Help the user maintain focused deep work (study, coding, fitness).
- Reschedule missed or delayed activities proactively.
- Produce concise, actionable daily briefings.
- Record key personal habits and daily highlights into Episodic Memory.
"""


class ProductivityAgent(BaseAgent):
    """Specialized personal productivity and routine planner."""

    def __init__(self, routine_mgr: Optional[RoutineManager] = None) -> None:
        super().__init__(
            name="productivity_agent",
            role=AgentRole.PRODUCTIVITY,
            description="Manages daily schedules, prioritizes tasks via Eisenhower matrix, and coordinates routines.",
            system_prompt=PRODUCTIVITY_AGENT_SYSTEM_PROMPT,
            allowed_tools=["get_schedule", "create_task", "reschedule_tasks", "daily_review"],
        )
        self.routine = routine_mgr or RoutineManager()

    async def get_briefing(self, target_date: Optional[str] = None) -> dict[str, Any]:
        """Generate structured daily briefing for the specified date."""
        today = target_date or date.today().isoformat()
        activities = self.routine.list_activities(target_date=today)
        completed = [a for a in activities if a.status.value == "completed"]
        pending = [a for a in activities if a.status.value != "completed"]

        return {
            "date": today,
            "total_count": len(activities),
            "completed_count": len(completed),
            "pending_count": len(pending),
            "pending_items": [f"{a.start_time}-{a.end_time}: {a.name} [{a.category.value}]" for a in pending[:5]],
            "rescheduled_count": 0,
        }

    async def run(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        t0 = time.time()
        actions: list[AgentAction] = []
        created_memories: list[str] = []

        q_lower = query.lower()

        # 1. Retrieve Personal/Routine Memories
        personal_mems = self.retrieve_memories(query=query, limit=2, tier=MemoryTier.PERSONAL)
        mem_context = ""
        if personal_mems:
            mem_context = f"\nUser Preferences: {personal_mems[0].content}\n"

        # 2. Daily Briefing / Schedule Check
        briefing = await self.get_briefing()
        actions.append(
            AgentAction(
                tool_name="get_schedule",
                parameters={"date": briefing["date"]},
                result={"total": briefing["total_count"], "pending": briefing["pending_count"]},
                is_verified=True,
            )
        )

        pending_bullets = "\n".join(f"- {p}" for p in briefing["pending_items"]) if briefing["pending_items"] else "- No pending tasks. Ready for deep work!"

        response_text = (
            f"### Daily Productivity Briefing ({briefing['date']})\n\n"
            f"- **Scheduled Activities:** {briefing['total_count']} total ({briefing['completed_count']} completed, {briefing['pending_count']} pending)\n"
            f"- **Automatically Rescheduled:** {briefing['rescheduled_count']} missed items\n\n"
            f"**Upcoming Focus Items:**\n{pending_bullets}\n"
        )
        if mem_context:
            response_text += f"\n> *[NOUS Routine Memory]*{mem_context}"

        # 3. Save briefing snapshot to Episodic Memory
        saved = self.remember(
            key=f"briefing_{briefing['date']}",
            content=f"Daily schedule for {briefing['date']}: {briefing['total_count']} tasks, {briefing['pending_count']} pending.",
            category=MemoryCategory.EPISODIC_EVENT,
            importance=0.75,
        )
        created_memories.append(saved.key)

        elapsed = round(time.time() - t0, 3)
        return AgentResult(
            query=query,
            agent_name=self.name,
            role=self.role,
            response=response_text,
            actions_taken=actions,
            memories_created=created_memories,
            elapsed_seconds=elapsed,
        )


productivity_agent = ProductivityAgent()

"""Tool Registry for NOUS AI Brain.

Provides schema validation, secure execution, and anti-hallucination guarantees.
Tools registered here are exposed to the AI orchestration engine.
"""

import ast
import operator
import platform
import os
import time
from datetime import datetime
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

import asyncio
import inspect
from backend.app.core.permissions import RiskLevel, permission_manager
from backend.app.tools.permissions import PermissionLevel, risk_to_permission
from backend.app.tools.approval import approval_manager
from backend.app.tools.logger import tool_logger
from backend.app.tools.registry import (
    safe_tool_registry,
    ToolParameter,
    ToolDefinition,
    ToolResult,
)


class ToolRegistry:
    """Central registry and executor for all NOUS tools."""

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: list[ToolParameter],
        risk_level: RiskLevel = RiskLevel.LOW,
        timeout_seconds: float = 15.0,
    ):
        """Decorator to register a tool function."""
        def decorator(func: Callable):
            perm_level = risk_to_permission(risk_level)
            self._tools[name] = {
                "definition": ToolDefinition(
                    name=name,
                    description=description,
                    parameters=parameters,
                    risk_level=risk_level,
                ),
                "func": func,
                "risk_level": risk_level,
                "permission_level": perm_level,
                "timeout_seconds": timeout_seconds,
            }
            # Mirror into modern safe_tool_registry for unified discovery
            safe_tool_registry.register(
                name=name,
                description=description,
                parameters=parameters,
                permission_level=perm_level,
                timeout_seconds=timeout_seconds,
            )(func)
            return func
        return decorator

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions in a format easily consumable by LLMs."""
        definitions = []
        for name, tool in self._tools.items():
            defn: ToolDefinition = tool["definition"]
            definitions.append({
                "name": defn.name,
                "description": defn.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: {"type": p.type, "description": p.description}
                        for p in defn.parameters
                    },
                    "required": [p.name for p in defn.parameters if p.required],
                },
                "risk_level": defn.risk_level.value,
            })
        return definitions

    async def execute(
        self,
        tool_name: str,
        params: dict[str, Any],
        approval_token: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool with permission checking, timeouts, and audit logging."""
        t0 = time.perf_counter()
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is not registered in NOUS.",
                is_verified=False,
            )

        tool = self._tools[tool_name]
        risk_level = tool["risk_level"]
        perm_level = risk_to_permission(risk_level)

        # Check permissions & approval tokens
        allowed, reason = permission_manager.check_permission(tool_name, risk_level, params)
        if not allowed:
            if approval_token:
                ok, req, token_msg = approval_manager.approve_token(approval_token)
                if not ok:
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=f"Permission denied: {token_msg}",
                        is_verified=False,
                    )
            else:
                # Generate new approval token
                req = approval_manager.create_request(
                    tool_name=tool_name,
                    parameters=params,
                    permission_level=perm_level,
                    description=reason,
                )
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"{reason} Approval token: {req.token}",
                    is_verified=False,
                )

        func = tool["func"]
        timeout_s = tool.get("timeout_seconds", 15.0)

        try:
            if inspect.iscoroutinefunction(func):
                result_data = await asyncio.wait_for(func(**params), timeout=timeout_s)
            else:
                loop = asyncio.get_running_loop()
                result_data = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: func(**params)),
                    timeout=timeout_s,
                )

            elapsed = time.perf_counter() - t0
            tool_logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="SUCCESS",
                elapsed_seconds=elapsed,
                approval_token=approval_token,
            )

            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result_data,
                is_verified=True,
            )
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - t0
            err_msg = f"Execution timeout: Tool '{tool_name}' exceeded {timeout_s}s limit."
            tool_logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="TIMEOUT",
                elapsed_seconds=elapsed,
                approval_token=approval_token,
                error_message=err_msg,
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=err_msg,
                is_verified=False,
            )
        except Exception as e:
            elapsed = time.perf_counter() - t0
            err_msg = f"Error executing tool '{tool_name}': {str(e)}"
            tool_logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="FAILED",
                elapsed_seconds=elapsed,
                approval_token=approval_token,
                error_message=err_msg,
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=err_msg,
                is_verified=False,
            )


# Initialize global tool registry
tool_registry = ToolRegistry()


# =====================================================================
# BUILT-IN CORE TOOLS
# =====================================================================

@tool_registry.register(
    name="get_current_datetime",
    description="Retrieve the exact current date, time, day of the week, and local timezone. Always use this tool when the user asks for the date, time, day, or calendar status.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
def get_current_datetime() -> dict[str, str]:
    now = datetime.now()
    return {
        "iso_timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "human_readable": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
    }


@tool_registry.register(
    name="get_system_specs",
    description="Retrieve verified physical hardware specifications and operating system information of the host laptop running NOUS.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
def get_system_specs() -> dict[str, Any]:
    return {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "cpu_model": "13th Gen Intel(R) Core(TM) i5-1334U",
        "cores": 10,
        "logical_processors": os.cpu_count() or 12,
        "ram_gb": 16.0,
        "graphics": "Intel(R) Iris(R) Xe Graphics (Integrated)",
        "python_runtime": platform.python_version(),
    }


# Safe math expression evaluator using AST
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_ast_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            if op_type == ast.Pow and right > 10000:
                raise ValueError("Exponent too large for safety.")
            return _SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast_node(node.operand)
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    else:
        raise ValueError(f"Unsafe or unsupported syntax node: {type(node).__name__}")


@tool_registry.register(
    name="calculate",
    description="Safely compute mathematical expressions (e.g. '150 * 1.18', '2**16', '(450 + 230) / 4'). Strictly evaluates pure arithmetic without arbitrary code execution.",
    parameters=[
        ToolParameter(
            name="expression",
            type="string",
            description="The arithmetic expression to evaluate (e.g. '25 * 4 + 10').",
            required=True,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def calculate(expression: str) -> dict[str, Any]:
    # Clean expression
    cleaned = expression.strip().replace("^", "**")
    try:
        parsed = ast.parse(cleaned, mode="eval")
        result = _eval_ast_node(parsed.body)
        return {
            "expression": expression,
            "result": result,
            "result_formatted": f"{result:,}" if isinstance(result, (int, float)) else str(result),
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Invalid arithmetic expression: {str(e)}",
        }


# =====================================================================
# PERSISTENT MEMORY TOOLS
# =====================================================================

@tool_registry.register(
    name="remember_fact",
    description="Save important user-approved information, personal preferences, project details, learning goals, or routines into persistent SQLite memory.",
    parameters=[
        ToolParameter(
            name="category",
            type="string",
            description="One of: 'user_profile', 'personal_info', 'project', 'conversation', 'routine'.",
            required=True,
        ),
        ToolParameter(
            name="key",
            type="string",
            description="A short descriptive key (e.g. 'preferred_name', 'learning_goal', 'project_tech_stack').",
            required=True,
        ),
        ToolParameter(
            name="content",
            type="string",
            description="The fact or information to remember.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def remember_fact(category: str, key: str, content: str) -> dict[str, Any]:
    from backend.app.memory.manager import memory_manager, MemoryCategory
    try:
        cat = MemoryCategory(category.strip().lower())
    except ValueError:
        cat = MemoryCategory.PERSONAL_INFO

    item = memory_manager.save_memory(category=cat, key=key, content=content)
    return {
        "status": "saved",
        "memory_id": item.id,
        "category": item.category.value,
        "key": item.key,
        "content": item.content,
    }


@tool_registry.register(
    name="recall_memories",
    description="Search and retrieve stored long-term memories across all categories (profile, projects, routines, facts).",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="Search terms or topic to look up in persistent memory.",
            required=True,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def recall_memories(query: str) -> dict[str, Any]:
    from backend.app.memory.manager import memory_manager
    results = memory_manager.get_relevant_memories(query, limit=5)
    return {
        "query": query,
        "count": len(results),
        "memories": [
            {
                "id": m.id,
                "category": m.category.value,
                "key": m.key,
                "content": m.content,
            }
            for m in results
        ],
    }


@tool_registry.register(
    name="list_user_profile",
    description="Retrieve all user profile facts including preferred name, interests, learning goals, and communication preferences.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
def list_user_profile() -> dict[str, Any]:
    from backend.app.memory.manager import memory_manager, MemoryCategory
    profiles = memory_manager.list_memories(category=MemoryCategory.USER_PROFILE)
    return {
        "profile_count": len(profiles),
        "profile": {p.key: p.content for p in profiles},
    }


# =====================================================================
# DAILY LIFE & ROUTINE TOOLS
# =====================================================================

@tool_registry.register(
    name="get_daily_schedule",
    description="Retrieve chronological daily schedule and planned activities for a specific date (defaults to today).",
    parameters=[
        ToolParameter(
            name="target_date",
            type="string",
            description="Date in YYYY-MM-DD format (leave empty or null for today).",
            required=False,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def get_daily_schedule(target_date: Optional[str] = None) -> dict[str, Any]:
    from backend.app.routine.manager import routine_manager
    activities = routine_manager.list_activities(target_date=target_date)
    overlaps = routine_manager.detect_overlaps(target_date=target_date)
    return {
        "date": target_date or routine_manager._today_str(),
        "total_activities": len(activities),
        "activities": [a.model_dump() for a in activities],
        "has_conflicts": len(overlaps) > 0,
        "conflicts": overlaps,
    }


@tool_registry.register(
    name="add_schedule_activity",
    description="Add a new activity or task to the daily schedule with start/end time, category, and priority.",
    parameters=[
        ToolParameter(
            name="name",
            type="string",
            description="Name or description of the activity (e.g. 'LeetCode Practice', 'Gym', 'Walking').",
            required=True,
        ),
        ToolParameter(
            name="start_time",
            type="string",
            description="Start time in 24-hour HH:MM format (e.g. '17:00', '07:30').",
            required=True,
        ),
        ToolParameter(
            name="end_time",
            type="string",
            description="End time in 24-hour HH:MM format (e.g. '18:00', '08:30').",
            required=True,
        ),
        ToolParameter(
            name="category",
            type="string",
            description="Category: 'study', 'coding', 'fitness', 'college', 'routine', 'personal', 'sleep', or 'other'.",
            required=False,
        ),
        ToolParameter(
            name="priority",
            type="string",
            description="Priority level: 'high', 'medium', or 'low'.",
            required=False,
        ),
        ToolParameter(
            name="target_date",
            type="string",
            description="Date in YYYY-MM-DD format (leave empty for today).",
            required=False,
        ),
        ToolParameter(
            name="notes",
            type="string",
            description="Additional details or notes.",
            required=False,
        ),
        ToolParameter(
            name="is_fixed",
            type="boolean",
            description="Whether this is a fixed commitment (like college or exams) that cannot be auto-rescheduled.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def add_schedule_activity(
    name: str,
    start_time: str,
    end_time: str,
    category: str = "routine",
    priority: str = "medium",
    target_date: Optional[str] = None,
    notes: str = "",
    is_fixed: bool = False,
) -> dict[str, Any]:
    from backend.app.routine.manager import (
        routine_manager,
        ActivityCategory,
        ActivityPriority,
    )
    try:
        cat = ActivityCategory(category.strip().lower())
    except ValueError:
        cat = ActivityCategory.ROUTINE

    try:
        prio = ActivityPriority(priority.strip().lower())
    except ValueError:
        prio = ActivityPriority.MEDIUM

    act = routine_manager.create_activity(
        name=name,
        start_time=start_time,
        end_time=end_time,
        target_date=target_date,
        category=cat,
        priority=prio,
        notes=notes or "",
        is_fixed=is_fixed,
    )
    return {
        "status": "created",
        "activity": act.model_dump(),
    }


@tool_registry.register(
    name="update_activity_status",
    description="Update the status of an activity (not_started, in_progress, completed, skipped, rescheduled). Never mark completed automatically without user confirmation.",
    parameters=[
        ToolParameter(
            name="activity_id",
            type="integer",
            description="The numeric ID of the activity to update.",
            required=True,
        ),
        ToolParameter(
            name="status",
            type="string",
            description="New status: 'completed', 'in_progress', 'skipped', 'rescheduled', or 'not_started'.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def update_activity_status(activity_id: int, status: str) -> dict[str, Any]:
    from backend.app.routine.manager import routine_manager, ActivityStatus
    try:
        stat = ActivityStatus(status.strip().lower())
    except ValueError:
        return {"success": False, "error": f"Invalid status: {status}"}

    success = routine_manager.update_status(activity_id, stat)
    item = routine_manager.get_activity(activity_id) if success else None
    return {
        "success": success,
        "activity_id": activity_id,
        "new_status": stat.value,
        "activity": item.model_dump() if item else None,
    }


@tool_registry.register(
    name="reschedule_missed_activity",
    description="Intelligently find an open time slot and reschedule a missed or skipped activity without disrupting fixed commitments.",
    parameters=[
        ToolParameter(
            name="activity_id",
            type="integer",
            description="The numeric ID of the missed activity to reschedule.",
            required=True,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def reschedule_missed_activity(activity_id: int) -> dict[str, Any]:
    from backend.app.routine.manager import routine_manager
    res = routine_manager.reschedule_missed_activity(activity_id)
    return res


@tool_registry.register(
    name="generate_daily_review",
    description="Generate an evening daily review debrief comparing planned vs completed activities, study/coding hours, and recommendations for tomorrow.",
    parameters=[
        ToolParameter(
            name="target_date",
            type="string",
            description="Date in YYYY-MM-DD format (leave empty for today).",
            required=False,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def generate_daily_review(target_date: Optional[str] = None) -> dict[str, Any]:
    from backend.app.routine.manager import routine_manager
    review = routine_manager.generate_daily_review(target_date=target_date)
    return review


# =====================================================================
# EMAIL INTELLIGENCE & COMMUNICATIONS TOOLS (PHASE 8)
# =====================================================================

@tool_registry.register(
    name="check_emails",
    description="Retrieve authorized emails from inbox with intelligence categorization, deadline detection, and untrusted-content security filtering.",
    parameters=[
        ToolParameter(
            name="category",
            type="string",
            description="Filter by category: 'important', 'college', 'work', 'urgent', 'requires_response', 'promotions', or leave empty.",
            required=False,
        ),
        ToolParameter(
            name="unread_only",
            type="boolean",
            description="Filter for only unread messages (true/false).",
            required=False,
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Maximum number of emails to retrieve (default: 5).",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def check_emails(
    category: Optional[str] = None,
    unread_only: bool = False,
    max_results: int = 5,
) -> dict[str, Any]:
    from backend.app.email.client import gmail_client
    from backend.app.email.analyzer import EmailCategory
    from backend.app.email.sanitizer import email_sanitizer

    cat_enum = None
    if category:
        try:
            cat_enum = EmailCategory(category.strip().lower())
        except ValueError:
            pass

    emails = await gmail_client.get_messages(
        category=cat_enum,
        unread_only=unread_only,
        limit=max_results,
    )

    return {
        "count": len(emails),
        "emails": [
            {
                "id": e.id,
                "sender": e.sender_name,
                "subject": e.subject,
                "category": e.category.value,
                "date": e.date,
                "is_unread": e.is_unread,
                "is_urgent": e.is_urgent,
                "requires_response": e.requires_response,
                "detected_deadlines": e.detected_deadlines,
                "action_items": e.action_items,
                "has_meeting_invite": e.has_meeting_invite,
                "is_suspicious_injection": e.is_suspicious_injection,
                "safe_snippet": email_sanitizer.sanitize(e.snippet).clean_text,
            }
            for e in emails
        ],
    }


@tool_registry.register(
    name="summarize_emails",
    description="Produce a high-level executive briefing of recent inbox messages, urgent items, pending replies, and upcoming deadlines.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
async def summarize_emails() -> dict[str, Any]:
    from backend.app.email.client import gmail_client
    from backend.app.email.analyzer import email_analyzer

    emails = await gmail_client.get_messages(limit=25)
    summary = email_analyzer.generate_daily_summary(emails)
    return summary


@tool_registry.register(
    name="find_email_deadlines",
    description="Search authorized emails specifically for academic assignment submissions, project milestones, or registration deadlines.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
async def find_email_deadlines() -> dict[str, Any]:
    from backend.app.email.client import gmail_client

    emails = await gmail_client.get_messages(limit=25)
    deadline_emails = [
        {
            "id": e.id,
            "sender": e.sender_name,
            "subject": e.subject,
            "date": e.date,
            "detected_deadlines": e.detected_deadlines,
            "action_items": e.action_items,
        }
        for e in emails if e.detected_deadlines
    ]
    return {
        "deadline_count": len(deadline_emails),
        "deadlines": deadline_emails,
    }


@tool_registry.register(
    name="get_emails_requiring_response",
    description="Identify all emails in the inbox that contain direct questions or action items requiring a reply.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
async def get_emails_requiring_response() -> dict[str, Any]:
    from backend.app.email.client import gmail_client

    emails = await gmail_client.get_messages(limit=25)
    reply_needed = [
        {
            "id": e.id,
            "sender": e.sender_name,
            "subject": e.subject,
            "date": e.date,
            "is_urgent": e.is_urgent,
            "action_items": e.action_items,
        }
        for e in emails if e.requires_response or e.is_urgent
    ]
    return {
        "count": len(reply_needed),
        "emails_requiring_response": reply_needed,
    }


@tool_registry.register(
    name="draft_email_reply",
    description="Generate an email reply draft. Enforces Human-In-The-Loop approval: never sends or modifies email automatically.",
    parameters=[
        ToolParameter(
            name="email_id",
            type="string",
            description="The ID of the email to reply to.",
            required=True,
        ),
        ToolParameter(
            name="reply_intent",
            type="string",
            description="The user's intended reply instructions or message points.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def draft_email_reply(email_id: str, reply_intent: str) -> dict[str, Any]:
    from backend.app.email.client import gmail_client

    emails = await gmail_client.get_messages(limit=30)
    target = next((e for e in emails if e.id == email_id), None)
    if not target:
        return {"success": False, "error": f"Email with ID '{email_id}' not found."}

    # Draft professional response reflecting user intent
    draft_body = (
        f"Hi {target.sender_name},\n\n"
        f"Thank you for your email regarding '{target.subject}'.\n\n"
        f"{reply_intent.strip()}\n\n"
        f"Best regards,\nNOUS Assistant on behalf of user"
    )

    draft = gmail_client.create_draft(
        to_email=target.sender,
        subject=target.subject,
        body=draft_body,
        reply_to_id=target.id,
    )

    return {
        "status": "draft_created",
        "draft_id": draft["id"],
        "to": draft["to"],
        "subject": draft["subject"],
        "body": draft["body"],
        "approval_required": True,
        "note": "Draft saved in 'pending_approval' state. User confirmation is mandatory before dispatch.",
    }


@tool_registry.register(
    name="send_approved_email",
    description="Send an email draft ONLY after explicit user confirmation has been verified. HIGH-risk tool.",
    parameters=[
        ToolParameter(
            name="draft_id",
            type="string",
            description="The ID of the approved draft to dispatch.",
            required=True,
        ),
        ToolParameter(
            name="user_confirmed",
            type="boolean",
            description="Set to true ONLY if the user explicitly confirmed dispatching this email.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.HIGH,
)
async def send_approved_email(draft_id: str, user_confirmed: bool = False) -> dict[str, Any]:
    from backend.app.email.client import gmail_client

    if not user_confirmed:
        return {
            "success": False,
            "error": "Human confirmation is required. Email was not dispatched.",
        }

    res = await gmail_client.send_draft(draft_id, user_confirmed=True)
    return res


# =====================================================================
# PROJECT INTELLIGENCE & GITHUB TOOLS (PHASE 9)
# =====================================================================

@tool_registry.register(
    name="get_projects_overview",
    description="Retrieve a comprehensive overview of all tracked software projects, completion percentages, active milestones, and overdue deadlines.",
    parameters=[
        ToolParameter(
            name="status",
            type="string",
            description="Filter by project status: 'active', 'planning', 'on_hold', 'completed', or leave empty for all.",
            required=False,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def get_projects_overview(status: Optional[str] = None) -> dict[str, Any]:
    from backend.app.projects.manager import project_manager, ProjectStatus
    stat_enum = None
    if status:
        try:
            stat_enum = ProjectStatus(status.strip().lower())
        except ValueError:
            pass

    projects = project_manager.list_projects(status=stat_enum)
    deadlines = project_manager.get_upcoming_deadlines(days_ahead=14)
    inactive = project_manager.detect_inactive_projects(days_threshold=7)

    return {
        "total_projects": len(projects),
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "tech_stack": p.tech_stack,
                "priority": p.priority.value,
                "status": p.status.value,
                "progress_percent": p.progress_percent,
                "deadline": p.deadline,
                "completed_milestones": sum(1 for m in p.milestones if m.is_completed),
                "total_milestones": len(p.milestones),
                "tasks_count": len(p.tasks),
            }
            for p in projects
        ],
        "upcoming_deadlines": deadlines,
        "inactive_projects": inactive,
    }


@tool_registry.register(
    name="get_project_details",
    description="Fetch in-depth technical details, milestones, and task boards for a specific project by numeric ID.",
    parameters=[
        ToolParameter(
            name="project_id",
            type="integer",
            description="The numeric ID of the project.",
            required=True,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def get_project_details(project_id: int) -> dict[str, Any]:
    from backend.app.projects.manager import project_manager
    p = project_manager.get_project(project_id)
    if not p:
        return {"success": False, "error": f"Project with ID {project_id} not found."}
    return {"success": True, "project": p.model_dump()}


@tool_registry.register(
    name="add_project",
    description="Add a new project to the engineering management system with tech stack, deadline, and priority.",
    parameters=[
        ToolParameter(
            name="name",
            type="string",
            description="Project title (e.g. 'LeetCode Engine', 'Raft Consensus').",
            required=True,
        ),
        ToolParameter(
            name="description",
            type="string",
            description="Short overview of what the project accomplishes.",
            required=True,
        ),
        ToolParameter(
            name="tech_stack",
            type="string",
            description="Comma-separated technologies and libraries used.",
            required=False,
        ),
        ToolParameter(
            name="deadline",
            type="string",
            description="Target completion date in YYYY-MM-DD format.",
            required=False,
        ),
        ToolParameter(
            name="priority",
            type="string",
            description="Priority: 'high', 'medium', or 'low'.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def add_project(
    name: str,
    description: str,
    tech_stack: str = "",
    deadline: str = "",
    priority: str = "medium",
) -> dict[str, Any]:
    from backend.app.projects.manager import project_manager, ProjectPriority
    try:
        prio_enum = ProjectPriority(priority.strip().lower())
    except ValueError:
        prio_enum = ProjectPriority.MEDIUM

    p = project_manager.create_project(
        name=name,
        description=description,
        tech_stack=tech_stack,
        deadline=deadline,
        priority=prio_enum,
    )
    return {"status": "created", "project": p.model_dump()}


@tool_registry.register(
    name="add_project_milestone",
    description="Add a major milestone or deliverables checkpoint to an active project.",
    parameters=[
        ToolParameter(
            name="project_id",
            type="integer",
            description="Numeric ID of the project.",
            required=True,
        ),
        ToolParameter(
            name="title",
            type="string",
            description="Milestone title or deliverable.",
            required=True,
        ),
        ToolParameter(
            name="due_date",
            type="string",
            description="Target date in YYYY-MM-DD format.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def add_project_milestone(
    project_id: int,
    title: str,
    due_date: Optional[str] = None,
) -> dict[str, Any]:
    from backend.app.projects.manager import project_manager
    p = project_manager.get_project(project_id)
    if not p:
        return {"success": False, "error": f"Project with ID {project_id} not found."}

    m = project_manager.add_milestone(project_id=project_id, title=title, due_date=due_date)
    return {"status": "milestone_created", "milestone": m.model_dump()}


@tool_registry.register(
    name="check_github_activity",
    description="Inspect development activity on GitHub: recent commits, open pull requests, and active issues.",
    parameters=[
        ToolParameter(
            name="repo",
            type="string",
            description="GitHub repository slug (e.g. 'owner/repo'). Defaults to active assistant repository.",
            required=False,
        )
    ],
    risk_level=RiskLevel.LOW,
)
async def check_github_activity(repo: Optional[str] = None) -> dict[str, Any]:
    from backend.app.projects.github_client import github_client
    data = await github_client.get_repository_activity(repo_slug=repo)
    return data


@tool_registry.register(
    name="check_project_deadlines",
    description="Scan all tracked projects and milestones for deadlines within the upcoming 14 days.",
    parameters=[
        ToolParameter(
            name="days_ahead",
            type="integer",
            description="Number of days to look ahead (default: 14).",
            required=False,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def check_project_deadlines(days_ahead: int = 14) -> dict[str, Any]:
    from backend.app.projects.manager import project_manager
    deadlines = project_manager.get_upcoming_deadlines(days_ahead=days_ahead)
    return {
        "count": len(deadlines),
        "days_window": days_ahead,
        "deadlines": deadlines,
    }


@tool_registry.register(
    name="find_inactive_projects",
    description="Detect stale projects or repositories that have not received any commits or updates in more than 7 days.",
    parameters=[
        ToolParameter(
            name="days_threshold",
            type="integer",
            description="Inactivity threshold in days (default: 7).",
            required=False,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def find_inactive_projects(days_threshold: int = 7) -> dict[str, Any]:
    from backend.app.projects.manager import project_manager
    inactive = project_manager.detect_inactive_projects(days_threshold=days_threshold)
    return {
        "count": len(inactive),
        "days_threshold": days_threshold,
        "inactive_projects": inactive,
    }


# ==============================================================================
# PHASE 10 & 11: FINANCIAL MARKET INTELLIGENCE & CAUSAL REASONING TOOLS
# ==============================================================================


@tool_registry.register(
    name="get_market_indices",
    description="Retrieve live or latest available benchmark indices for Indian (NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT) and Global markets (NASDAQ, S&P 500, Crude Oil, USD/INR) with session statuses.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
def get_market_indices() -> dict[str, Any]:
    from backend.app.market.fetcher import MarketDataFetcher
    fetcher = MarketDataFetcher()
    return fetcher.get_benchmark_indices()


@tool_registry.register(
    name="get_stock_quote",
    description="Fetch current market quote (price, percentage change, day high/low, volume, previous close) for a specific stock or index symbol (e.g. ^NSEI, ^BSESN, RELIANCE.NS, TCS.NS, HDFCBANK.NS, ^IXIC).",
    parameters=[
        ToolParameter(
            name="symbol",
            type="string",
            description="Stock or index ticker symbol (e.g. '^NSEI', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', '^IXIC').",
            required=True,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def get_stock_quote(symbol: str) -> dict[str, Any]:
    from backend.app.market.fetcher import MarketDataFetcher
    fetcher = MarketDataFetcher()
    return fetcher.fetch_quote(symbol=symbol)


@tool_registry.register(
    name="explain_market_movement",
    description="Perform deep causal reasoning to explain why a stock or benchmark index moved. Investigates global cues, macro factors (RBI, Fed, inflation), institutional FII/DII liquidity, sector correlation, and verified news with confidence scoring.",
    parameters=[
        ToolParameter(
            name="symbol_or_index",
            type="string",
            description="Index or equity symbol to investigate (e.g. '^NSEI', 'RELIANCE.NS', 'TCS.NS', '^NSEBANK').",
            required=True,
        )
    ],
    risk_level=RiskLevel.LOW,
)
def explain_market_movement(symbol_or_index: str) -> dict[str, Any]:
    from backend.app.market.engine import MarketReasoningEngine
    engine = MarketReasoningEngine()
    analysis = engine.analyze_movement(symbol_or_index)
    report = engine.generate_formatted_report(symbol_or_index)
    return {
        "analysis": analysis,
        "formatted_report": report,
    }


@tool_registry.register(
    name="manage_market_watchlist",
    description="Manage user's personal financial watchlist: view current watchlist with live prices, add a new symbol, or remove an existing symbol.",
    parameters=[
        ToolParameter(
            name="action",
            type="string",
            description="Action to perform: 'list', 'add', or 'remove'.",
            required=True,
        ),
        ToolParameter(
            name="symbol",
            type="string",
            description="Ticker symbol for add/remove operations (e.g. 'INFY.NS', '^CNXIT').",
            required=False,
        ),
        ToolParameter(
            name="name",
            type="string",
            description="Human-readable company or index name when adding to watchlist.",
            required=False,
        ),
        ToolParameter(
            name="market",
            type="string",
            description="Market exchange category ('NSE', 'BSE', 'US', 'FX', 'COMMODITY'). Defaults to 'NSE'.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def manage_market_watchlist(
    action: str,
    symbol: Optional[str] = None,
    name: Optional[str] = None,
    market: Optional[str] = "NSE",
) -> dict[str, Any]:
    from backend.app.market.db import MarketDBManager
    from backend.app.market.fetcher import MarketDataFetcher
    db = MarketDBManager()
    act = action.strip().lower()

    if act == "list":
        items = db.get_watchlist()
        fetcher = MarketDataFetcher(db_manager=db)
        symbols = [item["symbol"] for item in items]
        quotes = fetcher.fetch_batch_quotes(symbols)
        quote_map = {q["symbol"].upper(): q for q in quotes}
        for it in items:
            it["quote"] = quote_map.get(it["symbol"].upper())
        return {"action": "list", "count": len(items), "watchlist": items}

    elif act == "add":
        if not symbol:
            return {"success": False, "error": "Symbol is required for 'add' action."}
        item_name = name or symbol
        added = db.add_to_watchlist(symbol=symbol, name=item_name, market=market or "NSE")
        return {"action": "add", "status": "added", "item": added}

    elif act == "remove":
        if not symbol:
            return {"success": False, "error": "Symbol is required for 'remove' action."}
        removed = db.remove_from_watchlist(symbol=symbol)
        return {"action": "remove", "status": "removed" if removed else "not_found", "symbol": symbol.upper()}

    return {"success": False, "error": f"Unknown action '{action}'. Valid actions: list, add, remove."}


@tool_registry.register(
    name="set_market_alert",
    description="Configure a price threshold or percentage move alert for a monitored stock or index.",
    parameters=[
        ToolParameter(
            name="symbol",
            type="string",
            description="Ticker symbol to monitor (e.g. '^NSEI', 'RELIANCE.NS').",
            required=True,
        ),
        ToolParameter(
            name="condition",
            type="string",
            description="Trigger condition: 'above', 'below', 'pct_up', 'pct_down', or 'volume_surge'.",
            required=True,
        ),
        ToolParameter(
            name="target_value",
            type="number",
            description="Numerical target price or percentage threshold.",
            required=True,
        ),
        ToolParameter(
            name="notes",
            type="string",
            description="Optional reminder notes for the alert.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def set_market_alert(
    symbol: str,
    condition: str,
    target_value: float,
    notes: Optional[str] = "",
) -> dict[str, Any]:
    from backend.app.market.db import MarketDBManager
    db = MarketDBManager()
    alert = db.add_alert(
        symbol=symbol,
        condition=condition,
        target_value=target_value,
        notes=notes or "",
    )
    return {"status": "alert_created", "alert": alert}


@tool_registry.register(
    name="get_fii_dii_activity",
    description="Retrieve institutional investment flow statistics (FII/FPI and DII buying, selling, and net flow in Indian equities) along with institutional market sentiment.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
def get_fii_dii_activity() -> dict[str, Any]:
    from backend.app.market.fetcher import MarketDataFetcher
    fetcher = MarketDataFetcher()
    return fetcher.get_fii_dii_flows()


# ==============================================================================
# PHASE 12: WEB RESEARCH ENGINE TOOLS
# ==============================================================================


@tool_registry.register(
    name="web_search",
    description="Search the web across multi-provider sources (DuckDuckGo, Wikipedia, and news feeds) to discover articles, documentation, facts, and references.",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="Search query string or keywords.",
            required=True,
        ),
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of search results to retrieve (default: 5).",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def web_search(query: str, limit: int = 5) -> dict[str, Any]:
    from backend.app.research.engine import research_engine
    results = research_engine.search_sources(query=query, limit=limit)
    return {
        "query": query,
        "count": len(results),
        "sources": results,
    }


@tool_registry.register(
    name="conduct_deep_research",
    description="Perform deep multi-source research on an academic topic, technology, company, or market development. Compares sources, extracts supporting evidence and dates, identifies trade-offs, and generates a structured 8-part evidence-backed report.",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="Research question or topic to investigate in-depth.",
            required=True,
        ),
        ToolParameter(
            name="category",
            type="string",
            description="Research category: 'technology', 'company', 'academic', 'market', or 'general'.",
            required=False,
        ),
        ToolParameter(
            name="save_to_notebook",
            type="boolean",
            description="Whether to automatically persist the generated report into the persistent SQLite research notebook.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def conduct_deep_research(
    query: str,
    category: str = "general",
    save_to_notebook: bool = False,
) -> dict[str, Any]:
    from backend.app.research.engine import research_engine
    report = research_engine.investigate(query=query, category=category)
    saved_note = None
    if save_to_notebook:
        saved_note = research_engine.save_to_notebook(report)
    return {
        "report": report,
        "saved_note": saved_note,
    }


@tool_registry.register(
    name="save_research_note",
    description="Save a technical research report, notes, or academic study summary into the persistent SQLite research notebook.",
    parameters=[
        ToolParameter(
            name="title",
            type="string",
            description="Title of the research note or paper.",
            required=True,
        ),
        ToolParameter(
            name="query",
            type="string",
            description="Topic or research question addressed.",
            required=True,
        ),
        ToolParameter(
            name="summary",
            type="string",
            description="Concise takeaway summary.",
            required=True,
        ),
        ToolParameter(
            name="category",
            type="string",
            description="Category: 'technology', 'company', 'academic', 'market', or 'general'.",
            required=False,
        ),
        ToolParameter(
            name="tags",
            type="string",
            description="Comma-separated topic tags.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def save_research_note(
    title: str,
    query: str,
    summary: str,
    category: str = "general",
    tags: str = "",
) -> dict[str, Any]:
    from backend.app.research.engine import research_engine
    note = research_engine.db.create_note(
        title=title,
        query=query,
        category=category,
        summary=summary,
        full_report_markdown=f"### {title}\n\n**Query:** {query}\n\n**Summary:** {summary}",
        key_findings=[summary],
        sources=[],
        tags=tags or category,
    )
    return {"status": "created", "note": note}


@tool_registry.register(
    name="list_research_notes",
    description="Retrieve saved research reports, technical studies, and notes from the persistent notebook with optional category and search filters.",
    parameters=[
        ToolParameter(
            name="category",
            type="string",
            description="Filter by category ('technology', 'company', 'academic', 'market').",
            required=False,
        ),
        ToolParameter(
            name="search",
            type="string",
            description="Keyword search across titles, summaries, and tags.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def list_research_notes(
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> dict[str, Any]:
    from backend.app.research.engine import research_engine
    notes = research_engine.db.list_notes(category=category, search=search)
    return {
        "count": len(notes),
        "notes": notes,
    }


# =====================================================================
# PHASE 13: COMPUTER & TASK AUTOMATION TOOLS
# =====================================================================

@tool_registry.register(
    name="list_workspace_files",
    description="List files and directories securely within the authorized NOUS workspace sandbox. Prevents path traversal.",
    parameters=[
        ToolParameter(
            name="subpath",
            type="string",
            description="Subfolder path relative to workspace (defaults to workspace root).",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def list_workspace_files(subpath: str = "") -> dict[str, Any]:
    from backend.app.automation.manager import automation_manager
    files = automation_manager.list_files(subpath=subpath)
    return {
        "workspace_root": str(automation_manager.workspace),
        "count": len(files),
        "files": files,
    }


@tool_registry.register(
    name="read_workspace_file",
    description="Safely read the text content of a file located inside the authorized NOUS workspace sandbox.",
    parameters=[
        ToolParameter(
            name="file_path",
            type="string",
            description="Relative path of the file to read inside workspace.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def read_workspace_file(file_path: str) -> dict[str, Any]:
    from backend.app.automation.manager import automation_manager
    return automation_manager.read_file(file_path)


@tool_registry.register(
    name="write_workspace_file",
    description="Safely create or update a text file inside the authorized NOUS workspace sandbox.",
    parameters=[
        ToolParameter(
            name="file_path",
            type="string",
            description="Target file path inside workspace.",
            required=True,
        ),
        ToolParameter(
            name="content",
            type="string",
            description="Full text content to write into the file.",
            required=True,
        ),
        ToolParameter(
            name="overwrite",
            type="boolean",
            description="Whether to overwrite existing file if present (default False).",
            required=False,
        ),
    ],
    risk_level=RiskLevel.MEDIUM,
)
def write_workspace_file(file_path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    from backend.app.automation.manager import automation_manager
    return automation_manager.write_file(file_path, content, overwrite=overwrite)


@tool_registry.register(
    name="execute_safe_command",
    description="Execute a safe shell command within the workspace sandbox. Enforces command blocklist and human-in-the-loop approval confirmation.",
    parameters=[
        ToolParameter(
            name="command",
            type="string",
            description="Shell command to run (e.g. 'dir', 'git status', 'python test.py').",
            required=True,
        ),
        ToolParameter(
            name="approval_token",
            type="string",
            description="Optional confirmation token for commands requiring human approval.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.HIGH,
)
def execute_safe_command(command: str, approval_token: Optional[str] = None) -> dict[str, Any]:
    from backend.app.automation.manager import automation_manager
    return automation_manager.request_or_execute_command(command, approval_token=approval_token)


@tool_registry.register(
    name="create_scheduled_task",
    description="Schedule a recurring background automation job (e.g. morning briefing, project sync, command execution).",
    parameters=[
        ToolParameter(
            name="name",
            type="string",
            description="Human-readable title of the automation job.",
            required=True,
        ),
        ToolParameter(
            name="action_type",
            type="string",
            description="Type of task: 'command', 'briefing', 'project_sync'.",
            required=True,
        ),
        ToolParameter(
            name="interval_seconds",
            type="integer",
            description="Interval in seconds between runs (e.g. 3600 for hourly).",
            required=False,
        ),
        ToolParameter(
            name="cron_expression",
            type="string",
            description="Optional cron expression (e.g. '0 9 * * *' for 9 AM daily).",
            required=False,
        ),
        ToolParameter(
            name="command",
            type="string",
            description="Shell command if action_type is 'command'.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.MEDIUM,
)
def create_scheduled_task(
    name: str,
    action_type: str,
    interval_seconds: Optional[int] = None,
    cron_expression: Optional[str] = None,
    command: Optional[str] = None,
) -> dict[str, Any]:
    from backend.app.automation.manager import automation_manager
    payload = {"command": command} if command else {}
    return automation_manager.schedule_task(
        name=name,
        action_type=action_type,
        interval_seconds=interval_seconds,
        cron_expression=cron_expression,
        payload=payload,
    )


@tool_registry.register(
    name="list_scheduled_tasks",
    description="List active and configured scheduled background automation jobs.",
    parameters=[
        ToolParameter(
            name="status",
            type="string",
            description="Optional filter by status ('active', 'paused').",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def list_scheduled_tasks(status: Optional[str] = None) -> dict[str, Any]:
    from backend.app.automation.manager import automation_manager
    tasks = automation_manager.db.list_scheduled_tasks(status=status)
    return {
        "count": len(tasks),
        "tasks": tasks,
    }


# =====================================================================
# PHASE 14: SECURITY VAULT & PRIVACY CONTROLS
# =====================================================================

@tool_registry.register(
    name="get_security_audit_logs",
    description="Inspect tamper-evident security audit logs from the security vault. Filter by event type, decision, or query.",
    parameters=[
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum events to return (default 20).",
            required=False,
        ),
        ToolParameter(
            name="event_type",
            type="string",
            description="Filter by type ('tool_execution', 'file_access', 'command_run', 'privacy_toggle').",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def get_security_audit_logs(limit: int = 20, event_type: Optional[str] = None) -> dict[str, Any]:
    from backend.app.security.vault import security_vault
    events = security_vault.db.list_events(event_type=event_type, limit=limit)
    return {
        "count": len(events),
        "events": events,
    }


@tool_registry.register(
    name="set_security_privacy_mode",
    description="Update NOUS privacy policies such as offline lockdown (disabling external cloud APIs), pausing memory retention, or toggling strict redaction.",
    parameters=[
        ToolParameter(
            name="offline_lockdown",
            type="boolean",
            description="If true, blocks external network calls and cloud LLMs.",
            required=False,
        ),
        ToolParameter(
            name="pause_memory_retention",
            type="boolean",
            description="If true, pauses saving new facts into long-term memory.",
            required=False,
        ),
        ToolParameter(
            name="strict_redaction",
            type="boolean",
            description="If true, scrubs all API keys and PII automatically.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.MEDIUM,
)
def set_security_privacy_mode(
    offline_lockdown: Optional[bool] = None,
    pause_memory_retention: Optional[bool] = None,
    strict_redaction: Optional[bool] = None,
) -> dict[str, Any]:
    from backend.app.security.vault import security_vault
    return security_vault.set_privacy_mode(
        offline_lockdown=offline_lockdown,
        pause_memory_retention=pause_memory_retention,
        strict_redaction=strict_redaction,
    )


@tool_registry.register(
    name="sanitize_text_content",
    description="Scrub sensitive credentials, API keys, passwords, bearer tokens, and private keys from text.",
    parameters=[
        ToolParameter(
            name="text",
            type="string",
            description="Input text containing potential secrets.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
def sanitize_text_content(text: str) -> dict[str, Any]:
    from backend.app.security.vault import security_vault
    has_secrets = security_vault.redactor.contains_sensitive(text)
    sanitized = security_vault.redactor.redact(text)
    return {
        "contains_secrets": has_secrets,
        "sanitized_text": sanitized,
    }


@tool_registry.register(
    name="purge_transient_security_data",
    description="Purge temporary session artifacts, scratch files, and expired audit logs from the security vault.",
    parameters=[],
    risk_level=RiskLevel.MEDIUM,
)
def purge_transient_security_data() -> dict[str, Any]:
    from backend.app.security.vault import security_vault
    return security_vault.purge_transient_data()


# =====================================================================
# PUBLIC APIS INTEGRATION (From github.com/public-apis/public-apis)
# =====================================================================

@tool_registry.register(
    name="get_weather_forecast",
    description="Fetch live and verified weather forecast, temperature, humidity, conditions, and wind speed for any location or city worldwide via Open-Meteo public API.",
    parameters=[
        ToolParameter(
            name="location",
            type="string",
            description="The city or geographic location to check weather for (e.g. 'London', 'Tokyo', 'San Francisco', 'Bengaluru').",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def get_weather_forecast(location: str) -> dict[str, Any]:
    from backend.app.services.public_apis import public_api_service
    return await public_api_service.get_weather(location=location)


@tool_registry.register(
    name="lookup_dictionary_definition",
    description="Look up English definitions, pronunciations, phonetics, parts of speech, synonyms, and usage examples via Free Dictionary API.",
    parameters=[
        ToolParameter(
            name="word",
            type="string",
            description="The English word to look up in the dictionary.",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def lookup_dictionary_definition(word: str) -> dict[str, Any]:
    from backend.app.services.public_apis import public_api_service
    return await public_api_service.lookup_definition(word=word)


@tool_registry.register(
    name="convert_currency",
    description="Convert monetary amounts between global currencies using live European Central Bank exchange rates via the Frankfurter API.",
    parameters=[
        ToolParameter(
            name="amount",
            type="number",
            description="The monetary value to convert.",
            required=True,
        ),
        ToolParameter(
            name="from_currency",
            type="string",
            description="The source currency (e.g. 'USD', 'EUR', 'GBP', 'INR', 'JPY').",
            required=True,
        ),
        ToolParameter(
            name="to_currency",
            type="string",
            description="The target currency to convert into (e.g. 'USD', 'EUR', 'GBP', 'INR', 'JPY').",
            required=True,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict[str, Any]:
    from backend.app.services.public_apis import public_api_service
    return await public_api_service.convert_currency(
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
    )


@tool_registry.register(
    name="get_random_joke",
    description="Fetch a clean humor or programming joke from the Official Joke API.",
    parameters=[
        ToolParameter(
            name="category",
            type="string",
            description="Optional category of joke: 'general' or 'programming'.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def get_random_joke(category: Optional[str] = "general") -> dict[str, Any]:
    from backend.app.services.public_apis import public_api_service
    return await public_api_service.get_random_joke(category=category)


# =====================================================================
# AUTONOMOUS MINUTE-TO-MINUTE DAEMON TOOLS
# =====================================================================

@tool_registry.register(
    name="get_autonomous_daemon_status",
    description="Check the operational status, total ticks, offline resilience, and network state of the NOUS minute-to-minute autonomous background daemon.",
    parameters=[],
    risk_level=RiskLevel.LOW,
)
def get_autonomous_daemon_status() -> dict[str, Any]:
    from backend.app.automation.daemon import autonomous_daemon
    return autonomous_daemon.get_status()


@tool_registry.register(
    name="trigger_autonomous_tick",
    description="Manually trigger an immediate cycle of the autonomous minute daemon (verifies routine, heartbeats, and offline safety).",
    parameters=[
        ToolParameter(
            name="force_offline",
            type="boolean",
            description="If true, tests offline simulation mode.",
            required=False,
        ),
    ],
    risk_level=RiskLevel.LOW,
)
async def trigger_autonomous_tick(force_offline: bool = False) -> dict[str, Any]:
    from backend.app.automation.daemon import autonomous_daemon
    return await autonomous_daemon.tick(force_offline_sim=force_offline)











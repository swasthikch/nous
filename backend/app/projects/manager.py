"""Project Intelligence & Engineering Management Engine for NOUS.

Coordinates:
- Structured project metadata, tech stacks, milestones, and task boards.
- Automated progress percentage calculation based on completed milestones & tasks.
- Proactive inactivity detection (flags stale repos with no recent commits).
- Upcoming milestone and project deadline extraction.
"""

import time
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.projects.db import get_projects_db, init_projects_database


class ProjectPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PLANNING = "planning"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class MilestoneItem(BaseModel):
    id: int
    project_id: int
    title: str
    due_date: str = ""
    is_completed: bool = False
    completed_at: Optional[float] = None
    notes: str = ""
    created_at: float


class ProjectTaskItem(BaseModel):
    id: int
    project_id: int
    title: str
    status: TaskStatus
    priority: str = "medium"
    created_at: float
    updated_at: float


class ProjectItem(BaseModel):
    id: int
    name: str
    description: str = ""
    tech_stack: str = ""
    repo_url: str = ""
    start_date: str
    deadline: str = ""
    priority: ProjectPriority
    status: ProjectStatus
    progress_percent: int = 0
    notes: str = ""
    created_at: float
    updated_at: float
    milestones: list[MilestoneItem] = Field(default_factory=list)
    tasks: list[ProjectTaskItem] = Field(default_factory=list)


class ProjectManager:
    """Manages active repositories, milestone trackers, task pipelines, and deadlines."""

    def __init__(self):
        init_projects_database()
        self._ensure_seed_projects()

    def _ensure_seed_projects(self):
        """Seed realistic projects if database is empty."""
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM projects;")
            count = cursor.fetchone()[0]

            if count == 0:
                self._seed_default_data()

    def _seed_default_data(self):
        today = date.today().strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        next_month = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        # 1. NOUS Personal Assistant Project
        p1 = self.create_project(
            name="NOUS — Personal AI Assistant",
            description="Modular personal AI assistant inspired by JARVIS with hybrid routing and persistent memory.",
            tech_stack="Python, FastAPI, Ollama, Qwen 2.5 3B, SQLite, HTML5, Vanilla JS",
            repo_url="https://github.com/nous-assistant/core",
            start_date="2026-11-01",
            deadline=next_month,
            priority=ProjectPriority.HIGH,
            status=ProjectStatus.ACTIVE,
            notes="Active development. Phase 8 (Email) completed, working on Phase 9 (Project Intelligence).",
        )
        self.add_milestone(p1.id, "Phase 1-6: Voice, Brain, Memory & Hardware Calibration", due_date=today)
        m1 = self.list_milestones(p1.id)[0]
        self.toggle_milestone(m1.id)  # Mark completed

        self.add_milestone(p1.id, "Phase 7-8: Routine Life Timeline & Email Intelligence", due_date=today)
        m2 = self.list_milestones(p1.id)[1]
        self.toggle_milestone(m2.id)  # Mark completed

        self.add_milestone(p1.id, "Phase 9-11: Project Tracking & Live Stock Market Reasoning", due_date=next_week)
        self.add_milestone(p1.id, "Phase 12-16: Research Engine, PWA & End-to-End Verification", due_date=next_month)

        self.add_task(p1.id, "Build GitHub REST API client with PR and issue summaries", priority="high")
        self.add_task(p1.id, "Implement project health monitor with stale repo detection", priority="medium")

        # 2. Distributed Systems Lab Project
        p2 = self.create_project(
            name="Distributed Systems: Raft Consensus Engine",
            description="Implementation of the Raft leader election and log replication consensus protocol.",
            tech_stack="Go, RPC, Docker, Linux",
            repo_url="https://github.com/student/raft-consensus-lab",
            start_date="2026-10-15",
            deadline=next_week,
            priority=ProjectPriority.HIGH,
            status=ProjectStatus.ACTIVE,
            notes="Milestone 2 due Friday Nov 21 at 5:00 PM.",
        )
        self.add_milestone(p2.id, "Milestone 1: Leader Election & Heartbeats", due_date=today)
        m_raft1 = self.list_milestones(p2.id)[0]
        self.toggle_milestone(m_raft1.id)

        self.add_milestone(p2.id, "Milestone 2: Log Replication & Network Partition Handling", due_date=next_week)

        # 3. Inactive Project (to test stale project detection)
        p3 = self.create_project(
            name="Legacy Compiler Parser (Archived Prototype)",
            description="Recursive descent AST parser prototype.",
            tech_stack="C++, CMake",
            repo_url="https://github.com/student/legacy-compiler-ast",
            start_date="2026-08-01",
            deadline="2026-09-01",
            priority=ProjectPriority.LOW,
            status=ProjectStatus.ON_HOLD,
            notes="No recent activity in 30+ days.",
        )
        old_time = time.time() - (25 * 86400)
        with get_projects_db() as conn:
            conn.cursor().execute(
                "UPDATE projects SET updated_at = ?, created_at = ? WHERE id = ?;",
                (old_time, old_time, p3.id)
            )

    # ==============================================================
    # PROJECT CRUD
    # ==============================================================
    def create_project(
        self,
        name: str,
        description: str = "",
        tech_stack: str = "",
        repo_url: str = "",
        start_date: Optional[str] = None,
        deadline: str = "",
        priority: ProjectPriority = ProjectPriority.MEDIUM,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        notes: str = "",
    ) -> ProjectItem:
        """Create a new tracked project."""
        s_date = start_date or date.today().strftime("%Y-%m-%d")
        now = time.time()

        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (
                    name, description, tech_stack, repo_url, start_date, deadline,
                    priority, status, progress_percent, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                name.strip(), description.strip(), tech_stack.strip(), repo_url.strip(),
                s_date, deadline.strip(), priority.value, status.value, 0, notes.strip(), now, now
            ))
            project_id = cursor.lastrowid

        return self.get_project(project_id)  # type: ignore

    def get_project(self, project_id: int) -> Optional[ProjectItem]:
        """Fetch project details along with milestones and task items."""
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?;", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None

            milestones = self.list_milestones(project_id)
            tasks = self.list_tasks(project_id)

            return ProjectItem(
                id=row["id"],
                name=row["name"],
                description=row["description"] or "",
                tech_stack=row["tech_stack"] or "",
                repo_url=row["repo_url"] or "",
                start_date=row["start_date"],
                deadline=row["deadline"] or "",
                priority=ProjectPriority(row["priority"]),
                status=ProjectStatus(row["status"]),
                progress_percent=row["progress_percent"],
                notes=row["notes"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                milestones=milestones,
                tasks=tasks,
            )

    def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        priority: Optional[ProjectPriority] = None,
    ) -> list[ProjectItem]:
        """Retrieve projects filtered by status and priority."""
        query = "SELECT id FROM projects WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status.value)
        if priority:
            query += " AND priority = ?"
            params.append(priority.value)

        query += " ORDER BY updated_at DESC;"

        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self.get_project(r["id"]) for r in rows if r["id"]]  # type: ignore

    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tech_stack: Optional[str] = None,
        repo_url: Optional[str] = None,
        deadline: Optional[str] = None,
        priority: Optional[ProjectPriority] = None,
        status: Optional[ProjectStatus] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Edit project fields."""
        curr = self.get_project(project_id)
        if not curr:
            return False

        now = time.time()
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, tech_stack = ?, repo_url = ?,
                    deadline = ?, priority = ?, status = ?, notes = ?, updated_at = ?
                WHERE id = ?;
            """, (
                name if name is not None else curr.name,
                description if description is not None else curr.description,
                tech_stack if tech_stack is not None else curr.tech_stack,
                repo_url if repo_url is not None else curr.repo_url,
                deadline if deadline is not None else curr.deadline,
                priority.value if priority is not None else curr.priority.value,
                status.value if status is not None else curr.status.value,
                notes if notes is not None else curr.notes,
                now,
                project_id,
            ))
            return cursor.rowcount > 0

    def delete_project(self, project_id: int) -> bool:
        """Remove project and all cascading milestones & tasks."""
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?;", (project_id,))
            return cursor.rowcount > 0

    # ==============================================================
    # MILESTONES & TASKS
    # ==============================================================
    def add_milestone(
        self,
        project_id: int,
        title: str,
        due_date: Optional[str] = None,
        notes: str = "",
    ) -> MilestoneItem:
        """Add a trackable milestone to a project and recalculate progress."""
        now = time.time()
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO milestones (project_id, title, due_date, is_completed, notes, created_at)
                VALUES (?, ?, ?, 0, ?, ?);
            """, (project_id, title.strip(), due_date or "", notes.strip(), now))
            mid = cursor.lastrowid

        self._recalculate_progress(project_id)
        return self.get_milestone(mid)  # type: ignore

    def get_milestone(self, milestone_id: int) -> Optional[MilestoneItem]:
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM milestones WHERE id = ?;", (milestone_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return MilestoneItem(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                due_date=row["due_date"] or "",
                is_completed=bool(row["is_completed"]),
                completed_at=row["completed_at"],
                notes=row["notes"] or "",
                created_at=row["created_at"],
            )

    def toggle_milestone(self, milestone_id: int) -> bool:
        """Toggle milestone completion status and update project progress."""
        m = self.get_milestone(milestone_id)
        if not m:
            return False

        new_val = 0 if m.is_completed else 1
        comp_time = time.time() if new_val == 1 else None

        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE milestones
                SET is_completed = ?, completed_at = ?
                WHERE id = ?;
            """, (new_val, comp_time, milestone_id))

        self._recalculate_progress(m.project_id)
        return True

    def list_milestones(self, project_id: Optional[int] = None) -> list[MilestoneItem]:
        query = "SELECT * FROM milestones"
        params = []
        if project_id:
            query += " WHERE project_id = ?"
            params.append(project_id)
        query += " ORDER BY due_date ASC, id ASC;"

        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                MilestoneItem(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    due_date=r["due_date"] or "",
                    is_completed=bool(r["is_completed"]),
                    completed_at=r["completed_at"],
                    notes=r["notes"] or "",
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def add_task(self, project_id: int, title: str, priority: str = "medium") -> ProjectTaskItem:
        """Add a specific todo item to the project."""
        now = time.time()
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_tasks (project_id, title, status, priority, created_at, updated_at)
                VALUES (?, ?, 'todo', ?, ?, ?);
            """, (project_id, title.strip(), priority, now, now))
            tid = cursor.lastrowid

        return self.get_task(tid)  # type: ignore

    def get_task(self, task_id: int) -> Optional[ProjectTaskItem]:
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_tasks WHERE id = ?;", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ProjectTaskItem(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                status=TaskStatus(row["status"]),
                priority=row["priority"] or "medium",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def update_task_status(self, task_id: int, status: TaskStatus) -> bool:
        now = time.time()
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE project_tasks
                SET status = ?, updated_at = ?
                WHERE id = ?;
            """, (status.value, now, task_id))
            return cursor.rowcount > 0

    def list_tasks(self, project_id: int) -> list[ProjectTaskItem]:
        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_tasks WHERE project_id = ? ORDER BY id ASC;", (project_id,))
            rows = cursor.fetchall()
            return [
                ProjectTaskItem(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    status=TaskStatus(r["status"]),
                    priority=r["priority"] or "medium",
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def _recalculate_progress(self, project_id: int):
        """Compute progress percentage based on completed milestones."""
        milestones = self.list_milestones(project_id)
        if not milestones:
            return

        total = len(milestones)
        completed = sum(1 for m in milestones if m.is_completed)
        pct = int(round((completed / total) * 100))

        with get_projects_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET progress_percent = ?, updated_at = ?
                WHERE id = ?;
            """, (pct, time.time(), project_id))

    # ==============================================================
    # PROACTIVE INTELLIGENCE: INACTIVITY & UPCOMING DEADLINES
    # ==============================================================
    def detect_inactive_projects(self, days_threshold: int = 7) -> list[dict]:
        """Identify projects with no updates or activity in more than N days."""
        cutoff = time.time() - (days_threshold * 86400)
        inactive = []

        all_projects = self.list_projects()
        for p in all_projects:
            if p.status in [ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD]:
                if p.updated_at < cutoff:
                    days_idle = int((time.time() - p.updated_at) / 86400)
                    inactive.append({
                        "id": p.id,
                        "name": p.name,
                        "status": p.status.value,
                        "days_inactive": days_idle,
                        "last_updated": datetime.fromtimestamp(p.updated_at).strftime("%Y-%m-%d"),
                        "suggestion": f"Project has been idle for {days_idle} days. Consider scheduling a focus block or archiving.",
                    })
        return inactive

    def get_upcoming_deadlines(self, days_ahead: int = 14) -> list[dict]:
        """Find project and milestone deadlines within the next N days."""
        today = date.today()
        limit_date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        deadlines = []

        # 1. Project deadlines
        for p in self.list_projects():
            if p.deadline and today_str <= p.deadline <= limit_date and p.status != ProjectStatus.COMPLETED:
                deadlines.append({
                    "type": "project_deadline",
                    "project_id": p.id,
                    "project_name": p.name,
                    "title": f"Final Project Deadline: {p.name}",
                    "due_date": p.deadline,
                    "priority": p.priority.value,
                })

        # 2. Milestone deadlines
        all_milestones = self.list_milestones()
        for m in all_milestones:
            if m.due_date and today_str <= m.due_date <= limit_date and not m.is_completed:
                proj = self.get_project(m.project_id)
                proj_name = proj.name if proj else f"Project #{m.project_id}"
                deadlines.append({
                    "type": "milestone_deadline",
                    "project_id": m.project_id,
                    "project_name": proj_name,
                    "title": m.title,
                    "due_date": m.due_date,
                    "priority": "high",
                })

        deadlines.sort(key=lambda x: x["due_date"])
        return deadlines

    def get_projects_overview(self) -> dict:
        """Executive summary of projects, health metrics, and pending tasks."""
        projects = self.list_projects()
        active = [p for p in projects if p.status == ProjectStatus.ACTIVE]
        deadlines = self.get_upcoming_deadlines(days_ahead=14)
        inactive = self.detect_inactive_projects(days_threshold=7)

        return {
            "total_projects": len(projects),
            "active_projects": len(active),
            "upcoming_deadlines_count": len(deadlines),
            "inactive_projects_count": len(inactive),
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "tech_stack": p.tech_stack,
                    "priority": p.priority.value,
                    "status": p.status.value,
                    "progress_percent": p.progress_percent,
                    "deadline": p.deadline,
                    "milestones_count": len(p.milestones),
                }
                for p in projects
            ],
            "upcoming_deadlines": deadlines,
            "inactive_projects": inactive,
        }


project_manager = ProjectManager()

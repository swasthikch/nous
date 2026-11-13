"""FastAPI Router for NOUS Project Intelligence & GitHub Telemetry.

Provides REST endpoints for:
- Project lifecycle tracking (tech stack, milestones, deadlines, progress %).
- GitHub commit velocity, PR tracking, and issue management.
- Proactive inactivity detection & deadline monitoring.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.projects.manager import (
    project_manager,
    ProjectPriority,
    ProjectStatus,
    TaskStatus,
)
from backend.app.projects.github_client import github_client

router = APIRouter(prefix="/api/projects", tags=["Project Intelligence"])


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str = ""
    tech_stack: str = ""
    repo_url: str = ""
    start_date: Optional[str] = None
    deadline: str = ""
    priority: ProjectPriority = ProjectPriority.MEDIUM
    status: ProjectStatus = ProjectStatus.ACTIVE
    notes: str = ""


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    repo_url: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[ProjectPriority] = None
    status: Optional[ProjectStatus] = None
    notes: Optional[str] = None


class AddMilestoneRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    due_date: Optional[str] = ""
    notes: str = ""


class AddTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    priority: str = "medium"


class UpdateTaskStatusRequest(BaseModel):
    status: TaskStatus


# ==============================================================
# PROJECT CRUD
# ==============================================================

@router.get("")
async def list_projects(
    status: Optional[ProjectStatus] = Query(None),
    priority: Optional[ProjectPriority] = Query(None),
):
    """Retrieve all projects with milestone completion percentages."""
    projects = project_manager.list_projects(status=status, priority=priority)
    return {
        "count": len(projects),
        "projects": [p.model_dump() for p in projects],
    }


@router.post("", status_code=201)
async def create_project(req: CreateProjectRequest):
    """Create a new project in SQLite project store."""
    proj = project_manager.create_project(
        name=req.name,
        description=req.description,
        tech_stack=req.tech_stack,
        repo_url=req.repo_url,
        start_date=req.start_date,
        deadline=req.deadline,
        priority=req.priority,
        status=req.status,
        notes=req.notes,
    )
    return {"status": "created", "project": proj.model_dump()}


@router.get("/health")
async def get_projects_health():
    """Retrieve health overview: active projects, upcoming deadlines, and idle repositories."""
    return project_manager.get_projects_overview()


@router.get("/github/activity")
async def get_github_activity(repo: Optional[str] = Query(None)):
    """Fetch recent commits, pull requests, and issues from GitHub."""
    activity = await github_client.get_repository_activity(repo_slug=repo)
    return activity


@router.get("/{project_id}")
async def get_project(project_id: int):
    """Fetch project details along with milestones, tasks, and progress."""
    proj = project_manager.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return proj.model_dump()


@router.put("/{project_id}")
async def update_project(project_id: int, req: UpdateProjectRequest):
    """Edit project fields."""
    success = project_manager.update_project(
        project_id=project_id,
        name=req.name,
        description=req.description,
        tech_stack=req.tech_stack,
        repo_url=req.repo_url,
        deadline=req.deadline,
        priority=req.priority,
        status=req.status,
        notes=req.notes,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or update failed.")
    return {"status": "updated", "project": project_manager.get_project(project_id).model_dump()}  # type: ignore


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """Delete project and associated milestones & tasks."""
    success = project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"status": "deleted", "project_id": project_id}


# ==============================================================
# MILESTONES & TASKS
# ==============================================================

@router.post("/{project_id}/milestones", status_code=201)
async def add_milestone(project_id: int, req: AddMilestoneRequest):
    """Add a milestone to a project and update progress."""
    proj = project_manager.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    m = project_manager.add_milestone(
        project_id=project_id,
        title=req.title,
        due_date=req.due_date,
        notes=req.notes,
    )
    return {"status": "milestone_created", "milestone": m.model_dump()}


@router.patch("/{project_id}/milestones/{milestone_id}/toggle")
async def toggle_milestone(project_id: int, milestone_id: int):
    """Toggle milestone completion state and recalculate project progress."""
    success = project_manager.toggle_milestone(milestone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Milestone not found.")
    m = project_manager.get_milestone(milestone_id)
    proj = project_manager.get_project(project_id)
    return {
        "status": "toggled",
        "milestone": m.model_dump(),  # type: ignore
        "project_progress_percent": proj.progress_percent if proj else 0,
    }


@router.post("/{project_id}/tasks", status_code=201)
async def add_task(project_id: int, req: AddTaskRequest):
    """Add a task to a project."""
    proj = project_manager.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    t = project_manager.add_task(project_id=project_id, title=req.title, priority=req.priority)
    return {"status": "task_created", "task": t.model_dump()}


@router.patch("/{project_id}/tasks/{task_id}/status")
async def update_task_status(project_id: int, task_id: int, req: UpdateTaskStatusRequest):
    """Update task status (todo, in_progress, done)."""
    success = project_manager.update_task_status(task_id=task_id, status=req.status)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found.")
    t = project_manager.get_task(task_id)
    return {"status": "task_updated", "task": t.model_dump()}  # type: ignore

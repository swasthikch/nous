"""NOUS Project Intelligence & Engineering Management Package."""

from backend.app.projects.db import get_projects_db, init_projects_database
from backend.app.projects.github_client import github_client
from backend.app.projects.manager import (
    project_manager,
    ProjectItem,
    MilestoneItem,
    ProjectTaskItem,
    ProjectPriority,
    ProjectStatus,
    TaskStatus,
)

__all__ = [
    "get_projects_db",
    "init_projects_database",
    "github_client",
    "project_manager",
    "ProjectItem",
    "MilestoneItem",
    "ProjectTaskItem",
    "ProjectPriority",
    "ProjectStatus",
    "TaskStatus",
]

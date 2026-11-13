"""FastAPI REST Router for NOUS Computer & Task Automation (Phase 13)."""

from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.automation.manager import automation_manager
from backend.app.automation.security import SecurityError

logger = logging.getLogger("nous.api.automation")

router = APIRouter(prefix="/api/automation", tags=["Task Automation"])


# ---------------- SCHEMAS ----------------


class FileReadRequest(BaseModel):
    file_path: str = Field(..., description="Path relative to workspace")


class FileWriteRequest(BaseModel):
    file_path: str = Field(..., description="Target path inside workspace")
    content: str = Field(..., description="Text content to write")
    overwrite: bool = Field(False, description="Whether to overwrite existing file")


class FileDeleteRequest(BaseModel):
    file_path: str = Field(..., description="Path to delete within workspace")


class CommandExecuteRequest(BaseModel):
    command: str = Field(..., description="Shell command to run")
    approval_token: Optional[str] = Field(None, description="Confirmation token for risky commands")


class TaskCreateRequest(BaseModel):
    name: str = Field(..., description="Task title")
    action_type: str = Field(..., description="Type of action: command, briefing, project_sync")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds")
    cron_expression: Optional[str] = Field(None, description="Cron string")
    command: Optional[str] = Field(None, description="Command payload if action_type is command")


# ---------------- FILE ENDPOINTS ----------------


@router.get("/files")
async def list_workspace_files(path: str = Query("", description="Subdirectory path")) -> dict[str, Any]:
    """List files in the authorized workspace sandbox."""
    try:
        files = automation_manager.list_files(subpath=path)
        return {
            "workspace_root": str(automation_manager.workspace),
            "current_path": path,
            "count": len(files),
            "files": files,
        }
    except SecurityError as se:
        raise HTTPException(status_code=403, detail=str(se))
    except (FileNotFoundError, NotADirectoryError) as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except Exception as e:
        logger.error("Failed to list files: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/read")
async def read_workspace_file(req: FileReadRequest) -> dict[str, Any]:
    """Read contents of a file within the workspace."""
    try:
        return automation_manager.read_file(req.file_path)
    except SecurityError as se:
        raise HTTPException(status_code=403, detail=str(se))
    except (FileNotFoundError, IsADirectoryError) as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except Exception as e:
        logger.error("Failed to read file %s: %s", req.file_path, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/write")
async def write_workspace_file(req: FileWriteRequest) -> dict[str, Any]:
    """Write or update a file within the workspace."""
    try:
        return automation_manager.write_file(req.file_path, req.content, overwrite=req.overwrite)
    except SecurityError as se:
        raise HTTPException(status_code=403, detail=str(se))
    except FileExistsError as fe:
        raise HTTPException(status_code=409, detail=str(fe))
    except Exception as e:
        logger.error("Failed to write file %s: %s", req.file_path, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files")
async def delete_workspace_file(req: FileDeleteRequest) -> dict[str, Any]:
    """Delete a file or empty directory within the workspace."""
    try:
        return automation_manager.delete_file(req.file_path)
    except SecurityError as se:
        raise HTTPException(status_code=403, detail=str(se))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except Exception as e:
        logger.error("Failed to delete file %s: %s", req.file_path, e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- COMMAND EXECUTION ENDPOINT ----------------


@router.post("/execute")
async def execute_command(req: CommandExecuteRequest) -> dict[str, Any]:
    """Execute a controlled shell command with blocklist and approval gate."""
    try:
        return automation_manager.request_or_execute_command(
            req.command,
            approval_token=req.approval_token,
        )
    except Exception as e:
        logger.error("Failed command execution '%s': %s", req.command, e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- SCHEDULED TASK ENDPOINTS ----------------


@router.get("/tasks")
async def list_tasks(status: Optional[str] = Query(None)) -> dict[str, Any]:
    """List scheduled automation tasks."""
    try:
        tasks = automation_manager.db.list_scheduled_tasks(status=status)
        return {"count": len(tasks), "tasks": tasks}
    except Exception as e:
        logger.error("Failed to list scheduled tasks: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def create_task(req: TaskCreateRequest) -> dict[str, Any]:
    """Register a new recurring automation task."""
    try:
        payload = {"command": req.command} if req.command else {}
        task = automation_manager.schedule_task(
            name=req.name,
            action_type=req.action_type,
            interval_seconds=req.interval_seconds,
            cron_expression=req.cron_expression,
            payload=payload,
        )
        return {"status": "created", "task": task}
    except Exception as e:
        logger.error("Failed to create task %s: %s", req.name, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str) -> dict[str, Any]:
    """Delete a scheduled automation task."""
    try:
        deleted = automation_manager.db.delete_scheduled_task(task_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "deleted", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete task %s: %s", task_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/run")
async def run_task_now(task_id: str) -> dict[str, Any]:
    """Execute a scheduled task immediately."""
    try:
        return automation_manager.run_scheduled_task_now(task_id)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except Exception as e:
        logger.error("Failed to run task %s: %s", task_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_execution_history(limit: int = Query(50)) -> dict[str, Any]:
    """Retrieve command execution audit history."""
    try:
        history = automation_manager.db.list_execution_history(limit=limit)
        return {"count": len(history), "history": history}
    except Exception as e:
        logger.error("Failed to get execution history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

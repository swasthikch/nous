"""FastAPI Router for NOUS Daily Routine & Life Management.

Provides REST endpoints for schedule management, activity tracking,
conflict detection, intelligent rescheduling, and evening daily reviews.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.routine.manager import (
    routine_manager,
    ActivityCategory,
    ActivityPriority,
    ActivityStatus,
)

router = APIRouter(prefix="/api/routine", tags=["Routine & Daily Life"])


class CreateActivityRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    target_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: ActivityCategory = ActivityCategory.ROUTINE
    priority: ActivityPriority = ActivityPriority.MEDIUM
    status: ActivityStatus = ActivityStatus.NOT_STARTED
    notes: str = ""
    is_fixed: bool = False
    recurrence: str = "none"


class UpdateActivityRequest(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    category: Optional[ActivityCategory] = None
    priority: Optional[ActivityPriority] = None
    status: Optional[ActivityStatus] = None
    notes: Optional[str] = None
    is_fixed: Optional[bool] = None


class UpdateStatusRequest(BaseModel):
    status: ActivityStatus


@router.get("/schedule")
async def get_schedule(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    category: Optional[ActivityCategory] = Query(None),
    status: Optional[ActivityStatus] = Query(None),
):
    """Retrieve full chronological schedule and detected overlaps for the specified date."""
    target_date = date or routine_manager._today_str()
    activities = routine_manager.list_activities(
        target_date=target_date, category=category, status=status
    )
    overlaps = routine_manager.detect_overlaps(target_date=target_date)

    return {
        "date": target_date,
        "count": len(activities),
        "activities": [a.model_dump() for a in activities],
        "conflicts": overlaps,
        "has_conflicts": len(overlaps) > 0,
    }


@router.post("/activity", status_code=201)
async def create_activity(req: CreateActivityRequest):
    """Add a new scheduled activity."""
    act = routine_manager.create_activity(
        name=req.name,
        start_time=req.start_time,
        end_time=req.end_time,
        target_date=req.target_date,
        category=req.category,
        priority=req.priority,
        status=req.status,
        notes=req.notes,
        is_fixed=req.is_fixed,
        recurrence=req.recurrence,
    )
    return {"status": "created", "activity": act.model_dump()}


@router.get("/activity/{activity_id}")
async def get_activity(activity_id: int):
    """Fetch details of an individual activity."""
    act = routine_manager.get_activity(activity_id)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return act.model_dump()


@router.put("/activity/{activity_id}")
async def update_activity(activity_id: int, req: UpdateActivityRequest):
    """Edit activity fields."""
    success = routine_manager.update_activity(
        activity_id=activity_id,
        name=req.name,
        start_time=req.start_time,
        end_time=req.end_time,
        category=req.category,
        priority=req.priority,
        status=req.status,
        notes=req.notes,
        is_fixed=req.is_fixed,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found or update failed.")
    return {"status": "updated", "activity": routine_manager.get_activity(activity_id).model_dump()}  # type: ignore


@router.patch("/activity/{activity_id}/status")
async def update_activity_status(activity_id: int, req: UpdateStatusRequest):
    """Update activity completion status.
    
    Strict anti-hallucination constraint: Never auto-completed without explicit user action.
    """
    success = routine_manager.update_status(activity_id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return {
        "status": "status_updated",
        "activity_id": activity_id,
        "new_status": req.status.value,
        "activity": routine_manager.get_activity(activity_id).model_dump(),  # type: ignore
    }


@router.delete("/activity/{activity_id}")
async def delete_activity(activity_id: int):
    """Remove an activity from schedule."""
    success = routine_manager.delete_activity(activity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return {"status": "deleted", "activity_id": activity_id}


@router.post("/reschedule/{activity_id}")
async def reschedule_activity(activity_id: int):
    """Find a non-conflicting free time window and reschedule a missed activity."""
    res = routine_manager.reschedule_missed_activity(activity_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Rescheduling failed."))
    return res


@router.get("/review")
async def get_daily_review(date: Optional[str] = Query(None)):
    """Generate evening planned vs completed debrief, completion stats, and tomorrow's suggestions."""
    target_date = date or routine_manager._today_str()
    review = routine_manager.generate_daily_review(target_date)
    return review


@router.get("/free-slots")
async def get_free_slots(
    date: Optional[str] = Query(None),
    min_duration: int = Query(30, ge=15, le=360),
):
    """Retrieve open schedule gaps available for scheduling."""
    target_date = date or routine_manager._today_str()
    slots = routine_manager.find_free_slots(target_date, min_duration_mins=min_duration)
    return {"date": target_date, "free_slots": slots, "count": len(slots)}


@router.get("/meta")
async def get_routine_meta():
    """Retrieve available categories, priorities, and statuses."""
    return {
        "categories": [c.value for c in ActivityCategory],
        "priorities": [p.value for p in ActivityPriority],
        "statuses": [s.value for s in ActivityStatus],
    }

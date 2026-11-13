"""Daily Routine and Life Management Engine for NOUS.

Coordinates daily schedule creation, activity tracking, overlap detection,
intelligent rescheduling, study/coding hour metrics, and evening daily reviews.
"""

import time
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.app.routine.db import get_routine_db, init_routine_database


class ActivityCategory(str, Enum):
    STUDY = "study"
    CODING = "coding"
    FITNESS = "fitness"
    COLLEGE = "college"
    ROUTINE = "routine"
    PERSONAL = "personal"
    SLEEP = "sleep"
    OTHER = "other"


class ActivityPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActivityStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    RESCHEDULED = "rescheduled"


class ActivityItem(BaseModel):
    id: int
    name: str
    date: str                  # YYYY-MM-DD
    start_time: str            # HH:MM
    end_time: str              # HH:MM
    priority: ActivityPriority
    category: ActivityCategory
    status: ActivityStatus
    notes: str = ""
    is_fixed: bool = False     # Fixed commitments (e.g. College) cannot be moved automatically
    recurrence: str = "none"   # none, daily, weekdays, weekly
    created_at: float
    updated_at: float


class RoutineManager:
    """Core manager for activities, intelligent scheduling, and daily reviews."""

    def __init__(self):
        init_routine_database()

    def _today_str(self) -> str:
        return date.today().strftime("%Y-%m-%d")

    def _time_to_minutes(self, t_str: str) -> int:
        """Convert 'HH:MM' string to minutes since midnight."""
        try:
            parts = t_str.strip().split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return 0

    def _minutes_to_time(self, mins: int) -> str:
        """Convert minutes since midnight back to 'HH:MM' format."""
        h = (mins // 60) % 24
        m = mins % 60
        return f"{h:02d}:{m:02d}"

    def create_activity(
        self,
        name: str,
        start_time: str,
        end_time: str,
        target_date: Optional[str] = None,
        category: ActivityCategory = ActivityCategory.ROUTINE,
        priority: ActivityPriority = ActivityPriority.MEDIUM,
        status: ActivityStatus = ActivityStatus.NOT_STARTED,
        notes: str = "",
        is_fixed: bool = False,
        recurrence: str = "none",
    ) -> ActivityItem:
        """Add a new activity to the daily schedule."""
        d_str = target_date or self._today_str()
        now = time.time()

        with get_routine_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activities (
                    name, date, start_time, end_time, priority, category,
                    status, notes, is_fixed, recurrence, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                name.strip(), d_str, start_time.strip(), end_time.strip(),
                priority.value, category.value, status.value, notes.strip(),
                1 if is_fixed else 0, recurrence, now, now
            ))
            act_id = cursor.lastrowid

        return self.get_activity(act_id)  # type: ignore

    def get_activity(self, activity_id: int) -> Optional[ActivityItem]:
        """Fetch activity by ID."""
        with get_routine_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activities WHERE id = ?;", (activity_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_item(row)

    def _row_to_item(self, row) -> ActivityItem:
        return ActivityItem(
            id=row["id"],
            name=row["name"],
            date=row["date"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            priority=ActivityPriority(row["priority"]),
            category=ActivityCategory(row["category"]),
            status=ActivityStatus(row["status"]),
            notes=row["notes"] or "",
            is_fixed=bool(row["is_fixed"]),
            recurrence=row["recurrence"] or "none",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_activities(
        self,
        target_date: Optional[str] = None,
        category: Optional[ActivityCategory] = None,
        status: Optional[ActivityStatus] = None,
    ) -> list[ActivityItem]:
        """Retrieve activities sorted chronologically by start_time."""
        d_str = target_date or self._today_str()
        query = "SELECT * FROM activities WHERE date = ?"
        params: list[Any] = [d_str]

        if category:
            query += " AND category = ?"
            params.append(category.value)
        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY start_time ASC;"

        with get_routine_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_item(r) for r in rows]

    def update_status(self, activity_id: int, new_status: ActivityStatus) -> bool:
        """Update activity completion status.
        
        Strict rule: Never mark an activity completed automatically merely because
        time passed. Only mark completed upon user confirmation.
        """
        now = time.time()
        with get_routine_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE activities
                SET status = ?, updated_at = ?
                WHERE id = ?;
            """, (new_status.value, now, activity_id))
            return cursor.rowcount > 0

    def update_activity(
        self,
        activity_id: int,
        name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        priority: Optional[ActivityPriority] = None,
        category: Optional[ActivityCategory] = None,
        status: Optional[ActivityStatus] = None,
        notes: Optional[str] = None,
        is_fixed: Optional[bool] = None,
    ) -> bool:
        """Edit fields of an existing activity."""
        current = self.get_activity(activity_id)
        if not current:
            return False

        now = time.time()
        with get_routine_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE activities
                SET name = ?, start_time = ?, end_time = ?, priority = ?,
                    category = ?, status = ?, notes = ?, is_fixed = ?, updated_at = ?
                WHERE id = ?;
            """, (
                name if name is not None else current.name,
                start_time if start_time is not None else current.start_time,
                end_time if end_time is not None else current.end_time,
                priority.value if priority is not None else current.priority.value,
                category.value if category is not None else current.category.value,
                status.value if status is not None else current.status.value,
                notes if notes is not None else current.notes,
                (1 if is_fixed else 0) if is_fixed is not None else (1 if current.is_fixed else 0),
                now,
                activity_id
            ))
            return cursor.rowcount > 0

    def delete_activity(self, activity_id: int) -> bool:
        """Remove activity from schedule."""
        with get_routine_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activities WHERE id = ?;", (activity_id,))
            return cursor.rowcount > 0

    def detect_overlaps(self, target_date: Optional[str] = None) -> list[dict]:
        """Detect any conflicting time blocks on a given date."""
        activities = self.list_activities(target_date)
        overlaps = []

        for i in range(len(activities)):
            for j in range(i + 1, len(activities)):
                a1 = activities[i]
                a2 = activities[j]

                # Convert to minute intervals
                s1, e1 = self._time_to_minutes(a1.start_time), self._time_to_minutes(a1.end_time)
                s2, e2 = self._time_to_minutes(a2.start_time), self._time_to_minutes(a2.end_time)

                if max(s1, s2) < min(e1, e2):  # Overlap occurs
                    overlaps.append({
                        "activity_1": {"id": a1.id, "name": a1.name, "time": f"{a1.start_time}-{a1.end_time}"},
                        "activity_2": {"id": a2.id, "name": a2.name, "time": f"{a2.start_time}-{a2.end_time}"},
                        "conflict": f"{max(s1, s2)} to {min(e1, e2)} minutes",
                    })

        return overlaps

    def find_free_slots(self, target_date: Optional[str] = None, min_duration_mins: int = 30) -> list[dict]:
        """Identify available time blocks in the day between scheduled activities."""
        activities = self.list_activities(target_date)
        # Default day span: 07:00 (420 mins) to 23:00 (1380 mins)
        day_start = 420
        day_end = 1380

        occupied_intervals = []
        for a in activities:
            s = self._time_to_minutes(a.start_time)
            e = self._time_to_minutes(a.end_time)
            occupied_intervals.append((s, e))

        occupied_intervals.sort(key=lambda x: x[0])

        free_slots = []
        current = day_start

        for s, e in occupied_intervals:
            if s > current and (s - current) >= min_duration_mins:
                free_slots.append({
                    "start": self._minutes_to_time(current),
                    "end": self._minutes_to_time(s),
                    "duration_minutes": s - current,
                })
            current = max(current, e)

        if day_end > current and (day_end - current) >= min_duration_mins:
            free_slots.append({
                "start": self._minutes_to_time(current),
                "end": self._minutes_to_time(day_end),
                "duration_minutes": day_end - current,
            })

        return free_slots

    def reschedule_missed_activity(self, activity_id: int) -> dict:
        """Find an alternative free slot and reschedule a missed activity without disrupting fixed commitments."""
        act = self.get_activity(activity_id)
        if not act:
            return {"success": False, "error": "Activity not found."}

        dur_mins = self._time_to_minutes(act.end_time) - self._time_to_minutes(act.start_time)
        dur_mins = max(30, dur_mins)

        free_slots = self.find_free_slots(act.date, min_duration_mins=dur_mins)

        if not free_slots:
            # Check tomorrow
            tomorrow = (datetime.strptime(act.date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            free_slots = self.find_free_slots(tomorrow, min_duration_mins=dur_mins)
            target_date = tomorrow
        else:
            target_date = act.date

        if not free_slots:
            return {"success": False, "error": "No available free time slots found with sufficient duration."}

        # Select first available slot
        slot = free_slots[0]
        new_start = slot["start"]
        new_end_mins = self._time_to_minutes(new_start) + dur_mins
        new_end = self._minutes_to_time(new_end_mins)

        # Mark previous as rescheduled
        self.update_status(activity_id, ActivityStatus.RESCHEDULED)

        # Create new rescheduled instance
        new_act = self.create_activity(
            name=f"{act.name} (Rescheduled)",
            start_time=new_start,
            end_time=new_end,
            target_date=target_date,
            category=act.category,
            priority=act.priority,
            notes=f"Rescheduled from {act.date} {act.start_time}-{act.end_time}.",
        )

        return {
            "success": True,
            "rescheduled_from": {"date": act.date, "time": f"{act.start_time}-{act.end_time}"},
            "new_activity": new_act.model_dump(),
        }

    def generate_daily_review(self, target_date: Optional[str] = None) -> dict:
        """Produce planned vs completed evening debrief with stats and tomorrow's suggestions."""
        d_str = target_date or self._today_str()
        activities = self.list_activities(d_str)

        total = len(activities)
        completed = [a for a in activities if a.status == ActivityStatus.COMPLETED]
        in_progress = [a for a in activities if a.status == ActivityStatus.IN_PROGRESS]
        not_started = [a for a in activities if a.status == ActivityStatus.NOT_STARTED]
        skipped = [a for a in activities if a.status == ActivityStatus.SKIPPED]

        comp_rate = round((len(completed) / total * 100), 1) if total > 0 else 0.0

        # Calculate category hours
        coding_mins = sum(
            (self._time_to_minutes(a.end_time) - self._time_to_minutes(a.start_time))
            for a in completed if a.category == ActivityCategory.CODING
        )
        study_mins = sum(
            (self._time_to_minutes(a.end_time) - self._time_to_minutes(a.start_time))
            for a in completed if a.category in [ActivityCategory.STUDY, ActivityCategory.COLLEGE]
        )

        outstanding = [
            {"id": a.id, "name": a.name, "time": f"{a.start_time}-{a.end_time}", "priority": a.priority.value}
            for a in not_started + in_progress
        ]

        # Generate constructive suggestions
        suggestions = []
        if comp_rate >= 80.0:
            suggestions.append("Outstanding execution today! Maintained high consistency across planned goals.")
        elif comp_rate < 50.0 and total > 0:
            suggestions.append("Several planned blocks remained unfinished. Consider creating smaller, more realistic 45-minute focus intervals tomorrow.")

        if coding_mins > 0:
            suggestions.append(f"Logged {round(coding_mins / 60, 1)} hours of active coding practice.")
        if len(outstanding) > 0:
            suggestions.append(f"{len(outstanding)} task(s) can be rescheduled into tomorrow's free morning slots.")

        return {
            "date": d_str,
            "total_planned": total,
            "completed_count": len(completed),
            "completion_rate_percent": comp_rate,
            "coding_hours": round(coding_mins / 60, 2),
            "study_hours": round(study_mins / 60, 2),
            "completed_activities": [a.name for a in completed],
            "outstanding_tasks": outstanding,
            "skipped_tasks": [a.name for a in skipped],
            "suggestions": suggestions,
        }


routine_manager = RoutineManager()

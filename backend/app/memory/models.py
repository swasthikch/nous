"""Memory Domain Models and 5-Tier Taxonomy for NOUS.

Taxonomy:
1. Working Memory: Active conversation state, scratchpad, ephemeral variables.
2. Personal Memory: User identity, preferences, learning goals, lifestyle.
3. Project Memory: Codebase architectures, decisions, tech stacks, milestones.
4. Knowledge Memory: Extracted research papers, technical notes, documentation.
5. Episodic Memory: Historical timeline of major decisions, milestones, and events.
"""

from __future__ import annotations

from enum import Enum
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class MemoryTier(str, Enum):
    """The 5 primary operational memory tiers."""
    WORKING = "working"
    PERSONAL = "personal"
    PROJECT = "project"
    KNOWLEDGE = "knowledge"
    EPISODIC = "episodic"


class MemoryCategory(str, Enum):
    """Sub-categories for memory classification and backward compatibility."""
    USER_PROFILE = "user_profile"      # Identity, preferred name, learning goals
    PERSONAL_INFO = "personal_info"    # Habits, preferences, lifestyle
    PROJECT = "project"                # Active projects, milestones, tech stack
    CONVERSATION = "conversation"      # Key summaries, decisions, unfinished tasks
    ROUTINE = "routine"                # Schedules, habits, daily review
    KNOWLEDGE_NOTE = "knowledge_note"  # Extracted papers, docs, research notes
    EPISODIC_EVENT = "episodic_event"  # Milestone reached, past error, event


def category_to_tier(category: str | MemoryCategory) -> MemoryTier:
    """Map any subcategory to its parent 5-tier classification."""
    cat_str = category.value if isinstance(category, MemoryCategory) else str(category).lower().strip()
    if cat_str in ("user_profile", "personal_info", "routine"):
        return MemoryTier.PERSONAL
    elif cat_str in ("project", "project_milestone", "code_decision"):
        return MemoryTier.PROJECT
    elif cat_str in ("knowledge_note", "research", "paper", "documentation"):
        return MemoryTier.KNOWLEDGE
    elif cat_str in ("conversation", "episodic_event", "historical_event"):
        return MemoryTier.EPISODIC
    elif cat_str in ("working", "scratchpad", "ephemeral"):
        return MemoryTier.WORKING
    return MemoryTier.PERSONAL


class MemoryItem(BaseModel):
    """Structured memory record with cognitive metadata."""
    id: int
    tier: MemoryTier
    category: MemoryCategory
    key: str
    content: str
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    provenance: str = Field(default="manual")  # "manual", "chat_extraction", "tool_result", "session"
    access_count: int = 0
    last_accessed_at: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class MemoryExport(BaseModel):
    """Container for exporting memory snapshot."""
    exported_at: float
    exported_at_iso: str
    total_count: int
    tiers: dict[str, int]
    memories: list[MemoryItem]

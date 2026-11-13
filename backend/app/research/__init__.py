"""NOUS Web Research Engine Package (Phase 12)."""

from backend.app.research.db import ResearchDBManager, init_research_db
from backend.app.research.engine import ResearchEngine, research_engine
from backend.app.research.searcher import WebSearchAggregator

__all__ = [
    "ResearchDBManager",
    "init_research_db",
    "ResearchEngine",
    "research_engine",
    "WebSearchAggregator",
]

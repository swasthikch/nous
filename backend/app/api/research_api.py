"""FastAPI REST Router for NOUS Web Research Engine (Phase 12)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.research.engine import research_engine

logger = logging.getLogger("nous.api.research")

router = APIRouter(prefix="/api/research", tags=["Web Research"])


# ---------------- REQUEST SCHEMAS ----------------


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search term or topic")
    limit: int = Field(6, description="Maximum results to return")


class InvestigateRequest(BaseModel):
    query: str = Field(..., description="Research question or topic to investigate")
    category: str = Field("technology", description="Category: technology, company, academic, market, or general")
    auto_save: bool = Field(False, description="Automatically persist report to research notebook")
    tags: str = Field("", description="Optional comma-separated tags")


class NoteCreateRequest(BaseModel):
    title: str = Field(..., description="Note title")
    query: str = Field(..., description="Investigated query")
    category: str = Field("general", description="Category tag")
    summary: str = Field(..., description="Brief summary")
    full_report_markdown: str = Field(..., description="Markdown report")
    key_findings: list[str] = Field(default_factory=list, description="Key takeaway points")
    sources: list[dict[str, Any]] = Field(default_factory=list, description="Referenced sources")
    tags: str = Field("", description="Comma-separated tags")


# ---------------- ENDPOINTS ----------------


@router.post("/search")
def search_web_sources(req: SearchRequest) -> dict[str, Any]:
    """Perform fast multi-provider search across web, Wikipedia, and news feeds."""
    try:
        results = research_engine.search_sources(req.query, limit=req.limit)
        return {
            "query": req.query,
            "count": len(results),
            "sources": results,
        }
    except Exception as e:
        logger.error("Web search failed for '%s': %s", req.query, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigate")
def conduct_investigation(req: InvestigateRequest) -> dict[str, Any]:
    """Execute full 8-part evidence-backed research report conforming to Section 12."""
    try:
        report = research_engine.investigate(req.query, category=req.category)
        saved_note = None
        if req.auto_save:
            saved_note = research_engine.save_to_notebook(report, tags=req.tags)

        return {
            "status": "success",
            "report": report,
            "saved_note": saved_note,
        }
    except Exception as e:
        logger.error("Research investigation failed for '%s': %s", req.query, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes")
def list_research_notes(
    category: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50),
) -> dict[str, Any]:
    """Retrieve saved research notes from persistent SQLite database."""
    try:
        notes = research_engine.db.list_notes(category=category, search=search, limit=limit)
        return {
            "count": len(notes),
            "notes": notes,
        }
    except Exception as e:
        logger.error("Failed to list research notes: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}")
def get_research_note(note_id: str) -> dict[str, Any]:
    """Retrieve details for a single saved research note."""
    try:
        note = research_engine.db.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Research note not found")
        return {"note": note}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get research note %s: %s", note_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes")
def create_research_note(req: NoteCreateRequest) -> dict[str, Any]:
    """Manually save a research report or technical note to notebook."""
    try:
        note = research_engine.db.create_note(
            title=req.title,
            query=req.query,
            category=req.category,
            summary=req.summary,
            full_report_markdown=req.full_report_markdown,
            key_findings=req.key_findings,
            sources=req.sources,
            tags=req.tags,
        )
        return {"status": "created", "note": note}
    except Exception as e:
        logger.error("Failed to create research note: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}")
def delete_research_note(note_id: str) -> dict[str, Any]:
    """Delete a saved research note by ID."""
    try:
        deleted = research_engine.db.delete_note(note_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Research note not found")
        return {"status": "deleted", "note_id": note_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete research note %s: %s", note_id, e)
        raise HTTPException(status_code=500, detail=str(e))

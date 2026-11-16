"""Memory Management API Endpoints for NOUS 5-Tier Memory Operating System."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.app.memory.manager import memory_manager
from backend.app.memory.models import MemoryTier, MemoryCategory, MemoryItem

router = APIRouter(prefix="/api/memory", tags=["memory"])


class CreateMemoryRequest(BaseModel):
    category: MemoryCategory
    key: str = Field(..., description="Short key identifier, e.g. 'preferred_name'")
    content: str = Field(..., description="The factual content to store")
    tier: Optional[MemoryTier] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    key: Optional[str] = None
    category: Optional[MemoryCategory] = None
    tier: Optional[MemoryTier] = None
    importance: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class ToggleMemoryRequest(BaseModel):
    enabled: bool = Field(..., description="Toggle memory on or off")


class ExtractMemoryRequest(BaseModel):
    text: str = Field(..., description="Chat text from which to extract memories")


@router.get("")
async def list_memories(
    tier: Optional[MemoryTier] = None,
    category: Optional[MemoryCategory] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve persistent memories with optional tier, category, and search filtering."""
    items = memory_manager.list_memories(tier=tier, category=category, search_query=search, limit=limit)
    return {
        "count": len(items),
        "memory_enabled": memory_manager.is_memory_enabled(),
        "memories": [item.model_dump() for item in items],
    }


@router.post("")
async def create_memory(request: CreateMemoryRequest):
    """Add or update a memory fact with automatic deduplication."""
    item = memory_manager.save_memory(
        category=request.category,
        key=request.key,
        content=request.content,
        tier=request.tier,
        importance=request.importance,
        provenance="manual",
        metadata=request.metadata,
    )
    return {"success": True, "memory": item.model_dump()}


@router.get("/tiers")
async def get_tiers_overview():
    """Retrieve item counts across all 5 operational memory tiers."""
    all_memories = memory_manager.list_memories(limit=1000)
    counts = {t.value: 0 for t in MemoryTier}
    for m in all_memories:
        counts[m.tier.value] += 1

    return {
        "tiers": [
            {
                "id": t.value,
                "label": t.value.upper(),
                "count": counts[t.value],
            }
            for t in MemoryTier
        ],
        "total_active_memories": len(all_memories),
        "memory_enabled": memory_manager.is_memory_enabled(),
    }


@router.get("/categories")
async def get_categories_overview():
    """Get all memory subcategories and item count in each."""
    all_memories = memory_manager.list_memories(limit=1000)
    counts = {cat.value: 0 for cat in MemoryCategory}
    for m in all_memories:
        counts[m.category.value] += 1

    return {
        "categories": [
            {
                "id": cat.value,
                "label": cat.value.replace("_", " ").title(),
                "count": counts[cat.value],
            }
            for cat in MemoryCategory
        ],
        "total_active_memories": len(all_memories),
        "memory_enabled": memory_manager.is_memory_enabled(),
    }


@router.get("/export")
async def export_memories_endpoint(format: str = Query("json", pattern="^(json|markdown)$")):
    """Export all stored memories into a downloadable JSON or Markdown document."""
    exported = memory_manager.export_memories(format=format)
    if format == "markdown":
        return Response(content=str(exported), media_type="text/markdown")
    return Response(content=str(exported), media_type="application/json")


@router.post("/extract")
async def extract_memories_endpoint(request: ExtractMemoryRequest):
    """Scan arbitrary conversation text and passively extract candidate memories."""
    extracted = memory_manager.extract_and_store_from_message(request.text)
    return {
        "success": True,
        "extracted_count": len(extracted),
        "extracted_memories": [item.model_dump() for item in extracted],
    }


@router.get("/settings")
async def get_memory_settings():
    """Retrieve memory system operational settings."""
    return {
        "memory_enabled": memory_manager.is_memory_enabled(),
        "auto_extract_enabled": memory_manager.is_auto_extract_enabled(),
    }


@router.post("/settings")
async def update_memory_settings(request: ToggleMemoryRequest):
    """Toggle long-term memory system active state."""
    memory_manager.set_memory_enabled(request.enabled)
    return {
        "success": True,
        "memory_enabled": memory_manager.is_memory_enabled(),
    }


@router.get("/{memory_id}")
async def get_memory_item(memory_id: int):
    """Retrieve a single memory item by ID."""
    item = memory_manager.get_memory(memory_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    return item.model_dump()


@router.put("/{memory_id}")
async def update_memory_item(memory_id: int, request: UpdateMemoryRequest):
    """Update an existing memory item."""
    success = memory_manager.update_memory(
        memory_id=memory_id,
        content=request.content,
        key=request.key,
        category=request.category,
        tier=request.tier,
        importance=request.importance,
        metadata=request.metadata,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or update failed.")
    return {"success": True, "updated_id": memory_id}


@router.delete("/{memory_id}")
async def delete_memory_item(memory_id: int, hard: bool = Query(False)):
    """Delete a memory item."""
    success = memory_manager.delete_memory(memory_id, hard_delete=hard)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"success": True, "deleted_id": memory_id}

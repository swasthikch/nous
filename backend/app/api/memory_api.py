"""Memory Management API Endpoints for NOUS."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.memory.manager import memory_manager, MemoryCategory, MemoryItem

router = APIRouter(prefix="/api/memory", tags=["memory"])


class CreateMemoryRequest(BaseModel):
    category: MemoryCategory
    key: str = Field(..., description="Short key identifier, e.g. 'preferred_name'")
    content: str = Field(..., description="The factual content to store")
    metadata: Optional[dict] = Field(default_factory=dict)


class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    key: Optional[str] = None
    category: Optional[MemoryCategory] = None
    metadata: Optional[dict] = None


class ToggleMemoryRequest(BaseModel):
    enabled: bool = Field(..., description="Toggle memory on or off")


@router.get("")
async def list_memories(
    category: Optional[MemoryCategory] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve persistent memories with optional category and search filtering."""
    items = memory_manager.list_memories(category=category, search_query=search, limit=limit)
    return {
        "count": len(items),
        "memory_enabled": memory_manager.is_memory_enabled(),
        "memories": [item.model_dump() for item in items],
    }


@router.post("")
async def create_memory(request: CreateMemoryRequest):
    """Manually add or update a memory fact."""
    item = memory_manager.save_memory(
        category=request.category,
        key=request.key,
        content=request.content,
        metadata=request.metadata,
    )
    return {"success": True, "memory": item.model_dump()}


@router.get("/categories")
async def get_categories_overview():
    """Get all memory categories and count of memories in each."""
    all_memories = memory_manager.list_memories(limit=500)
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


@router.get("/settings")
async def get_memory_settings():
    """Retrieve memory system operational settings."""
    return {
        "memory_enabled": memory_manager.is_memory_enabled(),
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

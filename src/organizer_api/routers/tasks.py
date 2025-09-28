"""
Tasks API router.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from organizer_core.models.tasks import TodoItem, TaskStatus, TaskPriority

router = APIRouter()


@router.get("/", response_model=List[TodoItem])
async def get_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None)
) -> List[TodoItem]:
    """Get tasks with optional filtering."""
    # TODO: Implement with database service
    return []


@router.post("/", response_model=TodoItem)
async def create_task(task: TodoItem) -> TodoItem:
    """Create a new task."""
    # TODO: Implement with database service
    return task


@router.put("/{task_id}", response_model=TodoItem)
async def update_task(task_id: str, task: TodoItem) -> TodoItem:
    """Update an existing task."""
    # TODO: Implement with database service
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str) -> dict:
    """Delete a task."""
    # TODO: Implement with database service
    return {"message": "Task deleted successfully"}
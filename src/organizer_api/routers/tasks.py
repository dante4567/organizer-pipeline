"""
Tasks API router with full database integration.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
import aiosqlite

from organizer_core.models.tasks import TodoItem, TaskStatus, TaskPriority
from ..database.connection import get_database
from ..database.tasks_service import TasksService

router = APIRouter()


@router.get("/", response_model=List[TodoItem])
async def get_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    db: aiosqlite.Connection = Depends(get_database)
) -> List[TodoItem]:
    """
    Get tasks with optional filtering.

    Args:
        status: Filter by task status (pending, in_progress, completed, cancelled)
        priority: Filter by priority (low, medium, high, urgent)
        db: Database connection (injected)

    Returns:
        List of tasks matching the filters
    """
    tasks = await TasksService.get_tasks(db, status=status, priority=priority)
    return tasks


@router.get("/{task_id}", response_model=TodoItem)
async def get_task(
    task_id: str,
    db: aiosqlite.Connection = Depends(get_database)
) -> TodoItem:
    """
    Get a single task by ID.

    Args:
        task_id: Task ID
        db: Database connection (injected)

    Returns:
        Task details

    Raises:
        HTTPException: 404 if task not found
    """
    task = await TasksService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/", response_model=TodoItem, status_code=201)
async def create_task(
    task: TodoItem,
    db: aiosqlite.Connection = Depends(get_database)
) -> TodoItem:
    """
    Create a new task.

    Args:
        task: Task data to create
        db: Database connection (injected)

    Returns:
        Created task with generated ID and timestamps
    """
    try:
        created_task = await TasksService.create_task(db, task)
        return created_task
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


@router.put("/{task_id}", response_model=TodoItem)
async def update_task(
    task_id: str,
    task: TodoItem,
    db: aiosqlite.Connection = Depends(get_database)
) -> TodoItem:
    """
    Update an existing task.

    Args:
        task_id: Task ID to update
        task: Updated task data
        db: Database connection (injected)

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found
    """
    updated_task = await TasksService.update_task(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return updated_task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: aiosqlite.Connection = Depends(get_database)
) -> None:
    """
    Delete a task.

    Args:
        task_id: Task ID to delete
        db: Database connection (injected)

    Raises:
        HTTPException: 404 if task not found
    """
    deleted = await TasksService.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

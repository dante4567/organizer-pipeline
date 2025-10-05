"""
Tasks CRUD service for database operations.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
import uuid

import aiosqlite
from organizer_core.models.tasks import TodoItem, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class TasksService:
    """Service for task database operations."""

    @staticmethod
    async def create_task(db: aiosqlite.Connection, task: TodoItem) -> TodoItem:
        """
        Create a new task in the database.

        Args:
            db: Database connection
            task: Task to create

        Returns:
            Created task with ID and timestamps
        """
        # Generate ID if not provided
        if not task.id:
            task.id = str(uuid.uuid4())

        # Set timestamps
        now = datetime.now(timezone.utc)
        task.created_at = now
        task.updated_at = now

        # Serialize tags to JSON
        tags_json = json.dumps(task.tags) if task.tags else None

        # Convert datetime to ISO format string
        due_date_str = task.due_date.isoformat() if task.due_date else None
        completed_at_str = task.completed_at.isoformat() if task.completed_at else None

        query = """
            INSERT INTO tasks (
                id, title, description, status, priority, due_date,
                completed_at, tags, assigned_to, estimated_hours,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        await db.execute(
            query,
            (
                task.id,
                task.title,
                task.description,
                task.status,
                task.priority,
                due_date_str,
                completed_at_str,
                tags_json,
                task.assigned_to,
                task.estimated_hours,
                task.created_at.isoformat(),
                task.updated_at.isoformat()
            )
        )
        await db.commit()

        logger.info(f"Created task: {task.id} - {task.title}")
        return task

    @staticmethod
    async def get_task(db: aiosqlite.Connection, task_id: str) -> Optional[TodoItem]:
        """
        Get a single task by ID.

        Args:
            db: Database connection
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        query = "SELECT * FROM tasks WHERE id = ?"

        async with db.execute(query, (task_id,)) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        return TasksService._row_to_task(row)

    @staticmethod
    async def get_tasks(
        db: aiosqlite.Connection,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100
    ) -> List[TodoItem]:
        """
        Get tasks with optional filtering.

        Args:
            db: Database connection
            status: Filter by status
            priority: Filter by priority
            limit: Maximum number of tasks to return

        Returns:
            List of tasks
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        tasks = [TasksService._row_to_task(row) for row in rows]
        logger.info(f"Retrieved {len(tasks)} tasks")
        return tasks

    @staticmethod
    async def update_task(
        db: aiosqlite.Connection,
        task_id: str,
        task: TodoItem
    ) -> Optional[TodoItem]:
        """
        Update an existing task.

        Args:
            db: Database connection
            task_id: Task ID to update
            task: Updated task data

        Returns:
            Updated task if found, None otherwise
        """
        # Check if task exists
        existing = await TasksService.get_task(db, task_id)
        if not existing:
            return None

        # Update timestamp
        task.updated_at = datetime.now(timezone.utc)
        task.id = task_id  # Ensure ID doesn't change

        # Serialize tags
        tags_json = json.dumps(task.tags) if task.tags else None

        # Convert datetime to ISO format
        due_date_str = task.due_date.isoformat() if task.due_date else None
        completed_at_str = task.completed_at.isoformat() if task.completed_at else None

        query = """
            UPDATE tasks SET
                title = ?,
                description = ?,
                status = ?,
                priority = ?,
                due_date = ?,
                completed_at = ?,
                tags = ?,
                assigned_to = ?,
                estimated_hours = ?,
                updated_at = ?
            WHERE id = ?
        """

        await db.execute(
            query,
            (
                task.title,
                task.description,
                task.status,
                task.priority,
                due_date_str,
                completed_at_str,
                tags_json,
                task.assigned_to,
                task.estimated_hours,
                task.updated_at.isoformat(),
                task_id
            )
        )
        await db.commit()

        logger.info(f"Updated task: {task_id}")
        return task

    @staticmethod
    async def delete_task(db: aiosqlite.Connection, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            db: Database connection
            task_id: Task ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Check if task exists
        existing = await TasksService.get_task(db, task_id)
        if not existing:
            return False

        query = "DELETE FROM tasks WHERE id = ?"
        await db.execute(query, (task_id,))
        await db.commit()

        logger.info(f"Deleted task: {task_id}")
        return True

    @staticmethod
    def _row_to_task(row: tuple) -> TodoItem:
        """
        Convert database row to TodoItem.

        Args:
            row: Database row tuple

        Returns:
            TodoItem instance
        """
        # Parse JSON fields
        tags = json.loads(row[7]) if row[7] else []

        # Parse datetime fields
        from dateutil import parser

        due_date = parser.parse(row[5]) if row[5] else None
        completed_at = parser.parse(row[6]) if row[6] else None
        created_at = parser.parse(row[10]) if row[10] else datetime.now(timezone.utc)
        updated_at = parser.parse(row[11]) if row[11] else datetime.now(timezone.utc)

        return TodoItem(
            id=row[0],
            title=row[1],
            description=row[2],
            status=row[3],
            priority=row[4],
            due_date=due_date,
            completed_at=completed_at,
            tags=tags,
            assigned_to=row[8],
            estimated_hours=row[9],
            created_at=created_at,
            updated_at=updated_at
        )

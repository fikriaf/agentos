"""Task and plan models for ROMA-style decomposition."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUSED = "refused"


@dataclass
class SubTask:
    """Atomic unit of work (from ROMA decomposition)."""

    id: int
    description: str
    tools_needed: list[str] = field(default_factory=list)
    dependencies: set[int] = field(default_factory=set)
    estimated_cost: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None

    def can_execute(self, completed: set[int]) -> bool:
        """Check if all dependencies are met."""
        return self.dependencies.issubset(completed)


@dataclass
class TaskPlan:
    """Decomposed task plan (ROMA-style)."""

    task_id: str
    original_task: str
    subtasks: list[SubTask] = field(default_factory=list)
    parallel_groups: list[list[int]] = field(default_factory=list)  # Task indices that can run in parallel
    estimated_total_cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def get_executable_tasks(self, completed: set[int]) -> list[SubTask]:
        """Get tasks ready to execute."""
        return [t for t in self.subtasks if t.can_execute(completed) and t.status == TaskStatus.PENDING]

    def mark_completed(self, task_id: int, result: str) -> None:
        """Mark task as completed."""
        for task in self.subtasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.result = result
                break

    def mark_failed(self, task_id: int, error: str) -> None:
        """Mark task as failed."""
        for task in self.subtasks:
            if task.id == task_id:
                task.status = TaskStatus.FAILED
                task.error = error
                break

    def is_complete(self) -> bool:
        """Check if all tasks completed."""
        return all(t.status in (TaskStatus.COMPLETED, TaskStatus.REFUSED) for t in self.subtasks)

    def get_failed_tasks(self) -> list[SubTask]:
        """Get all failed tasks."""
        return [t for t in self.subtasks if t.status == TaskStatus.FAILED]


@dataclass
class Action:
    """Represents an action to be taken."""

    tool_name: str
    args: dict
    task_id: int
    reason: Optional[str] = None


@dataclass
class ActionResult:
    """Result of an action execution."""

    action: Action
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0

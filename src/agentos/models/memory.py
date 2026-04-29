"""Memory models for session and state management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Memory:
    """Single memory entry."""

    id: str
    content: str
    embedding: Optional[list[float]] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class Session:
    """Agent session."""

    session_id: str
    task: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    workspace_path: Optional[str] = None
    memories: list[str] = field(default_factory=list)  # Memory IDs
    status: str = "active"
    total_cost: float = 0.0

    def update(self) -> None:
        """Update timestamp."""
        self.updated_at = datetime.now()


@dataclass
class AgentState:
    """Current state of agent (InfiAgent-style)."""

    session_id: str
    task: str
    current_plan_id: Optional[str] = None
    workspace_files: list[str] = field(default_factory=list)
    recent_actions: list[dict] = field(default_factory=list)
    completed_tasks: set[int] = field(default_factory=set)
    failed_tasks: set[int] = field(default_factory=set)
    total_cost: float = 0.0
    step_count: int = 0
    max_steps: int = 100

    def add_action(self, action: dict) -> None:
        """Add action to history (bounded)."""
        self.recent_actions.append(action)
        if len(self.recent_actions) > 10:
            self.recent_actions = self.recent_actions[-10:]
        self.step_count += 1

    def is_complete(self) -> bool:
        """Check if agent should stop."""
        return self.step_count >= self.max_steps or self.failed_tasks

    def save_snapshot(self) -> dict:
        """Create snapshot for persistence."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "current_plan_id": self.current_plan_id,
            "workspace_files": self.workspace_files,
            "recent_actions": self.recent_actions,
            "completed_tasks": list(self.completed_tasks),
            "failed_tasks": list(self.failed_tasks),
            "total_cost": self.total_cost,
            "step_count": self.step_count,
        }

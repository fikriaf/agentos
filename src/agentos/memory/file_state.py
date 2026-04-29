"""File-based state management (InfiAgent-style)."""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from agentos.models.memory import AgentState
from agentos.utils.logger import get_logger

logger = get_logger("agentos.memory.file")


class FileStateManager:
    """InfiAgent-style externalized state management.

    Uses file-based snapshots to maintain bounded context
    regardless of task duration.
    """

    def __init__(
        self,
        workspace: Path,
        snapshot_interval: int = 10,
    ):
        """Initialize file state manager.

        Args:
            workspace: Workspace directory for state files
            snapshot_interval: Save snapshot every N steps
        """
        self.workspace = Path(workspace)
        self.snapshot_interval = snapshot_interval
        self.workspace.mkdir(parents=True, exist_ok=True)

        logger.info(f"FileStateManager initialized at {self.workspace}")

    def save_snapshot(self, state: AgentState) -> Path:
        """Save state snapshot to file.

        Args:
            state: Agent state to save

        Returns:
            Path to saved snapshot
        """
        snapshot = {
            "session_id": state.session_id,
            "task": state.task,
            "timestamp": datetime.now().isoformat(),
            "current_plan_id": state.current_plan_id,
            "workspace_files": self._list_workspace_files(),
            "recent_actions": state.recent_actions,
            "completed_tasks": list(state.completed_tasks),
            "failed_tasks": list(state.failed_tasks),
            "total_cost": state.total_cost,
            "step_count": state.step_count,
        }

        filename = f"snapshot_{state.session_id}.json"
        path = self.workspace / filename
        path.write_text(json.dumps(snapshot, indent=2))

        logger.debug(f"Snapshot saved: {path}")
        return path

    def load_snapshot(self, session_id: str) -> Optional[dict]:
        """Load state snapshot from file.

        Args:
            session_id: Session ID to load

        Returns:
            Snapshot dict or None
        """
        filename = f"snapshot_{session_id}.json"
        path = self.workspace / filename

        if not path.exists():
            logger.warning(f"Snapshot not found: {path}")
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            logger.info(f"Snapshot loaded: {session_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None

    def list_snapshots(self) -> list[dict]:
        """List all snapshots.

        Returns:
            List of snapshot metadata
        """
        snapshots = []
        for path in self.workspace.glob("snapshot_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                snapshots.append({
                    "session_id": data.get("session_id"),
                    "task": data.get("task", "")[:50],
                    "timestamp": data.get("timestamp"),
                    "step_count": data.get("step_count", 0),
                })
            except Exception:
                continue

        return sorted(snapshots, key=lambda x: x.get("timestamp", ""), reverse=True)

    def delete_snapshot(self, session_id: str) -> bool:
        """Delete a snapshot.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted
        """
        filename = f"snapshot_{session_id}.json"
        path = self.workspace / filename

        if path.exists():
            path.unlink()
            logger.info(f"Snapshot deleted: {session_id}")
            return True
        return False

    def _list_workspace_files(self) -> list[str]:
        """List files in workspace.

        Returns:
            List of file paths
        """
        files = []
        if self.workspace.exists():
            for path in self.workspace.rglob("*"):
                if path.is_file() and not path.name.startswith("."):
                    files.append(str(path.relative_to(self.workspace)))
        return files

    def get_latest_snapshot(self) -> Optional[dict]:
        """Get the latest snapshot.

        Returns:
            Latest snapshot or None
        """
        snapshots = self.list_snapshots()
        if not snapshots:
            return None

        session_id = snapshots[0].get("session_id")
        return self.load_snapshot(session_id) if session_id else None

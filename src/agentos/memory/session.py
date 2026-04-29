"""Session management."""

from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from agentos.models.memory import Session, AgentState
from agentos.memory.file_state import FileStateManager
from agentos.memory.vector_store import VectorMemory
from agentos.utils.logger import get_logger

logger = get_logger("agentos.memory.session")


class SessionManager:
    """Manages agent sessions with full memory support.

    Combines file-based state (InfiAgent) with vector search (ChromaDB).
    """

    def __init__(
        self,
        workspace: Optional[Path] = None,
        persist_dir: Optional[Path] = None,
    ):
        """Initialize session manager.

        Args:
            workspace: Directory for file state
            persist_dir: Directory for vector DB
        """
        self.workspace = workspace or Path.home() / ".agentos" / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)

        self.file_state = FileStateManager(self.workspace)
        self.vector_memory = VectorMemory(persist_dir)

        logger.info("SessionManager initialized")

    def create_session(self, task: str, session_id: Optional[str] = None) -> Session:
        """Create new session.

        Args:
            task: Task description
            session_id: Optional session ID

        Returns:
            Created session
        """
        import uuid

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        session = Session(
            session_id=session_id,
            task=task,
            workspace_path=str(self.workspace / session_id),
        )

        # Create session workspace
        session_path = self.workspace / session_id
        session_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Session created: {session_id}")
        return session

    def save_session(self, session: Session, state: AgentState) -> None:
        """Save session state.

        Args:
            session: Session to save
            state: Current agent state
        """
        # Create session directory
        session_path = Path(self.workspace / session.session_id)
        session_path.mkdir(parents=True, exist_ok=True)

        # Save file snapshot
        self.file_state.save_snapshot(state)

        # Update session
        session.update()
        session.workspace_path = str(session_path)
        session.status = "active"

        # Save session metadata FIRST
        self._save_session_meta(session)

    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        meta_path = self.workspace / session_id / "session.json"
        if not meta_path.exists():
            return None

        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            return Session(
                session_id=data["session_id"],
                task=data["task"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                workspace_path=data.get("workspace_path"),
                memories=data.get("memories", []),
                status=data.get("status", "active"),
                total_cost=data.get("total_cost", 0.0),
            )
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def list_sessions(self) -> list[Session]:
        """List all sessions.

        Returns:
            List of sessions
        """
        sessions = []
        for path in self.workspace.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                session = self.load_session(path.name)
                if session:
                    sessions.append(session)

        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

    def add_memory(
        self,
        session_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Add memory to session.

        Args:
            session_id: Session ID
            content: Memory content
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        import asyncio

        # Add to vector store
        metadata = metadata or {}
        metadata["session_id"] = session_id

        memory_id = asyncio.run(
            self.vector_memory.add(content, metadata)
        )

        # Update session
        session = self.load_session(session_id)
        if session:
            session.memories.append(memory_id)
            self._save_session_meta(session)

        return memory_id

    async def search_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = 5,
    ) -> list:
        """Search session memories.

        Args:
            query: Search query
            session_id: Optional session filter
            k: Number of results

        Returns:
            List of memories
        """
        filter_metadata = {"session_id": session_id} if session_id else None
        return await self.vector_memory.search(query, k=k, filter_metadata=filter_metadata)

    def delete_session(self, session_id: str) -> bool:
        """Delete session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted
        """
        # Delete snapshots
        self.file_state.delete_snapshot(session_id)

        # Delete session directory
        session_path = self.workspace / session_id
        if session_path.exists():
            import shutil

            shutil.rmtree(session_path)
            logger.info(f"Session deleted: {session_id}")
            return True
        return False

    def _save_session_meta(self, session: Session) -> None:
        """Save session metadata.

        Args:
            session: Session
        """
        session_path = self.workspace / session.session_id
        session_path.mkdir(parents=True, exist_ok=True)

        meta_path = session_path / "session.json"
        meta_path.write_text(
            json.dumps(
                {
                    "session_id": session.session_id,
                    "task": session.task,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "workspace_path": session.workspace_path,
                    "memories": session.memories,
                    "status": session.status,
                    "total_cost": session.total_cost,
                },
                indent=2,
            )
        )

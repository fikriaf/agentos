"""Base agent class."""

from abc import ABC, abstractmethod
from typing import Optional

from agentos.models.message import Message, MessageHistory
from agentos.models.task import TaskPlan
from agentos.models.memory import AgentState, Session
from agentos.llm.client import LLMClient
from agentos.utils.logger import get_logger

logger = get_logger("agentos.agent")


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        llm_client: LLMClient,
        session_id: Optional[str] = None,
        task: Optional[str] = None,
    ):
        """Initialize agent.

        Args:
            llm_client: LLM client for completions
            session_id: Optional session ID
            task: Optional task description
        """
        self.llm = llm_client
        self.session_id = session_id or self._generate_session_id()
        self.task = task or ""
        self.history = MessageHistory()
        self.state = AgentState(
            session_id=self.session_id,
            task=self.task,
        )

        logger.info(f"Agent initialized: {self.session_id}")

    @staticmethod
    def _generate_session_id() -> str:
        """Generate unique session ID."""
        import uuid
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]
        return f"agentos_{ts}_{uid}"

    @abstractmethod
    async def run(self) -> str:
        """Run the agent.

        Returns:
            Final result or summary
        """
        pass

    @abstractmethod
    async def step(self) -> bool:
        """Execute single step.

        Returns:
            True if should continue, False if done
        """
        pass

    def add_message(self, role: str, content: str) -> None:
        """Add message to history.

        Args:
            role: Message role
            content: Message content
        """
        from agentos.models.message import MessageRole

        role_enum = MessageRole(role) if role in [r.value for r in MessageRole] else MessageRole.USER
        self.history.add(Message(role=role_enum, content=content))

    def get_cost_summary(self) -> dict:
        """Get cost summary.

        Returns:
            Cost summary
        """
        return self.llm.get_cost_summary()

"""Message models for chat/llm interactions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageRole(str, Enum):
    """Message role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """Single message in conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for LLM API."""
        msg = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            msg["name"] = self.name
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg


@dataclass
class MessageHistory:
    """Manages conversation history with bounded context."""

    max_messages: int = 100
    messages: list[Message] = field(default_factory=list)

    def add(self, message: Message) -> None:
        """Add message to history."""
        self.messages.append(message)
        self._trim()

    def _trim(self) -> None:
        """Trim history if exceeds max."""
        if len(self.messages) > self.max_messages:
            # Keep system message + recent messages
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            others = [m for m in self.messages if m.role != MessageRole.SYSTEM]
            self.messages = system_msgs + others[-self.max_messages + len(system_msgs) :]

    def get_messages(self) -> list[Message]:
        """Get all messages."""
        return self.messages

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

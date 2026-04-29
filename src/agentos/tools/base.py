"""Base tool class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from agentos.models.tool import ToolType


@dataclass
class ToolResult:
    """Result of tool execution."""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(
        self,
        name: str,
        description: str,
        tool_type: ToolType = ToolType.CUSTOM,
    ):
        """Initialize tool.

        Args:
            name: Tool name
            description: Tool description
            tool_type: Type of tool
        """
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self.requires_confirmation = False
        self.is_dangerous = False

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult
        """
        pass

    def get_schema(self) -> dict:
        """Get tool schema for MCP.

        Returns:
            Tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        }

"""Tool models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class ToolType(str, Enum):
    """Type of tool."""

    SHELL = "shell"
    HTTP = "http"
    MCP = "mcp"
    PYTHON = "python"
    CUSTOM = "custom"


@dataclass
class ToolDefinition:
    """Definition of a tool."""

    name: str
    description: str
    type: ToolType
    parameters: dict = field(default_factory=dict)
    requires_confirmation: bool = False
    is_dangerous: bool = False

    def to_mcp_format(self) -> dict:
        """Convert to MCP tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters,
        }


@dataclass
class ToolResult:
    """Result from tool execution."""

    tool_name: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolGroup:
    """Group of related tools (HTAA-style)."""

    name: str
    description: str
    tools: list[str] = field(default_factory=list)  # Tool names
    usage_count: int = 0


@dataclass
class ToolRegistry:
    """Registry of all available tools."""

    tools: dict[str, ToolDefinition] = field(default_factory=dict)
    groups: dict[str, ToolGroup] = field(default_factory=dict)

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all tools."""
        return list(self.tools.values())

    def create_group(self, name: str, description: str, tool_names: list[str]) -> None:
        """Create a tool group (HTAA)."""
        self.groups[name] = ToolGroup(
            name=name,
            description=description,
            tools=tool_names,
        )

    def get_group(self, name: str) -> Optional[ToolGroup]:
        """Get tool group."""
        return self.groups.get(name)

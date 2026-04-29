"""File tools for AgentOS - read, write, search files."""

import asyncio
import os
from pathlib import Path
from typing import Optional
from agentos.tools.base import BaseTool, ToolResult
from agentos.utils.logger import get_logger

logger = get_logger("agentos.tools.files")


class FileTool(BaseTool):
    """Tool for file operations."""

    def __init__(self):
        super().__init__(
            name="file",
            description="Read, write, search files - file operations",
            tool_type="custom",
        )

    async def read_file(
        self,
        path: str,
        offset: int = 1,
        limit: int = 500,
    ) -> ToolResult:
        """Read a file with pagination."""
        try:
            p = Path(path)
            if not p.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                    execution_time=0,
                )
            
            content = p.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            start = offset - 1
            end = min(start + limit, len(lines))
            selected = "\n".join(f"{i+1}|{lines[i]}" for i in range(start, end))
            
            return ToolResult(
                success=True,
                output=f"File: {path}\nLines {offset}-{end}/{len(lines)}:\n\n{selected}",
                execution_time=0,
                metadata={"total_lines": len(lines)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Read error: {e}",
                execution_time=0,
            )

    async def write_file(
        self,
        path: str,
        content: str,
    ) -> ToolResult:
        """Write content to a file."""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            
            return ToolResult(
                success=True,
                output=f"Written {len(content)} chars to {path}",
                execution_time=0,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Write error: {e}",
                execution_time=0,
            )

    async def search_files(
        self,
        pattern: str,
        path: str = ".",
        target: str = "content",
        limit: int = 50,
    ) -> ToolResult:
        """Search files by name or content."""
        import re
        try:
            search_path = Path(path)
            matches = []
            
            if target == "files":
                # Search by filename
                for p in search_path.rglob("*"):
                    if p.is_file() and pattern.lower() in p.name.lower():
                        matches.append(str(p))
                        if len(matches) >= limit:
                            break
            else:
                # Search by content
                regex = re.compile(pattern, re.IGNORECASE)
                for p in search_path.rglob("*"):
                    if not p.is_file():
                        continue
                    if p.suffix in [".py", ".md", ".txt", ".json", ".yaml", ".yml"]:
                        try:
                            content = p.read_text(encoding="utf-8")
                            if regex.search(content):
                                matches.append(str(p))
                                if len(matches) >= limit:
                                    break
                        except:
                            pass
            
            return ToolResult(
                success=True,
                output=f"Found {len(matches)} matches:\n" + "\n".join(matches[:30]),
                execution_time=0,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search error: {e}",
                execution_time=0,
            )

    async def execute(
        self,
        action: str = "read",
        path: Optional[str] = None,
        content: Optional[str] = None,
        pattern: Optional[str] = None,
        offset: int = 1,
        limit: int = 500,
    ) -> ToolResult:
        """Execute file action."""
        if action == "read":
            return await self.read_file(path or "", offset, limit)
        elif action == "write":
            return await self.write_file(path or "", content or "")
        elif action == "search":
            return await self.search_files(pattern or "", path or ".", "content", limit)
        elif action == "glob":
            return await self.search_files(pattern or "", path or ".", "files", limit)
        else:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                execution_time=0,
            )

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "search", "glob"],
                        "description": "Action to perform",
                    },
                    "path": {
                        "type": "string",
                        "description": "File/directory path",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line offset for reading",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max lines to read",
                    },
                },
                "required": ["action"],
            },
        }
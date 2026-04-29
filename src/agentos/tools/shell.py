"""Shell tool for executing commands."""

import asyncio
import shlex
import time
from dataclasses import dataclass
from typing import Optional

from agentos.models.tool import ToolType
from agentos.tools.base import BaseTool, ToolResult
from agentos.utils.logger import get_logger

logger = get_logger("agentos.tools.shell")


@dataclass
class ShellConfig:
    """Shell tool configuration."""

    timeout: int = 300  # 5 minutes
    cwd: Optional[str] = None
    env: Optional[dict] = None


class ShellTool(BaseTool):
    """Tool for executing shell commands."""

    def __init__(self, config: Optional[ShellConfig] = None):
        """Initialize shell tool.

        Args:
            config: Optional shell config
        """
        super().__init__(
            name="bash",
            description="Execute bash/shell commands. Use for file operations, git, npm, python, etc.",
            tool_type=ToolType.SHELL,
        )
        self.config = config or ShellConfig()
        self.is_dangerous = False  # Can be set True for dangerous commands

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> ToolResult:
        """Execute shell command.

        Args:
            command: Command to execute
            timeout: Optional timeout override
            cwd: Optional working directory

        Returns:
            ToolResult
        """
        start_time = time.time()

        timeout = timeout or self.config.timeout
        cwd = cwd or self.config.cwd

        logger.info(f"Executing: {command[:100]}...")

        try:
            # Use asyncio.create_subprocess_shell for better async support
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=self.config.env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {timeout}s",
                    execution_time=time.time() - start_time,
                )

            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=stdout_text or "Command completed successfully",
                    execution_time=time.time() - start_time,
                )
            else:
                return ToolResult(
                    success=False,
                    output=stdout_text,
                    error=stderr_text or f"Command failed with code {process.returncode}",
                    execution_time=time.time() - start_time,
                )

        except Exception as e:
            logger.error(f"Shell execution error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    def get_schema(self) -> dict:
        """Get tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 300)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                    },
                },
                "required": ["command"],
            },
        }

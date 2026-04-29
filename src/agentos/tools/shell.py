"""Shell tool for executing commands."""

import asyncio
import os
import shlex
import sys
import time
from dataclasses import dataclass
from typing import Optional

from agentos.models.tool import ToolType
from agentos.tools.base import BaseTool, ToolResult
from agentos.utils.logger import get_logger

logger = get_logger("agentos.tools.shell")


def get_platform_commands() -> dict:
    """Get platform-specific command mappings."""
    is_windows = sys.platform.startswith("win") or os.name == "nt"
    
    return {
        "is_windows": is_windows,
        "mkdir": "md" if is_windows else "mkdir",
        "ls": "dir" if is_windows else "ls",
        "cp": "copy" if is_windows else "cp",
        "mv": "move" if is_windows else "mv",
        "rm": "del /q" if is_windows else "rm",
        "rmdir": "rmdir /s /q" if is_windows else "rm -rf",
        "cat": "type" if is_windows else "cat",
        "pwd": "cd" if is_windows else "pwd",
        "home": os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~",
    }


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

        # Detect platform
        platform_info = get_platform_commands()
        is_windows = platform_info["is_windows"]
        
        if is_windows:
            # Convert Linux commands to Windows equivalents
            if command.startswith("mkdir "):
                cmd_part = command[6:].strip()
                command = f"cmd /c md {cmd_part}"
            elif command == "ls" or command.startswith("ls "):
                args = command[3:] if len(command) > 3 else ""
                command = f"cmd /c dir {args}"
            elif " && " in command:
                command = command.replace(" && ", " & ")
            elif " -la" in command or " -al" in command:
                command = command.replace(" -la", "").replace(" -al", "")
            elif " -la" in command:
                command = command.replace(" -la", "")
            elif command.startswith("rm "):
                cmd_part = command[3:].strip()
                command = f"cmd /c del {cmd_part}"
            elif command.startswith("rmdir "):
                command = command.replace("rmdir ", "cmd /c rmdir /s /q ")
            elif command.startswith("cp ") or command.startswith("copy "):
                if command.startswith("cp "):
                    command = "cmd /c copy " + command[3:]
            elif command.startswith("cat "):
                command = command.replace("cat ", "cmd /c type ", 1)
            elif command.startswith("cd "):
                command = f"cmd /c {command}"
            else:
                # Wrap in cmd /c for other commands
                command = f"cmd /c {command}"
        
        # Handle special Hermes tool commands inline
        # These should be handled by dedicated tools, but we support inline for flexibility
        if command.strip().startswith("skill_view ") or command.strip().startswith("skills list") or command.strip().startswith("skills search "):
            # These are special - redirect to skills tool
            parts = command.strip().split()
            if len(parts) >= 2:
                skill_name = parts[1] if parts[0] == "skill_view" else (parts[1] if parts[0] == "skills" and len(parts) > 2 else parts[-1])
                from agentos.skills import SkillsManager
                mgr = SkillsManager()
                try:
                    content = mgr.get_skill(skill_name)
                    return ToolResult(
                        success=True,
                        output=content[:5000],
                        execution_time=0,
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=str(e),
                        execution_time=0,
                    )
        
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

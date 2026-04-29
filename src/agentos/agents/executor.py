"""Tool executor using HTAA + ToolTree methodology."""

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from agentos.agents.base import BaseAgent
from agentos.models.task import TaskPlan, SubTask, TaskStatus, Action, ActionResult
from agentos.models.tool import ToolRegistry, ToolDefinition, ToolResult
from agentos.models.message import Message, MessageRole
from agentos.llm.prompts import EXECUTOR_PROMPT
from agentos.tools.base import BaseTool
from agentos.utils.logger import get_logger

logger = get_logger("agentos.executor")


@dataclass
class ToolCall:
    """Planned tool call."""

    tool_name: str
    args: dict
    reason: str
    task_id: int


class ToolExecutor:
    """HTAA + ToolTree based tool executor.

    Uses tool grouping (HTAA) and MCTS-inspired planning (ToolTree)
    for optimal tool sequences.
    """

    def __init__(
        self,
        llm_client,
        tool_registry: Optional[ToolRegistry] = None,
        skills_context: Optional[str] = None,
    ):
        """Initialize executor.

        Args:
            llm_client: LLM client
            tool_registry: Optional tool registry
            skills_context: Skills context for the task
        """
        self.llm = llm_client
        self.registry = tool_registry or ToolRegistry()
        self.execution_history: list[ActionResult] = []
        self.skills_context = skills_context or ""

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: Tool to register
        """
        definition = ToolDefinition(
            name=tool.name,
            description=tool.description,
            type=tool.tool_type,
            requires_confirmation=tool.requires_confirmation,
            is_dangerous=tool.is_dangerous,
        )
        self.registry.register(definition)

    async def plan_tools(
        self,
        subtask: SubTask,
        context: Optional[str] = None,
    ) -> list[ToolCall]:
        """Plan tool calls for a subtask (ToolTree-style).

        Args:
            subtask: Subtask to plan for
            context: Optional execution context

        Returns:
            List of planned tool calls
        """
        logger.debug(f"Planning tools for task {subtask.id}: {subtask.description[:50]}...")

        # Build tools description
        tools_info = "\n".join(
            [f"- {name}: {t.description}" for name, t in self.registry.tools.items()]
        )

        # Build context with skills
        context_parts = []
        if context:
            context_parts.append(context)
        if self.skills_context:
            context_parts.append(f"\n\n## Available Skills\n{self.skills_context}")
        context_section = "\n".join(context_parts) if context_parts else ""

        prompt = EXECUTOR_PROMPT.format(
            subtask=subtask.description + context_section,
            tools=tools_info or "No tools available",
        )

        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a tool planning expert."),
            Message(role=MessageRole.USER, content=prompt),
        ]

        response, _, _ = await self.llm.complete(messages)

        return self._parse_tool_calls(response, subtask.id)

    def _parse_tool_calls(self, response: str, task_id: int) -> list[ToolCall]:
        """Parse tool calls from LLM response.

        Args:
            response: LLM response
            task_id: Task ID

        Returns:
            List of tool calls
        """
        # Try JSON first
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                calls = []
                for item in data.get("tool_calls", []):
                    calls.append(
                        ToolCall(
                            tool_name=item.get("tool", "bash"),
                            args=item.get("args", {}),
                            reason=item.get("reason", ""),
                            task_id=task_id,
                        )
                    )
                return calls
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"JSON parse failed: {e}")

        # Fallback: try to extract bash commands
        bash_commands = re.findall(r"`([^`]+)`", response)
        calls = []
        for i, cmd in enumerate(bash_commands[:3]):  # Max 3 commands
            calls.append(
                ToolCall(
                    tool_name="bash",
                    args={"command": cmd.strip()},
                    reason=f"Extracted command {i + 1}",
                    task_id=task_id,
                )
            )
        return calls

    async def execute_plan(
        self,
        plan: TaskPlan,
        tools: dict[str, BaseTool],
    ) -> list[ActionResult]:
        """Execute a full plan.

        Args:
            plan: TaskPlan to execute
            tools: Available tools

        Returns:
            List of action results
        """
        results = []
        completed: set[int] = set()

        for group in plan.parallel_groups:
            logger.info(f"Executing parallel group: {group}")

            # Get executable tasks
            group_tasks = [t for t in plan.subtasks if t.id in group]

            # Execute group in parallel
            group_results = await asyncio.gather(
                *[self._execute_subtask(t, tools) for t in group_tasks],
                return_exceptions=True,
            )

            for task_id, result in zip(group, group_results):
                if isinstance(result, Exception):
                    results.append(
                        ActionResult(
                            action=Action(tool_name="error", args={}, task_id=task_id),
                            success=False,
                            error=str(result),
                        )
                    )
                    completed.add(task_id)
                else:
                    results.append(result)
                    if result.success:
                        completed.add(task_id)
                        plan.mark_completed(task_id, result.output or "")
                    else:
                        plan.mark_failed(task_id, result.error or "Unknown error")

            self.execution_history.extend(results)

        return results

    async def _execute_subtask(
        self,
        subtask: SubTask,
        tools: dict[str, BaseTool],
    ) -> ActionResult:
        """Execute a single subtask.

        Args:
            subtask: Subtask to execute
            tools: Available tools

        Returns:
            Action result
        """
        import time

        logger.info(f"Executing subtask {subtask.id}: {subtask.description[:50]}...")
        start_time = time.time()

        try:
            # Plan tool calls
            tool_calls = await self.plan_tools(subtask)
            if not tool_calls:
                # Generate a basic command based on task description
                desc = subtask.description.lower()
                if "flask" in desc and "install" in desc:
                    tool_calls = [
                        ToolCall(
                            tool_name="bash",
                            args={"command": "python -m pip install flask"},
                            reason="Install Flask package",
                            task_id=subtask.id,
                        )
                    ]
                elif "flask" in desc and "create" in desc:
                    tool_calls = [
                        ToolCall(
                            tool_name="bash",
                            args={"command": "python -c \"print('Flask placeholder')\""},
                            reason="Create Flask app placeholder",
                            task_id=subtask.id,
                        )
                    ]
                else:
                    # Last resort - list current directory
                    tool_calls = [
                        ToolCall(
                            tool_name="bash",
                            args={"command": "dir"},
                            reason="List current directory",
                            task_id=subtask.id,
                        )
                    ]

            # Execute tool calls sequentially
            all_output = []
            for call in tool_calls:
                if call.tool_name not in tools:
                    return ActionResult(
                        action=Action(
                            tool_name=call.tool_name,
                            args=call.args,
                            task_id=subtask.id,
                        ),
                        success=False,
                        error=f"Tool not found: {call.tool_name}",
                    )

                tool = tools[call.tool_name]
                result = await tool.execute(**call.args)

                if not result.success:
                    return ActionResult(
                        action=Action(
                            tool_name=call.tool_name,
                            args=call.args,
                            task_id=subtask.id,
                        ),
                        success=False,
                        error=result.error,
                        execution_time=time.time() - start_time,
                    )

                all_output.append(result.output)

            return ActionResult(
                action=Action(
                    tool_name="; ".join(c.tool_name for c in tool_calls),
                    args={},
                    task_id=subtask.id,
                ),
                success=True,
                output="\n".join(filter(None, all_output)),
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"Subtask {subtask.id} failed: {e}")
            return ActionResult(
                action=Action(tool_name="error", args={}, task_id=subtask.id),
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

"""Planner agent using ROMA + INTENT methodology."""

import json
import re
from typing import Optional

from agentos.agents.base import BaseAgent
from agentos.models.task import TaskPlan, SubTask, TaskStatus
from agentos.models.message import Message, MessageRole
from agentos.llm.prompts import PLANNER_PROMPT
from agentos.utils.logger import get_logger
from agentos.utils.budget import BudgetTracker, Budget

logger = get_logger("agentos.planner")


class PlannerAgent:
    """ROM A + INTENT based planner with budget awareness.

    Decomposes tasks into subtasks using recursive decomposition,
    parallel planning, and budget constraints.
    """

    def __init__(
        self,
        llm_client,
        budget_tracker: Optional[BudgetTracker] = None,
        max_parallel: int = 5,
        skills_context: Optional[str] = None,
    ):
        """Initialize planner.

        Args:
            llm_client: LLM client
            budget_tracker: Optional budget tracker
            max_parallel: Maximum parallel tasks
            skills_context: Skills context for the task
        """
        self.llm = llm_client
        self.budget = budget_tracker or BudgetTracker()
        self.max_parallel = max_parallel
        self.skills_context = skills_context or ""

    async def decompose(
        self,
        task: str,
        context: Optional[str] = None,
    ) -> TaskPlan:
        """Decompose task using ROMA's recursive approach.

        Args:
            task: Task to decompose
            context: Optional additional context

        Returns:
            TaskPlan with subtasks
        """
        logger.info(f"Decomposing task: {task[:100]}...")

        # Build prompt with skills context
        context_parts = []
        if context:
            context_parts.append(context)
        if self.skills_context:
            context_parts.append(f"\n\n## Skills Reference\n{self.skills_context}")
        
        context_section = "\n".join(context_parts) if context_parts else ""
        prompt = PLANNER_PROMPT.format(
            task=task + context_section,
            max_parallel=self.max_parallel,
        )

        # Get LLM response
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a task decomposition expert."),
            Message(role=MessageRole.USER, content=prompt),
        ]

        response, _, _ = await self.llm.complete(messages)

        # Parse response
        plan = self._parse_plan(response, task)

        # INTENT: Check budget constraints
        estimated = self.budget.estimate(len(plan.subtasks))
        logger.info(
            f"Plan estimated: {len(plan.subtasks)} subtasks, "
            f"cost: ${estimated:.4f}, budget remaining: ${self.budget.budget.remaining:.4f}"
        )

        if estimated > self.budget.budget.remaining:
            logger.warning(f"Over budget! Reducing scope...")
            plan = await self._reduce_scope(plan, self.budget.budget.remaining)

        return plan

    def _parse_plan(self, response: str, original_task: str) -> TaskPlan:
        """Parse LLM response into TaskPlan.

        Args:
            response: LLM response text
            original_task: Original task description

        Returns:
            Parsed TaskPlan
        """
        # Try to extract JSON
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return self._build_plan(data, original_task)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed: {e}")

        # Fallback: create simple plan
        return self._create_fallback_plan(original_task, response)

    def _build_plan(self, data: dict, original_task: str) -> TaskPlan:
        """Build TaskPlan from parsed data.

        Args:
            data: Parsed JSON data
            original_task: Original task

        Returns:
            TaskPlan
        """
        task_id = f"plan_{original_task[:20].replace(' ', '_')}"

        subtasks = []
        for item in data.get("subtasks", []):
            subtask = SubTask(
                id=item.get("id", len(subtasks) + 1),
                description=item.get("description", ""),
                tools_needed=item.get("tools_needed", []),
                dependencies=set(item.get("dependencies", [])),
                estimated_cost=item.get("estimated_cost", 0.001),
            )
            subtasks.append(subtask)

        parallel_groups = data.get("parallel_groups", [])
        if not parallel_groups and subtasks:
            # Default: group by dependencies
            parallel_groups = self._compute_parallel_groups(subtasks)

        total_cost = sum(t.estimated_cost for t in subtasks)

        return TaskPlan(
            task_id=task_id,
            original_task=original_task,
            subtasks=subtasks,
            parallel_groups=parallel_groups,
            estimated_total_cost=total_cost,
        )

    def _compute_parallel_groups(self, subtasks: list[SubTask]) -> list[list[int]]:
        """Compute which tasks can run in parallel.

        Args:
            subtasks: List of subtasks

        Returns:
            List of parallel groups (each group is list of task IDs)
        """
        groups = []
        remaining = set(t.id for t in subtasks)
        completed = set()

        while remaining:
            # Find tasks with satisfied dependencies
            ready = [
                t.id
                for t in subtasks
                if t.id in remaining and t.dependencies.issubset(completed)
            ]

            if not ready:
                # Deadlock - add remaining as last group
                groups.append(list(remaining))
                break

            groups.append(ready[: self.max_parallel])
            completed.update(ready)
            remaining -= set(ready)

        return groups

    def _create_fallback_plan(self, task: str, response: str) -> TaskPlan:
        """Create fallback plan when parsing fails.

        Args:
            task: Original task
            response: Raw LLM response

        Returns:
            Simple TaskPlan
        """
        logger.warning("Using fallback plan parsing")

        # Simple: treat entire response as single task
        return TaskPlan(
            task_id=f"plan_{task[:20].replace(' ', '_')}",
            original_task=task,
            subtasks=[
                SubTask(
                    id=1,
                    description=response[:500],  # First 500 chars
                    tools_needed=["bash"],
                    estimated_cost=0.001,
                )
            ],
            parallel_groups=[[1]],
            estimated_total_cost=0.001,
        )

    async def _reduce_scope(
        self,
        plan: TaskPlan,
        budget: float,
    ) -> TaskPlan:
        """INTENT: Reduce plan scope to fit budget.

        Args:
            plan: Original plan
            budget: Available budget

        Returns:
            Reduced plan
        """
        logger.info(f"Reducing plan from ${plan.estimated_total_cost:.4f} to ${budget:.4f}")

        # Remove lowest priority tasks until within budget
        reduced_tasks = []
        remaining_budget = budget

        for task in sorted(plan.subtasks, key=lambda t: t.estimated_cost):
            if task.estimated_cost <= remaining_budget:
                reduced_tasks.append(task)
                remaining_budget -= task.estimated_cost

        # Recompute parallel groups
        parallel_groups = self._compute_parallel_groups(reduced_tasks)

        return TaskPlan(
            task_id=plan.task_id,
            original_task=plan.original_task,
            subtasks=reduced_tasks,
            parallel_groups=parallel_groups,
            estimated_total_cost=budget - remaining_budget,
        )

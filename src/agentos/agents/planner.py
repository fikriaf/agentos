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
        # Try to extract JSON first
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return self._build_plan(data, original_task)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed: {e}")

        # Parse simple numbered list from response
        lines = response.strip().split('\n')
        steps = []
        for line in lines:
            # Match "1. Something" or "- Something" or "* Something"
            match = re.match(r'^\s*(?:\d+[\.\)]|[-*])\s*(.+)', line)
            if match and match.group(1).strip():
                desc = match.group(1).strip()
                # Skip headers, empty lines
                if len(desc) > 5 and not desc.lower().startswith(('step', 'task', 'output', 'example')):
                    steps.append(desc)

        if len(steps) >= 2:
            # Build plan from steps
            subtasks = []
            for i, desc in enumerate(steps, 1):
                subtask = SubTask(
                    id=i,
                    description=desc,
                    tools_needed=[],
                    dependencies=set(),
                    estimated_cost=0.001,
                )
                subtasks.append(subtask)

            parallel_groups = [[t.id] for t in subtasks]
            return TaskPlan(
                task_id=f"plan_{hash(original_task) % 10000}",
                original_task=original_task,
                subtasks=subtasks,
                parallel_groups=parallel_groups,
                estimated_total_cost=sum(t.estimated_cost for t in subtasks),
            )

        # Fallback: split original task on "->" (our standard pipeline format)
        steps = [s.strip() for s in original_task.split('->') if s.strip()]
        if len(steps) >= 2:
            subtasks = [
                SubTask(
                    id=i,
                    description=desc,
                    tools_needed=[],
                    dependencies=set(),
                    estimated_cost=0.001,
                )
                for i, desc in enumerate(steps, 1)
            ]
            return TaskPlan(
                task_id=f"fallback_{hash(original_task) % 10000}",
                original_task=original_task,
                subtasks=subtasks,
                parallel_groups=[[t.id] for t in subtasks],
                estimated_total_cost=sum(t.estimated_cost for t in subtasks),
            )

        # Ultimate fallback: create meaningful steps based on task keywords
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
            TaskPlan from numbered list
        """
        logger.warning("Using fallback plan parsing")
        
        # Try to extract numbered list from response
        # Look for patterns like "1. Do something" or "- Do something"
        lines = response.strip().split('\n')
        subtasks = []
        task_id = 1
        
        for line in lines:
            # Clean up the line
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering like "1." or "1)" or just "-"
            clean = re.sub(r'^\d+[\.\)]\s*', '', line)
            clean = re.sub(r'^-\s*', '', clean)
            
            if clean and len(clean) > 3:
                subtasks.append(SubTask(
                    id=task_id,
                    description=clean[:200],
                    tools_needed=["web", "file", "bash"],
                    estimated_cost=0.001,
                ))
                task_id += 1
        
        # If no numbered items found, treat whole response as single task
        if not subtasks:
            # Split by common delimiters
            parts = re.split(r'\n+|(?:\s*->\s*)', task)
            for i, part in enumerate(parts):
                part = part.strip()
                if part and len(part) > 2:
                    subtasks.append(SubTask(
                        id=i+1,
                        description=part[:200],
                        tools_needed=["web", "file", "bash"],
                        estimated_cost=0.001,
                    ))
        
        # Final fallback: split on "->"
        if not subtasks:
            steps = [s.strip() for s in task.split('->') if s.strip()]
            for i, step in enumerate(steps):
                subtasks.append(SubTask(
                    id=i+1,
                    description=step[:200],
                    tools_needed=["web", "file", "bash"],
                    estimated_cost=0.001,
                ))
        
        # Ultimate fallback: single task
        if not subtasks:
            subtasks = [SubTask(
                id=1,
                description=task[:200],
                tools_needed=["web"],
                estimated_cost=0.001,
            )]
        
        # Build parallel groups - each step runs after previous
        groups = [[i+1] for i in range(len(subtasks))]
        
        return TaskPlan(
            task_id=f"plan_{task[:20].replace(' ', '_')}",
            original_task=task,
            subtasks=subtasks,
            parallel_groups=groups,
            estimated_total_cost=len(subtasks) * 0.001,
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

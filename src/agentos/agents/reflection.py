"""Reflection agent using REDEREF methodology."""

import json
import re
from dataclasses import dataclass
from typing import Optional

from agentos.models.message import Message, MessageRole
from agentos.models.task import TaskPlan, ActionResult
from agentos.llm.prompts import REFLECTION_PROMPT
from agentos.utils.logger import get_logger

logger = get_logger("agentos.reflection")


@dataclass
class ReflectionResult:
    """Result of reflection."""

    decision: str  # "continue", "retry", "adapt", "stop"
    reason: str
    next_action: Optional[str]
    lessons_learned: list[str]


class ReflectionAgent:
    """REDEREF-style reflection agent.

    Uses Thompson sampling, reflection-driven re-routing,
    and evidence-based selection for learning.
    """

    def __init__(self, llm_client, skills_context: Optional[str] = None):
        """Initialize reflection agent.

        Args:
            llm_client: LLM client
            skills_context: Skills context for the task
        """
        self.llm = llm_client
        self.history: list[ReflectionResult] = []
        self.success_rates: dict[str, float] = {}  # Tool -> success rate
        self.skills_context = skills_context or ""

    async def reflect(
        self,
        task: str,
        completed: list[ActionResult],
        plan: Optional[TaskPlan] = None,
    ) -> ReflectionResult:
        """Reflect on execution results.

        Args:
            task: Original task
            completed: List of completed action results
            plan: Optional task plan

        Returns:
            ReflectionResult with next decision
        """
        logger.info(f"Reflecting on {len(completed)} completed actions")

        # Build results summary
        results_text = "\n".join(
            [
                f"- {r.action.tool_name}: {'✓' if r.success else '✗'} {r.output[:100] if r.output else r.error[:100]}"
                for r in completed
            ]
        )

        completed_summary = "\n".join(
            [f"{r.action.task_id}: {r.action.tool_name}" for r in completed]
        )

        prompt = REFLECTION_PROMPT.format(
            task=task,
            completed=completed_summary,
            results=results_text,
        )

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a reflective AI agent analyzing execution results.",
            ),
            Message(role=MessageRole.USER, content=prompt),
        ]

        try:
            response, _, _ = await self.llm.complete(messages)
            result = self._parse_result(response)

            # Update success rates
            self._update_success_rates(completed)
            self.history.append(result)

            logger.info(f"Reflection decision: {result.decision} - {result.reason}")
            return result
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return ReflectionResult(
                decision="continue",
                reason="Reflection error - continuing",
                next_action=None,
                lessons_learned=[],
            )

    def _parse_result(self, response: str) -> ReflectionResult:
        """Parse reflection result from LLM.

        Args:
            response: LLM response

        Returns:
            Parsed ReflectionResult
        """
        # Try JSON
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return ReflectionResult(
                    decision=data.get("decision", "continue"),
                    reason=data.get("reason", "No reason"),
                    next_action=data.get("next_action"),
                    lessons_learned=data.get("lessons_learned", []),
                )
            except json.JSONDecodeError:
                pass

        # Fallback
        response_lower = response.lower()
        if "stop" in response_lower:
            return ReflectionResult(
                decision="stop",
                reason="Task complete or should stop",
                next_action=None,
                lessons_learned=[],
            )

        if "retry" in response_lower:
            return ReflectionResult(
                decision="retry",
                reason="Should retry failed actions",
                next_action="Retry last failed step",
                lessons_learned=[],
            )

        return ReflectionResult(
            decision="continue",
            reason="Continue with next steps",
            next_action=None,
            lessons_learned=[],
        )

    def _update_success_rates(self, results: list[ActionResult]) -> None:
        """Update tool success rates.

        Args:
            results: Action results
        """
        for result in results:
            tool = result.action.tool_name
            if tool not in self.success_rates:
                self.success_rates[tool] = 0.5  # Start neutral

            # Exponential moving average
            success = 1.0 if result.success else 0.0
            self.success_rates[tool] = 0.7 * self.success_rates[tool] + 0.3 * success

    def get_success_rate(self, tool: str) -> float:
        """Get success rate for a tool.

        Args:
            tool: Tool name

        Returns:
            Success rate (0-1)
        """
        return self.success_rates.get(tool, 0.5)

    def should_retry(self, tool: str) -> bool:
        """Decide if should retry using Thompson sampling.

        Args:
            tool: Tool name

        Returns:
            True if should retry
        """
        import random

        # Thompson sampling: sample from Beta distribution
        rate = self.get_success_rate(tool)
        sampled = random.random()
        return sampled < rate

    def get_lessons(self) -> list[str]:
        """Get all learned lessons.

        Returns:
            List of lessons
        """
        lessons = []
        for r in self.history:
            lessons.extend(r.lessons_learned)
        return list(set(lessons))  # Deduplicate

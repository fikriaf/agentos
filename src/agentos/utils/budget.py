"""Budget tracking for LLM costs (INTENT-style)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .logger import get_logger

logger = get_logger("agentos.budget")


@dataclass
class CostEntry:
    """Single cost entry."""

    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    operation: str


@dataclass
class Budget:
    """Budget configuration."""

    total: float
    remaining: float
    warn_threshold: float = 0.8  # Warn at 80% spent

    def is_exhausted(self) -> bool:
        """Check if budget exhausted."""
        return self.remaining <= 0

    def is_warning(self) -> bool:
        """Check if warning threshold reached."""
        return self.remaining <= self.total * (1 - self.warn_threshold)


class BudgetTracker:
    """Track and manage LLM costs (INTENT-style)."""

    # Token pricing per 1M tokens (approximate)
    PRICING = {
        # Claude
        "claude-3-5-sonnet-4": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-3": {"input": 0.8, "output": 4.0},
        "claude-sonnet-4-7": {"input": 3.0, "output": 15.0},
        # GPT
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        # Gemini
        "gemini-2-5-flash": {"input": 0.075, "output": 0.3},
        "gemini-2-5-pro": {"input": 1.25, "output": 5.0},
        # DeepSeek
        "deepseek-chat": {"input": 0.27, "output": 1.1},
        "deepseek-reasoner": {"input": 0.55, "output": 2.19},
        # Default
        "default": {"input": 1.0, "output": 5.0},
    }

    def __init__(self, budget: Optional[Budget] = None):
        """Initialize budget tracker.

        Args:
            budget: Optional budget configuration
        """
        self.budget = budget or Budget(total=10.0, remaining=10.0)
        self.entries: list[CostEntry] = []
        self.total_spent = 0.0

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate cost for LLM call.

        Args:
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            Cost in USD
        """
        pricing = self.PRICING.get(model, self.PRICING["default"])
        cost = (input_tokens / 1_000_000 * pricing["input"] +
                output_tokens / 1_000_000 * pricing["output"])
        return round(cost, 6)

    def track(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = "unknown",
    ) -> float:
        """Track LLM call cost.

        Args:
            model: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens
            operation: Operation description

        Returns:
            Cost of the call
        """
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        entry = CostEntry(
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            operation=operation,
        )
        self.entries.append(entry)
        self.total_spent += cost
        self.budget.remaining -= cost

        logger.debug(
            f"Cost tracked: {model} | "
            f"in:{input_tokens} out:{output_tokens} | "
            f"${cost:.4f} | remaining: ${self.budget.remaining:.4f}"
        )

        if self.budget.is_warning():
            logger.warning(
                f"Budget warning: ${self.budget.remaining:.4f} remaining "
                f"({(1 - self.budget.remaining / self.budget.total) * 100:.0f}% spent)"
            )

        return cost

    def estimate(self, subtask_count: int, avg_tokens_per_call: int = 2000) -> float:
        """Estimate cost for a plan.

        Args:
            subtask_count: Number of subtasks
            avg_tokens_per_call: Average tokens per LLM call

        Returns:
            Estimated cost
        """
        # Rough estimate: 2 calls per subtask (planning + reflection)
        calls = subtask_count * 2
        tokens = calls * avg_tokens_per_call
        return self.calculate_cost("default", tokens, tokens // 2)

    def can_afford(self, cost: float) -> bool:
        """Check if can afford a cost.

        Args:
            cost: Cost to check

        Returns:
            True if affordable
        """
        return self.budget.remaining >= cost

    def get_summary(self) -> dict:
        """Get cost summary.

        Returns:
            Summary dict
        """
        return {
            "total_budget": self.budget.total,
            "remaining": self.budget.remaining,
            "spent": self.total_spent,
            "calls": len(self.entries),
            "by_model": self._by_model(),
        }

    def _by_model(self) -> dict:
        """Group costs by model."""
        by_model: dict[str, dict] = {}
        for entry in self.entries:
            if entry.model not in by_model:
                by_model[entry.model] = {"calls": 0, "cost": 0.0, "tokens": 0}
            by_model[entry.model]["calls"] += 1
            by_model[entry.model]["cost"] += entry.cost
            by_model[entry.model]["tokens"] += entry.input_tokens + entry.output_tokens
        return by_model

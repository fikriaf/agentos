"""LLM client with OpenRouter multi-provider support."""

import os
from dataclasses import dataclass
from typing import Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from agentos.models.message import Message, MessageHistory
from agentos.utils.logger import get_logger
from agentos.utils.budget import BudgetTracker, Budget

logger = get_logger("agentos.llm")


@dataclass
class LLMConfig:
    """LLM configuration."""

    model: str = "minimax-m2.5-free"
    api_key: Optional[str] = None
    base_url: str = "https://opencode.ai/zen/v1"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
    system_prompt: Optional[str] = None


class LLMClient:
    """Multi-provider LLM client via OpenRouter."""

    DEFAULT_MODELS = [
        "anthropic/claude-3-5-sonnet-4-7",
        "openai/gpt-4o",
        "google/gemini-2-5-flash",
        "deepseek/deepseek-chat-v3",
    ]

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM client.

        Args:
            config: Optional LLM configuration
        """
        self.config = config or LLMConfig()
        self.api_key = self.config.api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENCODE_ZEN_API_KEY") or ""
        self.budget_tracker = BudgetTracker()

        if not self.api_key:
            logger.warning("No OpenRouter API key found. Set OPENROUTER_API_KEY env var.")

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agentos/agentos",
            "X-Title": "AgentOS",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def complete(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, int, int]:
        """Complete a chat completion.

        Args:
            messages: List of messages
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            Tuple of (response_text, input_tokens, output_tokens)
        """
        model = model or self.config.model
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Inject system prompt from config if not already present
        final_messages = list(messages)
        if self.config.system_prompt:
            has_system = any(m.role.value == "system" for m in messages)
            if not has_system:
                final_messages.insert(0, Message(role="system", content=self.config.system_prompt))

        payload = {
            "model": model,
            "messages": [m.to_dict() for m in final_messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.debug(f"LLM request: {model}, temp={temperature}")

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"LLM error: {response.status_code} - {response.text}")
                response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]

            # Track usage
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            cost = self.budget_tracker.track(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                operation="chat_complete",
            )

            logger.debug(
                f"LLM response: {len(content)} chars, "
                f"in:{input_tokens} out:{output_tokens}, "
                f"cost: ${cost:.4f}"
            )

            return content, input_tokens, output_tokens

    async def complete_simple(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Simple completion with prompt.

        Args:
            prompt: User prompt
            system: Optional system prompt
            **kwargs: Additional args for complete()

        Returns:
            Response text
        """
        messages = []
        if system:
            messages.append(Message(role="system", content=system))
        messages.append(Message(role="user", content=prompt))
        response, _, _ = await self.complete(messages, **kwargs)
        return response

    def set_budget(self, total: float) -> None:
        """Set budget.

        Args:
            total: Total budget in USD
        """
        self.budget_tracker = BudgetTracker(budget=Budget(total=total, remaining=total))

    def get_cost_summary(self) -> dict:
        """Get cost summary.

        Returns:
            Cost summary dict
        """
        return self.budget_tracker.get_summary()

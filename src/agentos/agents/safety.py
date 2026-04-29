"""Safety checker using MOSAIC methodology."""

import json
import re
from dataclasses import dataclass
from typing import Optional

from agentos.models.task import Action
from agentos.models.message import Message, MessageRole
from agentos.llm.prompts import SAFETY_PROMPT
from agentos.utils.logger import get_logger

logger = get_logger("agentos.safety")


@dataclass
class SafetyResult:
    """Result of safety check."""

    decision: str  # "proceed", "refuse", "verify"
    risk_level: str  # "low", "medium", "high", "critical"
    reason: str
    alternatives: list[str]
    verification_steps: list[str]


class SafetyChecker:
    """MOSAIC-style safety checker.

    Implements plan→check→act/refuse loop with explicit
    safety reasoning.
    """

    # Dangerous patterns to flag
    DANGEROUS_PATTERNS = [
        (r"rm\s+-rf\s+/", "Recursive delete of root directory"),
        (r"rm\s+-rf\s+/[a-z]+\s+/\s*$", "Recursive delete of system directory"),
        (r":()\s*\{\s*:\|:\s*&\s*\}", "Fork bomb"),
        (r"dd\s+if=/dev/zero\s+of=/dev/sd", "Disk wipe command"),
        (r"mkfs\.", "Filesystem format"),
        (r">\s*/dev/sd", "Direct device write"),
        (r"curl.*\|\s*sh", "Pipe to shell download"),
        (r"wget.*\|\s*sh", "Pipe to shell download"),
        (r"chmod\s+-R\s+777", "World-writable permissions"),
        (r"sudo\s+rm\s+-rf", "Root delete command"),
    ]

    # Patterns that require verification
    VERIFICATION_PATTERNS = [
        (r"rm\s+", "File deletion"),
        (r"chmod\s+", "Permission change"),
        (r"curl\s+", "Network download"),
        (r"wget\s+", "Network download"),
        (r"git\s+push", "Git push"),
        (r"docker\s+run", "Docker run"),
        (r"npm\s+install", "Package install"),
        (r"pip\s+install", "Python package install"),
        (r">\s*/", "File overwrite"),
    ]

    def __init__(self, llm_client):
        """Initialize safety checker.

        Args:
            llm_client: LLM client for analysis
        """
        self.llm = llm_client
        self.dangerous_history: list[str] = []

    async def check(
        self,
        action: Action,
        context: Optional[dict] = None,
    ) -> SafetyResult:
        """Check if action is safe (MOSAIC-style).

        Args:
            action: Action to check
            context: Optional context dict

        Returns:
            SafetyResult with decision
        """
        logger.debug(f"Safety check: {action.tool_name} | {str(action.args)[:50]}...")

        # Pattern-based quick check first
        pattern_result = self._pattern_check(action)
        if pattern_result.decision == "refuse":
            logger.warning(f"Blocked by pattern: {pattern_result.reason}")
            return pattern_result

        if pattern_result.decision == "verify":
            logger.info(f"Requires verification: {pattern_result.reason}")
            return pattern_result

        # Fast-path for known safe tools - skip LLM check
        if action.tool_name in ("web", "skills", "file", "http"):
            logger.info(f"Tool '{action.tool_name}' is safe - allowing without LLM check")
            return SafetyResult(
                decision="proceed",
                risk_level="low",
                reason=f"Tool '{action.tool_name}' is a safe, read-only operation",
                alternatives=[],
                verification_steps=[],
            )

        # LLM-based deep check for other tools
        return await self._llm_check(action, context or {})

    def _pattern_check(self, action: Action) -> SafetyResult:
        """Quick pattern-based safety check.

        Args:
            action: Action to check

        Returns:
            SafetyResult if pattern matches
        """
        action_str = f"{action.tool_name} {json.dumps(action.args)}"

        # Check dangerous patterns
        for pattern, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, action_str, re.IGNORECASE):
                self.dangerous_history.append(action_str)
                return SafetyResult(
                    decision="refuse",
                    risk_level="critical",
                    reason=reason,
                    alternatives=["Use safer alternatives", "Ask user for confirmation"],
                    verification_steps=[],
                )

        # Check verification patterns
        for pattern, reason in self.VERIFICATION_PATTERNS:
            if re.search(pattern, action_str, re.IGNORECASE):
                return SafetyResult(
                    decision="verify",
                    risk_level="medium",
                    reason=f"Action requires verification: {reason}",
                    alternatives=[f"Add --dry-run flag", "Review before execution"],
                    verification_steps=[
                        "Show exact command to user",
                        "Request explicit confirmation",
                    ],
                )

        return SafetyResult(
            decision="proceed",
            risk_level="low",
            reason="No safety concerns detected",
            alternatives=[],
            verification_steps=[],
        )

    async def _llm_check(
        self,
        action: Action,
        context: dict,
    ) -> SafetyResult:
        """LLM-based deep safety analysis.

        Args:
            action: Action to check
            context: Context dict

        Returns:
            SafetyResult from LLM analysis
        """
        prompt = SAFETY_PROMPT.format(
            action=f"{action.tool_name} with args {json.dumps(action.args)}",
            context=json.dumps(context, indent=2),
        )

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a security expert analyzing AI agent actions.",
            ),
            Message(role=MessageRole.USER, content=prompt),
        ]

        try:
            response, _, _ = await self.llm.complete(messages)
            return self._parse_safety_result(response)
        except Exception as e:
            logger.error(f"LLM safety check failed: {e}")
            # Fail-safe: require verification on error
            return SafetyResult(
                decision="verify",
                risk_level="medium",
                reason="Safety check error - requiring verification",
                alternatives=["Manual review"],
                verification_steps=["Review action manually"],
            )

    def _parse_safety_result(self, response: str) -> SafetyResult:
        """Parse LLM response into SafetyResult.

        Args:
            response: LLM response

        Returns:
            Parsed SafetyResult
        """
        # Try JSON
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return SafetyResult(
                    decision=data.get("decision", "verify"),
                    risk_level=data.get("risk_level", "medium"),
                    reason=data.get("reason", "No reason provided"),
                    alternatives=data.get("alternatives", []),
                    verification_steps=data.get("verification_steps", []),
                )
            except json.JSONDecodeError:
                pass

        # Fallback based on keywords
        response_lower = response.lower()
        if "refuse" in response_lower or "dangerous" in response_lower or "critical" in response_lower:
            return SafetyResult(
                decision="refuse",
                risk_level="high",
                reason="LLM flagged as dangerous",
                alternatives=["Reconsider approach", "Ask user"],
                verification_steps=[],
            )

        if "verify" in response_lower or "confirm" in response_lower:
            return SafetyResult(
                decision="verify",
                risk_level="medium",
                reason="LLM recommends verification",
                alternatives=["Proceed with caution"],
                verification_steps=["Manual review"],
            )

        return SafetyResult(
            decision="proceed",
            risk_level="low",
            reason="No major concerns",
            alternatives=[],
            verification_steps=[],
        )

    def get_dangerous_history(self) -> list[str]:
        """Get history of blocked dangerous actions.

        Returns:
            List of dangerous action strings
        """
        return self.dangerous_history.copy()

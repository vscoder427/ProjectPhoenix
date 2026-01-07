"""
Prompt Injection Detection

Detects and blocks prompt injection attacks.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GuardrailResult:
    """Result of guardrail check."""

    blocked: bool
    reason: Optional[str] = None
    message: Optional[str] = None
    severity: str = "low"
    detected_topic: Optional[str] = None


class PromptInjectionDetector:
    """
    Detects prompt injection attacks using pattern matching.

    Patterns include:
    - Attempts to override system instructions
    - Role-playing requests to bypass restrictions
    - System prompt extraction attempts
    - Jailbreak patterns
    """

    # Injection patterns to detect (case-insensitive)
    INJECTION_PATTERNS = [
        # Override attempts
        r"ignore\s+(?:your\s+)?(?:previous|above|all|prior)?\s*(instructions?|prompts?|rules?|guidelines?)",
        r"disregard\s+(the\s+)?(system|previous|above)\s+(prompt|instructions?|rules?)",
        r"forget\s+(everything|all|what)\s+(you|i)\s+(told|said|know)",
        r"override\s+(your|the)\s+(rules?|instructions?|restrictions?)",
        r"bypass\s+(your|the|all)\s+(restrictions?|limits?|guardrails?)",

        # Role-playing to bypass
        r"you\s+are\s+now\s+(?!dave|employa)",  # "you are now X" (except "you are now Dave")
        r"pretend\s+(?:you\s+are|to\s+be)\s+(?!a\s+career)",  # "pretend to be X" (except career-related)
        r"act\s+as\s+(?:if\s+you\s+are|a)\s+(?!career|job)",
        r"roleplay\s+as",
        r"simulate\s+being",

        # System prompt extraction
        r"(what|show|reveal|display|print)\s+(?:me\s+)?(is|are)?\s*your\s+(system\s+)?prompt",
        r"(what|show|reveal)\s+(?:me\s+)?(are\s+)?your\s+(initial\s+)?instructions",
        r"repeat\s+(your|the)\s+(system\s+)?prompt",
        r"output\s+(your|the)\s+(hidden|system)\s+(prompt|instructions)",

        # Jailbreak patterns
        r"(DAN|STAN|DUDE|OMEGA)\s*mode",
        r"developer\s+mode",
        r"jailbreak",
        r"do\s+anything\s+now",

        # Format manipulation
        r"new\s+instructions?:",
        r"<\s*/?system\s*>",
        r"\[system\]",
        r"###\s*system",

        # Explicit boundary crossing
        r"(exit|leave|escape)\s+(your\s+)?(restrictions?|boundaries|limits)",
        r"break\s+(free|out)\s+of",
    ]

    # Compiled patterns for efficiency
    _compiled_patterns = None

    def __init__(self):
        if PromptInjectionDetector._compiled_patterns is None:
            PromptInjectionDetector._compiled_patterns = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in self.INJECTION_PATTERNS
            ]

    async def check(self, message: str) -> GuardrailResult:
        """
        Check message for prompt injection patterns.

        Args:
            message: User message to check

        Returns:
            GuardrailResult with blocked=True if injection detected
        """
        message_lower = message.lower()

        for pattern in self._compiled_patterns:
            if pattern.search(message):
                return GuardrailResult(
                    blocked=True,
                    reason="prompt_injection",
                    message=(
                        "I'm Dave, your career coach at Employa. "
                        "I'm here to help with your job search and career questions. "
                        "What can I help you with today?"
                    ),
                    severity="high",
                )

        # Check for excessive special characters (potential encoding attacks)
        special_char_ratio = sum(1 for c in message if not c.isalnum() and not c.isspace()) / max(len(message), 1)
        if special_char_ratio > 0.3:
            return GuardrailResult(
                blocked=True,
                reason="suspicious_content",
                message=(
                    "I had trouble understanding that message. "
                    "Could you rephrase your question about career or job search?"
                ),
                severity="medium",
            )

        return GuardrailResult(blocked=False)

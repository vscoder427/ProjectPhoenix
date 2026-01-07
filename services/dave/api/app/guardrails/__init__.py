"""
Guardrails System

Protects Dave from:
- Prompt injection attacks
- Off-topic usage
- Rate limit abuse
- Malicious content
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.guardrails.prompt_injection import PromptInjectionDetector
from app.guardrails.topic_classifier import TopicClassifier
from app.guardrails.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class GuardrailResult:
    """Result of guardrail check."""

    blocked: bool
    reason: Optional[str] = None
    message: Optional[str] = None
    severity: str = "low"  # low, medium, high
    detected_topic: Optional[str] = None


class GuardrailsOrchestrator:
    """
    Orchestrates all guardrail checks.

    Runs checks in order of speed and criticality:
    1. Rate limiting (fast, prevents abuse)
    2. Prompt injection (fast, security critical)
    3. Topic classification (may need AI, user experience)
    """

    def __init__(self):
        self.injection_detector = PromptInjectionDetector()
        self.topic_classifier = TopicClassifier()
        self.rate_limiter = RateLimiter()

    async def check(
        self,
        message: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_tier: str = "free",
    ) -> GuardrailResult:
        """
        Run all guardrail checks on a message.

        Args:
            message: User message to check
            user_id: Optional user ID for rate limiting
            ip_address: Optional IP for rate limiting
            user_tier: User tier for rate limit thresholds

        Returns:
            GuardrailResult with blocked status and details
        """
        # 1. Rate limiting (fastest check)
        rate_result = await self.rate_limiter.check(
            user_id=user_id,
            ip_address=ip_address,
            tier=user_tier,
        )
        if rate_result.blocked:
            logger.warning(f"Rate limit exceeded for user={user_id}, ip={ip_address}")
            return rate_result

        # 2. Prompt injection detection (fast, security critical)
        injection_result = await self.injection_detector.check(message)
        if injection_result.blocked:
            logger.warning(f"Prompt injection detected: {injection_result.reason}")
            return injection_result

        # 3. Topic classification (may use AI)
        topic_result = await self.topic_classifier.check(message)
        if topic_result.blocked:
            logger.info(f"Off-topic message redirected: {topic_result.detected_topic}")
            return topic_result

        # All checks passed
        return GuardrailResult(
            blocked=False,
            detected_topic=topic_result.detected_topic,
        )

    async def record_request(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tokens_used: int = 0,
    ):
        """Record a successful request for rate limiting."""
        await self.rate_limiter.record_request(
            user_id=user_id,
            ip_address=ip_address,
            tokens_used=tokens_used,
        )


# Singleton instance
_guardrails: Optional[GuardrailsOrchestrator] = None


def get_guardrails() -> GuardrailsOrchestrator:
    """Get cached guardrails orchestrator."""
    global _guardrails
    if _guardrails is None:
        _guardrails = GuardrailsOrchestrator()
    return _guardrails

"""
Topic Classifier

Classifies messages and redirects off-topic requests politely.
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


class TopicClassifier:
    """
    Classifies message topics and redirects off-topic requests.

    Uses keyword matching for fast classification.
    Falls back to polite redirect for unrecognized topics.
    """

    # Career-related keywords that indicate on-topic messages
    CAREER_KEYWORDS = {
        # Job search
        "job", "jobs", "career", "careers", "work", "working", "employment", "employed",
        "unemployed", "hiring", "hired", "hire", "apply", "application", "applying",
        "position", "role", "opportunity", "opportunities",

        # Resume & cover letter
        "resume", "cv", "cover letter", "portfolio", "linkedin", "profile",

        # Interview
        "interview", "interviewing", "interviews", "meeting", "call",

        # Skills & qualifications
        "skill", "skills", "experience", "qualification", "qualifications",
        "education", "training", "certification", "certificate", "degree",

        # Workplace
        "workplace", "office", "coworker", "coworkers", "manager", "boss",
        "employer", "company", "companies", "organization", "business",

        # Salary & benefits
        "salary", "pay", "wage", "wages", "compensation", "benefits", "insurance",
        "401k", "pto", "vacation",

        # Career development
        "promotion", "raise", "growth", "advancement", "development",
        "networking", "network", "mentor", "mentoring",

        # Recovery-specific career
        "recovery", "background", "gap", "explanation", "second chance",
        "fair chance", "background check", "record", "conviction",

        # Employa-specific
        "employa", "dave", "match", "matching", "score", "employer",
    }

    # Topics that need polite redirects
    REDIRECT_RESPONSES = {
        "medical": (
            "I appreciate you sharing that with me. While I care about your wellbeing, "
            "I'm best equipped to help with career-related questions. For health concerns, "
            "please reach out to a healthcare professional. "
            "Now, is there anything I can help you with regarding your job search?"
        ),
        "therapy": (
            "Thank you for trusting me with that. I want to be honest - I'm a career coach, "
            "not a counselor. For personal challenges, please consider speaking with a "
            "mental health professional or your support network. "
            "In the meantime, how can I support your career goals?"
        ),
        "legal": (
            "That sounds like a legal matter that's beyond my expertise. "
            "I'd recommend consulting with a lawyer or legal aid organization. "
            "What I can help with is navigating the job search process. "
            "Is there anything career-related I can assist with?"
        ),
        "coding": (
            "While I'd love to help with coding, my specialty is career coaching and job search support. "
            "For programming questions, sites like Stack Overflow are great resources. "
            "But if you're looking for tech jobs or want to discuss your career in tech, I'm all ears!"
        ),
        "general": (
            "That's an interesting topic! I'm most helpful with career and job search questions though. "
            "Is there anything about your employment journey I can help with today?"
        ),
    }

    # Keywords that indicate off-topic categories
    OFF_TOPIC_KEYWORDS = {
        "medical": {"doctor", "hospital", "medicine", "prescription", "symptoms", "diagnosis", "medical", "health condition", "treatment plan"},
        "therapy": {"therapist", "counselor", "depression", "anxiety", "trauma", "mental health", "suicidal", "self-harm"},
        "legal": {"lawyer", "attorney", "lawsuit", "sue", "court", "legal advice", "custody", "divorce"},
        "coding": {"python", "javascript", "code", "programming", "debug", "function", "api", "database", "algorithm"},
    }

    async def check(self, message: str) -> GuardrailResult:
        """
        Classify message topic and redirect if off-topic.

        Args:
            message: User message to check

        Returns:
            GuardrailResult with redirect message if off-topic
        """
        message_lower = message.lower()
        words = set(re.findall(r'\w+', message_lower))

        # Check if message contains career keywords
        career_matches = words & self.CAREER_KEYWORDS
        if career_matches:
            # On-topic - allow through
            return GuardrailResult(
                blocked=False,
                detected_topic="career",
            )

        # Check for specific off-topic categories
        for category, keywords in self.OFF_TOPIC_KEYWORDS.items():
            if words & keywords:
                return GuardrailResult(
                    blocked=True,
                    reason="off_topic",
                    message=self.REDIRECT_RESPONSES[category],
                    severity="low",
                    detected_topic=category,
                )

        # Check message length - very short messages might just be greetings
        if len(message.strip()) < 20:
            # Allow short messages through (greetings, etc.)
            return GuardrailResult(
                blocked=False,
                detected_topic="greeting",
            )

        # For longer messages without career keywords, gently redirect
        # But don't block - the AI can still try to help
        return GuardrailResult(
            blocked=False,
            detected_topic="general",
        )

    def get_redirect_message(self, topic: str) -> str:
        """Get the redirect message for a topic."""
        return self.REDIRECT_RESPONSES.get(topic, self.REDIRECT_RESPONSES["general"])

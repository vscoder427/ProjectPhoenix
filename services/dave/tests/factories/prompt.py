"""
Prompt and prompt version test data factories.

These factories generate realistic prompt management data
for testing without requiring database access.
"""
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional


class PromptFactory:
    """Factory for creating test prompt data."""

    @staticmethod
    def create(**overrides) -> Dict[str, Any]:
        """
        Create a test prompt with sensible defaults.

        Args:
            **overrides: Override any default fields

        Returns:
            Dict representing a prompt record

        Example:
            >>> prompt = PromptFactory.create(
            ...     category="system",
            ...     name="dave_core_instructions"
            ... )
        """
        defaults = {
            "id": str(uuid4()),
            "category": "system",
            "name": "test_prompt",
            "description": "Test prompt for unit testing",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        return {**defaults, **overrides}

    @staticmethod
    def system_prompt(**overrides) -> Dict[str, Any]:
        """Create a system prompt."""
        return PromptFactory.create(
            category="system",
            name="dave_system_prompt",
            description="Core Dave system instructions",
            **overrides,
        )

    @staticmethod
    def user_prompt(**overrides) -> Dict[str, Any]:
        """Create a user-facing prompt template."""
        return PromptFactory.create(
            category="user",
            name="greeting_template",
            description="User greeting prompt template",
            **overrides,
        )

    @staticmethod
    def guardrail_prompt(**overrides) -> Dict[str, Any]:
        """Create a guardrail prompt."""
        return PromptFactory.create(
            category="guardrail",
            name="topic_classification",
            description="Prompt for classifying user message topics",
            **overrides,
        )


class PromptVersionFactory:
    """Factory for creating test prompt version data."""

    @staticmethod
    def create(**overrides) -> Dict[str, Any]:
        """
        Create a test prompt version with sensible defaults.

        Args:
            **overrides: Override any default fields

        Returns:
            Dict representing a prompt version record

        Example:
            >>> version = PromptVersionFactory.create(
            ...     prompt_id="test-prompt-123",
            ...     version=2,
            ...     content="Updated prompt content"
            ... )
        """
        defaults = {
            "id": str(uuid4()),
            "prompt_id": str(uuid4()),
            "version": 1,
            "content": "Test prompt content with {variable} placeholders",
            "variables": ["variable"],
            "is_current": True,
            "created_at": datetime.utcnow(),
            "created_by": "test-admin",
            "change_notes": "Initial test version",
        }
        return {**defaults, **overrides}

    @staticmethod
    def with_variables(
        variables: List[str], content: Optional[str] = None, **overrides
    ) -> Dict[str, Any]:
        """
        Create a prompt version with specific variables.

        Args:
            variables: List of variable names
            content: Optional content with variable placeholders
            **overrides: Additional field overrides

        Returns:
            Dict representing prompt version with variables

        Example:
            >>> version = PromptVersionFactory.with_variables(
            ...     variables=["user_name", "user_goal"],
            ...     content="Hello {user_name}, let's work on {user_goal}"
            ... )
        """
        if content is None:
            # Generate content with all variables as placeholders
            content = "Test prompt: " + ", ".join(f"{{{var}}}" for var in variables)

        return PromptVersionFactory.create(
            variables=variables, content=content, **overrides
        )

    @staticmethod
    def version_history(
        prompt_id: str, num_versions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Create a version history for a prompt.

        Args:
            prompt_id: Prompt ID for all versions
            num_versions: Number of versions to create (default: 3)

        Returns:
            List of prompt version dicts in chronological order

        Example:
            >>> history = PromptVersionFactory.version_history(
            ...     prompt_id="test-prompt-123",
            ...     num_versions=5
            ... )
        """
        versions = []
        base_time = datetime.utcnow()

        for i in range(num_versions):
            is_latest = i == num_versions - 1

            version = PromptVersionFactory.create(
                prompt_id=prompt_id,
                version=i + 1,
                content=f"Prompt content version {i + 1}",
                is_current=is_latest,
                created_at=datetime(
                    base_time.year,
                    base_time.month,
                    base_time.day,
                    base_time.hour,
                    base_time.minute - (num_versions - i - 1),
                ),
                change_notes=f"Version {i + 1} updates",
            )
            versions.append(version)

        return versions

    @staticmethod
    def dave_core_instructions(**overrides) -> Dict[str, Any]:
        """
        Create Dave's core system instructions prompt version.

        Returns:
            Dict representing Dave's main system prompt version
        """
        return PromptVersionFactory.create(
            content="""You are Dave, Employa's AI career coach specializing in recovery-focused career guidance.

Core Principles:
1. **Trauma-Informed**: Use supportive, non-judgmental language
2. **Recovery-Focused**: Understand the unique challenges of job seeking in recovery
3. **Practical Guidance**: Provide actionable career advice
4. **Resource-Rich**: Connect users with relevant resources
5. **Empowering**: Build confidence and self-efficacy

Communication Style:
- Warm and supportive, never clinical or patronizing
- Strength-based focus on skills and potential
- Honest about challenges while maintaining hope
- Respectful of privacy around recovery details

Knowledge Areas:
- Resume building and interview preparation
- Recovery-friendly employers and workplace accommodations
- Skill translation from recovery experiences
- Networking and professional development
- Work-life balance in recovery

When users ask about {user_goal}, tailor responses to their recovery stage and career aspirations.
""",
            variables=["user_goal"],
            is_current=True,
            change_notes="Core Dave personality and instructions",
            **overrides,
        )

    @staticmethod
    def topic_classifier(**overrides) -> Dict[str, Any]:
        """
        Create topic classification guardrail prompt version.

        Returns:
            Dict representing topic classification prompt
        """
        return PromptVersionFactory.create(
            content="""Classify the user's message into ONE of these categories:

1. **career_guidance**: Resume help, interview prep, job search strategies
2. **recovery_support**: Questions about recovery, 12-step programs, sobriety
3. **employer_questions**: Employer resources, hiring practices, accommodations
4. **off_topic**: Unrelated to career or recovery (politely redirect)

User message: {user_message}

Respond with ONLY the category name, nothing else.
""",
            variables=["user_message"],
            is_current=True,
            change_notes="Topic classification for guardrails",
            **overrides,
        )

"""
Conversation and message test data factories.

These factories generate realistic conversation and message data
for testing without requiring database access.
"""
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class ConversationFactory:
    """Factory for creating test conversation data."""

    @staticmethod
    def create(**overrides) -> Dict[str, Any]:
        """
        Create a test conversation with sensible defaults.

        Args:
            **overrides: Override any default fields

        Returns:
            Dict representing a conversation record

        Example:
            >>> conversation = ConversationFactory.create(
            ...     user_id="test-user-123",
            ...     title="Job Search Help"
            ... )
        """
        defaults = {
            "id": str(uuid4()),
            "user_id": "00000000-0000-0000-0000-000000000001",  # Default test user
            "title": "Test Conversation",
            "status": "active",
            "context": {
                "user_type": "job_seeker",
                "recovery_stage": "intermediate",
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        return {**defaults, **overrides}

    @staticmethod
    def with_messages(
        num_messages: int = 5,
        conversation_overrides: Optional[Dict] = None,
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a conversation with messages.

        Args:
            num_messages: Number of messages to create (default: 5)
            conversation_overrides: Optional overrides for conversation

        Returns:
            Tuple of (conversation, messages list)

        Example:
            >>> conversation, messages = ConversationFactory.with_messages(
            ...     num_messages=10,
            ...     conversation_overrides={"user_id": "custom-user"}
            ... )
        """
        conversation = ConversationFactory.create(**(conversation_overrides or {}))
        messages = [
            MessageFactory.create(
                conversation_id=conversation["id"],
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i + 1}",
                timestamp=conversation["created_at"] + timedelta(minutes=i),
            )
            for i in range(num_messages)
        ]
        return conversation, messages

    @staticmethod
    def archived() -> Dict[str, Any]:
        """Create an archived conversation."""
        return ConversationFactory.create(status="archived")

    @staticmethod
    def deleted() -> Dict[str, Any]:
        """Create a deleted conversation."""
        return ConversationFactory.create(status="deleted")


class MessageFactory:
    """Factory for creating test message data."""

    @staticmethod
    def create(**overrides) -> Dict[str, Any]:
        """
        Create a test message with sensible defaults.

        Args:
            **overrides: Override any default fields

        Returns:
            Dict representing a message record

        Example:
            >>> message = MessageFactory.create(
            ...     role="user",
            ...     content="Help me find a job"
            ... )
        """
        defaults = {
            "id": str(uuid4()),
            "conversation_id": str(uuid4()),
            "role": "user",
            "content": "Test message content",
            "timestamp": datetime.utcnow(),
            "metadata": {},
            "resources": [],
            "follow_up_suggestions": [],
        }
        return {**defaults, **overrides}

    @staticmethod
    def user_message(content: str, **overrides) -> Dict[str, Any]:
        """Create a user message."""
        return MessageFactory.create(role="user", content=content, **overrides)

    @staticmethod
    def assistant_message(
        content: str,
        resources: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None,
        **overrides,
    ) -> Dict[str, Any]:
        """
        Create an assistant message with resources and suggestions.

        Args:
            content: Message content
            resources: List of resource URLs
            suggestions: List of follow-up suggestions
            **overrides: Additional field overrides

        Returns:
            Dict representing assistant message
        """
        return MessageFactory.create(
            role="assistant",
            content=content,
            resources=resources or [],
            follow_up_suggestions=suggestions or [],
            metadata={
                "model": "gemini-1.5-pro",
                "tokens_used": 150,
                "latency_ms": 250,
            },
            **overrides,
        )

    @staticmethod
    def system_message(content: str, **overrides) -> Dict[str, Any]:
        """Create a system message."""
        return MessageFactory.create(role="system", content=content, **overrides)

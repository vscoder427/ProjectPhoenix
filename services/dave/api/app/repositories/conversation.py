"""
Conversation Repository

Database operations for AI conversations and messages.
"""

import logging
from typing import Optional
from uuid import uuid4
from datetime import datetime

from app.clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for ai_conversations and ai_messages database operations."""

    def __init__(self):
        self.client = get_supabase_client()

    async def create_conversation(
        self,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Create a new conversation.

        Args:
            user_id: Optional user ID (None for anonymous)
            title: Optional conversation title
            context: Optional context metadata

        Returns:
            Created conversation record
        """
        try:
            conversation_id = str(uuid4())
            data = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title or "New Conversation",
                "status": "active",
                "context": context or {},
            }

            result = self.client.table("ai_conversations").insert(data).execute()

            if result.data:
                return result.data[0]
            raise Exception("Failed to create conversation")

        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get a conversation by ID."""
        try:
            result = self.client.table("ai_conversations").select("*").eq(
                "id", conversation_id
            ).execute()

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id}: {e}")
            raise

    async def get_user_conversations(
        self,
        user_id: str,
        status: str = "active",
        limit: int = 50,
    ) -> list[dict]:
        """Get conversations for a user."""
        try:
            result = self.client.table("ai_conversations").select("*").eq(
                "user_id", user_id
            ).eq("status", status).order(
                "updated_at", desc=True
            ).limit(limit).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching conversations for user {user_id}: {e}")
            raise

    async def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> bool:
        """Update a conversation."""
        try:
            data = {"updated_at": datetime.utcnow().isoformat()}
            if title:
                data["title"] = title
            if status:
                data["status"] = status
            if context:
                data["context"] = context

            self.client.table("ai_conversations").update(data).eq(
                "id", conversation_id
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise

    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation (soft delete)."""
        return await self.update_conversation(conversation_id, status="archived")

    async def add_message(
        self,
        conversation_id: str,
        role: str,  # user, assistant, system
        content: str,
        metadata: Optional[dict] = None,
        resources: Optional[list] = None,
        follow_up_suggestions: Optional[list] = None,
    ) -> dict:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata (tokens, latency, etc.)
            resources: Optional knowledge base resources
            follow_up_suggestions: Optional follow-up suggestions

        Returns:
            Created message record
        """
        try:
            message_id = str(uuid4())
            data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "resources": resources or [],
                "follow_up_suggestions": follow_up_suggestions or [],
            }

            result = self.client.table("ai_messages").insert(data).execute()

            if result.data:
                # Update conversation timestamp
                await self.update_conversation(conversation_id)
                return result.data[0]

            raise Exception("Failed to add message")

        except Exception as e:
            logger.error(f"Error adding message to {conversation_id}: {e}")
            raise

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Max messages to return
            before_id: Optional message ID for pagination

        Returns:
            List of messages, oldest first
        """
        try:
            query = self.client.table("ai_messages").select("*").eq(
                "conversation_id", conversation_id
            ).order("timestamp", desc=False).limit(limit)

            if before_id:
                # Get timestamp of before_id message for pagination
                before_msg = self.client.table("ai_messages").select("timestamp").eq(
                    "id", before_id
                ).execute()
                if before_msg.data:
                    query = query.lt("timestamp", before_msg.data[0]["timestamp"])

            result = query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching messages for {conversation_id}: {e}")
            raise

    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get most recent messages for context building.

        Returns messages in chronological order (oldest first).
        """
        try:
            # Get last N messages
            result = self.client.table("ai_messages").select("*").eq(
                "conversation_id", conversation_id
            ).order("timestamp", desc=True).limit(limit).execute()

            # Reverse to get chronological order
            messages = result.data or []
            messages.reverse()
            return messages

        except Exception as e:
            logger.error(f"Error fetching recent messages for {conversation_id}: {e}")
            raise

    async def get_message_count(self, conversation_id: str) -> int:
        """Get total message count for a conversation."""
        try:
            result = self.client.table("ai_messages").select(
                "id", count="exact"
            ).eq("conversation_id", conversation_id).execute()

            return result.count or 0

        except Exception as e:
            logger.error(f"Error counting messages for {conversation_id}: {e}")
            return 0

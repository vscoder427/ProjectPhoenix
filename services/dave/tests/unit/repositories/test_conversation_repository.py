"""
Unit tests for ConversationRepository.

Tests database operations with mocked Supabase client.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.conversation import ConversationRepository


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for repository tests."""
    client = MagicMock()
    # Mock table method returns a fluent builder
    client.table = MagicMock()
    return client


@pytest.fixture
def conversation_repo(mock_supabase_client):
    """ConversationRepository with mocked Supabase client."""
    with patch("app.repositories.conversation.get_supabase_client", return_value=mock_supabase_client):
        repo = ConversationRepository()
        repo.client = mock_supabase_client  # Ensure mock is used
        return repo


class TestCreateConversation:
    """Test conversation creation."""

    @pytest.mark.asyncio
    async def test_create_conversation_with_user_id(self, conversation_repo, mock_supabase_client):
        """Test creating conversation with user_id."""
        user_id = str(uuid4())
        context = {"user_type": "job_seeker", "stage": "active_search"}

        # Mock the insert chain
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "user_id": user_id,
            "status": "active",
            "context": context,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }]

        mock_builder = MagicMock()
        mock_builder.insert = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.create_conversation(user_id=user_id, context=context)

        # Verify
        assert result is not None
        assert result["user_id"] == user_id
        assert result["status"] == "active"
        assert result["context"] == context

        # Verify Supabase was called correctly
        mock_supabase_client.table.assert_called_once_with("ai_conversations")
        mock_builder.insert.assert_called_once()
        insert_data = mock_builder.insert.call_args[0][0]
        assert insert_data["user_id"] == user_id
        assert insert_data["context"] == context

    @pytest.mark.asyncio
    async def test_create_conversation_anonymous(self, conversation_repo, mock_supabase_client):
        """Test creating anonymous conversation (user_id=None)."""
        # Mock the insert chain
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "user_id": None,
            "status": "active",
            "context": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }]

        mock_builder = MagicMock()
        mock_builder.insert = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.create_conversation(user_id=None)

        # Verify
        assert result is not None
        assert result["user_id"] is None
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_conversation_error_handling(self, conversation_repo, mock_supabase_client):
        """Test error handling when creation fails."""
        # Mock error response
        mock_builder = MagicMock()
        mock_builder.insert = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(side_effect=Exception("Database error"))
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Database error"):
            await conversation_repo.create_conversation(user_id=str(uuid4()))


class TestAddMessage:
    """Test adding messages to conversations."""

    @pytest.mark.asyncio
    async def test_add_user_message(self, conversation_repo, mock_supabase_client):
        """Test adding a user message."""
        conversation_id = str(uuid4())
        content = "I need help with my resume"

        # Mock the insert chain
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "conversation_id": conversation_id,
            "role": "user",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]

        mock_builder = MagicMock()
        mock_builder.insert = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

        # Verify
        assert result is not None
        assert result["conversation_id"] == conversation_id
        assert result["role"] == "user"
        assert result["content"] == content

    @pytest.mark.asyncio
    async def test_add_assistant_message_with_metadata(self, conversation_repo, mock_supabase_client):
        """Test adding assistant message with metadata."""
        conversation_id = str(uuid4())
        content = "I can help you with that!"
        metadata = {"model": "gemini-2.0-flash", "tokens": 150}
        resources = ["https://example.com/article1"]

        # Mock the insert chain
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": content,
            "metadata": metadata,
            "resources": resources,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]

        mock_builder = MagicMock()
        mock_builder.insert = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            metadata=metadata,
            resources=resources,
        )

        # Verify
        assert result is not None
        assert result["metadata"] == metadata
        assert result["resources"] == resources


class TestGetConversation:
    """Test retrieving conversations."""

    @pytest.mark.asyncio
    async def test_get_existing_conversation(self, conversation_repo, mock_supabase_client):
        """Test getting an existing conversation."""
        conversation_id = str(uuid4())

        # Mock the select chain
        mock_response = MagicMock()
        mock_response.data = [{
            "id": conversation_id,
            "user_id": str(uuid4()),
            "status": "active",
            "context": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.single = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_conversation(conversation_id)

        # Verify
        assert result is not None
        assert result["id"] == conversation_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, conversation_repo, mock_supabase_client):
        """Test getting conversation that doesn't exist."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.single = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_conversation(str(uuid4()))

        # Verify
        assert result is None


class TestGetRecentMessages:
    """Test retrieving recent messages."""

    @pytest.mark.asyncio
    async def test_get_recent_messages_with_limit(self, conversation_repo, mock_supabase_client):
        """Test getting recent messages with limit."""
        conversation_id = str(uuid4())

        # Mock response with 3 messages (ordered oldest first for context window)
        mock_response = MagicMock()
        mock_response.data = [
            {"id": str(uuid4()), "role": "user", "content": "Message 1"},
            {"id": str(uuid4()), "role": "assistant", "content": "Message 2"},
            {"id": str(uuid4()), "role": "user", "content": "Message 3"},
        ]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.limit = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_recent_messages(conversation_id, limit=10)

        # Verify
        assert len(result) == 3
        mock_builder.limit.assert_called_once_with(10)
        # The repository orders by timestamp descending
        mock_builder.order.assert_called_once_with("timestamp", desc=True)


class TestGetUserConversations:
    """Test getting user's conversations."""

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, conversation_repo, mock_supabase_client):
        """Test getting all conversations for a user."""
        user_id = str(uuid4())

        # Mock response with 2 conversations
        mock_response = MagicMock()
        mock_response.data = [
            {"id": str(uuid4()), "user_id": user_id, "status": "active"},
            {"id": str(uuid4()), "user_id": user_id, "status": "archived"},
        ]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.limit = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_user_conversations(user_id, limit=10)

        # Verify
        assert len(result) == 2
        assert all(conv["user_id"] == user_id for conv in result)


class TestGetMessages:
    """Test retrieving messages with pagination."""

    @pytest.mark.asyncio
    async def test_get_messages_basic(self, conversation_repo, mock_supabase_client):
        """Test getting messages without pagination."""
        conversation_id = str(uuid4())

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {"id": str(uuid4()), "role": "user", "content": "Message 1"},
            {"id": str(uuid4()), "role": "assistant", "content": "Message 2"},
        ]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.limit = MagicMock(return_value=mock_builder)
        mock_builder.lt = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_messages(conversation_id, limit=10)

        # Verify
        assert len(result) == 2
        mock_builder.limit.assert_called_with(10)
        mock_builder.order.assert_called_with("timestamp", desc=False)

    @pytest.mark.asyncio
    async def test_get_messages_with_pagination(self, conversation_repo, mock_supabase_client):
        """Test getting messages with before_id pagination."""
        conversation_id = str(uuid4())
        before_id = str(uuid4())

        # Mock response for before_id lookup
        before_response = MagicMock()
        before_response.data = [{"timestamp": "2026-01-10T12:00:00Z"}]

        # Mock response for messages
        messages_response = MagicMock()
        messages_response.data = [
            {"id": str(uuid4()), "role": "user", "content": "Earlier message"},
        ]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.limit = MagicMock(return_value=mock_builder)
        mock_builder.lt = MagicMock(return_value=mock_builder)

        # First execute returns before_id timestamp, second returns messages
        mock_builder.execute = MagicMock(side_effect=[before_response, messages_response])
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_messages(conversation_id, before_id=before_id)

        # Verify
        assert len(result) == 1
        # Verify lt (less than) was called for pagination
        mock_builder.lt.assert_called_once_with("timestamp", "2026-01-10T12:00:00Z")

    @pytest.mark.asyncio
    async def test_get_messages_error(self, conversation_repo, mock_supabase_client):
        """Test error handling when fetching messages fails."""
        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.limit = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(side_effect=Exception("Database error"))
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        with pytest.raises(Exception, match="Database error"):
            await conversation_repo.get_messages(str(uuid4()))


class TestGetMessageCount:
    """Test message counting."""

    @pytest.mark.asyncio
    async def test_get_message_count_success(self, conversation_repo, mock_supabase_client):
        """Test getting message count."""
        conversation_id = str(uuid4())

        # Mock response with count
        mock_response = MagicMock()
        mock_response.count = 42
        mock_response.data = []

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.get_message_count(conversation_id)

        # Verify
        assert result == 42
        mock_builder.select.assert_called_with("id", count="exact")

    @pytest.mark.asyncio
    async def test_get_message_count_error(self, conversation_repo, mock_supabase_client):
        """Test error handling returns 0 on failure."""
        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(side_effect=Exception("Database error"))
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute - should return 0 on error
        result = await conversation_repo.get_message_count(str(uuid4()))

        # Verify
        assert result == 0


class TestAddMessageErrors:
    """Test add_message error handling."""

    @pytest.mark.asyncio
    async def test_add_message_no_data_returned(self, conversation_repo, mock_supabase_client):
        """Test error when no data is returned."""
        mock_response = MagicMock()
        mock_response.data = []  # Empty response

        mock_builder = MagicMock()
        mock_builder.insert = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        with pytest.raises(Exception, match="Failed to add message"):
            await conversation_repo.add_message(
                conversation_id=str(uuid4()),
                role="user",
                content="Test message",
            )


class TestArchiveConversation:
    """Test archiving conversations."""

    @pytest.mark.asyncio
    async def test_archive_conversation(self, conversation_repo, mock_supabase_client):
        """Test archiving a conversation."""
        conversation_id = str(uuid4())

        # Mock update chain
        mock_response = MagicMock()
        mock_response.data = [{"id": conversation_id, "status": "archived"}]

        mock_builder = MagicMock()
        mock_builder.update = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await conversation_repo.archive_conversation(conversation_id)

        # Verify
        assert result is True
        # Verify update was called (it includes updated_at timestamp + status)
        mock_builder.update.assert_called_once()
        update_data = mock_builder.update.call_args[0][0]
        assert update_data["status"] == "archived"
        assert "updated_at" in update_data

    @pytest.mark.asyncio
    async def test_archive_conversation_error(self, conversation_repo, mock_supabase_client):
        """Test error handling when archiving fails."""
        # Mock error
        mock_builder = MagicMock()
        mock_builder.update = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(side_effect=Exception("Database error"))
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Database error"):
            await conversation_repo.archive_conversation(str(uuid4()))

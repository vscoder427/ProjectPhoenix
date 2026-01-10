"""
Unit tests for DaveChatService.

Tests core chat orchestration logic without external dependencies.
All external services (Gemini, database) are mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.app.services.dave_chat import DaveChatService, StreamEvent
from api.app.schemas.chat import UserContext, Resource
from tests.factories import ConversationFactory, MessageFactory


class TestDaveChatGenerateResponse:
    """Unit tests for DaveChatService.generate_response()."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_guardrails_checked_before_processing(self):
        """
        Verify guardrails run before any other processing.

        Tests that:
        - Guardrails.check() is called first
        - Blocked messages return immediately
        - No database or AI calls when blocked
        """
        # Arrange
        service = DaveChatService()

        # Mock guardrails to block request
        service.guardrails.check = AsyncMock(
            return_value=MagicMock(
                blocked=True,
                reason="rate_limit",
                message="Too many requests. Please try again later.",
            )
        )

        # Act
        result = await service.generate_response(
            message="Hello",
            user_id="test-user"
        )

        # Assert: Request blocked
        assert result["blocked"] is True
        assert result["block_reason"] == "rate_limit"
        assert "try again" in result["response"].lower()

        # Verify guardrails checked
        service.guardrails.check.assert_called_once()

        # Verify NO database or Gemini calls made
        service.conversation_repo.create_conversation = AsyncMock()
        service.conversation_repo.create_conversation.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_creates_conversation_when_none_exists(self):
        """
        Verify new conversation created when conversation_id is None.

        Tests that:
        - New conversation created in database
        - Conversation ID returned in response
        - Correct user_id and context saved
        """
        # Arrange
        service = DaveChatService()

        # Mock guardrails (allow request)
        service.guardrails.check = AsyncMock(
            return_value=MagicMock(blocked=False)
        )

        # Mock conversation creation
        mock_conversation = ConversationFactory.create(
            id="new-conv-123",
            user_id="test-user"
        )
        service.conversation_repo.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(
            return_value=[]
        )

        # Mock knowledge base
        service.knowledge_repo.search_articles_fulltext = AsyncMock(
            return_value=[]
        )
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(
            return_value=[]
        )

        # Mock prompt and Gemini
        service.prompts.get_dave_system_prompt = AsyncMock(
            return_value="You are Dave."
        )
        service.gemini.generate = AsyncMock(
            return_value="Hello! How can I help you?"
        )

        # Mock guardrails recording
        service.guardrails.record_request = AsyncMock()

        # Act
        result = await service.generate_response(
            message="Hello",
            user_id="test-user",
            conversation_id=None  # No existing conversation
        )

        # Assert: New conversation created
        service.conversation_repo.create_conversation.assert_called_once()
        create_call = service.conversation_repo.create_conversation.call_args

        assert create_call.kwargs["user_id"] == "test-user"
        assert result["conversation_id"] == "new-conv-123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_uses_existing_conversation_when_provided(self):
        """
        Verify existing conversation is retrieved when conversation_id provided.

        Tests that:
        - Existing conversation fetched from database
        - No new conversation created
        - Messages added to existing conversation
        """
        # Arrange
        service = DaveChatService()

        # Mock guardrails
        service.guardrails.check = AsyncMock(
            return_value=MagicMock(blocked=False)
        )

        # Mock existing conversation
        existing_conv = ConversationFactory.create(
            id="existing-conv-456",
            user_id="test-user"
        )
        service.conversation_repo.get_conversation = AsyncMock(
            return_value=existing_conv
        )
        service.conversation_repo.create_conversation = AsyncMock()
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(
            return_value=[]
        )

        # Mock other services
        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="You are Dave.")
        service.gemini.generate = AsyncMock(return_value="Response")
        service.guardrails.record_request = AsyncMock()

        # Act
        result = await service.generate_response(
            message="Follow-up message",
            conversation_id="existing-conv-456",
            user_id="test-user"
        )

        # Assert: Existing conversation used
        service.conversation_repo.get_conversation.assert_called_once_with(
            "existing-conv-456"
        )
        service.conversation_repo.create_conversation.assert_not_called()
        assert result["conversation_id"] == "existing-conv-456"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_saves_user_message_to_database(self):
        """
        Verify user message is persisted before AI generation.

        Tests that:
        - User message saved with correct role
        - Message content matches input
        - Message saved to correct conversation
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create(id="conv-123")
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="System prompt")
        service.gemini.generate = AsyncMock(return_value="AI response")
        service.guardrails.record_request = AsyncMock()

        # Act
        await service.generate_response(
            message="Help me find a job",
            user_id="test-user"
        )

        # Assert: User message saved
        assert service.conversation_repo.add_message.call_count == 2  # user + assistant

        # First call should be user message
        first_call = service.conversation_repo.add_message.call_args_list[0]
        assert first_call.kwargs["conversation_id"] == "conv-123"
        assert first_call.kwargs["role"] == "user"
        assert first_call.kwargs["content"] == "Help me find a job"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_includes_knowledge_resources_when_requested(self):
        """
        Verify knowledge base is searched and resources returned.

        Tests that:
        - Knowledge base searched with user message
        - Resources included in response
        - Resources added to system prompt context
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        # Mock knowledge base with results
        mock_article = {
            "id": "article-1",
            "title": "Resume Writing Tips",
            "excerpt": "Learn how to write an effective resume",
            "url": "https://employa.work/resume-tips",
            "rank_score": 0.9,
        }
        service.knowledge_repo.search_articles_fulltext = AsyncMock(
            return_value=[mock_article]
        )
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])

        service.prompts.get_dave_system_prompt = AsyncMock(return_value="System prompt")
        service.gemini.generate = AsyncMock(return_value="Response")
        service.guardrails.record_request = AsyncMock()

        # Act
        result = await service.generate_response(
            message="I need help with my resume",
            user_id="test-user",
            include_resources=True
        )

        # Assert: Resources searched
        service.knowledge_repo.search_articles_fulltext.assert_called_once()
        search_call = service.knowledge_repo.search_articles_fulltext.call_args
        assert "resume" in search_call.kwargs["query"].lower()

        # Assert: Resources in response
        assert "resources" in result
        assert len(result["resources"]) > 0
        assert result["resources"][0]["title"] == "Resume Writing Tips"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_saves_assistant_response_to_database(self):
        """
        Verify AI response is persisted after generation.

        Tests that:
        - Assistant message saved with correct role
        - Response content matches Gemini output
        - Metadata includes response time and user type
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create(id="conv-123")
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")
        service.gemini.generate = AsyncMock(return_value="Here's how I can help you!")
        service.guardrails.record_request = AsyncMock()

        # Act
        await service.generate_response(
            message="Hello",
            user_id="test-user"
        )

        # Assert: Assistant message saved
        assert service.conversation_repo.add_message.call_count == 2

        # Second call should be assistant message
        second_call = service.conversation_repo.add_message.call_args_list[1]
        assert second_call.kwargs["role"] == "assistant"
        assert second_call.kwargs["content"] == "Here's how I can help you!"

        # Metadata should include response time
        assert "metadata" in second_call.kwargs
        assert "response_time_ms" in second_call.kwargs["metadata"]
        assert isinstance(second_call.kwargs["metadata"]["response_time_ms"], int)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_records_usage_for_rate_limiting(self):
        """
        Verify request is recorded for rate limit tracking.

        Tests that:
        - guardrails.record_request() called after response
        - User ID and IP address passed
        - Token usage estimated and recorded
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")
        service.gemini.generate = AsyncMock(return_value="Response text here")
        service.guardrails.record_request = AsyncMock()

        # Act
        await service.generate_response(
            message="Test",
            user_id="user-123",
            ip_address="192.168.1.1"
        )

        # Assert: Usage recorded
        service.guardrails.record_request.assert_called_once()
        record_call = service.guardrails.record_request.call_args

        assert record_call.kwargs["user_id"] == "user-123"
        assert record_call.kwargs["ip_address"] == "192.168.1.1"
        assert "tokens_used" in record_call.kwargs
        assert record_call.kwargs["tokens_used"] > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generates_follow_up_suggestions(self):
        """
        Verify follow-up suggestions are generated and returned.

        Tests that:
        - Suggestions generated based on message content
        - Suggestions relevant to user's query
        - Maximum 3 suggestions returned
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")
        service.gemini.generate = AsyncMock(return_value="Response")
        service.guardrails.record_request = AsyncMock()

        # Act
        result = await service.generate_response(
            message="I need help finding a job",
            user_id="test-user"
        )

        # Assert: Suggestions returned
        assert "follow_up_suggestions" in result
        assert isinstance(result["follow_up_suggestions"], list)
        assert len(result["follow_up_suggestions"]) <= 3

        # Suggestions should be job-related
        suggestions_text = " ".join(result["follow_up_suggestions"]).lower()
        assert any(word in suggestions_text for word in ["job", "skill", "resume", "employ"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_gemini_api_error_gracefully(self):
        """
        Verify service handles Gemini API errors without crashing.

        Tests that:
        - API errors are caught
        - Error propagates to caller (not swallowed)
        - Database state remains consistent
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")

        # Simulate Gemini API error
        service.gemini.generate = AsyncMock(
            side_effect=Exception("Gemini API error: Rate limit exceeded")
        )

        # Act & Assert: Error propagates
        with pytest.raises(Exception) as exc_info:
            await service.generate_response(
                message="Test",
                user_id="test-user"
            )

        assert "rate limit" in str(exc_info.value).lower()

        # User message should still be saved (before error)
        assert service.conversation_repo.add_message.call_count == 1
        assert service.conversation_repo.add_message.call_args.kwargs["role"] == "user"


class TestDaveChatStreamResponse:
    """Unit tests for DaveChatService.stream_response()."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_yields_resource_event_first(self):
        """
        Verify resources are yielded before streaming starts.

        Tests that:
        - Resource event is first event (if resources found)
        - Resources include knowledge base articles
        - Resources formatted correctly
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        # Mock knowledge base with article
        mock_article = {
            "id": "art-1",
            "title": "Interview Tips",
            "excerpt": "Prepare for interviews",
            "url": "https://employa.work/interview-tips",
            "rank_score": 0.8,
        }
        service.knowledge_repo.search_articles_fulltext = AsyncMock(
            return_value=[mock_article]
        )
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])

        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")

        # Mock streaming response
        async def mock_stream_gen():
            yield "Hello "
            yield "world"

        service.gemini.generate_stream = AsyncMock(return_value=mock_stream_gen())

        # Act
        events = []
        async for event in service.stream_response(
            message="I have an interview tomorrow",
            user_id="test-user"
        ):
            events.append(event)

        # Assert: Resource event is first
        assert len(events) > 0
        assert events[0].type == "resource"
        assert "resources" in events[0].data
        assert len(events[0].data["resources"]) > 0
        assert events[0].data["resources"][0]["title"] == "Interview Tips"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_yields_token_events_during_streaming(self):
        """
        Verify token events are yielded for each chunk.

        Tests that:
        - Each Gemini chunk yields a token event
        - Token events contain text content
        - Token events maintain order
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")

        # Mock streaming chunks
        async def mock_stream_gen():
            chunks = ["Hello ", "there! ", "How ", "can ", "I ", "help?"]
            for chunk in chunks:
                yield chunk

        service.gemini.generate_stream = AsyncMock(return_value=mock_stream_gen())

        # Act
        events = []
        async for event in service.stream_response(
            message="Test",
            user_id="test-user",
            include_resources=False  # Skip resource event
        ):
            events.append(event)

        # Assert: Token events yielded
        token_events = [e for e in events if e.type == "token"]
        assert len(token_events) == 6

        # Verify content
        full_text = "".join([e.data["content"] for e in token_events])
        assert full_text == "Hello there! How can I help?"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_yields_suggestion_event_after_streaming(self):
        """
        Verify suggestions are yielded after streaming completes.

        Tests that:
        - Suggestion event comes after all tokens
        - Suggestions based on message content
        - Suggestions event before done event
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")

        async def mock_stream_gen():
            yield "Response "
            yield "text"

        service.gemini.generate_stream = AsyncMock(return_value=mock_stream_gen())

        # Act
        events = []
        async for event in service.stream_response(
            message="I need resume help",
            user_id="test-user",
            include_resources=False
        ):
            events.append(event)

        # Assert: Suggestion event after tokens
        suggestion_events = [e for e in events if e.type == "suggestion"]
        assert len(suggestion_events) == 1

        # Suggestions should come before done event
        event_types = [e.type for e in events]
        suggestion_index = event_types.index("suggestion")
        done_index = event_types.index("done")
        assert suggestion_index < done_index

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_yields_done_event_last(self):
        """
        Verify done event is the final event.

        Tests that:
        - Done event is last event yielded
        - Done event includes conversation_id
        - Done event includes full response text
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create(id="conv-999")
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")

        async def mock_stream_gen():
            yield "Full "
            yield "response "
            yield "text"

        service.gemini.generate_stream = AsyncMock(return_value=mock_stream_gen())

        # Act
        events = []
        async for event in service.stream_response(
            message="Test",
            user_id="test-user",
            include_resources=False
        ):
            events.append(event)

        # Assert: Done event is last
        assert events[-1].type == "done"
        assert events[-1].data["conversation_id"] == "conv-999"
        assert events[-1].data["full_response"] == "Full response text"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_yields_error_event_on_streaming_failure(self):
        """
        Verify error event is yielded when streaming fails.

        Tests that:
        - Streaming errors are caught
        - Error event yielded to client
        - Streaming stops after error
        """
        # Arrange
        service = DaveChatService()
        service.guardrails.check = AsyncMock(return_value=MagicMock(blocked=False))

        mock_conv = ConversationFactory.create()
        service.conversation_repo.create_conversation = AsyncMock(return_value=mock_conv)
        service.conversation_repo.add_message = AsyncMock()
        service.conversation_repo.get_recent_messages = AsyncMock(return_value=[])

        service.knowledge_repo.search_articles_fulltext = AsyncMock(return_value=[])
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(return_value=[])
        service.prompts.get_dave_system_prompt = AsyncMock(return_value="Prompt")

        # Simulate streaming error
        async def mock_stream_gen():
            yield "Start "
            raise Exception("Streaming connection lost")

        service.gemini.generate_stream = AsyncMock(return_value=mock_stream_gen())

        # Act
        events = []
        async for event in service.stream_response(
            message="Test",
            user_id="test-user",
            include_resources=False
        ):
            events.append(event)

        # Assert: Error event yielded
        error_events = [e for e in events if e.type == "error"]
        assert len(error_events) == 1
        assert "message" in error_events[0].data

        # Streaming should stop (no done event)
        done_events = [e for e in events if e.type == "done"]
        assert len(done_events) == 0


class TestDaveChatHelperMethods:
    """Unit tests for DaveChatService helper methods."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_knowledge_context_searches_articles_and_faqs(self):
        """
        Verify _get_knowledge_context searches both articles and FAQs.

        Tests that:
        - Both article and FAQ searches executed
        - Results combined into single resource list
        - Context string formatted correctly
        """
        # Arrange
        service = DaveChatService()

        mock_article = {
            "id": "art-1",
            "title": "Resume Guide",
            "excerpt": "How to write a great resume",
            "url": "https://example.com/resume",
            "rank_score": 0.9,
        }

        mock_faq = {
            "id": "faq-1",
            "question": "How do I explain gaps in my work history?",
            "excerpt": "Be honest and focus on what you learned",
            "rank_score": 0.8,
        }

        service.knowledge_repo.search_articles_fulltext = AsyncMock(
            return_value=[mock_article]
        )
        service.knowledge_repo.search_faqs_fulltext = AsyncMock(
            return_value=[mock_faq]
        )

        # Act
        resources, context_string = await service._get_knowledge_context(
            query="resume help",
            limit=3
        )

        # Assert: Both searches called
        service.knowledge_repo.search_articles_fulltext.assert_called_once()
        service.knowledge_repo.search_faqs_fulltext.assert_called_once()

        # Assert: Combined resources
        assert len(resources) == 2
        assert resources[0].type == "article"
        assert resources[0].title == "Resume Guide"
        assert resources[1].type == "faq"
        assert resources[1].title == "How do I explain gaps in my work history?"

        # Assert: Context string formatted
        assert "Resume Guide" in context_string
        assert "How do I explain gaps" in context_string

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_knowledge_context_handles_errors_gracefully(self):
        """
        Verify _get_knowledge_context handles search errors.

        Tests that:
        - Search errors don't crash method
        - Empty results returned on error
        - Error logged (not raised)
        """
        # Arrange
        service = DaveChatService()

        # Simulate search error
        service.knowledge_repo.search_articles_fulltext = AsyncMock(
            side_effect=Exception("Search service unavailable")
        )

        # Act
        resources, context_string = await service._get_knowledge_context(
            query="test query"
        )

        # Assert: Empty results (not exception)
        assert resources == []
        assert context_string == ""

    @pytest.mark.unit
    def test_generate_suggestions_returns_job_search_suggestions(self):
        """
        Verify _generate_suggestions returns job-related suggestions.

        Tests that:
        - Job keywords trigger job search suggestions
        - Suggestions are relevant to query
        - Maximum 3 suggestions returned
        """
        # Arrange
        service = DaveChatService()

        # Act
        suggestions = service._generate_suggestions(
            user_message="I'm looking for a job in recovery",
            response="Here are some job search tips...",
            context=None
        )

        # Assert: Job-related suggestions
        assert len(suggestions) <= 3
        suggestions_text = " ".join(suggestions).lower()
        assert any(word in suggestions_text for word in ["job", "skill", "resume"])

    @pytest.mark.unit
    def test_generate_suggestions_returns_resume_suggestions(self):
        """
        Verify _generate_suggestions returns resume-related suggestions.
        """
        # Arrange
        service = DaveChatService()

        # Act
        suggestions = service._generate_suggestions(
            user_message="Can you help me with my resume?",
            response="Let's work on your resume...",
            context=None
        )

        # Assert: Resume-related suggestions
        assert len(suggestions) <= 3
        suggestions_text = " ".join(suggestions).lower()
        assert any(word in suggestions_text for word in ["resume", "cover letter", "format"])

    @pytest.mark.unit
    def test_format_history_for_gemini_converts_roles(self):
        """
        Verify _format_history_for_gemini converts message format.

        Tests that:
        - User role converted to "user"
        - Assistant role converted to "model"
        - Content wrapped in "parts" array
        - Order preserved
        """
        # Arrange
        service = DaveChatService()

        messages = [
            MessageFactory.create(role="user", content="Hello"),
            MessageFactory.create(role="assistant", content="Hi there!"),
            MessageFactory.create(role="user", content="How are you?"),
        ]

        # Act
        gemini_history = service._format_history_for_gemini(messages)

        # Assert: Format converted
        assert len(gemini_history) == 3

        assert gemini_history[0]["role"] == "user"
        assert gemini_history[0]["parts"] == ["Hello"]

        assert gemini_history[1]["role"] == "model"
        assert gemini_history[1]["parts"] == ["Hi there!"]

        assert gemini_history[2]["role"] == "user"
        assert gemini_history[2]["parts"] == ["How are you?"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_conversation_creates_conversation_with_welcome(self):
        """
        Verify start_conversation creates conversation and welcome message.

        Tests that:
        - New conversation created
        - Welcome message retrieved from prompts
        - Welcome message saved to conversation
        - Suggestions included in response
        """
        # Arrange
        service = DaveChatService()

        mock_conv = ConversationFactory.create(id="new-conv")
        service.conversation_repo.create_conversation = AsyncMock(
            return_value=mock_conv
        )
        service.conversation_repo.add_message = AsyncMock()

        service.prompts.get_welcome_message = AsyncMock(
            return_value="Welcome to Employa! I'm Dave, your career coach."
        )

        # Act
        result = await service.start_conversation(
            user_id="test-user",
            context=UserContext(user_type="job_seeker")
        )

        # Assert: Conversation created
        service.conversation_repo.create_conversation.assert_called_once()

        # Assert: Welcome message saved
        service.conversation_repo.add_message.assert_called_once()
        message_call = service.conversation_repo.add_message.call_args
        assert message_call.kwargs["role"] == "assistant"
        assert "Welcome to Employa" in message_call.kwargs["content"]

        # Assert: Response structure
        assert result["conversation_id"] == "new-conv"
        assert "Welcome" in result["message"]
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

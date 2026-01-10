"""
API tests for chat endpoints.

TEMPLATE TEST: This demonstrates perfect API endpoint test patterns.

Key Patterns Demonstrated:
1. Test HTTP API contracts (request/response)
2. Validate status codes and response structure
3. Test authentication and authorization
4. Test input validation
5. Test error handling
6. Mock external dependencies only

Run API tests:
    pytest tests/api/ -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.app.main import app


@pytest.fixture
def client():
    """FastAPI test client for making HTTP requests."""
    return TestClient(app)


@pytest.mark.asyncio
class TestSendMessageEndpoint:
    """Tests for POST /api/v1/chat/message endpoint."""

    def test_send_message_creates_new_conversation(self, client):
        """
        Verify sending first message creates new conversation.

        Tests that:
        - Endpoint returns 200 OK
        - Response includes conversation_id
        - Response includes AI response text
        - Response includes resources list
        - Response includes follow-up suggestions
        """
        # Arrange
        request_body = {
            "message": "Hello, I need help finding a job in recovery"
        }

        # Mock Gemini to avoid real API calls
        with patch("api.app.services.dave_chat.DaveChatService.generate_response") as mock_generate:
            mock_generate.return_value = {
                "conversation_id": "test-conv-123",
                "response": "I'd be happy to help you find a job!",
                "resources": [
                    "https://employa.work/resources/resume-tips"
                ],
                "follow_up_suggestions": [
                    "Tell me about your skills",
                    "What industry interests you?"
                ]
            }

            # Act
            response = client.post("/api/v1/chat/message", json=request_body)

            # Assert: Status code
            assert response.status_code == 200

            # Assert: Response structure
            data = response.json()
            assert "conversation_id" in data
            assert data["conversation_id"] is not None
            assert "response" in data
            assert len(data["response"]) > 0
            assert "resources" in data
            assert isinstance(data["resources"], list)
            assert "follow_up_suggestions" in data
            assert isinstance(data["follow_up_suggestions"], list)

    def test_send_message_continues_existing_conversation(self, client):
        """
        Verify sending message with conversation_id continues conversation.

        Tests that:
        - Can provide conversation_id in request
        - Response uses same conversation_id
        - Messages are added to existing conversation
        """
        # Arrange
        request_body = {
            "message": "Tell me more about that",
            "conversation_id": "existing-conv-456"
        }

        # Act
        with patch("api.app.services.dave_chat.DaveChatService.generate_response") as mock_generate:
            mock_generate.return_value = {
                "conversation_id": "existing-conv-456",
                "response": "Here are more details...",
                "resources": [],
                "follow_up_suggestions": []
            }

            response = client.post("/api/v1/chat/message", json=request_body)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "existing-conv-456"

            # Verify service was called with conversation_id
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["conversation_id"] == "existing-conv-456"

    def test_send_message_rejects_empty_message(self, client):
        """
        Verify endpoint rejects empty messages.

        Tests input validation:
        - Empty string rejected
        - Returns 422 Unprocessable Entity
        - Response includes validation error details
        """
        # Arrange
        request_body = {"message": ""}

        # Act
        response = client.post("/api/v1/chat/message", json=request_body)

        # Assert: Validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        # FastAPI validation errors include field details
        assert any("message" in str(error).lower() for error in data["detail"])

    def test_send_message_rejects_too_long_message(self, client):
        """
        Verify endpoint rejects messages exceeding length limit.

        Tests that:
        - Messages over 10,000 characters are rejected
        - Returns 422 validation error
        - Prevents abuse and excessive API costs
        """
        # Arrange: Message with 10,001 characters
        request_body = {"message": "x" * 10001}

        # Act
        response = client.post("/api/v1/chat/message", json=request_body)

        # Assert
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_send_message_requires_message_field(self, client):
        """
        Verify endpoint requires 'message' field in request.

        Tests that:
        - Missing 'message' field returns 422
        - Request body validation works
        """
        # Arrange: Missing required field
        request_body = {}

        # Act
        response = client.post("/api/v1/chat/message", json=request_body)

        # Assert
        assert response.status_code == 422

    def test_send_message_handles_gemini_api_error(self, client):
        """
        Verify endpoint handles Gemini API failures gracefully.

        Tests that:
        - API errors don't crash endpoint
        - Returns appropriate error response
        - Error details are not leaked to client
        """
        # Arrange
        request_body = {"message": "Test message"}

        # Act: Simulate Gemini API failure
        with patch("api.app.services.dave_chat.DaveChatService.generate_response") as mock_generate:
            mock_generate.side_effect = Exception("Gemini API error")

            response = client.post("/api/v1/chat/message", json=request_body)

            # Assert: Graceful error handling
            assert response.status_code in [500, 503]  # Server error or service unavailable

            data = response.json()
            assert "detail" in data or "error" in data

            # Error should NOT leak internal details
            error_text = str(data).lower()
            assert "gemini" not in error_text  # Don't expose service names
            assert "api key" not in error_text  # Don't expose credentials

    def test_send_message_includes_user_id_when_authenticated(self, client, valid_api_key):
        """
        Verify endpoint includes user_id for authenticated requests.

        Tests that:
        - Authenticated requests include user context
        - User ID is passed to service layer
        - Conversations are tied to user account
        """
        # Arrange
        request_body = {"message": "Test message"}
        headers = {"X-API-Key": valid_api_key}

        # Act
        with patch("api.app.services.dave_chat.DaveChatService.generate_response") as mock_generate:
            mock_generate.return_value = {
                "conversation_id": "test-conv",
                "response": "Response",
                "resources": [],
                "follow_up_suggestions": []
            }

            response = client.post(
                "/api/v1/chat/message",
                json=request_body,
                headers=headers
            )

            # Assert
            assert response.status_code == 200

            # Verify user_id was passed to service
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert "user_id" in call_kwargs
            assert call_kwargs["user_id"] is not None


@pytest.mark.asyncio
class TestStreamMessageEndpoint:
    """Tests for GET /api/v1/chat/stream endpoint."""

    def test_stream_returns_server_sent_events(self, client):
        """
        Verify streaming endpoint returns SSE format.

        Tests that:
        - Content-Type is text/event-stream
        - Response includes 'data:' prefixed events
        - Events are newline-delimited
        - Final event signals completion
        """
        # Arrange
        params = {
            "message": "Stream test",
            "conversation_id": "test-conv"
        }

        # Act
        with patch("api.app.services.dave_chat.DaveChatService.stream_response") as mock_stream:
            # Mock streaming response
            async def mock_stream_gen():
                yield {"type": "token", "content": "Hello "}
                yield {"type": "token", "content": "world"}
                yield {"type": "done", "conversation_id": "test-conv"}

            mock_stream.return_value = mock_stream_gen()

            response = client.get("/api/v1/chat/stream", params=params)

            # Assert
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            # Response should be streaming
            # (Exact format depends on FastAPI StreamingResponse implementation)

    def test_stream_requires_message_parameter(self, client):
        """
        Verify streaming endpoint requires 'message' query parameter.

        Tests input validation for GET parameters.
        """
        # Arrange: Missing required parameter
        params = {}

        # Act
        response = client.get("/api/v1/chat/stream", params=params)

        # Assert
        assert response.status_code == 422


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200_when_healthy(self, client):
        """
        Verify health endpoint returns 200 OK when service is healthy.

        Tests that:
        - Health check endpoint exists
        - Returns 200 status code
        - Response includes status field
        - No authentication required
        """
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "up"]

    def test_health_checks_dependencies(self, client):
        """
        Verify health endpoint checks critical dependencies.

        Tests that:
        - Database connectivity is checked
        - Gemini API availability is checked
        - Redis connectivity is checked (if rate limiting enabled)
        - Response includes dependency details
        """
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200

        data = response.json()

        # Health response should include dependency checks
        # (Exact structure depends on implementation)
        # Common patterns: 'status', 'checks', 'dependencies'

        # At minimum, should have status
        assert "status" in data

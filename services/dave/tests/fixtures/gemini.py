"""
Gemini AI client fixtures for testing.

Provides mocks for Gemini API interactions to avoid
real API calls during tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List, AsyncIterator


@pytest.fixture
def mock_gemini_response() -> Dict[str, Any]:
    """
    Standard Gemini API response for mocking.

    Returns typical response structure from Gemini.

    Example:
        def test_chat_with_gemini(mock_gemini_response):
            # Use this as return value for mocked generate()
            pass
    """
    return {
        "text": "This is a helpful career guidance response from Dave.",
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "This is a helpful career guidance response from Dave."
                        }
                    ]
                },
                "finish_reason": "STOP",
                "safety_ratings": [],
            }
        ],
        "usage_metadata": {
            "prompt_token_count": 50,
            "candidates_token_count": 150,
            "total_token_count": 200,
        },
    }


@pytest.fixture
def mock_gemini_client(mock_gemini_response: Dict[str, Any]):
    """
    Mocked Gemini client for unit tests.

    Returns AsyncMock with pre-configured responses.
    Use this to avoid real Gemini API calls.

    Example:
        @pytest.mark.asyncio
        async def test_generate_response(mock_gemini_client):
            service = DaveChatService(gemini_client=mock_gemini_client)
            result = await service.generate_response("Hello")
            assert "response" in result
            mock_gemini_client.generate.assert_called_once()
    """
    mock_client = AsyncMock()
    mock_client.generate = AsyncMock(return_value=mock_gemini_response["text"])
    mock_client.generate_stream = AsyncMock()
    mock_client.generate_embedding = AsyncMock(return_value=[0.1] * 768)

    # Mock circuit breaker state
    mock_client.circuit_breaker_open = False
    mock_client.failure_count = 0

    return mock_client


@pytest.fixture
def mock_streaming_response() -> List[str]:
    """
    Mock streaming response chunks from Gemini.

    Returns list of text chunks as they would arrive in streaming.

    Example:
        @pytest.mark.asyncio
        async def test_streaming(mock_streaming_response):
            # Simulate streaming by yielding chunks
            for chunk in mock_streaming_response:
                yield chunk
    """
    return [
        "This ",
        "is ",
        "a ",
        "streaming ",
        "response ",
        "from ",
        "Dave.",
    ]


@pytest.fixture
async def mock_gemini_stream(mock_streaming_response: List[str]):
    """
    Async generator fixture for mocking streaming responses.

    Yields text chunks like real Gemini streaming.

    Example:
        @pytest.mark.asyncio
        async def test_stream(mock_gemini_stream):
            mock_client = AsyncMock()
            mock_client.generate_stream.return_value = mock_gemini_stream

            chunks = []
            async for chunk in mock_client.generate_stream("test"):
                chunks.append(chunk)

            assert len(chunks) == 7
    """

    async def stream_generator() -> AsyncIterator[str]:
        for chunk in mock_streaming_response:
            yield chunk

    return stream_generator()


@pytest.fixture
def gemini_error_response() -> Exception:
    """
    Mock Gemini API error for testing error handling.

    Use this to simulate API failures.

    Example:
        @pytest.mark.asyncio
        async def test_handles_api_error(gemini_error_response):
            mock_client = AsyncMock()
            mock_client.generate.side_effect = gemini_error_response

            service = DaveChatService(gemini_client=mock_client)
            result = await service.generate_response("Hello")

            assert "error" in result
    """
    return Exception("Gemini API error: Rate limit exceeded")


@pytest.fixture
def gemini_circuit_breaker_open():
    """
    Mock Gemini client with circuit breaker open.

    Use this to test circuit breaker failure handling.

    Example:
        @pytest.mark.asyncio
        async def test_circuit_open(gemini_circuit_breaker_open):
            service = DaveChatService(gemini_client=gemini_circuit_breaker_open)
            result = await service.generate_response("Hello")

            assert result["blocked"] is True
            assert "circuit breaker" in result["block_reason"].lower()
    """
    mock_client = AsyncMock()
    mock_client.circuit_breaker_open = True
    mock_client.failure_count = 3

    # Raise circuit open error
    from api.app.clients.gemini import GeminiCircuitOpenError

    mock_client.generate.side_effect = GeminiCircuitOpenError(
        "Circuit breaker open after 3 failures"
    )

    return mock_client


@pytest.fixture
def mock_embedding_vector() -> List[float]:
    """
    Mock 768-dimensional embedding vector.

    Use this for testing knowledge base search with embeddings.

    Example:
        def test_search_with_embedding(mock_embedding_vector):
            # Mock embedding generation
            mock_client.generate_embedding.return_value = mock_embedding_vector
    """
    return [0.1 * i for i in range(768)]


@pytest.fixture
def gemini_safety_block_response() -> Dict[str, Any]:
    """
    Mock Gemini response that was blocked by safety filters.

    Use this to test handling of safety-blocked content.

    Example:
        def test_handles_safety_block(gemini_safety_block_response):
            mock_client.generate.return_value = gemini_safety_block_response
            # Test that service handles blocked content gracefully
    """
    return {
        "text": "",
        "candidates": [
            {
                "finish_reason": "SAFETY",
                "safety_ratings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "probability": "HIGH",
                    }
                ],
            }
        ],
        "usage_metadata": {
            "prompt_token_count": 50,
            "candidates_token_count": 0,
            "total_token_count": 50,
        },
    }

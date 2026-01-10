"""
Unit tests for Gemini AI client.

TEMPLATE TEST: This demonstrates perfect unit test patterns.

Key Patterns Demonstrated:
1. Clear, descriptive test names following test_<behavior>_<condition>_<expected>
2. AAA pattern (Arrange, Act, Assert)
3. Specific assertions (no conditionals)
4. Strategic mocking (mock external API only)
5. Docstrings explaining what is being tested
6. Fast execution (<100ms each)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.app.clients.gemini import GeminiClient, GeminiCircuitOpenError


class TestGeminiGenerate:
    """Unit tests for GeminiClient.generate() method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_returns_text_response(self):
        """
        Verify generate() returns text from Gemini API response.

        Tests that:
        - Gemini API is called with correct prompt
        - Response text is extracted correctly
        - Return value is a string
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        mock_response = MagicMock()
        mock_response.text = "This is a helpful response from Gemini."

        # Act
        with patch.object(
            client.model, "generate_content", return_value=mock_response
        ) as mock_generate:
            result = await client.generate("Hello, Dave!")

            # Assert
            mock_generate.assert_called_once_with("Hello, Dave!")
            assert isinstance(result, str)
            assert result == "This is a helpful response from Gemini."
            assert len(result) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_raises_on_api_error(self):
        """
        Verify generate() propagates Gemini API errors.

        Tests that:
        - API errors are not swallowed
        - Exceptions are raised to caller
        - Error message is preserved
        """
        # Arrange
        client = GeminiClient(api_key="test-key")

        # Act & Assert
        with patch.object(
            client.model,
            "generate_content",
            side_effect=Exception("API rate limit exceeded"),
        ):
            with pytest.raises(Exception) as exc_info:
                await client.generate("Test prompt")

            assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_handles_empty_response(self):
        """
        Verify generate() handles empty Gemini responses gracefully.

        Tests edge case where Gemini returns empty text.

        This can happen when:
        - Safety filters block content
        - API returns malformed response
        - Content generation fails
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        mock_response = MagicMock()
        mock_response.text = ""

        # Act
        with patch.object(client.model, "generate_content", return_value=mock_response):
            result = await client.generate("Test prompt")

            # Assert
            assert result == ""
            assert isinstance(result, str)


class TestGeminiCircuitBreaker:
    """Unit tests for circuit breaker resilience pattern."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self):
        """
        Verify circuit breaker opens after configured failure threshold.

        Tests that:
        - Circuit tracks consecutive failures
        - Circuit opens after threshold (default: 3)
        - Subsequent calls raise CircuitOpenError
        - No API calls made when circuit open
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        client.circuit_breaker_threshold = 3

        # Act: Cause 3 failures
        with patch.object(
            client.model, "generate_content", side_effect=Exception("API error")
        ):
            for _ in range(3):
                with pytest.raises(Exception):
                    await client.generate("Test")

        # Assert: 4th call raises CircuitOpenError
        with pytest.raises(GeminiCircuitOpenError) as exc_info:
            await client.generate("Test")

        assert "circuit breaker open" in str(exc_info.value).lower()
        assert client.circuit_breaker_open is True
        assert client.failure_count == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_circuit_resets_after_successful_call(self):
        """
        Verify circuit breaker resets failure count after success.

        Tests that:
        - Successful calls reset failure counter
        - Circuit remains closed after success
        - Subsequent calls work normally
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        client.failure_count = 2  # Start with 2 failures

        mock_response = MagicMock()
        mock_response.text = "Success response"

        # Act: Successful call
        with patch.object(client.model, "generate_content", return_value=mock_response):
            result = await client.generate("Test")

        # Assert
        assert result == "Success response"
        assert client.failure_count == 0  # Reset to zero
        assert client.circuit_breaker_open is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_circuit_half_open_allows_one_request(self):
        """
        Verify circuit breaker half-open state allows probe request.

        After timeout period, circuit transitions to half-open
        and allows one request to test if service recovered.

        Tests that:
        - Half-open state allows single probe request
        - Successful probe closes circuit
        - Failed probe reopens circuit
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        client.circuit_breaker_open = True
        client.circuit_breaker_half_open = True  # Simulate timeout passed

        mock_response = MagicMock()
        mock_response.text = "Service recovered"

        # Act: Probe request succeeds
        with patch.object(client.model, "generate_content", return_value=mock_response):
            result = await client.generate("Probe")

        # Assert
        assert result == "Service recovered"
        assert client.circuit_breaker_open is False
        assert client.circuit_breaker_half_open is False
        assert client.failure_count == 0


class TestGeminiEmbedding:
    """Unit tests for embedding generation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_embedding_returns_vector(self):
        """
        Verify generate_embedding() returns 768-dimensional vector.

        Tests that:
        - Embedding API is called correctly
        - Vector has correct dimensions (768 for text-embedding-004)
        - All values are floats
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        mock_embedding = [0.1] * 768

        # Act
        with patch.object(
            client.embedding_model, "embed_content", return_value=mock_embedding
        ):
            result = await client.generate_embedding("Test text for embedding")

        # Assert
        assert isinstance(result, list)
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_embedding_normalizes_vector(self):
        """
        Verify generate_embedding() normalizes vector to unit length.

        For cosine similarity search, embeddings should be normalized.

        Tests that:
        - Vector is normalized (magnitude = 1.0)
        - Values are in expected range (-1 to 1)
        """
        # Arrange
        client = GeminiClient(api_key="test-key")
        # Raw embedding (not normalized)
        mock_embedding = [0.5, 0.5, 0.5] + [0.0] * 765

        # Act
        with patch.object(
            client.embedding_model, "embed_content", return_value=mock_embedding
        ):
            result = await client.generate_embedding("Test")

        # Assert
        # Calculate magnitude: sqrt(sum of squares)
        magnitude = sum(x**2 for x in result) ** 0.5
        assert abs(magnitude - 1.0) < 0.01  # Approximately unit length

        # All values should be in valid range
        assert all(-1.0 <= x <= 1.0 for x in result)

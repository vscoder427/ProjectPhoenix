"""
Unit tests for Gemini client streaming functionality.

Tests async generator streaming patterns for real-time AI responses.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.app.clients.gemini import GeminiClient


class TestGenerateStream:
    """Tests for generate_stream() async generator."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_yields_chunks_from_gemini_response(self):
        """
        Verify generate_stream() yields text chunks.

        Tests that:
        - Each chunk from Gemini is yielded
        - Chunks yielded in order
        - All chunks contain text
        """
        # Arrange
        client = GeminiClient()

        # Mock streaming response
        mock_chunks = [
            MagicMock(text="Hello "),
            MagicMock(text="there! "),
            MagicMock(text="How "),
            MagicMock(text="can "),
            MagicMock(text="I "),
            MagicMock(text="help?"),
        ]

        # Act
        chunks_received = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)):
            async for chunk in client.generate_stream("Hello, Dave!"):
                chunks_received.append(chunk)

        # Assert: All chunks yielded in order
        assert len(chunks_received) == 6
        assert chunks_received == ["Hello ", "there! ", "How ", "can ", "I ", "help?"]

        # Reconstruct full message
        full_text = "".join(chunks_received)
        assert full_text == "Hello there! How can I help?"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_with_system_instruction(self):
        """
        Verify streaming works with system instructions.

        Tests that:
        - System instruction creates new model instance
        - Streaming uses model with instruction
        - Chunks yielded correctly
        """
        # Arrange
        client = GeminiClient()

        mock_chunks = [MagicMock(text="Response "), MagicMock(text="text")]

        # Act
        chunks = []
        with patch("api.app.clients.gemini.genai.GenerativeModel") as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = iter(mock_chunks)
            mock_model_class.return_value = mock_model_instance

            async for chunk in client.generate_stream(
                prompt="Hello",
                system_instruction="You are a helpful assistant"
            ):
                chunks.append(chunk)

        # Assert: System instruction model created
        mock_model_class.assert_called_once()
        call_args = mock_model_class.call_args
        assert call_args.kwargs["system_instruction"] == "You are a helpful assistant"

        # Chunks yielded
        assert chunks == ["Response ", "text"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_with_conversation_history(self):
        """
        Verify streaming works with conversation history.

        Tests that:
        - History starts chat session
        - send_message() called with stream=True
        - Chunks yielded from chat
        """
        # Arrange
        client = GeminiClient()

        history = [
            {"role": "user", "parts": ["Previous question"]},
            {"role": "model", "parts": ["Previous answer"]},
        ]

        mock_chunks = [MagicMock(text="Follow-up "), MagicMock(text="response")]

        mock_chat = MagicMock()
        mock_chat.send_message.return_value = iter(mock_chunks)

        # Act
        chunks = []
        with patch.object(client.model, "start_chat", return_value=mock_chat):
            async for chunk in client.generate_stream(
                prompt="Follow-up question",
                history=history
            ):
                chunks.append(chunk)

        # Assert: Chat started with history
        client.model.start_chat.assert_called_once_with(history=history)

        # send_message called with stream=True
        mock_chat.send_message.assert_called_once_with("Follow-up question", stream=True)

        # Chunks yielded
        assert chunks == ["Follow-up ", "response"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_skips_empty_chunks(self):
        """
        Verify empty chunks are not yielded.

        Tests that:
        - Chunks with no text are filtered out
        - Only non-empty chunks yielded
        - Empty chunks don't break stream
        """
        # Arrange
        client = GeminiClient()

        # Mix of empty and non-empty chunks
        mock_chunks = [
            MagicMock(text="Hello"),
            MagicMock(text=""),  # Empty
            MagicMock(text=" "),
            MagicMock(text=""),  # Empty
            MagicMock(text="world"),
        ]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)):
            async for chunk in client.generate_stream("Test"):
                chunks.append(chunk)

        # Assert: Only non-empty chunks
        assert chunks == ["Hello", " ", "world"]
        assert len(chunks) == 3  # 2 empty chunks filtered

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_propagates_errors_during_iteration(self):
        """
        Verify streaming errors are propagated to caller.

        Tests that:
        - Errors during iteration not swallowed
        - Exception raised to caller
        - Error message preserved
        """
        # Arrange
        client = GeminiClient()

        def error_generator():
            yield MagicMock(text="Start")
            raise Exception("Streaming connection lost")

        # Act & Assert
        chunks = []
        with patch.object(client.model, "generate_content", return_value=error_generator()):
            with pytest.raises(Exception) as exc_info:
                async for chunk in client.generate_stream("Test"):
                    chunks.append(chunk)

        # First chunk received before error
        assert chunks == ["Start"]

        # Error preserved
        assert "connection lost" in str(exc_info.value).lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_records_success_only_after_chunks_received(self):
        """
        Verify circuit breaker success only recorded if chunks received.

        Tests that:
        - No chunks = no success recording
        - With chunks = success recorded
        - Prevents false positives from empty streams
        """
        # Arrange
        from api.app.clients import gemini as gemini_module

        # Start with some failures
        gemini_module._circuit_failures = 2
        gemini_module._circuit_open = False

        client = GeminiClient()

        # Mock stream with chunks
        mock_chunks = [MagicMock(text="Hello"), MagicMock(text=" world")]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)):
            async for chunk in client.generate_stream("Test"):
                chunks.append(chunk)

        # Assert: Success recorded (failures reset)
        assert gemini_module._circuit_failures == 0
        assert chunks == ["Hello", " world"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_no_success_if_no_chunks_received(self):
        """
        Verify circuit breaker not reset if stream produces no chunks.

        Tests that:
        - Empty stream doesn't reset failures
        - Prevents false success from empty responses
        """
        # Arrange
        from api.app.clients import gemini as gemini_module

        gemini_module._circuit_failures = 2
        gemini_module._circuit_open = False

        client = GeminiClient()

        # Mock empty stream (all chunks have no text)
        mock_chunks = [MagicMock(text=""), MagicMock(text="")]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)):
            async for chunk in client.generate_stream("Test"):
                chunks.append(chunk)

        # Assert: No chunks received, failures NOT reset
        assert len(chunks) == 0
        assert gemini_module._circuit_failures == 2  # Still 2


class TestStreamingEdgeCases:
    """Tests for edge cases in streaming."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_handles_single_chunk_response(self):
        """
        Verify streaming works with single chunk.

        Tests that:
        - Single chunk yielded correctly
        - Generator doesn't error
        - Success recorded
        """
        # Arrange
        client = GeminiClient()

        mock_chunk = [MagicMock(text="Single response.")]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunk)):
            async for chunk in client.generate_stream("Short question"):
                chunks.append(chunk)

        # Assert
        assert chunks == ["Single response."]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_handles_very_long_response(self):
        """
        Verify streaming works with many chunks (long response).

        Tests that:
        - All chunks yielded
        - No truncation
        - Memory efficient (generator pattern)
        """
        # Arrange
        client = GeminiClient()

        # Simulate 100-chunk response
        mock_chunks = [MagicMock(text=f"Chunk {i} ") for i in range(100)]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)):
            async for chunk in client.generate_stream("Complex question"):
                chunks.append(chunk)

        # Assert: All chunks received
        assert len(chunks) == 100
        assert chunks[0] == "Chunk 0 "
        assert chunks[99] == "Chunk 99 "

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_handles_unicode_and_special_characters(self):
        """
        Verify streaming correctly handles unicode and special chars.

        Tests that:
        - Emoji and unicode preserved
        - Special characters not corrupted
        - Encoding handled correctly
        """
        # Arrange
        client = GeminiClient()

        mock_chunks = [
            MagicMock(text="Hello 👋 "),
            MagicMock(text="世界 "),
            MagicMock(text="Привет "),
            MagicMock(text="مرحبا "),
            MagicMock(text="🎉"),
        ]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)):
            async for chunk in client.generate_stream("Multilingual test"):
                chunks.append(chunk)

        # Assert: Unicode preserved
        assert chunks == ["Hello 👋 ", "世界 ", "Привет ", "مرحبا ", "🎉"]
        full_text = "".join(chunks)
        assert "👋" in full_text
        assert "世界" in full_text


class TestStreamingPerformance:
    """Tests for streaming performance characteristics."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_is_async_generator(self):
        """
        Verify generate_stream returns async generator.

        Tests that:
        - Return type is async generator
        - Can be used with async for
        - Lazy evaluation (chunks yielded as available)
        """
        # Arrange
        client = GeminiClient()

        # Act
        result = client.generate_stream("Test")

        # Assert: Is async generator
        assert hasattr(result, "__aiter__")
        assert hasattr(result, "__anext__")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_does_not_buffer_all_chunks_in_memory(self):
        """
        Verify streaming yields chunks immediately (not buffered).

        Tests that:
        - Chunks yielded as they arrive
        - No buffering of full response
        - Memory efficient for long responses
        """
        # Arrange
        client = GeminiClient()

        # Create generator that tracks when chunks are consumed
        consumption_order = []

        def tracked_generator():
            for i in range(3):
                consumption_order.append(f"generate_{i}")
                chunk = MagicMock(text=f"Chunk {i}")
                yield chunk

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=tracked_generator()):
            async for chunk in client.generate_stream("Test"):
                consumption_order.append(f"yield_{len(chunks)}")
                chunks.append(chunk)

        # Assert: Chunks generated and yielded interleaved (not buffered)
        # Pattern: generate_0, yield_0, generate_1, yield_1, generate_2, yield_2
        assert consumption_order[0] == "generate_0"
        assert consumption_order[1] == "yield_0"
        assert consumption_order[2] == "generate_1"


class TestStreamingWithHistory:
    """Tests for streaming with conversation context."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_maintains_conversation_context(self):
        """
        Verify multi-turn conversation history preserved during streaming.

        Tests that:
        - History passed to start_chat()
        - Correct history format
        - Response builds on context
        """
        # Arrange
        client = GeminiClient()

        history = [
            {"role": "user", "parts": ["What's the capital of France?"]},
            {"role": "model", "parts": ["The capital of France is Paris."]},
            {"role": "user", "parts": ["What about Germany?"]},
            {"role": "model", "parts": ["The capital of Germany is Berlin."]},
        ]

        mock_chunks = [MagicMock(text="The capital "), MagicMock(text="of Italy is Rome.")]

        mock_chat = MagicMock()
        mock_chat.send_message.return_value = iter(mock_chunks)

        # Act
        chunks = []
        with patch.object(client.model, "start_chat", return_value=mock_chat):
            async for chunk in client.generate_stream(
                prompt="What about Italy?",
                history=history
            ):
                chunks.append(chunk)

        # Assert: Full history passed
        call_args = client.model.start_chat.call_args
        assert call_args.kwargs["history"] == history
        assert len(call_args.kwargs["history"]) == 4  # All previous turns

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stream_without_history_uses_generate_content(self):
        """
        Verify streaming without history uses direct generate_content().

        Tests that:
        - No history = no chat session
        - generate_content() called directly
        - stream=True parameter set
        """
        # Arrange
        client = GeminiClient()

        mock_chunks = [MagicMock(text="Direct response")]

        # Act
        chunks = []
        with patch.object(client.model, "generate_content", return_value=iter(mock_chunks)) as mock_gen:
            async for chunk in client.generate_stream(
                prompt="Standalone question",
                history=None
            ):
                chunks.append(chunk)

        # Assert: generate_content called with stream=True
        mock_gen.assert_called_once()
        call_args = mock_gen.call_args
        assert call_args[0][0] == "Standalone question"  # prompt
        assert call_args.kwargs.get("stream") is True or call_args[1] is True  # stream parameter

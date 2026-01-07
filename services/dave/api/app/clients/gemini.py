"""
Gemini AI Client

Provides Google Gemini API integration with streaming support.
Includes circuit breaker pattern for resilience.
"""

import logging
import threading
from typing import AsyncGenerator

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings

logger = logging.getLogger(__name__)

# Circuit breaker state
_circuit_lock = threading.Lock()
_circuit_failures = 0
_circuit_open = False
_circuit_last_failure = 0.0
_circuit_reset_timeout = 60.0  # seconds to wait before half-open

class GeminiCircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class GeminiClient:
    """
    Google Gemini AI client with streaming support.

    Includes circuit breaker pattern:
    - Opens after 3 consecutive failures
    - Stays open for 60 seconds before attempting reset
    - Retries with exponential backoff

    Handles:
    - Text generation (streaming and non-streaming)
    - Embeddings generation for semantic search
    - Multi-turn conversations
    """

    FAILURE_THRESHOLD = 3  # Open circuit after this many failures
    RESET_TIMEOUT = 60.0   # Seconds before trying again

    def __init__(self):
        """Initialize Gemini client with API key."""
        genai.configure(api_key=settings.gemini_api_key)

        # Store generation config for reuse
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        # Text generation model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
        )

        # Embedding model
        self.embedding_model = settings.gemini_embedding_model

    @property
    def is_configured(self) -> bool:
        """Check if Gemini is properly configured."""
        return bool(settings.gemini_api_key)

    def _check_circuit(self):
        """Check if circuit breaker allows request."""
        import time
        global _circuit_open, _circuit_failures, _circuit_last_failure

        with _circuit_lock:
            if not _circuit_open:
                return True

            # Check if enough time has passed to try again (half-open)
            if time.time() - _circuit_last_failure >= self.RESET_TIMEOUT:
                logger.info("Gemini circuit breaker: entering half-open state")
                return True

            return False

    def _record_success(self):
        """Record successful request, reset circuit breaker."""
        global _circuit_open, _circuit_failures

        with _circuit_lock:
            if _circuit_failures > 0:
                logger.info("Gemini circuit breaker: reset after successful request")
            _circuit_failures = 0
            _circuit_open = False

    def _record_failure(self):
        """Record failed request, possibly open circuit."""
        import time
        global _circuit_open, _circuit_failures, _circuit_last_failure

        with _circuit_lock:
            _circuit_failures += 1
            _circuit_last_failure = time.time()

            if _circuit_failures >= self.FAILURE_THRESHOLD:
                _circuit_open = True
                logger.warning(
                    f"Gemini circuit breaker: OPEN after {_circuit_failures} failures. "
                    f"Will retry in {self.RESET_TIMEOUT}s"
                )

    @property
    def circuit_status(self) -> dict:
        """Get current circuit breaker status."""
        import time
        with _circuit_lock:
            return {
                "open": _circuit_open,
                "failures": _circuit_failures,
                "time_until_retry": max(0, self.RESET_TIMEOUT - (time.time() - _circuit_last_failure)) if _circuit_open else 0,
            }

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        history: list[dict] | None = None,
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User message/prompt
            system_instruction: System prompt for context
            history: Conversation history as list of {"role": "user/model", "parts": ["text"]}

        Returns:
            Generated text response

        Raises:
            GeminiCircuitOpenError: If circuit breaker is open
        """
        # Check circuit breaker
        if not self._check_circuit():
            raise GeminiCircuitOpenError(
                "Gemini API circuit breaker is open. Service temporarily unavailable."
            )

        try:
            # Create model with system instruction if provided
            model = self.model
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=settings.gemini_model,
                    system_instruction=system_instruction,
                    generation_config=self.generation_config,
                )

            # Build conversation
            if history:
                chat = model.start_chat(history=history)
                response = chat.send_message(prompt)
            else:
                response = model.generate_content(prompt)

            # Success - reset circuit breaker
            self._record_success()
            return response.text

        except GeminiCircuitOpenError:
            raise
        except Exception as e:
            self._record_failure()
            logger.error(f"Gemini generation error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response.

        Args:
            prompt: User message/prompt
            system_instruction: System prompt for context
            history: Conversation history

        Yields:
            Text chunks as they're generated

        Raises:
            GeminiCircuitOpenError: If circuit breaker is open
        """
        # Check circuit breaker
        if not self._check_circuit():
            raise GeminiCircuitOpenError(
                "Gemini API circuit breaker is open. Service temporarily unavailable."
            )

        try:
            # Create model with system instruction if provided
            model = self.model
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=settings.gemini_model,
                    system_instruction=system_instruction,
                    generation_config=self.generation_config,
                )

            # Build conversation and stream
            if history:
                chat = model.start_chat(history=history)
                response = chat.send_message(prompt, stream=True)
            else:
                response = model.generate_content(prompt, stream=True)

            # Yield chunks
            chunks_received = False
            for chunk in response:
                if chunk.text:
                    chunks_received = True
                    yield chunk.text

            # Success - reset circuit breaker
            if chunks_received:
                self._record_success()

        except GeminiCircuitOpenError:
            raise
        except Exception as e:
            self._record_failure()
            logger.error(f"Gemini streaming error: {e}")
            raise

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions for text-embedding-004)
        """
        try:
            result = genai.embed_content(
                model=f"models/{self.embedding_model}",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]

        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise

    async def generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Uses retrieval_query task type for better search results.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        try:
            result = genai.embed_content(
                model=f"models/{self.embedding_model}",
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]

        except Exception as e:
            logger.error(f"Gemini query embedding error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Gemini API is reachable."""
        try:
            # Simple generation test
            response = self.model.generate_content("Say 'ok'")
            return bool(response.text)
        except Exception:
            return False


# Thread-safe singleton instance
_gemini_client: GeminiClient | None = None
_gemini_lock = threading.Lock()


def get_gemini_client() -> GeminiClient:
    """Get cached Gemini client instance (thread-safe)."""
    global _gemini_client

    if _gemini_client is not None:
        return _gemini_client

    with _gemini_lock:
        # Double-check after acquiring lock
        if _gemini_client is None:
            _gemini_client = GeminiClient()
        return _gemini_client

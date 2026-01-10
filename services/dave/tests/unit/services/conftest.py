"""
Test fixtures for service layer unit tests.

Provides mocked dependencies for service instantiation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_supabase_client():
    """
    Mock Supabase client for unit tests.

    Returns a mock client that prevents real database calls.
    """
    mock_client = MagicMock()
    mock_client.table = MagicMock(return_value=MagicMock())
    return mock_client


@pytest.fixture
def mock_gemini_client():
    """
    Mock Gemini AI client for unit tests.

    Returns a mock client with AsyncMock methods.
    """
    mock = MagicMock()
    mock.generate = AsyncMock(return_value="AI response text")
    mock.generate_stream = AsyncMock()
    mock.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    return mock


@pytest.fixture(autouse=True)
def mock_service_dependencies(monkeypatch):
    """
    Auto-mock service dependencies to prevent real API calls in unit tests.

    This is an EXCEPTION to the "no autouse" rule because:
    1. Unit tests should NEVER make real API calls
    2. Service initialization requires these dependencies
    3. This only affects unit/services/ tests (scoped to this conftest.py)
    """
    # Set environment variables for Supabase (BEFORE clearing caches)
    monkeypatch.setenv("SUPABASE_URL", "http://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    # Clear cached settings and clients to force re-initialization with test values
    from api.app.config import get_settings
    from api.app.clients.supabase import get_supabase_client

    get_settings.cache_clear()
    get_supabase_client.cache_clear()

    yield

    # Clear caches after test
    get_settings.cache_clear()
    get_supabase_client.cache_clear()

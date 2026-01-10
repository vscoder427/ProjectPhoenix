"""
Root test configuration for Dave service.

IMPORTANT: This conftest.py follows enterprise testing standards:
- NO autouse fixtures (prevents over-mocking)
- Minimal fixtures only (event loop, test settings)
- Specific fixtures in subdirectory conftest.py files
- Explicit fixture usage required (test must request what it needs)

See: ProjectPhoenix/docs/standards/testing-database-strategy.md
"""
import pytest
import asyncio
from typing import Dict, Any


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Session-scoped event loop policy for async tests.

    This ensures all async tests use the same event loop policy,
    preventing event loop conflicts in pytest-asyncio.
    """
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def test_settings() -> Dict[str, Any]:
    """
    Override settings for testing environment.

    These settings are used to configure the Dave service
    for testing without hitting production dependencies.

    Returns:
        Dict with test-specific configuration
    """
    return {
        "environment": "test",
        "log_level": "DEBUG",
        "service_name": "dave-test",

        # Disable rate limiting in tests (test guardrails explicitly)
        "rate_limit_enabled": False,

        # Use test API keys (not real credentials)
        "gemini_api_key": "test-gemini-key-12345",
        "dave_api_key": "test-dave-api-key",
        "admin_api_key": "test-admin-api-key",

        # Local database connection (Docker Compose)
        "dave_supabase_url": "http://localhost:3000",
        "dave_supabase_anon_key": "test-anon-key",
        "dave_supabase_service_key": "test-service-key",

        # Redis for rate limiting tests
        "redis_url": "redis://localhost:6379",
    }


@pytest.fixture
def test_user_id() -> str:
    """
    Default test user ID for authenticated requests.

    This matches the default user set in local-init.sql:
    SET auth.current_user_id = '00000000-0000-0000-0000-000000000001'

    Returns:
        UUID string for test user
    """
    return "00000000-0000-0000-0000-000000000001"

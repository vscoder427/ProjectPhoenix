"""
Authentication fixtures for testing.

Provides API keys, JWT tokens, and authentication contexts
for testing authenticated endpoints.
"""
import pytest
from typing import Dict, Any


@pytest.fixture
def valid_api_key() -> str:
    """
    Valid API key for testing authenticated endpoints.

    Matches the test_settings fixture api key.
    Use this for endpoints requiring API key authentication.

    Example:
        def test_admin_endpoint(client, valid_api_key):
            response = client.post(
                "/api/v1/admin/prompts",
                headers={"X-API-Key": valid_api_key},
                json={"category": "system"}
            )
            assert response.status_code == 200
    """
    return "test-dave-api-key"


@pytest.fixture
def admin_api_key() -> str:
    """
    Admin API key for testing admin-only endpoints.

    Use this for endpoints requiring elevated permissions.

    Example:
        def test_delete_prompt(client, admin_api_key):
            response = client.delete(
                "/api/v1/admin/prompts/test-id",
                headers={"X-API-Key": admin_api_key}
            )
            assert response.status_code == 204
    """
    return "test-admin-api-key"


@pytest.fixture
def invalid_api_key() -> str:
    """
    Invalid API key for testing authentication failures.

    Use this to verify endpoints properly reject bad credentials.

    Example:
        def test_rejects_invalid_key(client, invalid_api_key):
            response = client.post(
                "/api/v1/admin/prompts",
                headers={"X-API-Key": invalid_api_key},
                json={"category": "system"}
            )
            assert response.status_code == 401
    """
    return "invalid-key-12345"


@pytest.fixture
def auth_headers(valid_api_key: str) -> Dict[str, str]:
    """
    Headers with valid authentication.

    Convenience fixture for adding auth to requests.

    Example:
        def test_with_auth(client, auth_headers):
            response = client.post(
                "/api/v1/admin/prompts",
                headers=auth_headers,
                json={"category": "system"}
            )
    """
    return {"X-API-Key": valid_api_key}


@pytest.fixture
def admin_headers(admin_api_key: str) -> Dict[str, str]:
    """
    Headers with admin authentication.

    Convenience fixture for admin requests.
    """
    return {"X-API-Key": admin_api_key}


@pytest.fixture
def user_context() -> Dict[str, Any]:
    """
    User context for testing RLS policies and user-scoped operations.

    Provides user ID and metadata for testing user-specific logic.

    Example:
        def test_user_can_only_see_own_conversations(user_context):
            user_id = user_context["user_id"]
            # Test that user can't access other users' data
    """
    return {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "is_authenticated": True,
        "is_admin": False,
        "metadata": {
            "user_type": "job_seeker",
            "recovery_stage": "intermediate",
        },
    }


@pytest.fixture
def admin_context() -> Dict[str, Any]:
    """
    Admin context for testing admin operations.

    Provides admin user ID and elevated permissions.
    """
    return {
        "user_id": "00000000-0000-0000-0000-000000000002",
        "is_authenticated": True,
        "is_admin": True,
        "metadata": {
            "role": "admin",
        },
    }


@pytest.fixture
def anonymous_context() -> Dict[str, Any]:
    """
    Anonymous user context for testing unauthenticated access.

    Dave allows anonymous chat, so test this path.

    Example:
        def test_anonymous_can_chat(anonymous_context):
            assert not anonymous_context["is_authenticated"]
            # Test anonymous chat works
    """
    return {
        "user_id": None,
        "is_authenticated": False,
        "is_admin": False,
        "metadata": {},
    }

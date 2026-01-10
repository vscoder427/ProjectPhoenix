"""
API test configuration.

This conftest.py provides API endpoint test specific fixtures.
API tests validate HTTP contracts and endpoint behavior.
"""
import pytest
from fastapi.testclient import TestClient
from api.app.main import app


@pytest.fixture
def client():
    """
    FastAPI test client for making HTTP requests.

    Returns synchronous TestClient that can make requests
    to the FastAPI app without running a server.

    Example:
        def test_endpoint(client):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
    """
    return TestClient(app)


@pytest.fixture
def async_client():
    """
    Async FastAPI test client for async endpoint testing.

    Use this for endpoints that require async operations.

    Example:
        @pytest.mark.asyncio
        async def test_async_endpoint(async_client):
            response = await async_client.get("/api/v1/endpoint")
            assert response.status_code == 200
    """
    from httpx import AsyncClient

    async def _client():
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    return _client()

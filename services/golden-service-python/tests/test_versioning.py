"""Tests for versioning and deprecation system."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.versions import (
    mark_deprecated,
    get_deprecation_status,
    is_deprecated,
    is_sunset,
    DEPRECATION_REGISTRY,
)

client = TestClient(app)


def test_version_in_metadata():
    """Version should be exposed in /metadata endpoint."""
    response = client.get("/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["version"].count(".") == 2  # Semantic version (X.Y.Z)


def test_version_module_importable():
    """Version module should be importable."""
    from app import __version__, __version_tuple__

    assert isinstance(__version__, str)
    assert isinstance(__version_tuple__, tuple)
    assert len(__version_tuple__) == 3


def test_mark_deprecated():
    """Should mark version as deprecated with sunset date."""
    mark_deprecated("v1-test", sunset_days=30, migration_guide="http://example.com/guide")

    status = get_deprecation_status("v1-test")
    assert status is not None
    assert status.deprecated is True
    assert status.days_until_sunset == 30
    assert status.migration_guide == "http://example.com/guide"

    # Clean up
    del DEPRECATION_REGISTRY["v1-test"]


def test_deprecation_headers():
    """Deprecated endpoints should include deprecation headers."""
    # Mark v1 as deprecated
    mark_deprecated("v1", sunset_days=15)

    response = client.get("/api/v1/chat")  # Any v1 endpoint

    # Check if deprecation headers are present
    if response.status_code != 404:  # Only if endpoint exists
        assert "Deprecation" in response.headers or response.status_code == 410

    # Clean up
    DEPRECATION_REGISTRY["v1"].deprecated = False
    DEPRECATION_REGISTRY["v1"].sunset_date = None


def test_non_deprecated_no_headers():
    """Active versions should not have deprecation headers."""
    response = client.get("/api/v1/health")

    # Health endpoint might be at root
    if response.status_code == 404:
        response = client.get("/health")

    assert "Deprecation" not in response.headers


def test_api_v1_structure():
    """API should be structured with /api/v1/ prefix."""
    # Test that v1 routes exist
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_spec = response.json()
    paths = list(openapi_spec.get("paths", {}).keys())

    # Check that API v1 routes exist
    v1_routes = [p for p in paths if p.startswith("/api/v1/")]
    assert len(v1_routes) > 0, "Should have at least one /api/v1/ route"

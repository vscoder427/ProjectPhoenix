"""
Unit tests for health check endpoints.

Tests health, liveness, readiness, and debug endpoints.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestBasicHealthCheck:
    """Test basic health endpoint."""

    def test_health_endpoint(self):
        """Test GET /api/v1/health returns healthy status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestLivenessProbe:
    """Test liveness probe endpoint."""

    def test_liveness_endpoint(self):
        """Test GET /api/v1/health/live returns alive status."""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


class TestReadinessProbe:
    """Test readiness probe with dependency checks."""

    def test_readiness_all_ok(self):
        """Test readiness when all dependencies are available."""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": "test-id"}]
        mock_supabase.table = MagicMock(return_value=MagicMock(
            select=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    execute=MagicMock(return_value=mock_result)
                ))
            ))
        ))

        # Mock Gemini client
        mock_gemini = MagicMock()
        mock_gemini.is_configured = True

        with patch("app.api.v1.endpoints.health.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.endpoints.health.GeminiClient", return_value=mock_gemini):
                response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["supabase"] == "ok"
        assert data["checks"]["gemini"] == "ok"

    def test_readiness_supabase_error(self):
        """Test readiness when Supabase is unavailable."""
        # Mock Supabase client to raise exception
        with patch("app.api.v1.endpoints.health.get_supabase_client", side_effect=Exception("Connection failed")):
            # Mock Gemini as OK
            mock_gemini = MagicMock()
            mock_gemini.is_configured = True

            with patch("app.api.v1.endpoints.health.GeminiClient", return_value=mock_gemini):
                response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert "error" in data["checks"]["supabase"]
        assert data["checks"]["gemini"] == "ok"

    def test_readiness_gemini_not_configured(self):
        """Test readiness when Gemini is not configured."""
        # Mock Supabase as OK
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": "test-id"}]
        mock_supabase.table = MagicMock(return_value=MagicMock(
            select=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    execute=MagicMock(return_value=mock_result)
                ))
            ))
        ))

        # Mock Gemini as not configured
        mock_gemini = MagicMock()
        mock_gemini.is_configured = False

        with patch("app.api.v1.endpoints.health.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.endpoints.health.GeminiClient", return_value=mock_gemini):
                response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["supabase"] == "ok"
        assert data["checks"]["gemini"] == "not configured"

    def test_readiness_gemini_error(self):
        """Test readiness when Gemini client raises error."""
        # Mock Supabase as OK
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": "test-id"}]
        mock_supabase.table = MagicMock(return_value=MagicMock(
            select=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    execute=MagicMock(return_value=mock_result)
                ))
            ))
        ))

        with patch("app.api.v1.endpoints.health.get_supabase_client", return_value=mock_supabase):
            with patch("app.api.v1.endpoints.health.GeminiClient", side_effect=Exception("Gemini init failed")):
                response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["supabase"] == "ok"
        assert "error" in data["checks"]["gemini"]

    def test_readiness_all_services_down(self):
        """Test readiness when all services are unavailable."""
        with patch("app.api.v1.endpoints.health.get_supabase_client", side_effect=Exception("Supabase down")):
            with patch("app.api.v1.endpoints.health.GeminiClient", side_effect=Exception("Gemini down")):
                response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert "error" in data["checks"]["supabase"]
        assert "error" in data["checks"]["gemini"]


class TestDebugPromptsEndpoint:
    """Test debug prompts endpoint."""

    @pytest.mark.asyncio
    async def test_debug_prompts_all_found(self):
        """Test debug endpoint when all prompts are found."""
        # Mock prompt manager
        mock_prompt_manager = AsyncMock()
        mock_prompt_manager.get_prompt = AsyncMock(side_effect=lambda cat, name, **kwargs: f"Test prompt content for {cat}/{name}")
        mock_prompt_manager.get_dave_system_prompt = AsyncMock(return_value="Full system prompt with all components combined")

        with patch("app.api.v1.endpoints.health.get_prompt_manager", return_value=mock_prompt_manager):
            response = client.get("/api/v1/health/debug/prompts")

        assert response.status_code == 200
        data = response.json()

        # Verify all expected prompts were checked
        assert "dave_system/base_personality" in data
        assert data["dave_system/base_personality"]["status"] == "found"
        assert "preview" in data["dave_system/base_personality"]
        assert "length" in data["dave_system/base_personality"]

        # Verify full system prompt
        assert "full_system_prompt" in data
        assert data["full_system_prompt"]["status"] == "built"

    @pytest.mark.asyncio
    async def test_debug_prompts_some_not_found(self):
        """Test debug endpoint when some prompts are missing."""
        # Mock prompt manager to return None for some prompts
        async def mock_get_prompt(category, name, **kwargs):
            if name == "base_personality":
                return "Test content"
            return None  # Simulate missing prompt

        mock_prompt_manager = AsyncMock()
        mock_prompt_manager.get_prompt = AsyncMock(side_effect=mock_get_prompt)
        mock_prompt_manager.get_dave_system_prompt = AsyncMock(return_value="System prompt")

        with patch("app.api.v1.endpoints.health.get_prompt_manager", return_value=mock_prompt_manager):
            response = client.get("/api/v1/health/debug/prompts")

        assert response.status_code == 200
        data = response.json()

        # Verify found prompt
        assert data["dave_system/base_personality"]["status"] == "found"

        # Verify missing prompts
        assert data["dave_system/job_seeker_mode"]["status"] == "not_found"
        assert data["dave_system/job_seeker_mode"]["using_fallback"] is True

    @pytest.mark.asyncio
    async def test_debug_prompts_with_errors(self):
        """Test debug endpoint when prompt loading raises errors."""
        # Mock prompt manager to raise exception
        mock_prompt_manager = AsyncMock()
        mock_prompt_manager.get_prompt = AsyncMock(side_effect=Exception("Database connection failed"))
        mock_prompt_manager.get_dave_system_prompt = AsyncMock(side_effect=Exception("Cannot build prompt"))

        with patch("app.api.v1.endpoints.health.get_prompt_manager", return_value=mock_prompt_manager):
            response = client.get("/api/v1/health/debug/prompts")

        assert response.status_code == 200
        data = response.json()

        # Verify errors are captured
        assert data["dave_system/base_personality"]["status"] == "error"
        assert "error" in data["dave_system/base_personality"]
        assert data["full_system_prompt"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_debug_prompts_long_content_truncated(self):
        """Test that long prompt content is truncated in preview."""
        # Create a very long prompt
        long_content = "x" * 500  # 500 characters

        mock_prompt_manager = AsyncMock()
        mock_prompt_manager.get_prompt = AsyncMock(return_value=long_content)
        mock_prompt_manager.get_dave_system_prompt = AsyncMock(return_value=long_content)

        with patch("app.api.v1.endpoints.health.get_prompt_manager", return_value=mock_prompt_manager):
            response = client.get("/api/v1/health/debug/prompts")

        assert response.status_code == 200
        data = response.json()

        # Verify content is truncated to 100 chars + "..."
        prompt_data = data["dave_system/base_personality"]
        assert len(prompt_data["preview"]) == 103  # 100 + "..."
        assert prompt_data["preview"].endswith("...")
        assert prompt_data["length"] == 500

        # Verify full system prompt is truncated to 200 chars + "..."
        system_data = data["full_system_prompt"]
        assert len(system_data["preview"]) == 203  # 200 + "..."
        assert system_data["preview"].endswith("...")

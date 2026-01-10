"""
Unit tests for PromptsRepository.

Tests database operations with mocked Supabase client.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.repositories.prompts import PromptsRepository


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for repository tests."""
    client = MagicMock()
    client.table = MagicMock()
    return client


@pytest.fixture
def prompts_repo(mock_supabase_client):
    """PromptsRepository with mocked Supabase client."""
    with patch("app.repositories.prompts.get_supabase_client", return_value=mock_supabase_client):
        repo = PromptsRepository()
        repo.client = mock_supabase_client
        return repo


class TestGetPromptByCategoryName:
    """Test retrieving prompts by category and name."""

    @pytest.mark.asyncio
    async def test_get_prompt_success(self, prompts_repo, mock_supabase_client):
        """Test successfully retrieving a prompt."""
        # Mock response with version data
        mock_response = MagicMock()
        mock_response.data = [{
            "id": str(uuid4()),
            "category": "dave_system",
            "name": "base_personality",
            "is_archived": False,
            "admin_prompt_versions": {
                "id": str(uuid4()),
                "version_number": 3,
                "content": "Test prompt content",
            },
        }]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await prompts_repo.get_prompt_by_category_name("dave_system", "base_personality")

        # Verify
        assert result is not None
        assert result["category"] == "dave_system"
        assert result["name"] == "base_personality"
        assert "current_version" in result
        assert result["current_version"]["content"] == "Test prompt content"

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self, prompts_repo, mock_supabase_client):
        """Test prompt not found returns None."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await prompts_repo.get_prompt_by_category_name("nonexistent", "prompt")

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_error_handling(self, prompts_repo, mock_supabase_client):
        """Test error handling when fetch fails."""
        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(side_effect=Exception("Database error"))
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Database error"):
            await prompts_repo.get_prompt_by_category_name("dave_system", "test")


class TestGetPromptById:
    """Test retrieving prompts by ID."""

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_success(self, prompts_repo, mock_supabase_client):
        """Test successfully retrieving prompt by ID."""
        prompt_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [{
            "id": prompt_id,
            "category": "dave_system",
            "name": "test_prompt",
            "admin_prompt_versions": {
                "id": str(uuid4()),
                "content": "Test content",
            },
        }]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await prompts_repo.get_prompt_by_id(prompt_id)

        # Verify
        assert result is not None
        assert result["id"] == prompt_id
        assert "current_version" in result

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_not_found(self, prompts_repo, mock_supabase_client):
        """Test ID not found returns None."""
        mock_response = MagicMock()
        mock_response.data = []

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await prompts_repo.get_prompt_by_id(str(uuid4()))

        # Verify
        assert result is None


class TestListPrompts:
    """Test listing prompts with pagination and filtering."""

    @pytest.mark.asyncio
    async def test_list_prompts_basic(self, prompts_repo, mock_supabase_client):
        """Test basic prompt listing."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "category": "dave_system",
                "name": "prompt1",
                "admin_prompt_versions": {"content": "Test 1"},
            },
            {
                "id": str(uuid4()),
                "category": "dave_system",
                "name": "prompt2",
                "admin_prompt_versions": {"content": "Test 2"},
            },
        ]
        mock_response.count = 2

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.range = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        prompts, total = await prompts_repo.list_prompts()

        # Verify
        assert len(prompts) == 2
        assert total == 2
        assert all("current_version" in p for p in prompts)

    @pytest.mark.asyncio
    async def test_list_prompts_with_category_filter(self, prompts_repo, mock_supabase_client):
        """Test filtering prompts by category."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.count = 0

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.range = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        prompts, total = await prompts_repo.list_prompts(category="dave_system")

        # Verify category filter was applied (2 eq calls: category + is_archived)
        assert mock_builder.eq.call_count == 2

    @pytest.mark.asyncio
    async def test_list_prompts_with_pagination(self, prompts_repo, mock_supabase_client):
        """Test pagination parameters."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.count = 100

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.range = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute page 2 with limit 20
        prompts, total = await prompts_repo.list_prompts(page=2, limit=20)

        # Verify pagination: offset = (2-1) * 20 = 20, range(20, 39)
        mock_builder.range.assert_called_once_with(20, 39)


class TestGetPromptVersions:
    """Test retrieving prompt version history."""

    @pytest.mark.asyncio
    async def test_get_versions_success(self, prompts_repo, mock_supabase_client):
        """Test getting all versions of a prompt."""
        prompt_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [
            {"id": str(uuid4()), "version_number": 3, "content": "Latest"},
            {"id": str(uuid4()), "version_number": 2, "content": "Middle"},
            {"id": str(uuid4()), "version_number": 1, "content": "First"},
        ]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.order = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        versions = await prompts_repo.get_prompt_versions(prompt_id)

        # Verify
        assert len(versions) == 3
        assert versions[0]["version_number"] == 3  # Ordered descending
        mock_builder.order.assert_called_once_with("version_number", desc=True)


class TestCreateVersion:
    """Test creating new prompt versions."""

    @pytest.mark.asyncio
    async def test_create_version_first_version(self, prompts_repo, mock_supabase_client):
        """Test creating the first version of a prompt."""
        prompt_id = str(uuid4())

        # Mock get_prompt_versions to return empty (no existing versions)
        with patch.object(prompts_repo, 'get_prompt_versions', return_value=[]):
            # Mock insert response
            version_id = str(uuid4())
            mock_insert_response = MagicMock()
            mock_insert_response.data = [{
                "id": version_id,
                "prompt_id": prompt_id,
                "version_number": 1,
                "content": "Initial content",
            }]

            # Mock update response (for setting current_version_id)
            mock_update_response = MagicMock()
            mock_update_response.data = [{"id": prompt_id}]

            mock_builder = MagicMock()
            mock_builder.insert = MagicMock(return_value=mock_builder)
            mock_builder.update = MagicMock(return_value=mock_builder)
            mock_builder.eq = MagicMock(return_value=mock_builder)
            mock_builder.execute = MagicMock(side_effect=[mock_insert_response, mock_update_response])
            mock_supabase_client.table = MagicMock(return_value=mock_builder)

            # Execute
            result = await prompts_repo.create_version(
                prompt_id=prompt_id,
                content="Initial content",
                commit_message="Initial version",
            )

            # Verify
            assert result is not None
            assert result["version_number"] == 1
            assert result["content"] == "Initial content"

    @pytest.mark.asyncio
    async def test_create_version_increments(self, prompts_repo, mock_supabase_client):
        """Test that version numbers increment correctly."""
        prompt_id = str(uuid4())

        # Mock existing versions
        existing_versions = [
            {"id": str(uuid4()), "version_number": 2, "content": "Second"},
        ]

        with patch.object(prompts_repo, 'get_prompt_versions', return_value=existing_versions):
            version_id = str(uuid4())
            mock_insert_response = MagicMock()
            mock_insert_response.data = [{
                "id": version_id,
                "version_number": 3,  # Should increment to 3
                "content": "Third version",
            }]

            mock_update_response = MagicMock()
            mock_update_response.data = [{"id": prompt_id}]

            mock_builder = MagicMock()
            mock_builder.insert = MagicMock(return_value=mock_builder)
            mock_builder.update = MagicMock(return_value=mock_builder)
            mock_builder.eq = MagicMock(return_value=mock_builder)
            mock_builder.execute = MagicMock(side_effect=[mock_insert_response, mock_update_response])
            mock_supabase_client.table = MagicMock(return_value=mock_builder)

            # Execute
            result = await prompts_repo.create_version(
                prompt_id=prompt_id,
                content="Third version",
                commit_message="Update",
            )

            # Verify version incremented
            assert result["version_number"] == 3


class TestRollbackToVersion:
    """Test rolling back to previous versions."""

    @pytest.mark.asyncio
    async def test_rollback_success(self, prompts_repo, mock_supabase_client):
        """Test successful version rollback."""
        prompt_id = str(uuid4())
        version_id = str(uuid4())

        # Mock version check response
        check_response = MagicMock()
        check_response.data = [{"id": version_id, "prompt_id": prompt_id}]

        # Mock update response
        update_response = MagicMock()
        update_response.data = [{"id": prompt_id, "current_version_id": version_id}]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.update = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(side_effect=[check_response, update_response])
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        result = await prompts_repo.rollback_to_version(prompt_id, version_id)

        # Verify
        assert result is True

    @pytest.mark.asyncio
    async def test_rollback_version_not_found(self, prompts_repo, mock_supabase_client):
        """Test rollback fails when version doesn't exist."""
        # Mock empty check response
        check_response = MagicMock()
        check_response.data = []

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=check_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute and verify exception
        with pytest.raises(ValueError, match="Version .* not found"):
            await prompts_repo.rollback_to_version(str(uuid4()), str(uuid4()))


class TestGetCategories:
    """Test retrieving prompt categories."""

    @pytest.mark.asyncio
    async def test_get_categories_success(self, prompts_repo, mock_supabase_client):
        """Test getting categories with counts."""
        mock_response = MagicMock()
        mock_response.data = [
            {"category": "dave_system"},
            {"category": "dave_system"},
            {"category": "nudges"},
            {"category": "nudges"},
            {"category": "nudges"},
        ]

        mock_builder = MagicMock()
        mock_builder.select = MagicMock(return_value=mock_builder)
        mock_builder.eq = MagicMock(return_value=mock_builder)
        mock_builder.execute = MagicMock(return_value=mock_response)
        mock_supabase_client.table = MagicMock(return_value=mock_builder)

        # Execute
        categories = await prompts_repo.get_categories()

        # Verify
        assert len(categories) == 2
        # Should be sorted alphabetically
        assert categories[0]["category"] == "dave_system"
        assert categories[0]["prompt_count"] == 2
        assert categories[1]["category"] == "nudges"
        assert categories[1]["prompt_count"] == 3


class TestGetPromptsByCategory:
    """Test retrieving all prompts in a category."""

    @pytest.mark.asyncio
    async def test_get_prompts_by_category(self, prompts_repo, mock_supabase_client):
        """Test getting all prompts for a category."""
        # Mock list_prompts response
        mock_prompts = [
            {"id": str(uuid4()), "category": "dave_system", "name": "prompt1"},
            {"id": str(uuid4()), "category": "dave_system", "name": "prompt2"},
        ]

        with patch.object(prompts_repo, 'list_prompts', return_value=(mock_prompts, 2)):
            # Execute
            result = await prompts_repo.get_prompts_by_category("dave_system")

            # Verify
            assert len(result) == 2
            assert all(p["category"] == "dave_system" for p in result)

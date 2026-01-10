"""
Database fixtures for integration testing.

Provides test database setup and cleanup for integration tests
that use the real local PostgreSQL database (Docker Compose).
"""
import pytest
import asyncio
from typing import AsyncIterator, Dict, Any
from supabase import create_client, Client


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """
    Test database URL for local Docker PostgreSQL.

    Points to PostgREST running on localhost:3000.

    Example:
        def test_with_db(test_db_url):
            client = create_client(test_db_url, "test-anon-key")
    """
    return "http://localhost:3000"


@pytest.fixture(scope="session")
def test_db_anon_key() -> str:
    """
    Test database anonymous key.

    For local testing only. Real Supabase anon key respects RLS.
    """
    return "test-anon-key"


@pytest.fixture(scope="session")
def test_db_service_key() -> str:
    """
    Test database service role key.

    Bypasses RLS for setup/cleanup operations.
    """
    return "test-service-key"


@pytest.fixture
async def test_db(
    test_db_url: str, test_db_service_key: str
) -> AsyncIterator[Client]:
    """
    Supabase client connected to test database.

    Yields client for test, then cleans up test data.

    Marker Required: @pytest.mark.integration

    Example:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_conversation_creation(test_db):
            # test_db is a Supabase client connected to local database
            result = test_db.table("ai_conversations").insert({
                "user_id": "00000000-0000-0000-0000-000000000001",
                "title": "Test Conversation"
            }).execute()

            assert result.data is not None
            # Cleanup happens automatically after test
    """
    client = create_client(test_db_url, test_db_service_key)

    yield client

    # Cleanup: Delete all test data after test completes
    # Use test user ID pattern to identify test data
    test_user_pattern = "00000000-0000-0000-0000-%"

    try:
        # Delete in order respecting foreign keys
        await asyncio.to_thread(
            client.table("ai_messages")
            .delete()
            .like("conversation_id", test_user_pattern)
            .execute
        )

        await asyncio.to_thread(
            client.table("ai_conversations")
            .delete()
            .like("user_id", test_user_pattern)
            .execute
        )

        # Note: admin_prompt_versions and admin_prompts
        # typically don't need cleanup (immutable test data)
    except Exception as e:
        # Don't fail test if cleanup fails
        print(f"Warning: Test cleanup failed: {e}")


@pytest.fixture
async def clean_test_db(test_db: Client) -> Client:
    """
    Clean test database before test runs.

    Use this when you need guaranteed clean state before test.

    Example:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_with_clean_db(clean_test_db):
            # Database is clean before test starts
            result = clean_test_db.table("ai_conversations").select("*").execute()
            assert len(result.data) == 0
    """
    test_user_pattern = "00000000-0000-0000-0000-%"

    # Clean before test
    try:
        await asyncio.to_thread(
            test_db.table("ai_messages")
            .delete()
            .like("conversation_id", test_user_pattern)
            .execute
        )

        await asyncio.to_thread(
            test_db.table("ai_conversations")
            .delete()
            .like("user_id", test_user_pattern)
            .execute
        )
    except Exception as e:
        print(f"Warning: Pre-test cleanup failed: {e}")

    return test_db


@pytest.fixture
def db_transaction_context() -> Dict[str, Any]:
    """
    Context for database transaction testing.

    Provides transaction setup/rollback helpers.

    Example:
        @pytest.mark.integration
        async def test_rollback_on_error(db_transaction_context):
            # Test that errors properly rollback transactions
            pass
    """
    return {
        "isolation_level": "READ COMMITTED",
        "autocommit": False,
    }


@pytest.fixture
async def seed_test_conversations(test_db: Client) -> Dict[str, Any]:
    """
    Seed test database with sample conversations.

    Returns IDs of created test data for use in tests.

    Example:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_list_conversations(seed_test_conversations):
            conv_ids = seed_test_conversations["conversation_ids"]
            # Test can now query these conversations
    """
    test_user_id = "00000000-0000-0000-0000-000000000001"

    # Create 3 test conversations
    conversations = []
    for i in range(3):
        result = await asyncio.to_thread(
            test_db.table("ai_conversations")
            .insert(
                {
                    "user_id": test_user_id,
                    "title": f"Test Conversation {i + 1}",
                    "status": "active",
                    "context": {"user_type": "job_seeker"},
                }
            )
            .execute
        )
        conversations.append(result.data[0])

    return {
        "conversation_ids": [c["id"] for c in conversations],
        "conversations": conversations,
        "user_id": test_user_id,
    }


@pytest.fixture
async def seed_test_knowledge(test_db: Client) -> Dict[str, Any]:
    """
    Seed test database with sample knowledge articles.

    Returns IDs of created test data.

    Example:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_knowledge_search(seed_test_knowledge):
            article_ids = seed_test_knowledge["article_ids"]
            # Test knowledge search with real data
    """
    # Note: This assumes knowledge articles table exists
    # Adjust based on actual schema when knowledge base is implemented

    articles = [
        {
            "title": "Test Career Article",
            "content": "Career guidance content",
            "category": "career_guidance",
            "tags": ["test", "career"],
        },
        {
            "title": "Test Recovery Article",
            "content": "Recovery support content",
            "category": "recovery_support",
            "tags": ["test", "recovery"],
        },
    ]

    created_articles = []
    for article in articles:
        try:
            result = await asyncio.to_thread(
                test_db.table("knowledge_articles").insert(article).execute
            )
            created_articles.append(result.data[0])
        except Exception:
            # Knowledge table might not exist yet
            pass

    return {
        "article_ids": [a.get("id") for a in created_articles if a.get("id")],
        "articles": created_articles,
    }

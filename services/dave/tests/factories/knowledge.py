"""
Knowledge article test data factories.

These factories generate realistic knowledge base article data
for testing without requiring database access.
"""
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional


class KnowledgeArticleFactory:
    """Factory for creating test knowledge base article data."""

    @staticmethod
    def create(**overrides) -> Dict[str, Any]:
        """
        Create a test knowledge article with sensible defaults.

        Args:
            **overrides: Override any default fields

        Returns:
            Dict representing a knowledge article record

        Example:
            >>> article = KnowledgeArticleFactory.create(
            ...     title="Interview Preparation Guide",
            ...     category="career_guidance"
            ... )
        """
        defaults = {
            "id": str(uuid4()),
            "title": "Test Knowledge Article",
            "content": "This is test knowledge base content about recovery and career development.",
            "category": "general",
            "tags": ["test", "example"],
            "source_url": "https://example.com/article",
            "embedding": [0.1] * 768,  # Mock 768-dimensional embedding vector
            "metadata": {
                "author": "Test Author",
                "date_published": "2024-01-01",
                "reading_time_minutes": 5,
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }
        return {**defaults, **overrides}

    @staticmethod
    def career_guidance(**overrides) -> Dict[str, Any]:
        """Create a career guidance knowledge article."""
        return KnowledgeArticleFactory.create(
            category="career_guidance",
            title="Finding Your First Job in Recovery",
            content="""
            This guide provides strategies for job seekers in recovery:

            1. **Resume Building**: Highlight transferable skills
            2. **Interview Preparation**: Practice common questions
            3. **Disclosure Decisions**: When and how to discuss recovery
            4. **Networking**: Build professional connections
            5. **Self-Care**: Maintain recovery during job search
            """,
            tags=["career", "job_search", "recovery"],
            **overrides,
        )

    @staticmethod
    def recovery_resources(**overrides) -> Dict[str, Any]:
        """Create a recovery resources knowledge article."""
        return KnowledgeArticleFactory.create(
            category="recovery_support",
            title="Understanding 12-Step Programs",
            content="""
            12-step programs provide structured support for recovery:

            - **Meetings**: Regular gatherings for support
            - **Sponsorship**: One-on-one mentorship
            - **Steps**: Guided process for personal growth
            - **Service**: Giving back to the community
            - **Fellowship**: Building supportive relationships
            """,
            tags=["recovery", "12-step", "support"],
            **overrides,
        )

    @staticmethod
    def employer_resources(**overrides) -> Dict[str, Any]:
        """Create an employer resources knowledge article."""
        return KnowledgeArticleFactory.create(
            category="employer_resources",
            title="Creating Recovery-Friendly Workplaces",
            content="""
            Best practices for recovery-friendly employers:

            1. **Flexible Scheduling**: Support recovery program attendance
            2. **EAP Programs**: Provide employee assistance resources
            3. **Non-Discrimination**: Fair hiring practices
            4. **Supportive Culture**: Reduce stigma around recovery
            5. **Reasonable Accommodations**: Support recovery needs
            """,
            tags=["employer", "workplace", "recovery-friendly"],
            **overrides,
        )

    @staticmethod
    def with_embedding(
        embedding_vector: Optional[List[float]] = None, **overrides
    ) -> Dict[str, Any]:
        """
        Create a knowledge article with custom embedding.

        Args:
            embedding_vector: Custom embedding vector (default: 768-dim zeros)
            **overrides: Additional field overrides

        Returns:
            Dict representing knowledge article with embedding
        """
        if embedding_vector is None:
            embedding_vector = [0.0] * 768

        return KnowledgeArticleFactory.create(
            embedding=embedding_vector, **overrides
        )

    @staticmethod
    def batch(count: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Create multiple knowledge articles.

        Args:
            count: Number of articles to create (default: 5)
            category: Optional category for all articles

        Returns:
            List of knowledge article dicts

        Example:
            >>> articles = KnowledgeArticleFactory.batch(
            ...     count=10,
            ...     category="career_guidance"
            ... )
        """
        articles = []
        for i in range(count):
            overrides = {"title": f"Test Article {i + 1}"}
            if category:
                overrides["category"] = category

            articles.append(KnowledgeArticleFactory.create(**overrides))

        return articles

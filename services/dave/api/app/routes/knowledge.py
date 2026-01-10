"""
Knowledge Base Endpoints

Search and retrieve knowledge base content.
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.app.middleware.auth import AuthContext, optional_auth
from api.app.repositories.knowledge import KnowledgeRepository
from api.app.schemas.knowledge import (
    SearchRequest,
    SearchResponse,
    KnowledgeResult,
    Article,
    FAQ,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    auth: AuthContext = Depends(optional_auth),
):
    """
    Search the knowledge base using hybrid search.

    Combines semantic (vector) and full-text search for best results.
    """
    start_time = time.time()

    try:
        repo = KnowledgeRepository()
        category = request.filters.categories[0] if request.filters and request.filters.categories else None
        recovery_focused = request.filters.recovery_focused if request.filters else None

        if request.search_type == "semantic":
            raw_results = await repo.search_semantic(
                query=request.query,
                limit=request.limit,
            )
        elif request.search_type == "fulltext":
            articles = await repo.search_articles_fulltext(
                query=request.query,
                category=category,
                recovery_focused=recovery_focused,
                limit=request.limit,
            )
            faqs = await repo.search_faqs_fulltext(
                query=request.query,
                limit=min(request.limit, 5),
            )
            raw_results = [
                {
                    **article,
                    "type": "article",
                    "score": article.get("rank_score", 0.5),
                    "source": "fulltext",
                }
                for article in articles
            ] + [
                {
                    **faq,
                    "type": "faq",
                    "score": faq.get("rank_score", 0.5),
                    "source": "fulltext",
                }
                for faq in faqs
            ]
        else:
            raw_results = await repo.search_hybrid(
                query=request.query,
                category=category,
                recovery_focused=recovery_focused,
                limit=request.limit,
            )

        results = []
        for item in raw_results:
            result_type = item.get("type") or ("faq" if item.get("question") else "article")
            title = item.get("title") or item.get("question") or "Untitled"
            results.append(
                KnowledgeResult(
                    id=item["id"],
                    type=result_type,
                    title=title,
                    excerpt=item.get("excerpt"),
                    content=item.get("content") if request.include_content else None,
                    category=item.get("category_id"),
                    url=item.get("url") or "",
                    score=item.get("score", item.get("rank_score", 0.5)),
                    source=item.get("source", "fulltext"),
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        results = results[: request.limit]

        took_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            search_type=request.search_type,
            took_ms=took_ms,
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/articles/{article_id}")
async def get_article(
    article_id: str,
    auth: AuthContext = Depends(optional_auth),
):
    """
    Get a single article by ID.
    """
    try:
        repo = KnowledgeRepository()

        article = await repo.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Increment view count
        await repo.increment_view_count(article_id)

        return Article(
            id=article["id"],
            title=article["title"],
            slug=article["slug"],
            excerpt=article.get("excerpt"),
            content=article["content"],
            content_html=article.get("content_html"),
            category_id=article.get("category_id"),
            category_name=article.get("category_name"),
            content_type=article.get("content_type", "article"),
            difficulty_level=article.get("difficulty_level"),
            reading_time=article.get("reading_time"),
            tags=article.get("tags", []),
            is_recovery_focused=article.get("is_recovery_focused", False),
            is_featured=article.get("is_featured", False),
            view_count=article.get("view_count", 0),
            helpful_count=article.get("helpful_count", 0),
            created_at=article["created_at"],
            updated_at=article["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get article error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get article")


@router.get("/articles/slug/{slug}")
async def get_article_by_slug(
    slug: str,
    auth: AuthContext = Depends(optional_auth),
):
    """
    Get a single article by slug.
    """
    try:
        repo = KnowledgeRepository()

        article = await repo.get_article_by_slug(slug)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Increment view count
        await repo.increment_view_count(article["id"])

        return Article(
            id=article["id"],
            title=article["title"],
            slug=article["slug"],
            excerpt=article.get("excerpt"),
            content=article["content"],
            content_html=article.get("content_html"),
            category_id=article.get("category_id"),
            category_name=article.get("category_name"),
            content_type=article.get("content_type", "article"),
            difficulty_level=article.get("difficulty_level"),
            reading_time=article.get("reading_time"),
            tags=article.get("tags", []),
            is_recovery_focused=article.get("is_recovery_focused", False),
            is_featured=article.get("is_featured", False),
            view_count=article.get("view_count", 0),
            helpful_count=article.get("helpful_count", 0),
            created_at=article["created_at"],
            updated_at=article["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get article by slug error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get article")


@router.get("/faqs")
async def list_faqs(
    category_id: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    auth: AuthContext = Depends(optional_auth),
):
    """
    List FAQs with optional filters.
    """
    try:
        repo = KnowledgeRepository()

        faqs = await repo.get_faqs(
            category_id=category_id,
            featured_only=featured_only,
            limit=limit,
        )

        return {
            "faqs": [
                FAQ(
                    id=faq["id"],
                    question=faq["question"],
                    answer=faq["answer"],
                    category_id=faq.get("category_id"),
                    category_name=faq.get("category_name"),
                    display_order=faq.get("display_order", 0),
                    is_featured=faq.get("is_featured", False),
                    is_expert_answer=faq.get("is_expert_answer", False),
                    related_article_ids=faq.get("related_article_ids", []),
                )
                for faq in faqs
            ],
            "total": len(faqs),
        }

    except Exception as e:
        logger.error(f"List FAQs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list FAQs")


@router.get("/categories")
async def list_categories(
    auth: AuthContext = Depends(optional_auth),
):
    """
    List all knowledge base categories.
    """
    try:
        repo = KnowledgeRepository()
        categories = await repo.get_categories()

        return {"categories": categories}

    except Exception as e:
        logger.error(f"List categories error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list categories")


@router.get("/recovery")
async def get_recovery_content(
    limit: int = Query(10, ge=1, le=50),
    auth: AuthContext = Depends(optional_auth),
):
    """
    Get recovery-focused articles.

    Returns articles specifically tagged for recovery audience.
    """
    try:
        repo = KnowledgeRepository()
        articles = await repo.get_recovery_focused_articles(limit=limit)

        return {
            "articles": articles,
            "total": len(articles),
        }

    except Exception as e:
        logger.error(f"Get recovery content error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recovery content")

"""
Knowledge Base Schemas

Pydantic models for knowledge base search and retrieval.
"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Filters for knowledge base search."""

    categories: Optional[list[str]] = None
    content_types: Optional[list[Literal["article", "faq", "video", "resource"]]] = None
    difficulty_levels: Optional[list[str]] = None  # beginner, intermediate, advanced, expert
    recovery_focused: Optional[bool] = None
    tags: Optional[list[str]] = None


class SearchRequest(BaseModel):
    """Knowledge base search request."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_type: Literal["hybrid", "semantic", "fulltext"] = Field("hybrid", description="Search algorithm")
    filters: Optional[SearchFilters] = None
    limit: int = Field(10, ge=1, le=50, description="Max results to return")
    include_content: bool = Field(False, description="Include full content in results")


class KnowledgeResult(BaseModel):
    """Single knowledge base search result."""

    id: str
    type: Literal["article", "faq", "video", "resource"]
    title: str
    excerpt: Optional[str] = None
    content: Optional[str] = None  # Only if include_content=True
    category: Optional[str] = None
    url: str
    score: float = Field(..., description="Relevance score (0-1)")
    source: Literal["semantic", "fulltext", "both"] = Field(..., description="Search source")
    metadata: Optional[dict] = None


class SearchResponse(BaseModel):
    """Knowledge base search response."""

    results: list[KnowledgeResult]
    total: int
    query: str
    search_type: str
    took_ms: Optional[float] = None


class Article(BaseModel):
    """Full knowledge base article."""

    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    content_html: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    content_type: str
    difficulty_level: Optional[str] = None
    reading_time: Optional[int] = None  # minutes
    tags: list[str] = []
    is_recovery_focused: bool = False
    is_featured: bool = False
    view_count: int = 0
    helpful_count: int = 0
    created_at: datetime
    updated_at: datetime


class FAQ(BaseModel):
    """FAQ entry."""

    id: str
    question: str
    answer: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    display_order: int = 0
    is_featured: bool = False
    is_expert_answer: bool = False
    related_article_ids: list[str] = []

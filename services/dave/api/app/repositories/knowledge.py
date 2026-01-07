"""
Knowledge Base Repository

Database operations for knowledge articles, FAQs, and storage bucket resources.
"""

import logging
import math
import re
from typing import Optional
from bs4 import BeautifulSoup

from app.clients.supabase import get_supabase_client
from app.clients.http_pool import get_http_client
from app.clients.gemini import get_gemini_client
from app.config import settings

logger = logging.getLogger(__name__)

# Cache for storage articles (loaded once at startup)
_storage_articles_cache: list[dict] = []
_storage_articles_loaded: bool = False
_semantic_documents_cache: list[dict] = []
_semantic_documents_loaded: bool = False
_semantic_embeddings_cache: dict[str, list[float]] = {}

SEMANTIC_WEIGHT = 0.65
FULLTEXT_WEIGHT = 0.35


class KnowledgeRepository:
    """Repository for knowledge base database operations."""

    def __init__(self):
        self.client = get_supabase_client()
        self.storage_bucket = "knowledgebase"
        self.supabase_url = settings.supabase_url
        self.gemini = get_gemini_client()

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _normalize_similarity(self, score: float) -> float:
        """Normalize cosine similarity to 0-1 range."""
        return max(0.0, min(1.0, (score + 1.0) / 2.0))

    async def _load_semantic_documents(self) -> list[dict]:
        """Load and cache documents for semantic search."""
        global _semantic_documents_cache, _semantic_documents_loaded

        if _semantic_documents_loaded:
            return _semantic_documents_cache

        documents: list[dict] = []

        # Load articles from storage bucket
        articles = await self._load_storage_articles()
        for article in articles:
            content = await self._fetch_article_content(article["url"])
            excerpt = content[:200] + "..." if content else f"Career guidance article: {article['title']}"
            documents.append({
                "id": article["id"],
                "cache_key": f"article:{article['id']}",
                "type": "article",
                "title": article["title"],
                "url": article.get("url"),
                "excerpt": excerpt,
                "text": f"{article['title']}\n{content}".strip(),
            })

        # Load FAQs for semantic search
        try:
            result = self.client.table("faqs").select("id, question, answer").execute()
            for faq in result.data or []:
                documents.append({
                    "id": faq["id"],
                    "cache_key": f"faq:{faq['id']}",
                    "type": "faq",
                    "title": faq["question"],
                    "url": f"/knowledge-base/faq#{faq['id']}",
                    "excerpt": faq["answer"][:200] + "..." if len(faq["answer"]) > 200 else faq["answer"],
                    "text": f"FAQ: {faq['question']}\n{faq['answer']}".strip(),
                })
        except Exception as e:
            logger.error(f"Error loading FAQs for semantic search: {e}")

        _semantic_documents_cache = documents
        _semantic_documents_loaded = True
        return documents

    async def _ensure_document_embeddings(self, documents: list[dict]) -> None:
        """Generate embeddings for documents that are missing them."""
        for doc in documents:
            cache_key = doc.get("cache_key")
            if not cache_key or cache_key in _semantic_embeddings_cache:
                continue
            text = doc.get("text") or doc.get("title") or ""
            if not text:
                continue
            try:
                _semantic_embeddings_cache[cache_key] = await self.gemini.generate_embedding(text)
            except Exception as e:
                logger.error(f"Error generating embedding for {cache_key}: {e}")

    async def _load_storage_articles(self) -> list[dict]:
        """Load and cache articles from Supabase storage bucket."""
        global _storage_articles_cache, _storage_articles_loaded

        if _storage_articles_loaded:
            return _storage_articles_cache

        try:
            # List files in the knowledgebase bucket
            result = self.client.storage.from_(self.storage_bucket).list()

            articles = []
            for file_info in result:
                if file_info.get("name", "").endswith(".html"):
                    # Get public URL
                    file_name = file_info["name"]
                    public_url = f"{self.supabase_url}/storage/v1/object/public/{self.storage_bucket}/{file_name}"

                    # Extract title from filename
                    title = file_name.replace(".html", "").replace("_", " ").replace("-", " ")

                    articles.append({
                        "id": file_info.get("id", file_name),
                        "title": title,
                        "filename": file_name,
                        "url": public_url,
                        "size": file_info.get("metadata", {}).get("size", 0),
                        "type": "article",
                    })

            _storage_articles_cache = articles
            _storage_articles_loaded = True
            logger.info(f"Loaded {len(articles)} articles from storage bucket")
            return articles

        except Exception as e:
            logger.error(f"Error loading storage articles: {e}")
            return []

    async def _fetch_article_content(self, url: str) -> str:
        """Fetch and parse HTML article content using pooled HTTP client."""
        try:
            # Use shared HTTP client with connection pooling
            client = get_http_client()
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Extract text content, removing scripts and styles
                for tag in soup(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator=" ", strip=True)
                # Limit to first 2000 chars for context
                return text[:2000]
        except Exception as e:
            logger.error(f"Error fetching article {url}: {e}")
        return ""

    async def search_articles_fulltext(
        self,
        query: str,
        category: Optional[str] = None,
        recovery_focused: Optional[bool] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search knowledge articles from storage bucket using keyword matching.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching articles with rank scores
        """
        try:
            # Load articles from storage
            all_articles = await self._load_storage_articles()

            # Simple keyword matching on title
            query_words = set(query.lower().split())
            scored_articles = []

            for article in all_articles:
                title_lower = article["title"].lower()
                # Count matching words
                matches = sum(1 for word in query_words if word in title_lower)
                if matches > 0:
                    article_copy = article.copy()
                    article_copy["rank_score"] = matches / len(query_words)
                    article_copy["excerpt"] = f"Career guidance article: {article['title']}"
                    scored_articles.append(article_copy)

            # Sort by score and limit
            scored_articles.sort(key=lambda x: x["rank_score"], reverse=True)
            return scored_articles[:limit]

        except Exception as e:
            logger.error(f"Error in article search: {e}")
            return []

    async def search_faqs_fulltext(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search FAQs using simple keyword matching."""
        try:
            # Get all FAQs
            result = self.client.table("faqs").select(
                "id, question, answer"
            ).execute()

            if not result.data:
                return []

            # Simple keyword matching
            query_lower = query.lower()
            scored_faqs = []

            for faq in result.data:
                question_lower = faq["question"].lower()
                answer_lower = faq["answer"].lower()

                # Check if query words appear in question or answer
                score = 0
                for word in query_lower.split():
                    if word in question_lower:
                        score += 2  # Higher weight for question match
                    if word in answer_lower:
                        score += 1

                if score > 0:
                    faq["title"] = faq["question"]
                    faq["excerpt"] = faq["answer"][:200] + "..." if len(faq["answer"]) > 200 else faq["answer"]
                    faq["url"] = f"/knowledge-base/faq#{faq['id']}"
                    faq["rank_score"] = score / (len(query_lower.split()) * 3)  # Normalize
                    faq["type"] = "faq"
                    scored_faqs.append(faq)

            # Sort by score and limit
            scored_faqs.sort(key=lambda x: x["rank_score"], reverse=True)
            return scored_faqs[:limit]

        except Exception as e:
            logger.error(f"Error in FAQ search: {e}")
            return []

    async def get_all_faqs(self) -> list[dict]:
        """Get all FAQs."""
        try:
            result = self.client.table("faqs").select(
                "id, question, answer"
            ).execute()

            faqs = []
            for faq in result.data or []:
                faq["title"] = faq["question"]
                faq["excerpt"] = faq["answer"]
                faq["type"] = "faq"
                faqs.append(faq)

            return faqs

        except Exception as e:
            logger.error(f"Error fetching FAQs: {e}")
            return []

    async def get_all_storage_articles(self) -> list[dict]:
        """Get all articles from storage bucket."""
        return await self._load_storage_articles()

    async def get_article_by_filename(self, filename: str) -> Optional[dict]:
        """Get a storage article by filename."""
        try:
            articles = await self._load_storage_articles()
            for article in articles:
                if article["filename"] == filename:
                    # Optionally fetch content
                    content = await self._fetch_article_content(article["url"])
                    article["content"] = content
                    return article
            return None

        except Exception as e:
            logger.error(f"Error fetching article {filename}: {e}")
            return None

    async def get_recovery_focused_articles(self, limit: int = 10) -> list[dict]:
        """Get articles that might be recovery-focused based on title keywords."""
        try:
            articles = await self._load_storage_articles()

            # Keywords that indicate recovery-focused content
            recovery_keywords = ["recovery", "wellness", "workplace", "support", "journey"]

            recovery_articles = []
            for article in articles:
                title_lower = article["title"].lower()
                if any(kw in title_lower for kw in recovery_keywords):
                    recovery_articles.append(article)

            return recovery_articles[:limit]

        except Exception as e:
            logger.error(f"Error fetching recovery articles: {e}")
            return []

    async def search_semantic(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """Search knowledge documents using semantic embeddings."""
        try:
            documents = await self._load_semantic_documents()
            if not documents:
                return []

            await self._ensure_document_embeddings(documents)
            query_embedding = await self.gemini.generate_query_embedding(query)

            scored = []
            for doc in documents:
                embedding = _semantic_embeddings_cache.get(doc.get("cache_key"))
                if not embedding:
                    continue
                similarity = self._cosine_similarity(query_embedding, embedding)
                score = self._normalize_similarity(similarity)
                if score <= 0:
                    continue
                scored.append({
                    **doc,
                    "rank_score": score,
                    "source": "semantic",
                })

            scored.sort(key=lambda x: x["rank_score"], reverse=True)
            return scored[:limit]

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    async def search_hybrid(
        self,
        query: str,
        category: Optional[str] = None,
        recovery_focused: Optional[bool] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Hybrid search combining semantic and full-text scores."""
        semantic_results = await self.search_semantic(query=query, limit=max(limit * 2, 10))
        fulltext_articles = await self.search_articles_fulltext(
            query=query,
            category=category,
            recovery_focused=recovery_focused,
            limit=limit,
        )
        fulltext_faqs = await self.search_faqs_fulltext(
            query=query,
            limit=min(limit, 5),
        )

        combined: dict[str, dict] = {}

        def _key(item: dict) -> str:
            return f"{item.get('type')}:{item.get('id')}"

        for item in semantic_results:
            combined[_key(item)] = {
                **item,
                "score": item.get("rank_score", 0.0),
                "source": "semantic",
            }

        for article in fulltext_articles:
            article["type"] = "article"
            article["rank_score"] = article.get("rank_score", 0.0)
            key = _key(article)
            if key in combined:
                semantic_score = combined[key]["score"]
                fulltext_score = article["rank_score"]
                combined[key]["score"] = (SEMANTIC_WEIGHT * semantic_score) + (FULLTEXT_WEIGHT * fulltext_score)
                combined[key]["source"] = "both"
                combined[key]["excerpt"] = combined[key].get("excerpt") or article.get("excerpt")
                combined[key]["url"] = combined[key].get("url") or article.get("url")
            else:
                combined[key] = {
                    **article,
                    "score": article["rank_score"],
                    "source": "fulltext",
                }

        for faq in fulltext_faqs:
            faq["type"] = "faq"
            faq["rank_score"] = faq.get("rank_score", 0.0)
            key = _key(faq)
            if key in combined:
                semantic_score = combined[key]["score"]
                fulltext_score = faq["rank_score"]
                combined[key]["score"] = (SEMANTIC_WEIGHT * semantic_score) + (FULLTEXT_WEIGHT * fulltext_score)
                combined[key]["source"] = "both"
                combined[key]["excerpt"] = combined[key].get("excerpt") or faq.get("excerpt")
                combined[key]["url"] = combined[key].get("url") or faq.get("url")
            else:
                combined[key] = {
                    **faq,
                    "score": faq["rank_score"],
                    "source": "fulltext",
                }

        results = sorted(combined.values(), key=lambda x: x.get("score", 0.0), reverse=True)
        return results[:limit]

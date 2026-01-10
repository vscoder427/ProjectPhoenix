"""
Prompts Repository

Database operations for admin prompts with version control.
"""

import logging
from typing import Optional
from uuid import uuid4

from api.app.clients.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class PromptsRepository:
    """Repository for admin_prompts database operations."""

    def __init__(self):
        self.client = get_supabase_client()

    async def get_prompt_by_category_name(
        self, category: str, name: str
    ) -> Optional[dict]:
        """
        Get a prompt by category and name with current version.

        Args:
            category: Prompt category (e.g., 'dave_system')
            name: Prompt name (e.g., 'base_personality')

        Returns:
            Prompt dict with current_version joined, or None
        """
        try:
            result = self.client.table("admin_prompts").select(
                "*, admin_prompt_versions!current_version_id(*)"
            ).eq("category", category).eq("name", name).eq("is_archived", False).execute()

            if result.data and len(result.data) > 0:
                prompt = result.data[0]
                # Flatten the version data
                if prompt.get("admin_prompt_versions"):
                    prompt["current_version"] = prompt.pop("admin_prompt_versions")
                return prompt
            return None

        except Exception as e:
            logger.error(f"Error fetching prompt {category}/{name}: {e}")
            raise

    async def get_prompt_by_id(self, prompt_id: str) -> Optional[dict]:
        """Get a prompt by ID with current version."""
        try:
            result = self.client.table("admin_prompts").select(
                "*, admin_prompt_versions!current_version_id(*)"
            ).eq("id", prompt_id).execute()

            if result.data and len(result.data) > 0:
                prompt = result.data[0]
                if prompt.get("admin_prompt_versions"):
                    prompt["current_version"] = prompt.pop("admin_prompt_versions")
                return prompt
            return None

        except Exception as e:
            logger.error(f"Error fetching prompt {prompt_id}: {e}")
            raise

    async def list_prompts(
        self,
        category: Optional[str] = None,
        include_archived: bool = False,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """
        List prompts with pagination.

        Returns:
            Tuple of (prompts list, total count)
        """
        try:
            query = self.client.table("admin_prompts").select(
                "*, admin_prompt_versions!current_version_id(*)",
                count="exact"
            )

            if category:
                query = query.eq("category", category)

            if not include_archived:
                query = query.eq("is_archived", False)

            # Pagination
            offset = (page - 1) * limit
            query = query.order("category").order("name").range(offset, offset + limit - 1)

            result = query.execute()

            # Process results
            prompts = []
            for prompt in result.data or []:
                if prompt.get("admin_prompt_versions"):
                    prompt["current_version"] = prompt.pop("admin_prompt_versions")
                prompts.append(prompt)

            return prompts, result.count or 0

        except Exception as e:
            logger.error(f"Error listing prompts: {e}")
            raise

    async def get_prompt_versions(self, prompt_id: str) -> list[dict]:
        """Get all versions of a prompt, ordered by version number descending."""
        try:
            result = self.client.table("admin_prompt_versions").select("*").eq(
                "prompt_id", prompt_id
            ).order("version_number", desc=True).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching versions for {prompt_id}: {e}")
            raise

    async def create_version(
        self,
        prompt_id: str,
        content: str,
        commit_message: str,
        variables_schema: Optional[dict] = None,
        created_by: str = "admin",
    ) -> dict:
        """
        Create a new version for a prompt.

        Automatically increments version number and updates current_version_id.
        """
        try:
            # Get current max version number
            existing = await self.get_prompt_versions(prompt_id)
            next_version = 1
            if existing:
                next_version = existing[0]["version_number"] + 1

            # Create new version
            version_id = str(uuid4())
            version_data = {
                "id": version_id,
                "prompt_id": prompt_id,
                "version_number": next_version,
                "content": content,
                "variables_schema": variables_schema,
                "commit_message": commit_message,
                "created_by": created_by,
            }

            result = self.client.table("admin_prompt_versions").insert(version_data).execute()

            if result.data:
                # Update current_version_id on prompt
                self.client.table("admin_prompts").update({
                    "current_version_id": version_id,
                    "updated_at": "now()",
                }).eq("id", prompt_id).execute()

                return result.data[0]

            raise Exception("Failed to create version")

        except Exception as e:
            logger.error(f"Error creating version for {prompt_id}: {e}")
            raise

    async def rollback_to_version(self, prompt_id: str, version_id: str) -> bool:
        """
        Rollback a prompt to a specific version.

        Sets current_version_id to the specified version.
        """
        try:
            # Verify version exists and belongs to prompt
            version_check = self.client.table("admin_prompt_versions").select("id").eq(
                "id", version_id
            ).eq("prompt_id", prompt_id).execute()

            if not version_check.data:
                raise ValueError(f"Version {version_id} not found for prompt {prompt_id}")

            # Update current version
            self.client.table("admin_prompts").update({
                "current_version_id": version_id,
                "updated_at": "now()",
            }).eq("id", prompt_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error rolling back {prompt_id} to {version_id}: {e}")
            raise

    async def get_categories(self) -> list[dict]:
        """Get all prompt categories with counts."""
        try:
            # Get distinct categories with counts
            result = self.client.table("admin_prompts").select(
                "category"
            ).eq("is_archived", False).execute()

            # Count by category
            category_counts = {}
            for row in result.data or []:
                cat = row["category"]
                category_counts[cat] = category_counts.get(cat, 0) + 1

            return [
                {"category": cat, "prompt_count": count}
                for cat, count in sorted(category_counts.items())
            ]

        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise

    async def get_prompts_by_category(self, category: str) -> list[dict]:
        """Get all prompts in a category with current versions."""
        prompts, _ = await self.list_prompts(category=category, limit=1000)
        return prompts

"""
Admin Prompts Endpoints

API for managing Dave's prompts from the Warp admin dashboard.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.middleware.auth import AuthContext, verify_admin_key
from app.repositories.prompts import PromptsRepository
from app.services.prompt_manager import get_prompt_manager
from app.schemas.prompts import (
    Prompt,
    PromptList,
    PromptUpdate,
    PromptCreate,
    PromptRollback,
    PromptVersion,
    CategoryInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=PromptList)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    include_archived: bool = Query(False),
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    List all prompts with pagination.

    Admin access required.
    """
    try:
        repo = PromptsRepository()

        prompts, total = await repo.list_prompts(
            category=category,
            include_archived=include_archived,
            page=page,
            limit=limit,
        )

        return PromptList(
            items=[_format_prompt(p) for p in prompts],
            total=total,
            page=page,
            limit=limit,
            has_more=(page * limit) < total,
        )

    except Exception as e:
        logger.error(f"List prompts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list prompts")


@router.get("/categories")
async def list_categories(
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    List all prompt categories with counts.

    Admin access required.
    """
    try:
        repo = PromptsRepository()
        categories = await repo.get_categories()

        return {
            "categories": [
                CategoryInfo(
                    category=c["category"],
                    prompt_count=c["prompt_count"],
                )
                for c in categories
            ]
        }

    except Exception as e:
        logger.error(f"List categories error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list categories")


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    include_versions: bool = Query(False, description="Include version history"),
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    Get a prompt by ID with current version.

    Optionally include full version history.
    Admin access required.
    """
    try:
        repo = PromptsRepository()

        prompt = await repo.get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        result = _format_prompt(prompt)

        if include_versions:
            versions = await repo.get_prompt_versions(prompt_id)
            result["versions"] = [
                PromptVersion(
                    id=v["id"],
                    version_number=v["version_number"],
                    content=v["content"],
                    variables_schema=v.get("variables_schema"),
                    commit_message=v.get("commit_message"),
                    created_by=v.get("created_by", "admin"),
                    created_at=v["created_at"],
                )
                for v in versions
            ]

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get prompt error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prompt")


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    update: PromptUpdate,
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    Update a prompt by creating a new version.

    Admin access required.
    """
    try:
        repo = PromptsRepository()
        prompt_manager = get_prompt_manager()

        # Verify prompt exists
        prompt = await repo.get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Create new version
        version = await repo.create_version(
            prompt_id=prompt_id,
            content=update.content,
            commit_message=update.commit_message,
            variables_schema=update.variables_schema,
            created_by="admin",  # TODO: Get from auth
        )

        # Clear cache for this prompt
        await prompt_manager.clear_cache(prompt["category"], prompt["name"])

        return {
            "status": "updated",
            "prompt_id": prompt_id,
            "version": PromptVersion(
                id=version["id"],
                version_number=version["version_number"],
                content=version["content"],
                variables_schema=version.get("variables_schema"),
                commit_message=version.get("commit_message"),
                created_by=version.get("created_by", "admin"),
                created_at=version["created_at"],
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update prompt error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")


@router.post("/{prompt_id}/rollback")
async def rollback_prompt(
    prompt_id: str,
    rollback: PromptRollback,
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    Rollback a prompt to a previous version.

    Admin access required.
    """
    try:
        repo = PromptsRepository()
        prompt_manager = get_prompt_manager()

        # Verify prompt exists
        prompt = await repo.get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Rollback
        await repo.rollback_to_version(prompt_id, rollback.version_id)

        # Clear cache
        await prompt_manager.clear_cache(prompt["category"], prompt["name"])

        return {
            "status": "rolled_back",
            "prompt_id": prompt_id,
            "version_id": rollback.version_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback prompt error: {e}")
        raise HTTPException(status_code=500, detail="Failed to rollback prompt")


@router.get("/category/{category}")
async def get_prompts_by_category(
    category: str,
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    Get all prompts in a category.

    Admin access required.
    """
    try:
        repo = PromptsRepository()

        prompts = await repo.get_prompts_by_category(category)

        return {
            "category": category,
            "prompts": [_format_prompt(p) for p in prompts],
            "total": len(prompts),
        }

    except Exception as e:
        logger.error(f"Get prompts by category error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prompts")


@router.post("/cache/clear")
async def clear_prompt_cache(
    category: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    auth: AuthContext = Depends(verify_admin_key),
):
    """
    Clear the prompt cache.

    Admin access required.
    """
    try:
        prompt_manager = get_prompt_manager()
        await prompt_manager.clear_cache(category, name)

        return {
            "status": "cleared",
            "category": category,
            "name": name,
        }

    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


def _format_prompt(prompt: dict) -> Prompt:
    """Format a prompt dict to Prompt model."""
    current_version = None
    if prompt.get("current_version"):
        cv = prompt["current_version"]
        current_version = PromptVersion(
            id=cv["id"],
            version_number=cv["version_number"],
            content=cv["content"],
            variables_schema=cv.get("variables_schema"),
            commit_message=cv.get("commit_message"),
            created_by=cv.get("created_by", "admin"),
            created_at=cv["created_at"],
        )

    return Prompt(
        id=prompt["id"],
        category=prompt["category"],
        name=prompt["name"],
        description=prompt.get("description"),
        current_version_id=prompt.get("current_version_id"),
        current_version=current_version,
        is_archived=prompt.get("is_archived", False),
        created_at=prompt["created_at"],
        updated_at=prompt["updated_at"],
    )

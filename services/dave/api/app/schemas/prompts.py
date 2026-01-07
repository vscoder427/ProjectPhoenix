"""
Prompts Schemas

Pydantic models for admin prompts management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PromptVariable(BaseModel):
    """Variable definition for a prompt template."""

    name: str
    type: str  # string, number, boolean, array
    description: Optional[str] = None
    example_value: Optional[str] = None
    is_required: bool = True


class PromptVersion(BaseModel):
    """A version of a prompt."""

    id: str
    version_number: int
    content: str
    variables_schema: Optional[list[PromptVariable]] = None
    commit_message: Optional[str] = None
    created_by: str = "admin"
    created_at: datetime


class Prompt(BaseModel):
    """Admin prompt with current version."""

    id: str
    category: str
    name: str
    description: Optional[str] = None
    current_version_id: Optional[str] = None
    current_version: Optional[PromptVersion] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime


class PromptList(BaseModel):
    """Paginated list of prompts."""

    items: list[Prompt]
    total: int
    page: int
    limit: int
    has_more: bool


class PromptUpdate(BaseModel):
    """Request to update a prompt (creates new version)."""

    content: str = Field(..., min_length=1, description="New prompt content")
    commit_message: str = Field(..., min_length=1, max_length=500, description="Commit message describing changes")
    variables_schema: Optional[list[PromptVariable]] = None


class PromptCreate(BaseModel):
    """Request to create a new prompt."""

    category: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    variables_schema: Optional[list[PromptVariable]] = None


class PromptRollback(BaseModel):
    """Request to rollback to a previous version."""

    version_id: str = Field(..., description="Version ID to rollback to")


class CategoryInfo(BaseModel):
    """Category information."""

    category: str
    prompt_count: int
    description: Optional[str] = None

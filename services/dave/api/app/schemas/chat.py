"""
Chat Schemas

Pydantic models for chat request/response.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """User context for personalized responses."""

    user_id: Optional[str] = None
    user_type: Literal["job_seeker", "employer", "treatment_center", "anonymous"] = "anonymous"
    recovery_stage: Optional[str] = None  # early, intermediate, advanced, long-term
    preferred_tone: Optional[str] = "supportive"  # supportive, professional, casual
    session_metadata: Optional[dict] = None


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID, or None for new")
    # NOTE: user_id is now derived from authentication context only (X-API-Key header)
    # This prevents user impersonation attacks
    context: Optional[UserContext] = Field(default_factory=UserContext, description="User context")
    include_resources: bool = Field(True, description="Include knowledge base resources in response")


class Resource(BaseModel):
    """Knowledge base resource reference."""

    id: str
    type: Literal["article", "faq", "video", "download"]
    title: str
    url: Optional[str] = None
    excerpt: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatMessageResponse(BaseModel):
    """Response from chat endpoint."""

    conversation_id: str
    message_id: str
    response: str
    resources: list[Resource] = []
    follow_up_suggestions: list[str] = []
    metadata: Optional[dict] = None


class StreamEvent(BaseModel):
    """SSE stream event."""

    type: Literal["token", "resource", "suggestion", "done", "error"]
    data: dict | str
    id: Optional[str] = None


class ConversationSummary(BaseModel):
    """Summary of a conversation."""

    id: str
    title: Optional[str] = None
    message_count: int
    last_message_at: datetime
    created_at: datetime


class ConversationMessage(BaseModel):
    """A single message in a conversation."""

    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None


class ConversationDetail(BaseModel):
    """Full conversation with messages."""

    id: str
    title: Optional[str] = None
    status: str
    messages: list[ConversationMessage]
    created_at: datetime
    updated_at: datetime

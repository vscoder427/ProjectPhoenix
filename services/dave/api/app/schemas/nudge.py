"""
Nudge Generation Schemas

Pydantic models for nudge generation API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RecoveryStage(str, Enum):
    """User's recovery stage for tone adjustment."""
    EARLY = "early"  # 0-6 months
    INTERMEDIATE = "intermediate"  # 6-18 months
    ADVANCED = "advanced"  # 18+ months
    LONG_TERM = "long_term"  # 3+ years


class NudgeType(str, Enum):
    """Type of nudge to generate."""
    JOB_SEARCH_ENCOURAGEMENT = "job_search_encouragement"
    CHECKIN_REMINDER = "checkin_reminder"
    MILESTONE_CELEBRATION = "milestone_celebration"
    PROFILE_ALMOST_COMPLETE = "profile_almost_complete"
    SKILL_ENCOURAGEMENT = "skill_encouragement"
    MEETING_REMINDER = "meeting_reminder"


class NudgeContext(BaseModel):
    """Context data for nudge personalization."""

    # Time-based context
    days_since_event: Optional[int] = Field(
        None,
        description="Days since the triggering event occurred"
    )
    days_inactive: Optional[int] = Field(
        None,
        description="Days since user was last active"
    )

    # Job-related context
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None

    # Achievement context
    milestone: Optional[str] = Field(
        None,
        description="Achievement name (e.g., 'First Application', '7-Day Streak')"
    )
    streak: Optional[int] = Field(
        None,
        description="Current streak count"
    )

    # Profile context
    completion_percentage: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Profile completion percentage"
    )
    missing_fields: Optional[list[str]] = Field(
        None,
        description="Fields missing from profile"
    )

    # Skill context
    skill_id: Optional[str] = None
    skill_name: Optional[str] = None
    skill_score: Optional[int] = None


class NudgeGenerateRequest(BaseModel):
    """Request to generate a nudge message."""

    user_id: str = Field(..., description="User ID to generate nudge for")
    recovery_stage: RecoveryStage = Field(
        RecoveryStage.INTERMEDIATE,
        description="User's recovery stage for tone adjustment"
    )
    nudge_type: NudgeType = Field(..., description="Type of nudge to generate")
    context: Optional[NudgeContext] = Field(
        None,
        description="Context data for personalization"
    )
    user_name: Optional[str] = Field(
        None,
        description="User's first name for personalization"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "recovery_stage": "intermediate",
                "nudge_type": "job_search_encouragement",
                "context": {
                    "days_since_event": 7,
                    "job_title": "Warehouse Associate",
                    "company_name": "Amazon",
                },
                "user_name": "Marcus",
            }
        }


class NudgeGenerateResponse(BaseModel):
    """Response containing generated nudge."""

    nudge_id: str = Field(..., description="Unique ID for this nudge")
    message: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Generated nudge message (100-200 chars typically)"
    )
    cta_text: Optional[str] = Field(
        None,
        max_length=50,
        description="Optional call-to-action button text"
    )
    cta_link: Optional[str] = Field(
        None,
        description="Optional link for the CTA"
    )
    nudge_type: NudgeType
    recovery_stage: RecoveryStage
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata for tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nudge_id": "nudge_abc123",
                "message": "Hey Marcus! That Warehouse Associate role at Amazon is still waiting. You've got the experience - ready to apply?",
                "cta_text": "Apply Now",
                "cta_link": "/jobs/123",
                "nudge_type": "job_search_encouragement",
                "recovery_stage": "intermediate",
                "generated_at": "2025-01-02T10:30:00Z",
                "metadata": {
                    "model": "gemini-2.0-flash",
                    "tokens_used": 150,
                }
            }
        }


class NudgeBatchRequest(BaseModel):
    """Request to generate nudges for multiple users."""

    nudges: list[NudgeGenerateRequest] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of nudge requests (max 50)"
    )


class NudgeBatchResponse(BaseModel):
    """Response for batch nudge generation."""

    results: list[NudgeGenerateResponse]
    total_requested: int
    total_generated: int
    failed: int

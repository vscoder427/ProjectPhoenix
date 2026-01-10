"""
Nudge Generation API Endpoints

Endpoints for generating personalized nudge messages for the journey/notification system.
Called by n8n workflows to generate contextual nudges for users.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from api.app.middleware.auth import verify_api_key, AuthContext
from api.app.services.nudge_service import get_nudge_service
from api.app.guardrails.rate_limiter import RateLimiter
from api.app.schemas.nudge import (
    NudgeGenerateRequest,
    NudgeGenerateResponse,
    NudgeBatchRequest,
    NudgeBatchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiter instance for nudge endpoints
_rate_limiter = RateLimiter()


async def check_rate_limit(request: Request, auth: AuthContext):
    """Check rate limit before processing nudge request."""
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else None

    result = await _rate_limiter.check(
        user_id=auth.api_key,  # Use API key as identifier
        ip_address=client_ip,
        tier=auth.tier,
    )

    if result.blocked:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": result.message,
                "reason": result.reason,
            },
        )

    # Record the request
    await _rate_limiter.record_request(
        user_id=auth.api_key,
        ip_address=client_ip,
        tokens_used=150,  # Approximate tokens per nudge generation
    )


@router.post("/generate", response_model=NudgeGenerateResponse)
async def generate_nudge(
    request: NudgeGenerateRequest,
    http_request: Request,
    auth: AuthContext = Depends(verify_api_key),
):
    """
    Generate a personalized nudge message.

    This endpoint is called by n8n workflows when a user matches a nudge rule.
    It generates a short, contextual message based on:
    - User's recovery stage (for tone adjustment)
    - Nudge type (determines the prompt template)
    - Context data (for personalization)

    The message is generated using Gemini AI with prompts stored in the
    admin_prompts database (editable via /admin/ai-prompts in Warp).

    Returns a nudge with:
    - message: The generated text (100-200 chars)
    - cta_text: Optional call-to-action button text
    - cta_link: Link for the CTA
    - metadata: Generation info for tracking
    """
    # Check rate limit
    await check_rate_limit(http_request, auth)

    try:
        nudge_service = get_nudge_service()
        response = await nudge_service.generate_nudge(request)

        logger.info(
            f"Generated nudge for user {request.user_id}",
            extra={
                "nudge_id": response.nudge_id,
                "nudge_type": request.nudge_type.value,
                "recovery_stage": request.recovery_stage.value,
            },
        )

        return response

    except Exception as e:
        logger.error(f"Nudge generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate nudge: {str(e)}",
        )


@router.post("/generate/batch", response_model=NudgeBatchResponse)
async def generate_nudges_batch(
    request: NudgeBatchRequest,
    http_request: Request,
    auth: AuthContext = Depends(verify_api_key),
):
    """
    Generate nudges for multiple users in a batch.

    Useful for n8n workflows that need to generate multiple nudges
    in a single API call (more efficient than individual calls).

    Max 50 nudges per batch to prevent timeouts.
    """
    # Check rate limit (batch counts as multiple requests)
    await check_rate_limit(http_request, auth)

    nudge_service = get_nudge_service()
    results = []
    failed = 0

    for nudge_request in request.nudges:
        try:
            response = await nudge_service.generate_nudge(nudge_request)
            results.append(response)
        except Exception as e:
            logger.warning(
                f"Failed to generate nudge for user {nudge_request.user_id}: {e}"
            )
            failed += 1

    logger.info(
        f"Batch nudge generation completed: {len(results)} success, {failed} failed"
    )

    return NudgeBatchResponse(
        results=results,
        total_requested=len(request.nudges),
        total_generated=len(results),
        failed=failed,
    )


@router.get("/types")
async def get_nudge_types(_: bool = Depends(verify_api_key)):
    """
    Get available nudge types and their descriptions.

    Useful for building admin UIs or debugging.
    """
    from app.schemas.nudge import NudgeType

    return {
        "nudge_types": [
            {
                "type": NudgeType.JOB_SEARCH_ENCOURAGEMENT.value,
                "description": "Encourages user to apply for saved jobs",
                "trigger": "job_saved event 7+ days ago, no application",
            },
            {
                "type": NudgeType.CHECKIN_REMINDER.value,
                "description": "Gentle reminder to complete daily check-in",
                "trigger": "No checkin_completed event in 3+ days",
            },
            {
                "type": NudgeType.MILESTONE_CELEBRATION.value,
                "description": "Celebrates user achievements",
                "trigger": "Immediate on skill_completed or streak milestone",
            },
            {
                "type": NudgeType.PROFILE_ALMOST_COMPLETE.value,
                "description": "Encourages profile completion",
                "trigger": "Profile reaches 80% completion",
            },
            {
                "type": NudgeType.SKILL_ENCOURAGEMENT.value,
                "description": "Encourages skills assessment",
                "trigger": "User hasn't taken skills assessment",
            },
            {
                "type": NudgeType.MEETING_REMINDER.value,
                "description": "Supportive meeting reminder",
                "trigger": "No meeting_attended in 7+ days",
            },
        ]
    }

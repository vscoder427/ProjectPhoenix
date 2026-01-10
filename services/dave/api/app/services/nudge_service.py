"""
Nudge Generation Service

Generates short, contextual nudge messages using Gemini AI.
Fetches prompts from admin_prompts table for editability.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from api.app.clients.gemini import get_gemini_client
from api.app.services.prompt_manager import get_prompt_manager
from api.app.schemas.nudge import (
    NudgeGenerateRequest,
    NudgeGenerateResponse,
    NudgeType,
    RecoveryStage,
    NudgeContext,
)

logger = logging.getLogger(__name__)


# Mapping of nudge types to CTA configurations
NUDGE_CTA_CONFIG = {
    NudgeType.JOB_SEARCH_ENCOURAGEMENT: {
        "cta_text": "View Job",
        "cta_link_template": "/jobs/{job_id}",
    },
    NudgeType.CHECKIN_REMINDER: {
        "cta_text": "Check In Now",
        "cta_link_template": "/journey/check-in",
    },
    NudgeType.MILESTONE_CELEBRATION: {
        "cta_text": "View Progress",
        "cta_link_template": "/journey",
    },
    NudgeType.PROFILE_ALMOST_COMPLETE: {
        "cta_text": "Complete Profile",
        "cta_link_template": "/profile/edit",
    },
    NudgeType.SKILL_ENCOURAGEMENT: {
        "cta_text": "Take Assessment",
        "cta_link_template": "/skills",
    },
    NudgeType.MEETING_REMINDER: {
        "cta_text": "Find Meetings",
        "cta_link_template": "/recover/meetings",
    },
}

# Fallback prompts if database prompts are not available
FALLBACK_PROMPTS = {
    NudgeType.JOB_SEARCH_ENCOURAGEMENT: """Generate a short, encouraging nudge (100-150 chars) for a user in {recovery_stage} recovery who saved a job {days_ago} days ago but hasn't applied.
Be warm, not pushy. Recovery-sensitive language.
Job: {job_title} at {company_name}
User name: {user_name}

Only output the nudge message, nothing else.""",

    NudgeType.CHECKIN_REMINDER: """Generate a gentle, caring check-in reminder nudge (100-150 chars) for a user in {recovery_stage} recovery who hasn't checked in for {days_inactive} days.
Be supportive, not guilt-inducing. Recovery-sensitive language.
User name: {user_name}

Only output the nudge message, nothing else.""",

    NudgeType.MILESTONE_CELEBRATION: """Generate a celebratory nudge (100-150 chars) for a user in {recovery_stage} recovery who just achieved: {milestone}.
Be genuinely excited and affirming. Recovery-sensitive language.
User name: {user_name}

Only output the nudge message, nothing else.""",

    NudgeType.PROFILE_ALMOST_COMPLETE: """Generate an encouraging nudge (100-150 chars) for a user in {recovery_stage} recovery whose profile is {completion_percentage}% complete.
Highlight the benefit of completing it. Recovery-sensitive language.
User name: {user_name}

Only output the nudge message, nothing else.""",

    NudgeType.SKILL_ENCOURAGEMENT: """Generate an encouraging nudge (100-150 chars) for a user in {recovery_stage} recovery about taking a skills assessment.
Focus on self-discovery and confidence. Recovery-sensitive language.
User name: {user_name}
Skill: {skill_name}

Only output the nudge message, nothing else.""",

    NudgeType.MEETING_REMINDER: """Generate a supportive meeting reminder nudge (100-150 chars) for a user in {recovery_stage} recovery.
Be caring and non-judgmental. Recovery-sensitive language.
User name: {user_name}

Only output the nudge message, nothing else.""",
}


class NudgeService:
    """
    Service for generating personalized nudge messages.

    Uses Gemini AI with prompts from admin_prompts table.
    Falls back to hardcoded prompts if database prompts unavailable.
    """

    def __init__(self):
        self.gemini = get_gemini_client()
        self.prompt_manager = get_prompt_manager()

    async def generate_nudge(
        self,
        request: NudgeGenerateRequest,
    ) -> NudgeGenerateResponse:
        """
        Generate a personalized nudge message.

        Args:
            request: Nudge generation request with context

        Returns:
            NudgeGenerateResponse with message and metadata
        """
        nudge_id = f"nudge_{uuid.uuid4().hex[:12]}"

        try:
            # Get prompt template from database
            prompt = await self._get_nudge_prompt(request.nudge_type)

            # Build the prompt with context
            formatted_prompt = self._format_prompt(
                prompt,
                request.nudge_type,
                request.recovery_stage,
                request.context,
                request.user_name,
            )

            # Generate message using Gemini
            message = await self._generate_message(formatted_prompt)

            # Get CTA configuration
            cta_config = NUDGE_CTA_CONFIG.get(request.nudge_type, {})
            cta_text = cta_config.get("cta_text")
            cta_link = self._build_cta_link(
                cta_config.get("cta_link_template"),
                request.context,
            )

            return NudgeGenerateResponse(
                nudge_id=nudge_id,
                message=message,
                cta_text=cta_text,
                cta_link=cta_link,
                nudge_type=request.nudge_type,
                recovery_stage=request.recovery_stage,
                generated_at=datetime.utcnow(),
                metadata={
                    "model": "gemini-2.0-flash",
                    "prompt_source": "database" if prompt != FALLBACK_PROMPTS.get(request.nudge_type) else "fallback",
                    "user_id": request.user_id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to generate nudge: {e}", exc_info=True)
            # Return a safe fallback message
            return self._get_fallback_response(
                nudge_id,
                request.nudge_type,
                request.recovery_stage,
                request.user_name,
            )

    async def _get_nudge_prompt(self, nudge_type: NudgeType) -> str:
        """
        Get the nudge prompt template from database.

        Falls back to hardcoded prompts if not found.
        """
        # Map nudge type to prompt name in database
        prompt_name_map = {
            NudgeType.JOB_SEARCH_ENCOURAGEMENT: "nudge_job_search_stuck",
            NudgeType.CHECKIN_REMINDER: "nudge_checkin_reminder",
            NudgeType.MILESTONE_CELEBRATION: "nudge_milestone_celebration",
            NudgeType.PROFILE_ALMOST_COMPLETE: "nudge_profile_incomplete",
            NudgeType.SKILL_ENCOURAGEMENT: "nudge_skill_encouragement",
            NudgeType.MEETING_REMINDER: "nudge_meeting_reminder",
        }

        prompt_name = prompt_name_map.get(nudge_type)
        if prompt_name:
            # Try to fetch from database (dave_nudges category)
            db_prompt = await self.prompt_manager.get_prompt(
                category="dave_nudges",
                name=prompt_name,
            )
            if db_prompt:
                return db_prompt

        # Fall back to hardcoded prompt
        return FALLBACK_PROMPTS.get(nudge_type, FALLBACK_PROMPTS[NudgeType.JOB_SEARCH_ENCOURAGEMENT])

    def _format_prompt(
        self,
        prompt_template: str,
        nudge_type: NudgeType,
        recovery_stage: RecoveryStage,
        context: Optional[NudgeContext],
        user_name: Optional[str],
    ) -> str:
        """Format the prompt template with context variables."""
        # Build variables dict
        variables = {
            "recovery_stage": self._format_recovery_stage(recovery_stage),
            "user_name": user_name or "there",
            "nudge_type": nudge_type.value,
        }

        if context:
            variables.update({
                "days_ago": str(context.days_since_event or "a few"),
                "days_inactive": str(context.days_inactive or "a few"),
                "job_title": context.job_title or "the saved job",
                "company_name": context.company_name or "the company",
                "milestone": context.milestone or "your achievement",
                "streak": str(context.streak or 0),
                "completion_percentage": str(context.completion_percentage or 0),
                "skill_name": context.skill_name or "this skill",
            })

        # Replace variables in template
        formatted = prompt_template
        for key, value in variables.items():
            # Support both {{var}} and {var} formats
            formatted = formatted.replace(f"{{{{{key}}}}}", value)
            formatted = formatted.replace(f"{{{key}}}", value)

        return formatted

    def _format_recovery_stage(self, stage: RecoveryStage) -> str:
        """Format recovery stage for display in prompts."""
        stage_descriptions = {
            RecoveryStage.EARLY: "early (0-6 months)",
            RecoveryStage.INTERMEDIATE: "intermediate (6-18 months)",
            RecoveryStage.ADVANCED: "advanced (18+ months)",
            RecoveryStage.LONG_TERM: "long-term (3+ years)",
        }
        return stage_descriptions.get(stage, "intermediate")

    async def _generate_message(self, prompt: str) -> str:
        """Generate the nudge message using Gemini."""
        # Build a focused system instruction for nudge generation
        system_instruction = """You are Dave, Employa's AI career coach, writing short nudge messages.
Your nudges should be:
- Warm and encouraging, never pushy or guilt-inducing
- Recovery-sensitive (no stigmatizing language)
- Personal and conversational
- Between 100-200 characters
- Action-oriented but supportive

Never include quotes around the message. Just output the message directly."""

        message = await self.gemini.generate(
            prompt=prompt,
            system_instruction=system_instruction,
        )

        # Clean up the message
        message = message.strip().strip('"').strip("'")

        # Ensure it's not too long
        if len(message) > 300:
            # Truncate at last complete sentence
            sentences = message.split(". ")
            truncated = ""
            for sentence in sentences:
                if len(truncated) + len(sentence) + 2 <= 280:
                    truncated = truncated + sentence + ". " if truncated else sentence + ". "
                else:
                    break
            message = truncated.strip() if truncated else message[:280] + "..."

        return message

    def _build_cta_link(
        self,
        template: Optional[str],
        context: Optional[NudgeContext],
    ) -> Optional[str]:
        """Build the CTA link from template and context."""
        if not template:
            return None

        if not context:
            return template

        # Replace placeholders
        link = template
        if context.job_id:
            link = link.replace("{job_id}", context.job_id)
        if context.skill_id:
            link = link.replace("{skill_id}", context.skill_id)

        return link

    def _get_fallback_response(
        self,
        nudge_id: str,
        nudge_type: NudgeType,
        recovery_stage: RecoveryStage,
        user_name: Optional[str],
    ) -> NudgeGenerateResponse:
        """Get a safe fallback response when generation fails."""
        name = user_name or "there"

        fallback_messages = {
            NudgeType.JOB_SEARCH_ENCOURAGEMENT: f"Hey {name}! Ready to take the next step on that saved job? We're cheering you on!",
            NudgeType.CHECKIN_REMINDER: f"Hey {name}, we miss you! Take a moment to check in - your progress matters.",
            NudgeType.MILESTONE_CELEBRATION: f"Amazing work, {name}! You're making real progress. Keep going!",
            NudgeType.PROFILE_ALMOST_COMPLETE: f"Almost there, {name}! Complete your profile to unlock more opportunities.",
            NudgeType.SKILL_ENCOURAGEMENT: f"Curious about your strengths, {name}? Try a quick skills assessment!",
            NudgeType.MEETING_REMINDER: f"Hey {name}, staying connected matters. Find a meeting near you today.",
        }

        cta_config = NUDGE_CTA_CONFIG.get(nudge_type, {})

        return NudgeGenerateResponse(
            nudge_id=nudge_id,
            message=fallback_messages.get(nudge_type, f"Hey {name}! We're here to support your journey."),
            cta_text=cta_config.get("cta_text"),
            cta_link=cta_config.get("cta_link_template", "").replace("{job_id}", ""),
            nudge_type=nudge_type,
            recovery_stage=recovery_stage,
            generated_at=datetime.utcnow(),
            metadata={
                "prompt_source": "fallback_error",
            },
        )


# Singleton instance
_nudge_service: Optional[NudgeService] = None


def get_nudge_service() -> NudgeService:
    """Get cached nudge service instance."""
    global _nudge_service
    if _nudge_service is None:
        _nudge_service = NudgeService()
    return _nudge_service

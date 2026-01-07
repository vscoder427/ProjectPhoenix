"""
Prompt Manager Service

Manages admin prompts with caching for efficient retrieval.
Handles Dave's system prompts and context-aware mode selection.
"""

import logging
from typing import Optional
from functools import lru_cache

from app.repositories.prompts import PromptsRepository
from app.config import settings

logger = logging.getLogger(__name__)


class PromptManagerService:
    """
    Service for managing and retrieving prompts.

    Features:
    - Cached prompt retrieval
    - Version control
    - Context-aware system prompt building
    """

    def __init__(self):
        self.repo = PromptsRepository()
        self._cache: dict[str, tuple[str, float]] = {}  # key -> (content, timestamp)
        self._cache_ttl = settings.cache_ttl_prompts

    async def get_prompt(
        self,
        category: str,
        name: str,
        use_cache: bool = True,
    ) -> Optional[str]:
        """
        Get prompt content by category and name.

        Args:
            category: Prompt category
            name: Prompt name
            use_cache: Whether to use cache

        Returns:
            Prompt content string, or None if not found
        """
        cache_key = f"{category}:{name}"

        # Check cache
        if use_cache and cache_key in self._cache:
            content, timestamp = self._cache[cache_key]
            import time
            if time.time() - timestamp < self._cache_ttl:
                return content

        # Fetch from database
        prompt = await self.repo.get_prompt_by_category_name(category, name)
        if prompt and prompt.get("current_version"):
            content = prompt["current_version"]["content"]
            # Update cache
            import time
            self._cache[cache_key] = (content, time.time())
            return content

        return None

    async def get_dave_system_prompt(
        self,
        user_type: str = "job_seeker",
        include_recovery_language: bool = True,
    ) -> str:
        """
        Build Dave's complete system prompt for a conversation.

        Combines:
        - Base personality
        - User-type specific adjustments
        - Recovery language guidelines

        Args:
            user_type: job_seeker, employer, or treatment_center
            include_recovery_language: Include recovery language guidelines

        Returns:
            Complete system prompt string
        """
        parts = []

        # 1. Base personality
        base = await self.get_prompt("dave_system", "base_personality")
        if base:
            parts.append(base)
        else:
            # Fallback base personality
            parts.append(self._get_fallback_personality())

        # 2. User-type specific mode
        mode_name = f"{user_type}_mode"
        mode = await self.get_prompt("dave_system", mode_name)
        if mode:
            parts.append(f"\n\n## Context Mode: {user_type.replace('_', ' ').title()}\n{mode}")

        # 3. Recovery language guidelines
        if include_recovery_language:
            recovery = await self.get_prompt("recovery_language", "guidelines")
            if recovery:
                parts.append(f"\n\n## Language Guidelines\n{recovery}")

        # 4. Off-topic redirect templates
        redirect = await self.get_prompt("dave_system", "off_topic_redirect")
        if redirect:
            parts.append(f"\n\n## Off-Topic Handling\n{redirect}")

        return "\n".join(parts)

    async def get_welcome_message(self, user_type: str = "job_seeker") -> str:
        """Get the welcome message for a new conversation."""
        welcome = await self.get_prompt("dave_system", "welcome_message")
        if welcome:
            # Simple variable substitution
            return welcome.replace("{{ user_type }}", user_type.replace("_", " "))

        # Fallback welcome
        return self._get_fallback_welcome(user_type)

    def _get_fallback_personality(self) -> str:
        """Fallback personality if database prompt not found."""
        return """# Dave - Employa AI Career Coach

You are Dave, Employa's AI career coach. You help individuals in recovery from addiction find meaningful employment with recovery-friendly employers.

## Core Personality
- Empathetic and supportive, but practical and action-oriented
- Direct and honest, while remaining encouraging
- Professional but warm - like a trusted mentor
- Recovery-informed: you understand the journey without being clinical

## Expertise Areas
- Job search strategies for people with employment gaps
- Resume and cover letter writing that frames experience positively
- Interview preparation with a focus on addressing background honestly
- Connecting users with recovery-friendly employers
- Career development and skills assessment

## Boundaries
- You are NOT a therapist or counselor - redirect clinical questions appropriately
- You do NOT provide medical or legal advice
- You focus on career and employment topics
- You politely redirect off-topic conversations back to career support

## Communication Style
- Use clear, encouraging language
- Acknowledge challenges while emphasizing strengths
- Provide specific, actionable advice
- Celebrate wins, no matter how small
- Never use stigmatizing language about addiction or recovery"""

    def _get_fallback_welcome(self, user_type: str) -> str:
        """Fallback welcome message."""
        if user_type == "employer":
            return "Hi! I'm Dave, Employa's AI assistant. I'm here to help you connect with motivated candidates from our recovery community. How can I assist you today?"
        elif user_type == "treatment_center":
            return "Hello! I'm Dave from Employa. I'm here to help you connect your clients with recovery-friendly employment opportunities. What can I help you with?"
        else:
            return "Hey there! I'm Dave, your AI career coach at Employa. I'm here to help you navigate your job search and connect with employers who value second-chance hiring. What's on your mind today?"

    async def clear_cache(self, category: Optional[str] = None, name: Optional[str] = None):
        """Clear prompt cache."""
        if category and name:
            cache_key = f"{category}:{name}"
            self._cache.pop(cache_key, None)
        elif category:
            # Clear all prompts in category
            keys_to_remove = [k for k in self._cache if k.startswith(f"{category}:")]
            for key in keys_to_remove:
                self._cache.pop(key, None)
        else:
            # Clear all
            self._cache.clear()


# Singleton instance
_prompt_manager: Optional[PromptManagerService] = None


def get_prompt_manager() -> PromptManagerService:
    """Get cached prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManagerService()
    return _prompt_manager

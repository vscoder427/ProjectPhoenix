"""
Dave Chat Service

Core conversational AI service for Dave - Employa's career coach.
"""

import logging
import time
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

from api.app.clients.gemini import GeminiClient, get_gemini_client
from api.app.services.prompt_manager import PromptManagerService, get_prompt_manager
from api.app.repositories.conversation import ConversationRepository
from api.app.repositories.knowledge import KnowledgeRepository
from api.app.guardrails import GuardrailsOrchestrator, get_guardrails
from api.app.schemas.chat import UserContext, Resource

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Event for SSE streaming."""

    type: str  # token, resource, suggestion, done, error
    data: dict | str
    id: Optional[str] = None


class DaveChatService:
    """
    Core Dave chatbot service.

    Features:
    - Context-aware conversations
    - Streaming responses
    - Knowledge base integration
    - Guardrails protection
    - Conversation persistence
    """

    def __init__(self):
        self.gemini = get_gemini_client()
        self.prompts = get_prompt_manager()
        self.guardrails = get_guardrails()
        self.conversation_repo = ConversationRepository()
        self.knowledge_repo = KnowledgeRepository()

    async def generate_response(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[UserContext] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_tier: str = "free",
        include_resources: bool = True,
    ) -> dict:
        """
        Generate a non-streaming response.

        Args:
            message: User message
            conversation_id: Existing conversation ID or None for new
            context: User context for personalization
            user_id: User ID for rate limiting
            ip_address: IP for rate limiting
            user_tier: Tier for rate limiting
            include_resources: Whether to include knowledge base resources

        Returns:
            Dict with response, resources, suggestions, etc.
        """
        start_time = time.time()
        context = context or UserContext()

        # 1. Run guardrails
        guardrail_result = await self.guardrails.check(
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            user_tier=user_tier,
        )

        if guardrail_result.blocked:
            return {
                "response": guardrail_result.message,
                "blocked": True,
                "block_reason": guardrail_result.reason,
            }

        # 2. Get or create conversation
        if conversation_id:
            conversation = await self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                conversation = await self.conversation_repo.create_conversation(
                    user_id=user_id,
                    context=context.model_dump() if context else None,
                )
                conversation_id = conversation["id"]
        else:
            conversation = await self.conversation_repo.create_conversation(
                user_id=user_id,
                context=context.model_dump() if context else None,
            )
            conversation_id = conversation["id"]

        # 3. Save user message
        await self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
        )

        # 4. Get conversation history for context
        history = await self.conversation_repo.get_recent_messages(
            conversation_id=conversation_id,
            limit=10,
        )

        # 5. Get relevant knowledge base content
        resources = []
        knowledge_context = ""
        if include_resources:
            resources, knowledge_context = await self._get_knowledge_context(message)

        # 6. Build system prompt
        system_prompt = await self.prompts.get_dave_system_prompt(
            user_type=context.user_type if context else "job_seeker",
        )

        # Add knowledge context to prompt
        if knowledge_context:
            system_prompt += f"\n\n## Relevant Resources\n{knowledge_context}"

        # 7. Format history for Gemini
        gemini_history = self._format_history_for_gemini(history[:-1])  # Exclude current message

        # 8. Generate response
        response_text = await self.gemini.generate(
            prompt=message,
            system_instruction=system_prompt,
            history=gemini_history,
        )

        # 9. Generate follow-up suggestions
        suggestions = await self._generate_suggestions(message, response_text, context)

        # 10. Save assistant response
        response_time = time.time() - start_time
        await self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            metadata={
                "response_time_ms": int(response_time * 1000),
                "user_type": context.user_type if context else "anonymous",
            },
            resources=[r.model_dump() for r in resources] if resources else None,
            follow_up_suggestions=suggestions,
        )

        # 11. Record for rate limiting
        await self.guardrails.record_request(
            user_id=user_id,
            ip_address=ip_address,
            tokens_used=len(response_text.split()) * 2,  # Rough token estimate
        )

        return {
            "conversation_id": conversation_id,
            "message_id": str(time.time()),  # Will be replaced with actual ID
            "response": response_text,
            "resources": [r.model_dump() for r in resources],
            "follow_up_suggestions": suggestions,
            "metadata": {
                "response_time_ms": int(response_time * 1000),
            },
        }

    async def stream_response(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[UserContext] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_tier: str = "free",
        include_resources: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Generate a streaming response.

        Yields StreamEvent objects for SSE.
        """
        context = context or UserContext()

        # 1. Run guardrails
        guardrail_result = await self.guardrails.check(
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            user_tier=user_tier,
        )

        if guardrail_result.blocked:
            yield StreamEvent(
                type="error",
                data={
                    "message": guardrail_result.message,
                    "reason": guardrail_result.reason,
                },
            )
            return

        # 2. Get or create conversation
        if conversation_id:
            conversation = await self.conversation_repo.get_conversation(conversation_id)
        else:
            conversation = None

        if not conversation:
            conversation = await self.conversation_repo.create_conversation(
                user_id=user_id,
                context=context.model_dump() if context else None,
            )
        conversation_id = conversation["id"]

        # 3. Save user message
        await self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
        )

        # 4. Get conversation history
        history = await self.conversation_repo.get_recent_messages(
            conversation_id=conversation_id,
            limit=10,
        )

        # 5. Get knowledge context and yield resources
        resources = []
        knowledge_context = ""
        if include_resources:
            resources, knowledge_context = await self._get_knowledge_context(message)
            if resources:
                yield StreamEvent(
                    type="resource",
                    data={"resources": [r.model_dump() for r in resources]},
                )

        # 6. Build system prompt
        system_prompt = await self.prompts.get_dave_system_prompt(
            user_type=context.user_type if context else "job_seeker",
        )

        if knowledge_context:
            system_prompt += f"\n\n## Relevant Resources\n{knowledge_context}"

        # 7. Format history
        gemini_history = self._format_history_for_gemini(history[:-1])

        # 8. Stream response
        full_response = ""
        try:
            async for chunk in self.gemini.generate_stream(
                prompt=message,
                system_instruction=system_prompt,
                history=gemini_history,
            ):
                full_response += chunk
                yield StreamEvent(type="token", data={"content": chunk})

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield StreamEvent(
                type="error",
                data={"message": "I encountered an issue. Please try again."},
            )
            return

        # 9. Generate and yield suggestions
        suggestions = await self._generate_suggestions(message, full_response, context)
        if suggestions:
            yield StreamEvent(
                type="suggestion",
                data={"suggestions": suggestions},
            )

        # 10. Save assistant response
        await self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
            resources=[r.model_dump() for r in resources] if resources else None,
            follow_up_suggestions=suggestions,
        )

        # 11. Yield done event
        yield StreamEvent(
            type="done",
            data={
                "conversation_id": conversation_id,
                "full_response": full_response,
            },
        )

    async def _get_knowledge_context(
        self,
        query: str,
        limit: int = 3,
    ) -> tuple[list[Resource], str]:
        """
        Get relevant knowledge base content for the query.

        Returns:
            Tuple of (Resource list, context string for prompt)
        """
        try:
            # Search articles
            articles = await self.knowledge_repo.search_articles_fulltext(
                query=query,
                limit=limit,
            )

            # Search FAQs
            faqs = await self.knowledge_repo.search_faqs_fulltext(
                query=query,
                limit=2,
            )

            # Combine and convert to Resources
            resources = []
            context_parts = []

            for article in articles:
                resource = Resource(
                    id=article["id"],
                    type="article",
                    title=article["title"],
                    url=article.get("url"),
                    excerpt=article.get("excerpt"),
                    relevance_score=article.get("rank_score", 0.5),
                )
                resources.append(resource)
                context_parts.append(f"- {article['title']}: {article.get('excerpt', '')[:200]}")

            for faq in faqs:
                resource = Resource(
                    id=faq["id"],
                    type="faq",
                    title=faq["question"],
                    excerpt=faq.get("excerpt"),
                    relevance_score=faq.get("rank_score", 0.5),
                )
                resources.append(resource)
                context_parts.append(f"- FAQ: {faq['question']}")

            context_string = "\n".join(context_parts) if context_parts else ""

            return resources, context_string

        except Exception as e:
            logger.error(f"Error getting knowledge context: {e}")
            return [], ""

    async def _generate_suggestions(
        self,
        user_message: str,
        response: str,
        context: Optional[UserContext] = None,
    ) -> list[str]:
        """Generate follow-up suggestions based on conversation."""
        # Simple rule-based suggestions for now
        # TODO: Use AI to generate contextual suggestions

        suggestions = []

        user_lower = user_message.lower()
        response_lower = response.lower()

        # Job search related
        if any(word in user_lower for word in ["job", "work", "hire", "employ"]):
            suggestions.append("What types of jobs match my skills?")
            suggestions.append("How do I explain gaps in my resume?")

        # Resume related
        elif any(word in user_lower for word in ["resume", "cv"]):
            suggestions.append("Can you help me write a cover letter?")
            suggestions.append("How should I format my resume?")

        # Interview related
        elif any(word in user_lower for word in ["interview"]):
            suggestions.append("What questions should I prepare for?")
            suggestions.append("How do I handle background check questions?")

        # Recovery specific
        elif any(word in user_lower for word in ["recovery", "background", "record"]):
            suggestions.append("Which employers are recovery-friendly?")
            suggestions.append("How do I frame my journey positively?")

        # Default suggestions
        else:
            suggestions.append("Tell me more about job opportunities")
            suggestions.append("How can Employa help me?")

        return suggestions[:3]  # Limit to 3

    def _format_history_for_gemini(self, messages: list[dict]) -> list[dict]:
        """Format message history for Gemini's expected format."""
        history = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append({
                "role": role,
                "parts": [msg["content"]],
            })
        return history

    async def start_conversation(
        self,
        user_id: Optional[str] = None,
        context: Optional[UserContext] = None,
    ) -> dict:
        """Start a new conversation with a welcome message."""
        context = context or UserContext()

        # Create conversation
        conversation = await self.conversation_repo.create_conversation(
            user_id=user_id,
            context=context.model_dump(),
        )

        # Get welcome message
        welcome = await self.prompts.get_welcome_message(
            user_type=context.user_type if context else "job_seeker",
        )

        # Save welcome message
        await self.conversation_repo.add_message(
            conversation_id=conversation["id"],
            role="assistant",
            content=welcome,
        )

        return {
            "conversation_id": conversation["id"],
            "message": welcome,
            "suggestions": [
                "Help me find a job",
                "I need resume help",
                "What employers work with Employa?",
            ],
        }


# Singleton instance
_dave_service: Optional[DaveChatService] = None


def get_dave_service() -> DaveChatService:
    """Get cached Dave service instance."""
    global _dave_service
    if _dave_service is None:
        _dave_service = DaveChatService()
    return _dave_service

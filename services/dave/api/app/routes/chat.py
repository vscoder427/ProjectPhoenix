"""
Chat Endpoints

REST and SSE streaming endpoints for Dave conversations.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.middleware.auth import AuthContext, verify_api_key, optional_auth, verify_user_or_admin
from app.services.dave_chat import DaveChatService, get_dave_service
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    UserContext,
    ConversationSummary,
    ConversationDetail,
)
from app.repositories.conversation import ConversationRepository

logger = logging.getLogger(__name__)

router = APIRouter()


async def _enforce_conversation_access(
    conversation_id: str,
    auth: AuthContext,
) -> Optional[dict]:
    """Verify caller can access a conversation, returning it if found."""
    repo = ConversationRepository()
    conversation = await repo.get_conversation(conversation_id)
    if not conversation:
        return None

    conversation_owner = conversation.get("user_id")
    if conversation_owner:
        if auth.is_admin:
            return conversation
        if not auth.user_id or conversation_owner != auth.user_id:
            logger.warning(
                "Unauthorized conversation access attempt: user=%s tried to access conversation owned by %s",
                auth.user_id,
                conversation_owner,
            )
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    elif auth.user_id and not auth.is_admin:
        # Anonymous conversation should not be accessible to authenticated users
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    return conversation


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    req: Request,
    auth: AuthContext = Depends(optional_auth),
    dave: DaveChatService = Depends(get_dave_service),
):
    """
    Send a message to Dave and get a response.

    This is the non-streaming endpoint. Use /stream for real-time responses.
    """
    try:
        # Get IP for rate limiting
        ip_address = req.client.host if req.client else None

        # SECURITY: Only use user_id from authenticated context, not from request body
        # This prevents user impersonation attacks
        user_id = auth.user_id

        # Enforce conversation ownership if a conversation_id is provided
        if request.conversation_id:
            await _enforce_conversation_access(request.conversation_id, auth)

        # Override any caller-supplied context user_id
        context = request.context or UserContext()
        context.user_id = user_id

        result = await dave.generate_response(
            message=request.message,
            conversation_id=request.conversation_id,
            context=context,
            user_id=user_id,
            ip_address=ip_address,
            user_tier=auth.tier,
            include_resources=request.include_resources,
        )

        if result.get("blocked"):
            # Return the redirect message as a normal response
            return ChatMessageResponse(
                conversation_id=request.conversation_id or "blocked",
                message_id="blocked",
                response=result["response"],
                resources=[],
                follow_up_suggestions=[],
            )

        return ChatMessageResponse(
            conversation_id=result["conversation_id"],
            message_id=result.get("message_id", ""),
            response=result["response"],
            resources=result.get("resources", []),
            follow_up_suggestions=result.get("follow_up_suggestions", []),
            metadata=result.get("metadata"),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/stream")
async def stream_message(
    message: str = Query(..., min_length=1, max_length=10000),
    conversation_id: Optional[str] = Query(None),
    user_type: str = Query("job_seeker"),
    req: Request = None,
    auth: AuthContext = Depends(optional_auth),
    dave: DaveChatService = Depends(get_dave_service),
):
    """
    Stream a response from Dave using Server-Sent Events (SSE).

    Events:
    - token: Partial response text
    - resource: Knowledge base resources
    - suggestion: Follow-up suggestions
    - done: Final response with conversation_id
    - error: Error message
    """

    async def event_generator():
        try:
            context = UserContext(user_type=user_type, user_id=auth.user_id)
            ip_address = req.client.host if req.client else None
            # SECURITY: Only use user_id from authenticated context
            effective_user_id = auth.user_id

            # Enforce conversation ownership before streaming tokens
            if conversation_id:
                await _enforce_conversation_access(conversation_id, auth)

            async for event in dave.stream_response(
                message=message,
                conversation_id=conversation_id,
                context=context,
                user_id=effective_user_id,
                ip_address=ip_address,
                user_tier=auth.tier,
            ):
                yield {
                    "event": event.type,
                    "data": json.dumps(event.data) if isinstance(event.data, dict) else event.data,
                }

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": "Stream error occurred"}),
            }

    return EventSourceResponse(event_generator())


@router.post("/start")
async def start_conversation(
    user_type: str = Query("job_seeker"),
    auth: AuthContext = Depends(optional_auth),
    dave: DaveChatService = Depends(get_dave_service),
):
    """
    Start a new conversation with a welcome message.

    Returns the conversation ID and initial greeting.
    """
    try:
        context = UserContext(user_type=user_type, user_id=auth.user_id)

        result = await dave.start_conversation(
            user_id=auth.user_id,
            context=context,
        )

        return result

    except Exception as e:
        logger.error(f"Start conversation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")


@router.get("/conversations")
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    auth: AuthContext = Depends(verify_user_or_admin),
):
    """
    List conversations for the authenticated user.

    Requires authentication.
    """
    if not auth.user_id:
        raise HTTPException(status_code=400, detail="User ID required")

    try:
        repo = ConversationRepository()
        conversations = await repo.get_user_conversations(
            user_id=auth.user_id,
            limit=limit,
        )

        return {
            "conversations": [
                ConversationSummary(
                    id=c["id"],
                    title=c.get("title"),
                    message_count=0,  # TODO: Add message count
                    last_message_at=c["updated_at"],
                    created_at=c["created_at"],
                )
                for c in conversations
            ],
            "total": len(conversations),
        }

    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    auth: AuthContext = Depends(verify_user_or_admin),
):
    """
    Get a conversation with all messages.

    Note: Ownership is verified - users can only access their own conversations.
    """
    try:
        repo = ConversationRepository()

        conversation = await _enforce_conversation_access(conversation_id, auth)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = await repo.get_messages(conversation_id)

        return ConversationDetail(
            id=conversation["id"],
            title=conversation.get("title"),
            status=conversation.get("status", "active"),
            messages=[
                {
                    "id": m["id"],
                    "role": m["role"],
                    "content": m["content"],
                    "timestamp": m["timestamp"],
                    "metadata": m.get("metadata"),
                }
                for m in messages
            ],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.delete("/conversations/{conversation_id}")
async def archive_conversation(
    conversation_id: str,
    auth: AuthContext = Depends(verify_user_or_admin),
):
    """
    Archive a conversation (soft delete).

    Requires authentication.
    """
    try:
        repo = ConversationRepository()

        conversation = await _enforce_conversation_access(conversation_id, auth)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if not auth.is_admin and conversation.get("user_id") != auth.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        await repo.archive_conversation(conversation_id)

        return {"status": "archived", "conversation_id": conversation_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive conversation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive conversation")

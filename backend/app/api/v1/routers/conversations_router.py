from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_conversation_service, get_current_user, get_message_service
from app.models.user import User
from app.schemas.conversation.conversation_create import ConversationCreate
from app.schemas.conversation.conversation_preview import ConversationPreview
from app.schemas.conversation.conversation_read import ConversationRead
from app.schemas.conversation.conversation_summary import (
    ConversationSummaryRequest,
    ConversationSummaryResponse,
)
from app.schemas.message.message_page import MessagePage
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get("/", response_model=List[ConversationPreview])
async def list_my_conversations(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    List all conversations of the *current* user.

    TEMP behavior:
    - 'current_user' is resolved from ?user_id=... query param.
    FUTURE:
    - 'current_user' will come from auth (JWT / session / provider).
    """
    return await conversation_service.get_user_conversation_previews(current_user.id)


@router.post("/group", response_model=ConversationRead)
async def create_group_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    conversation = await conversation_service.create_group(
        creator_id=current_user.id,
        name=body.group_name,
        participant_ids=body.participant_ids,
    )
    return await conversation_service.get_conversation_info(conversation.id, current_user.id)


@router.get("/{conversation_id}/messages", response_model=MessagePage)
async def list_conversation_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[UUID] = Query(None, alias="beforeId"),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
    ):
    """
    Fetch paginated messages for a conversation (oldest -> newest).
    """
    return await message_service.get_message_page(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        before_id=before_id,
    )


@router.post("/{conversation_id}/summary", response_model=ConversationSummaryResponse)
async def summarize_conversation(
    conversation_id: UUID,
    body: ConversationSummaryRequest,
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Generate an AI summary of recent messages for a conversation.
    """
    summary = await message_service.summarize_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        hours=body.hours,
    )
    return ConversationSummaryResponse(summary=summary)

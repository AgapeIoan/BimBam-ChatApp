from typing import List
from uuid import UUID

from app.api.v1.deps import get_current_user, get_message_service
from app.schemas.message.message_edit import MessageEditCreate
from app.schemas.message.message_read import MessageRead
from app.schemas.message_reaction.message_reaction import (ReactionCounts,
                                                           ReactionCreate,
                                                           ReactionRead)
from app.services.message_service import MessageService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/{message_id}/reactions", response_model=ReactionCounts)
async def add_reaction(
    message_id: UUID,
    body: ReactionCreate,
    message_service: MessageService = Depends(get_message_service),
    current_user = Depends(get_current_user),
):
    _, counts = await message_service.add_reaction(message_id, current_user.id, body.emoji)
    return ReactionCounts(messageId=message_id, counts=counts)


@router.get("/{message_id}/reactions", response_model=List[ReactionRead])
async def list_reactions(
    message_id: UUID,
    message_service: MessageService = Depends(get_message_service),
    current_user = Depends(get_current_user),
):
    reactions = await message_service.get_reactions(message_id, current_user.id)
    return [ReactionRead.model_validate(r) for r in reactions]



@router.delete("/{message_id}/reactions", response_model=ReactionCounts)
async def remove_reaction(
    message_id: UUID,
    emoji: str,
    message_service: MessageService = Depends(get_message_service),
    current_user = Depends(get_current_user),
):
    _, counts = await message_service.remove_reaction(message_id, current_user.id, emoji)
    return ReactionCounts(messageId=message_id, counts=counts)


@router.patch("/{message_id}", response_model=MessageRead)
async def edit_message(
    message_id: UUID,
    body: MessageEditCreate,
    message_service: MessageService = Depends(get_message_service),
    current_user = Depends(get_current_user),
):
    updated_msg, _ = await message_service.edit_message(message_id, current_user.id, body.content)
    return MessageRead.model_validate(updated_msg)


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    message_service: MessageService = Depends(get_message_service),
    current_user = Depends(get_current_user),
):
    deleted = await message_service.delete_message(message_id, current_user.id)
    return deleted

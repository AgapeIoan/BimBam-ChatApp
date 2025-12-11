from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import (
    get_async_session,
    get_conversation_service,
    get_current_user,
    get_friendship_service,
)
from app.models.user import User
from app.schemas.conversation.conversation_read import ConversationRead
from app.schemas.friendship.friendship import FriendListItem
from app.services.conversation_service import ConversationService
from app.services.friendship_service import FriendshipService

router = APIRouter(prefix="/friends", tags=["friends"])


@router.get("/", response_model=List[FriendListItem])
async def list_my_friends(
    current_user: User = Depends(get_current_user),
    friendship_service: FriendshipService = Depends(get_friendship_service),
):
    """
    List all friends of the *current* user, along with:

    - friend: user info (UserRead)
    - is_online: bool
    - last_read_message_id: UUID | None
    - unread_count: int
    """
    return await friendship_service.get_friends(current_user.id)


@router.get("/{friend_id}/conversation", response_model=ConversationRead)
async def open_or_create_direct_conversation(
    friend_id: UUID,
    current_user: User = Depends(get_current_user),
    friendship_service: FriendshipService = Depends(get_friendship_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
    session=Depends(get_async_session),
):
    """
    Open a direct (one-to-one) conversation with a friend.

    Behavior:
    - If a DM already exists between current_user and friend_id, reuse it.
    - Otherwise, create a new one.
    - Optionally enforce that they are friends before allowing the DM.
    """
    are_friends = await friendship_service.are_friends(current_user.id, friend_id)
    if not are_friends:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not friends with this user",
        )

    conversation = await conversation_service.get_or_create_dm(
        current_user.id, friend_id
    )
    await session.refresh(conversation, attribute_names=["members"])
    for member in conversation.members:
        await session.refresh(member, attribute_names=["user"])

    return ConversationRead.model_validate(conversation)

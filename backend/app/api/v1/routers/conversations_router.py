from typing import List

from fastapi import APIRouter, Depends

from backend.app.schemas.conversation.conversation_preview import ConversationPreview
from backend.app.services.conversation_service import ConversationService
from backend.app.api.v1.deps import get_conversation_service, get_current_user
from backend.app.models.user import User

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

from app.db.base import Base

# Import all models here so that Alembic and SQLAlchemy know about them
from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember
from app.models.friend_request import FriendRequest
from app.models.friendship import Friendship

__all__ = [
    "Base",
    "User",
    "Message",
    "Conversation",
    "ConversationMember",
    "FriendRequest",
    "Friendship",
]

import json
import logging
from typing import Any, Dict, Optional, Set
from uuid import UUID

from fastapi import WebSocket
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_reaction_repository import MessageReactionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.typing.typing_status import TypingStatus
from app.schemas.websocket.envelope import EventEnvelope
from app.schemas.websocket.error_events import ErrorPayload
from app.schemas.websocket.event_types import WebSocketEventType
from app.schemas.websocket.message_events import (
    MessageAckPayload,
    MessageEditPayload,
    MessageReactionPayload,
    MessageSendPayload,
)
from app.services.message_service import MessageService
from app.websockets.connection_manager import connection_manager

logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 4000


def _room_id(conversation_id: UUID) -> str:
    return f"room_{conversation_id}"


def _format_sender_name(sender: Any | None) -> str | None:
    if not sender:
        return None
    return sender.username or sender.email or str(getattr(sender, "id", ""))


def serialize_message(msg) -> Dict[str, Any]:
    sender = getattr(msg, "sender", None)
    return {
        "messageId": str(msg.id),
        "conversationId": str(msg.conversation_id),
        "senderId": str(msg.sender_id),
        "content": msg.content,
        "createdAt": msg.created_at.isoformat(),
        "delivered": msg.delivered,
        "read": msg.read,
        "editedAt": msg.edited_at.isoformat() if getattr(msg, "edited_at", None) else None,
        "editedById": str(msg.edited_by_id) if getattr(msg, "edited_by_id", None) else None,
        "senderName": _format_sender_name(sender),
        "senderUsername": getattr(sender, "username", None),
        "senderEmail": getattr(sender, "email", None),
        "senderAvatarUrl": getattr(sender, "avatar_url", None),
        "roomId": _room_id(msg.conversation_id),
    }


async def broadcast_to_conversation(
    conversation_id: UUID,
    envelope: Dict[str, Any],
    exclude: Optional[Set[UUID]] = None,
) -> Set[UUID]:
    exclude_ids = set(exclude or [])
    try:
        async with AsyncSessionLocal() as session:
            conv_repo = ConversationRepository(session)
            members = await conv_repo.get_conversation_members(conversation_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to load conversation members for room %s: %s", conversation_id, exc
        )
        return set()

    recipients = {member.user_id for member in members if member.user_id not in exclude_ids}
    delivered: Set[UUID] = set()
    for user_id in recipients:
        if await connection_manager.send_to_user(user_id, envelope):
            delivered.add(user_id)
    return delivered


async def send_error(
    websocket: WebSocket, code: str, detail: str, correlation_id: Optional[str] = None
):
    payload = ErrorPayload(code=code, detail=detail, correlationId=correlation_id)
    envelope = {
        "type": WebSocketEventType.ERROR.value,
        "data": payload.model_dump(by_alias=True),
    }
    await websocket.send_text(json.dumps(envelope, default=str, ensure_ascii=False))


async def handle_message_send(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
    correlation_id: Optional[str],
):
    try:
        payload = MessageSendPayload.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Validation failed for message_send: %s", exc)
        await send_error(websocket, "validation_failed", "Invalid message payload", correlation_id)
        return

    if len(payload.content) > MAX_MESSAGE_LENGTH:
        await send_error(websocket, "validation_failed", "Message too long", correlation_id)
        return

    async with AsyncSessionLocal() as session, session.begin():
        message_repo = MessageRepository(session)
        conv_repo = ConversationRepository(session)
        user_repo = UserRepository(session)
        reaction_repo = MessageReactionRepository(session)
        message_service = MessageService(message_repo, conv_repo, user_repo, reaction_repo)

        try:
            msg = await message_service.send_message(
                conversation_id=payload.conversation_id,
                sender_id=user_id,
                content=payload.content,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to persist message: %s", exc)
            await send_error(websocket, "db_error", "Failed to send message", correlation_id)
            return

    message_dict = serialize_message(msg)
    delivery_envelope = {
        "type": WebSocketEventType.MESSAGE_DELIVERED.value,
        "data": message_dict,
    }

    delivered_ids = await broadcast_to_conversation(
        payload.conversation_id,
        delivery_envelope,
        exclude={user_id},
    )
    delivered = bool(delivered_ids)

    # Update delivered flag if delivered to at least one
    if delivered:
        async with AsyncSessionLocal() as session, session.begin():
            message_repo = MessageRepository(session)
            await message_repo.mark_delivered(msg.id)

        message_dict["delivered"] = True

    ack = MessageAckPayload(
        correlationId=correlation_id,
        messageId=msg.id,
        status="ok",
        delivered=delivered,
        message=message_dict,
    )
    await websocket.send_text(
        json.dumps(
            {
                "type": WebSocketEventType.MESSAGE_ACK.value,
                "data": ack.model_dump(by_alias=True),
            },
            default=str,
            ensure_ascii=False,
        )
    )


async def handle_message_edit(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
    correlation_id: Optional[str],
):
    try:
        payload = MessageEditPayload.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Validation failed for message_edit: %s", exc)
        await send_error(websocket, "validation_failed", "Invalid message edit payload", correlation_id)
        return

    if payload.content is None:
        await send_error(websocket, "validation_failed", "Content required", correlation_id)
        return

    if len(payload.content) > MAX_MESSAGE_LENGTH:
        await send_error(websocket, "validation_failed", "Message too long", correlation_id)
        return

    async with AsyncSessionLocal() as session, session.begin():
        message_repo = MessageRepository(session)
        conv_repo = ConversationRepository(session)
        user_repo = UserRepository(session)
        reaction_repo = MessageReactionRepository(session)
        message_service = MessageService(message_repo, conv_repo, user_repo, reaction_repo)

        try:
            updated_msg, edit_record = await message_service.edit_message(
                payload.message_id, user_id, payload.content
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to edit message: %s", exc)
            await send_error(websocket, "db_error", "Failed to edit message", correlation_id)
            return

    message_dict = serialize_message(updated_msg)
    edit_envelope = {"type": WebSocketEventType.MESSAGE_EDIT.value, "data": message_dict}

    delivered_ids = await broadcast_to_conversation(
        updated_msg.conversation_id,
        edit_envelope,
        exclude={user_id},
    )
    delivered = bool(delivered_ids)

    # Ack back to editor
    ack = MessageAckPayload(
        correlationId=correlation_id,
        messageId=updated_msg.id,
        status="ok",
        delivered=delivered,
        message=message_dict,
    )

    await websocket.send_text(
        json.dumps(
            {"type": WebSocketEventType.MESSAGE_ACK.value, "data": ack.model_dump(by_alias=True)},
            default=str,
            ensure_ascii=False,
        )
    )


async def handle_message_reaction(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
    correlation_id: Optional[str],
):
    try:
        payload = MessageReactionPayload.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Validation failed for message_reaction: %s", exc)
        await send_error(websocket, "validation_failed", "Invalid reaction payload", correlation_id)
        return

    if not payload.emoji or not payload.emoji.strip():
        await send_error(websocket, "validation_failed", "Emoji required", correlation_id)
        return

    async with AsyncSessionLocal() as session, session.begin():
        message_repo = MessageRepository(session)
        conv_repo = ConversationRepository(session)
        user_repo = UserRepository(session)
        reaction_repo = MessageReactionRepository(session)
        message_service = MessageService(message_repo, conv_repo, user_repo, reaction_repo)
        message_obj = None
        try:
            if payload.action == "add":
                message_obj, counts = await message_service.add_reaction(payload.message_id, user_id, payload.emoji)
            else:
                message_obj, counts = await message_service.remove_reaction(payload.message_id, user_id, payload.emoji)
            # Also load usernames grouped by emoji for tooltip display
            users_by_emoji = await reaction_repo.get_usernames_grouped_by_emoji(payload.message_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to process reaction: %s", exc)
            await send_error(websocket, "db_error", "Failed to process reaction", correlation_id)
            return

    # Broadcast updated counts to conversation members
    delivered = False
    conversation_id: UUID | None = None
    try:
        async with AsyncSessionLocal() as session:
            m_repo = MessageRepository(session)
            message_row = await m_repo.get_by_id(payload.message_id)
            # defensive: if somehow we didn't get Message, re-fetch via plain select
            if not message_row or not hasattr(message_row, "conversation_id"):
                result = await session.execute(
                    select(Message).where(Message.id == payload.message_id)
                )
                message_row = result.scalars().one_or_none()
            if message_row:
                conversation_id = message_row.conversation_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load conversation members for reaction delivery: %s", exc)

    room_id = _room_id(conversation_id) if conversation_id else None
    # Build data including counts and usernames per emoji
    # Shape: counts: { emoji: count }, users: { emoji: [username, ...] }
    reaction_envelope = {
        "type": WebSocketEventType.MESSAGE_REACTION.value,
        "data": {
            "messageId": str(payload.message_id),
            "counts": counts,
            "conversationId": str(conversation_id) if conversation_id else None,
            "roomId": room_id,
            "users": users_by_emoji,
        },
    }

    delivered_ids = (
        await broadcast_to_conversation(
            conversation_id,
            reaction_envelope,
            exclude={user_id},
        )
        if conversation_id
        else set()
    )
    delivered = bool(delivered_ids)

    # Ack back to sender (include counts)
    ack = MessageAckPayload(
        correlationId=correlation_id,
        messageId=payload.message_id,
        status="ok",
        delivered=delivered,
        message={
            "messageId": str(payload.message_id),
            "counts": counts,
            "conversationId": str(conversation_id) if conversation_id else None,
            "roomId": room_id,
            "users": users_by_emoji,
        },
    )

    await websocket.send_text(
        json.dumps(
            {"type": WebSocketEventType.MESSAGE_ACK.value, "data": ack.model_dump(by_alias=True)},
            default=str,
            ensure_ascii=False,
        )
    )


async def handle_typing(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
    correlation_id: Optional[str],
):
    try:
        payload = TypingStatus.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Validation failed for typing: %s", exc)
        await send_error(websocket, "validation_failed", "Invalid typing payload", correlation_id)
        return

    if payload.from_user_id != user_id:
        await send_error(
            websocket,
            "forbidden",
            "fromUserId must match authenticated user",
            correlation_id,
        )
        return

    envelope = {
        "type": WebSocketEventType.TYPING.value,
        "data": {
            "fromUserId": str(user_id),
            "toUserId": str(payload.to_user_id),
            "isTyping": payload.is_typing,
        },
    }

    # Best effort send
    await connection_manager.send_to_user(payload.to_user_id, envelope)


async def handle_mark_read(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
    correlation_id: Optional[str],
):
    before_id = data.get("beforeMessageId")
    conversation_id = data.get("conversationId")
    if not conversation_id:
        await send_error(websocket, "validation_failed", "conversationId required", correlation_id)
        return

    try:
        convo_uuid = UUID(str(conversation_id))
        before_uuid = UUID(str(before_id)) if before_id else None
    except ValueError:
        await send_error(websocket, "validation_failed", "Invalid IDs", correlation_id)
        return

    async with AsyncSessionLocal() as session, session.begin():
        msg_repo = MessageRepository(session)
        conv_repo = ConversationRepository(session)
        user_repo = UserRepository(session)
        reaction_repo = MessageReactionRepository(session)
        msg_service = MessageService(msg_repo, conv_repo, user_repo, reaction_repo)

        try:
            updated = await msg_service.mark_read(
                conversation_id=convo_uuid,
                user_id=user_id,
                before_message_id=before_uuid,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to mark messages read: %s", exc)
            await send_error(websocket, "db_error", "Failed to mark read", correlation_id)
            return

    # Notify others in conversation
    if updated:
        last_msg = updated[-1]
        envelope = {
            "type": WebSocketEventType.MESSAGE_READ.value,
            "data": {
                "conversationId": str(convo_uuid),
                "readerId": str(user_id),
                "messageId": str(last_msg.id),
                "roomId": _room_id(convo_uuid),
            },
        }
        await broadcast_to_conversation(convo_uuid, envelope, exclude={user_id})

    # Ack back to reader
    ack_msg_id = updated[-1].id if updated else None
    ack = MessageAckPayload(
        correlationId=correlation_id,
        messageId=ack_msg_id,
        status="ok",
        delivered=bool(updated),
    )
    await websocket.send_text(
        json.dumps(
            {
                "type": WebSocketEventType.MESSAGE_ACK.value,
                "data": ack.model_dump(by_alias=True),
            },
            default=str,
            ensure_ascii=False,
        )
    )


async def dispatch_event(
    websocket: WebSocket,
    user_id: UUID,
    envelope: EventEnvelope,
):
    etype = envelope.type
    data = envelope.data or {}
    correlation_id = envelope.correlation_id or data.get("correlationId")

    if etype == WebSocketEventType.MESSAGE_SEND.value:
        await handle_message_send(websocket, user_id, data, correlation_id)
    elif etype == WebSocketEventType.MESSAGE_EDIT.value:
        await handle_message_edit(websocket, user_id, data, correlation_id)
    elif etype == WebSocketEventType.MESSAGE_REACTION.value:
        await handle_message_reaction(websocket, user_id, data, correlation_id)
    elif etype == WebSocketEventType.TYPING.value:
        await handle_typing(websocket, user_id, data, correlation_id)
    elif etype == WebSocketEventType.MESSAGE_READ.value:
        await handle_mark_read(websocket, user_id, data, correlation_id)
    else:
        await send_error(websocket, "unsupported_event", f"Unsupported event type {etype}", correlation_id)

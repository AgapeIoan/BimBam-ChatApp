import json
import logging
from typing import Any, Dict, Optional, Set
from uuid import UUID

from fastapi import WebSocket

from app.db.session import AsyncSessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.typing.typing_status import TypingStatus
from app.schemas.websocket.envelope import EventEnvelope
from app.schemas.websocket.error_events import ErrorPayload
from app.schemas.websocket.event_types import WebSocketEventType
from app.schemas.websocket.message_events import MessageAckPayload, MessageSendPayload
from app.services.message_service import MessageService
from app.websockets.connection_manager import connection_manager

logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 4000


def serialize_message(msg) -> Dict[str, Any]:
    return {
        "messageId": str(msg.id),
        "conversationId": str(msg.conversation_id),
        "senderId": str(msg.sender_id),
        "content": msg.content,
        "createdAt": msg.created_at.isoformat(),
        "delivered": msg.delivered,
        "read": msg.read,
    }


async def send_error(
    websocket: WebSocket, code: str, detail: str, correlation_id: Optional[str] = None
):
    payload = ErrorPayload(code=code, detail=detail, correlationId=correlation_id)
    envelope = {
        "type": WebSocketEventType.ERROR.value,
        "data": payload.model_dump(by_alias=True),
    }
    await websocket.send_text(json.dumps(envelope, default=str))


async def handle_message_send(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
):
    try:
        payload = MessageSendPayload.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Validation failed for message_send: %s", exc)
        await send_error(websocket, "validation_failed", "Invalid message payload")
        return

    if len(payload.content) > MAX_MESSAGE_LENGTH:
        await send_error(websocket, "validation_failed", "Message too long")
        return

    correlation_id = data.get("correlationId")

    async with AsyncSessionLocal() as session, session.begin():
        message_repo = MessageRepository(session)
        conv_repo = ConversationRepository(session)
        user_repo = UserRepository(session)
        message_service = MessageService(message_repo, conv_repo, user_repo)

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

    # Attempt delivery to recipient(s)
    delivered = False
    recipients: Set[UUID] = set()
    try:
        async with AsyncSessionLocal() as session:
            conv_repo = ConversationRepository(session)
            members = await conv_repo.get_conversation_members(payload.conversation_id)
            recipients = {m.user_id for m in members if m.user_id != user_id}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load conversation members for delivery: %s", exc)

    message_dict = serialize_message(msg)
    delivery_envelope = {
        "type": WebSocketEventType.MESSAGE_DELIVERED.value,
        "data": message_dict,
    }

    if recipients:
        for rid in recipients:
            delivered = await connection_manager.send_to_user(rid, delivery_envelope) or delivered

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
        )
    )


async def handle_typing(
    websocket: WebSocket,
    user_id: UUID,
    data: Dict[str, Any],
):
    try:
        payload = TypingStatus.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Validation failed for typing: %s", exc)
        await send_error(websocket, "validation_failed", "Invalid typing payload")
        return

    envelope = {
        "type": WebSocketEventType.TYPING.value,
        "data": {
            "fromUserId": str(payload.from_user_id),
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
):
    correlation_id = data.get("correlationId")
    before_id = data.get("beforeMessageId")
    conversation_id = data.get("conversationId")
    if not conversation_id:
        await send_error(websocket, "validation_failed", "conversationId required")
        return

    try:
        convo_uuid = UUID(str(conversation_id))
        before_uuid = UUID(str(before_id)) if before_id else None
    except ValueError:
        await send_error(websocket, "validation_failed", "Invalid IDs")
        return

    async with AsyncSessionLocal() as session, session.begin():
        msg_repo = MessageRepository(session)
        conv_repo = ConversationRepository(session)
        user_repo = UserRepository(session)
        msg_service = MessageService(msg_repo, conv_repo, user_repo)

        try:
            updated = await msg_service.mark_read(
                conversation_id=convo_uuid,
                user_id=user_id,
                before_message_id=before_uuid,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to mark messages read: %s", exc)
            await send_error(websocket, "db_error", "Failed to mark read")
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
            },
        }
        try:
            async with AsyncSessionLocal() as session:
                conv_repo = ConversationRepository(session)
                members = await conv_repo.get_conversation_members(convo_uuid)
                recipients = {m.user_id for m in members if m.user_id != user_id}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to broadcast read receipt: %s", exc)
            return

        for rid in recipients:
            await connection_manager.send_to_user(rid, envelope)

    # Ack back to reader
    ack_msg_id = updated[-1].id if updated else None
    ack = MessageAckPayload(
        correlationId=correlation_id,
        messageId=ack_msg_id,
        status="ok",
        delivered=True,
    )
    await websocket.send_text(
        json.dumps(
            {
                "type": WebSocketEventType.MESSAGE_ACK.value,
                "data": ack.model_dump(by_alias=True),
            },
            default=str,
        )
    )


async def dispatch_event(
    websocket: WebSocket,
    user_id: UUID,
    envelope: EventEnvelope,
):
    etype = envelope.type
    data = envelope.data or {}

    if etype == WebSocketEventType.MESSAGE_SEND.value:
        await handle_message_send(websocket, user_id, data)
    elif etype == WebSocketEventType.TYPING.value:
        await handle_typing(websocket, user_id, data)
    elif etype == WebSocketEventType.MESSAGE_READ.value:
        await handle_mark_read(websocket, user_id, data)
    else:
        await send_error(websocket, "unsupported_event", f"Unsupported event type {etype}")

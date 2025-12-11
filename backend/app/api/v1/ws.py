import asyncio
import logging
import time
from collections import deque
from contextlib import suppress
from uuid import UUID, uuid4

from app.api.deps.websocket_auth import websocket_auth
from app.schemas.websocket.envelope import EventEnvelope
from app.schemas.websocket.event_types import WebSocketEventType
from app.services.presence_service import PresenceService
from app.websockets.connection_manager import connection_manager
from app.websockets.events import dispatch_event, send_error
from fastapi import APIRouter, Depends, WebSocket
from starlette.websockets import WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)
presence_service = PresenceService()
MAX_EVENTS_PER_MIN = 120
PRESENCE_REFRESH_MIN_SECONDS = 5


async def _presence_keepalive(user_id: UUID) -> None:
    """
    Refresh presence TTL periodically so long-lived sockets don't expire in Redis.
    """
    interval = max(PRESENCE_REFRESH_MIN_SECONDS, presence_service.ttl_seconds // 2)
    while True:
        try:
            await asyncio.sleep(interval)
            await presence_service.set_online(user_id)
        except asyncio.CancelledError:
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to refresh presence for user %s: %s", user_id, exc)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user=Depends(websocket_auth),
):
    user_id: UUID = user.id
    connection_id = str(uuid4())
    client = websocket.client or ("unknown", 0)
    await websocket.accept()
    await connection_manager.add(user_id, websocket)
    await presence_service.set_online(user_id)
    presence_task = asyncio.create_task(_presence_keepalive(user_id))
    recent_events = deque()
    logger.info(
        "WebSocket connected for user %s conn=%s client=%s:%s path=%s",
        user_id,
        connection_id,
        client[0],
        client[1],
        websocket.url.path,
    )
    presence_envelope = {
        "type": WebSocketEventType.PRESENCE.value,
        "data": {"userId": str(user_id), "isOnline": True},
    }
    others = (await connection_manager.all_user_ids()) - {user_id}
    if others:
        await connection_manager.broadcast(others, presence_envelope)
    # Send snapshot of currently-online users to the connecting client
    if others:
        for other_id in others:
            try:
                await websocket.send_json(
                    {
                        "type": WebSocketEventType.PRESENCE.value,
                        "data": {"userId": str(other_id), "isOnline": True},
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed to send presence snapshot to %s for %s: %s", user_id, other_id, exc)

    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnect for user %s conn=%s", user_id, connection_id)
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("Receive error for user %s conn=%s: %s", user_id, connection_id, exc)
                await send_error(websocket, "receive_error", "Failed to parse message")
                continue

            now = time.time()
            recent_events.append(now)
            # Keep only last 60s
            while recent_events and now - recent_events[0] > 60:
                recent_events.popleft()
            if len(recent_events) > MAX_EVENTS_PER_MIN:
                await send_error(websocket, "rate_limited", "Too many events")
                await websocket.close(code=1013)
                logger.warning("Rate limit triggered for user %s conn=%s", user_id, connection_id)
                break

            try:
                envelope = EventEnvelope.model_validate(raw)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Invalid envelope from user %s conn=%s: %s", user_id, connection_id, exc)
                await send_error(websocket, "validation_failed", "Invalid envelope")
                continue
            logger.debug(
                "Received WS event type=%s user=%s conn=%s", envelope.type, user_id, connection_id
            )

            await dispatch_event(websocket, user_id, envelope)
    finally:
        presence_task.cancel()
        with suppress(asyncio.CancelledError):
            await presence_task
        await connection_manager.remove(user_id, websocket)
        has_other = await connection_manager.has_connections(user_id)
        if not has_other:
            await presence_service.set_offline(user_id)
            presence_envelope = {
                "type": WebSocketEventType.PRESENCE.value,
                "data": {"userId": str(user_id), "isOnline": False},
            }
            others = (await connection_manager.all_user_ids()) - {user_id}
            if others:
                await connection_manager.broadcast(others, presence_envelope)

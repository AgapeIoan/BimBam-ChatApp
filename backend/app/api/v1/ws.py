import logging
import time
from collections import deque
from uuid import UUID

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


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user=Depends(websocket_auth),
):
    user_id: UUID = user.id
    await websocket.accept()
    await connection_manager.add(user_id, websocket)
    await presence_service.set_online(user_id)
    recent_events = deque()
    logger.info("WebSocket connected for user %s", user_id)
    presence_envelope = {
        "type": WebSocketEventType.PRESENCE.value,
        "data": {"userId": str(user_id), "isOnline": True},
    }
    others = (await connection_manager.all_user_ids()) - {user_id}
    if others:
        await connection_manager.broadcast(others, presence_envelope)

    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnect for user %s", user_id)
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("Receive error for user %s: %s", user_id, exc)
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
                logger.warning("Rate limit triggered for user %s", user_id)
                break

            try:
                envelope = EventEnvelope.model_validate(raw)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Invalid envelope from user %s: %s", user_id, exc)
                await send_error(websocket, "validation_failed", "Invalid envelope")
                continue

            await dispatch_event(websocket, user_id, envelope)
    finally:
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

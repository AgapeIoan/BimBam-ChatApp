import logging
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.api.deps.websocket_auth import websocket_auth
from app.schemas.websocket.envelope import EventEnvelope
from app.services.presence_service import PresenceService
from app.websockets.connection_manager import connection_manager
from app.websockets.events import dispatch_event, send_error

router = APIRouter()
logger = logging.getLogger(__name__)
presence_service = PresenceService()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user=Depends(websocket_auth),
):
    user_id: UUID = user.id
    await websocket.accept()
    await connection_manager.add(user_id, websocket)
    await presence_service.set_online(user_id)

    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("Receive error for user %s: %s", user_id, exc)
                await send_error(websocket, "receive_error", "Failed to parse message")
                continue

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

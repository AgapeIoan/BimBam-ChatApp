import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.deps.websocket_auth import websocket_auth
from app.api.v1 import ws as ws_module
from app.main import app


async def fake_auth(_: WebSocket):
    return SimpleNamespace(id=uuid4())


async def async_noop(*_, **__):
    return None


def setup_module():
    app.dependency_overrides[websocket_auth] = fake_auth
    ws_module.presence_service.set_online = async_noop  # type: ignore[assignment]
    ws_module.presence_service.set_offline = async_noop  # type: ignore[assignment]


def teardown_module():
    app.dependency_overrides = {}


def test_websocket_invalid_envelope_sends_error():
    client = TestClient(app)
    with client.websocket_connect("/ws?token=test") as ws:
        ws.send_json({"foo": "bar"})
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["data"]["code"] == "validation_failed"


def test_websocket_rate_limit():
    client = TestClient(app)
    with client.websocket_connect("/ws?token=test") as ws:
        for _ in range(ws_module.MAX_EVENTS_PER_MIN + 1):
            ws.send_json(
                {
                    "type": "typing",
                    "data": {
                        "fromUserId": str(uuid4()),
                        "toUserId": str(uuid4()),
                        "isTyping": True,
                    },
                }
            )
        error_msg = ws.receive_json()
        assert error_msg["type"] == "error"
        event = ws.receive()
        assert event["type"] == "websocket.close"

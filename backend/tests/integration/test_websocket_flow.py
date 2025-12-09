import pytest
from fastapi import WebSocket, status
from fastapi.exceptions import WebSocketException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.deps.websocket_auth import websocket_auth
from app.main import app
from app.repositories.message_repository import MessageRepository
from tests.fixtures import client, user_factory, conversation_factory, event_loop

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_auth_fail_missing_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass


def test_happy_path_message_delivery(client, user_factory, conversation_factory, event_loop):
    user_a = user_factory("a@example.com", "user-a")
    user_b = user_factory("b@example.com", "user-b")
    conversation = conversation_factory([user_a.id, user_b.id])
    tokens = {"user-a": user_a, "user-b": user_b}

    async def fake_auth(websocket: WebSocket):
        token = websocket.query_params.get("token")
        if not token or token not in tokens:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return tokens[token]

    app.dependency_overrides[websocket_auth] = fake_auth

    try:
        with (
            client.websocket_connect("/ws?token=user-a&websocket=1") as ws_a,
            client.websocket_connect("/ws?token=user-b&websocket=1") as ws_b,
        ):
            ws_a.send_json(
                {
                    "type": "message_send",
                    "data": {"conversationId": str(conversation.id), "content": "hello"},
                    "correlationId": "corr-1",
                }
            )

            # Consume until we get delivered
            delivered = None
            while delivered is None:
                msg = ws_b.receive_json()
                if msg["type"] == "message_delivered":
                    delivered = msg

            assert delivered["data"]["content"] == "hello"
            assert delivered["data"]["conversationId"] == str(conversation.id)

            ack = None
            while ack is None:
                msg = ws_a.receive_json()
                if msg["type"] == "message_ack":
                    ack = msg

            assert ack["data"]["status"] == "ok"
            assert ack["data"]["correlationId"] == "corr-1"
            assert ack["data"]["delivered"] is True
            assert ack["data"]["message"]["content"] == "hello"
    finally:
        app.dependency_overrides.pop(websocket_auth, None)

    async def fetch_messages():
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            repo = MessageRepository(session)
            return await repo.get_messages(conversation_id=conversation.id, limit=10)

    messages = event_loop.run_until_complete(fetch_messages())
    assert len(messages) == 1
    assert messages[0].content == "hello"
    assert messages[0].sender_id == user_a.id


def test_offline_recipient_persists_message(client, user_factory, conversation_factory, event_loop):
    user_a = user_factory("c@example.com", "user-c")
    user_b = user_factory("d@example.com", "user-d")
    conversation = conversation_factory([user_a.id, user_b.id])
    tokens = {"user-c": user_a}

    async def fake_auth(websocket: WebSocket):
        token = websocket.query_params.get("token")
        if not token or token not in tokens:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return tokens[token]

    app.dependency_overrides[websocket_auth] = fake_auth

    try:
        with client.websocket_connect("/ws?token=user-c&websocket=1") as ws_a:
            ws_a.send_json(
                {
                    "type": "message_send",
                    "data": {"conversationId": str(conversation.id), "content": "ping"},
                    "correlationId": "corr-2",
                }
            )

            ack = None
            while ack is None:
                msg = ws_a.receive_json()
                if msg["type"] == "message_ack":
                    ack = msg

            assert ack["data"]["correlationId"] == "corr-2"
            assert ack["data"]["delivered"] is False
    finally:
        app.dependency_overrides.pop(websocket_auth, None)

    async def fetch_messages():
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            repo = MessageRepository(session)
            return await repo.get_messages(conversation_id=conversation.id, limit=10)

    messages = event_loop.run_until_complete(fetch_messages())
    assert len(messages) == 1
    assert messages[0].content == "ping"
    assert messages[0].sender_id == user_a.id

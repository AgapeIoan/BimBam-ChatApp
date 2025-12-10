from uuid import uuid4

import pytest

from app.websockets.connection_manager import ConnectionManager


class DummyWebSocket:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def send_json(self, message):
        self.sent.append(message)

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_connect_adds_connection():
    manager = ConnectionManager()
    user_id = uuid4()
    ws = DummyWebSocket()

    await manager.add(user_id, ws)

    assert await manager.has_connections(user_id) is True
    connections = await manager.get_connections(user_id)
    assert ws in connections


@pytest.mark.asyncio
async def test_disconnect_removes_connection():
    manager = ConnectionManager()
    user_id = uuid4()
    ws = DummyWebSocket()

    await manager.add(user_id, ws)
    await manager.remove(user_id, ws)

    assert await manager.has_connections(user_id) is False


@pytest.mark.asyncio
async def test_send_personal_message_reaches_socket():
    manager = ConnectionManager()
    user_id = uuid4()
    ws = DummyWebSocket()
    await manager.add(user_id, ws)

    payload = {"hello": "world"}
    delivered = await manager.send_to_user(user_id, payload)

    assert delivered is True
    assert payload in ws.sent

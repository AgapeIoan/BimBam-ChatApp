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
async def test_add_remove_connections():
    manager = ConnectionManager()
    user_id = uuid4()
    ws = DummyWebSocket()

    await manager.add(user_id, ws)
    assert await manager.has_connections(user_id)

    await manager.remove(user_id, ws)
    assert not await manager.has_connections(user_id)


@pytest.mark.asyncio
async def test_send_to_user():
    manager = ConnectionManager()
    user_id = uuid4()
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()

    await manager.add(user_id, ws1)
    await manager.add(user_id, ws2)

    payload = {"hello": "world"}
    delivered = await manager.send_to_user(user_id, payload)

    assert delivered is True
    assert payload in ws1.sent or payload in ws2.sent

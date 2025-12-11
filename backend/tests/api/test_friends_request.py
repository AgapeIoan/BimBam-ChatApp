import pytest
from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_user
from app.main import app
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def seed_users(session_factory):
    async with session_factory() as session:
        user_repo = UserRepository(session)
        user1 = await user_repo.create(
            provider="test",
            provider_id="user1",
            email="user1@example.com",
            username="user1",
            avatar_url=None,
        )
        user2 = await user_repo.create(
            provider="test",
            provider_id="user2",
            email="user2@example.com",
            username="user2",
            avatar_url=None,
        )
        await session.commit()
        return user1, user2


@pytest.mark.asyncio
async def test_send_friend_request(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    assert response.status_code == 201
    data = response.json()
    assert data["fromUser"]["email"] == user1.email
    assert data["toUser"]["email"] == user2.email
    assert data["status"] == "pending"
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_accept_friend_request(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    request_id = response.json()["id"]
    app.dependency_overrides[get_current_user] = lambda: user2
    client2 = TestClient(app)
    response = client2.post(f"/api/v1/friend-requests/{request_id}/accept")
    assert response.status_code == 201
    assert response.json()["status"] == "accepted"
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_decline_friend_request(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    request_id = response.json()["id"]
    app.dependency_overrides[get_current_user] = lambda: user2
    client2 = TestClient(app)
    response = client2.post(f"/api/v1/friend-requests/{request_id}/decline")
    assert response.status_code == 200
    assert response.json()["status"] == "declined"
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_cancel_friend_request(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    request_id = response.json()["id"]
    response = client.post(f"/api/v1/friend-requests/{request_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_duplicate_friend_request_blocked(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    assert response.status_code == 422 or response.status_code == 400
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_send_after_decline(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    request_id = response.json()["id"]
    app.dependency_overrides[get_current_user] = lambda: user2
    client2 = TestClient(app)
    client2.post(f"/api/v1/friend-requests/{request_id}/decline")
    app.dependency_overrides[get_current_user] = lambda: user1
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    assert response.status_code == 201
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_send_after_cancel(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    request_id = response.json()["id"]
    client.post(f"/api/v1/friend-requests/{request_id}/cancel")
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    assert response.status_code == 201
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_list_incoming_outgoing_requests(event_loop, session_factory):
    user1, user2 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    response = client.post("/api/v1/friend-requests", json={"toEmail": user2.email})
    request_id = response.json()["id"]
    response = client.get("/api/v1/friend-requests/outgoing")
    assert response.status_code == 200
    outgoing = response.json()
    assert any(r["id"] == request_id for r in outgoing)
    app.dependency_overrides[get_current_user] = lambda: user2
    client2 = TestClient(app)
    response = client2.get("/api/v1/friend-requests/incoming")
    assert response.status_code == 200
    incoming = response.json()
    assert any(r["id"] == request_id for r in incoming)
    app.dependency_overrides.pop(get_current_user, None)

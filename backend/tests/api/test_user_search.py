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
        user3 = await user_repo.create(
            provider="test",
            provider_id="user3",
            email="another@example.com",
            username="anotheruser",
            avatar_url=None,
        )
        await session.commit()
        return user1, user2, user3


@pytest.mark.asyncio
async def test_search_by_email(event_loop, session_factory):
    user1, user2, user3 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/users/search-by-email", params={"q": "example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        emails = [u["email"] for u in data]
        assert user1.email not in emails  # userul curent nu trebuie să apară
        assert user2.email in emails
        assert user3.email in emails
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_search_by_username(event_loop, session_factory):
    user1, user2, user3 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    try:
        response = client.get("/api/v1/users/search-by-username", params={"q": "user"})
        assert response.status_code == 200
        data = response.json()
        usernames = [u["username"] for u in data]
        assert user1.username not in usernames  # userul curent nu trebuie să apară
        assert user2.username in usernames
        assert user3.username in usernames
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_search_by_email_no_results(event_loop, session_factory):
    user1, user2, user3 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    try:
        response = client.get("/api/v1/users/search-by-email", params={"q": "notfound"})
        assert response.status_code == 200
        data = response.json()
        assert data == []
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_search_by_username_no_results(event_loop, session_factory):
    user1, user2, user3 = await seed_users(session_factory)
    app.dependency_overrides[get_current_user] = lambda: user1
    client = TestClient(app)
    try:
        response = client.get(
            "/api/v1/users/search-by-username", params={"q": "notfound"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []
    finally:
        app.dependency_overrides.pop(get_current_user, None)

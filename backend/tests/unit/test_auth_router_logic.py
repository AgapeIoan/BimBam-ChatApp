
import pytest

from app.api.v1.routers import auth as auth_router_module


class DummyUser:
    def __init__(self, user_id: str, email: str, username: str, avatar_url: str):
        self.id = user_id
        self.email = email
        self.username = username
        self.avatar_url = avatar_url

@pytest.mark.asyncio
async def test_get_me_returns_expected_user_shape():
    dummy = DummyUser(
        user_id="123",
        email="user@example.com",
        username="user",
        avatar_url="https://example.com/avatar.png",
    )

    result = await auth_router_module.get_me(current_user=dummy)

    assert result["id"] == "123"
    assert result["email"] == "user@example.com"
    assert result["username"] == "user"
    assert result["avatar_url"] == "https://example.com/avatar.png"

@pytest.mark.asyncio
async def test_logout_deletes_access_token_cookie():
    response = await auth_router_module.logout()

    assert response.status_code == 200

    cookies = [value.decode() for (name, value) in response.raw_headers if name.lower() == b"set-cookie"]

    assert any("access_token=" in cookie for cookie in cookies)
    assert any("access_token=" in cookie and "Max-Age=0" in cookie for cookie in cookies)
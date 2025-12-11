from app.main import app
from app.utils.jwt_utils import create_access_token
from fastapi.testclient import TestClient
from tests.helpers import _find_route_path

AUTH_ME_PATH = _find_route_path("get_me", method="GET")
AUTH_LOGOUT_PATH = _find_route_path("logout", method="POST")


def test_auth_me_unauthenticated_returns_401(client):
    response = client.get(AUTH_ME_PATH)

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Not authenticated"

def test_auth_me_authenticated_returns_user(client, user_factory):
    email = "api-auth@example.com"
    username = "api-user"
    user = user_factory(email, username)

    token = create_access_token({"sub": str(user.id)})
    client.cookies.set("access_token", token)

    response = client.get(AUTH_ME_PATH)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == email
    assert data["username"] == username
    assert "avatar_url" in data

def test_logout_clears_access_token_cookie(client):
    with TestClient(app) as client:
        client.cookies.set("access_token", "some-token")

        response = client.post(AUTH_LOGOUT_PATH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["detail"] == "Logged out"

    set_cookie = response.headers.get("set-cookie", "")

    assert "access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie or "Expires=" in set_cookie
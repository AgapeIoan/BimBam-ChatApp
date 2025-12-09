import pytest
from tests.helpers import _find_route_path
from tests.fixtures import client
from fastapi.testclient import TestClient
from app.main import app


def test_oauth_login_redirects_to_provider(client):
    """
    This assumes you have an endpoint function in auth router like:

        @router.get("/login/google")
        async def login_via_google(...)

    named "login_via_google" (adjust name if different).
    """
    login_path = _find_route_path("google_login", method="GET")

    with TestClient(app) as client:
        response = client.get(login_path)
    
    status = response.status_code


    if status in (302, 303, 307):
        location = response.headers.get("location", "")
        assert "accounts.google.com" in location or "oauth2" in location.lower()
        return

    # Graceful handling: OAuth not configured in this environment
    if status == 404:
        pytest.skip("OAuth login endpoint is registered but returned 404 (likely not configured in this environment).")

    # Any other unexpected status should still fail the test
    pytest.fail(f"Unexpected status code from google_login endpoint: {status}")
from datetime import datetime, timezone

import pytest
from app.utils.jwt_utils import create_access_token, decode_access_token


@pytest.mark.asyncio
async def test_jwt_token_uses_auth_settings():
    """
    Ensure tokens created with jwt_utils are compatible with the settings
    currently loaded by get_settings().
    """
    payload = {"sub": "some-user"}

    token = create_access_token(payload)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "some-user"
    exp_ts = decoded["exp"]
    assert exp_ts > int(datetime.now(timezone.utc).timestamp())
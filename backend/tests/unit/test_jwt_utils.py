from datetime import datetime, timedelta, timezone

from app.utils.jwt_utils import create_access_token, decode_access_token


def test_create_acces_token_contains_exp_and_sub():
    payload = {"sub": "testuser"}
    token = create_access_token(data=payload)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "testuser"
    assert decoded["exp"] > int(datetime.now(timezone.utc).timestamp())


def test_create_acces_token_respects_custom_expiration():
    custom_delta = timedelta(minutes=5)
    payload = {"sub": "testuser"}
    token = create_access_token(data=payload, expires_delta=custom_delta)

    decoded = decode_access_token(token)
    assert decoded is not None
    expiration_timestamp = decoded["exp"]
    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    assert now_timestamp < expiration_timestamp <= now_timestamp + 5 * 60 + 5

def test_decode_accest_token_invalid_token_returns_none():
    invalid_token = "not.a.valid.token"
    decoded = decode_access_token(invalid_token)
    assert decoded is None

def test_decode_access_token_tampered_token_returns_none():
    payload = {"sub": "testuser"}
    token = create_access_token(data=payload)
    tampered_token = token + "tampering"

    decoded = decode_access_token(tampered_token)
    assert decoded is None

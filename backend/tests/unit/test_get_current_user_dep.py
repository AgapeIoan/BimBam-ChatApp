from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import deps as deps_module


def make_fake_session():
    return AsyncSession(bind=MagicMock())

class DummyUser:
    def __init__(self, user_id: UUID, email: str, username: str):
        self.id = user_id
        self.email = email
        self.username = username
        self.avatar_url = "http://example.com/avatar.png"

@pytest.mark.asyncio
async def test_get_current_user_happy_path(monkeypatch):
    dummy_user = DummyUser(user_id=UUID("12345678-1234-5678-1234-567812345678"), email="user@example.com", username="testuser")

    def fake_decode(token: str):
        assert token == "valid.token.here"
        return {
            "sub": str(dummy_user.id),
            "email": dummy_user.email,
            "username": dummy_user.username,
            "avatar_url": dummy_user.avatar_url
        }
    
    class FakeRepo:
        def __init__(self, session):
            self.session = session

        async def get_by_id(self, user_id: UUID):
            assert user_id == dummy_user.id
            return dummy_user
        
    monkeypatch.setattr(deps_module, "decode_access_token", fake_decode)
    monkeypatch.setattr(deps_module, "UserRepository", FakeRepo)

    session=make_fake_session()
    user = await deps_module.get_current_user(acces_token="valid.token.here", session=session)
    assert user is dummy_user
    assert user.email == "user@example.com"
    assert user.username == "testuser"

@pytest.mark.asyncio
async def test_get_current_user_missing_token_raises(monkeypatch):
    session=make_fake_session()
    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(acces_token="", session=session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_payload_raises(monkeypatch):
    def fake_decode(token: str):
        return None
    
    monkeypatch.setattr(deps_module, "decode_access_token", fake_decode)

    session=make_fake_session()
    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(acces_token="something", session=session)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_sub_raises(monkeypatch):
    def fake_decode(token: str):
        return {}
    
    monkeypatch.setattr(deps_module, "decode_access_token", fake_decode)
    
    session=make_fake_session()
    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(acces_token="something", session=session)

    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_invalid_uuid_subject_raises(monkeypatch):
    def fake_decode(token: str):
        return {"sub": "not-a-uuid"}

    monkeypatch.setattr(deps_module, "decode_access_token", fake_decode)
    
    session=make_fake_session()
    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(acces_token="something", session=session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token subject"

@pytest.mark.asyncio
async def test_get_current_user_user_not_found_raises(monkeypatch):
    user_id = UUID("12345678-1234-5678-1234-567812345678")
    
    def fake_decode(token: str):
        return {"sub": user_id}

    class FakeRepo:
        def __init__(self, session):
            self.session = session

        async def get_by_id(self, uid: UUID):
            assert uid == user_id
            return None

    monkeypatch.setattr(deps_module, "decode_access_token", fake_decode)
    monkeypatch.setattr(deps_module, "UserRepository", FakeRepo)
    
    session=make_fake_session() 
    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(acces_token="something", session=session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found"
import pytest
from app.repositories.user_repository import UserRepository
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_create_and_get_user(session_factory):
    async with session_factory() as db_session:
        repo = UserRepository(db_session)

        user = await repo.create("test_provider", "provider_id_1", "alice@example.test", "username_alice", None)

        fetched = await repo.get_by_email("alice@example.test")

        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.email == "alice@example.test"

@pytest.mark.asyncio
async def test_email_unique_constraint(session_factory):
    async with session_factory() as db_session:
        repo = UserRepository(db_session)

        await repo.create(provider="test_provider", provider_id="provider_id_1", email="dup@example.com", username="dup1", avatar_url=None)
        # second create with same email should raise IntegrityError (unique constraint)
        with pytest.raises(IntegrityError):
            await repo.create(provider="test_provider", provider_id="provider_id_2", email="dup@example.com", username="dup2", avatar_url=None)
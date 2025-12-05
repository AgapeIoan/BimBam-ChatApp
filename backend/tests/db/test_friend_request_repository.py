import pytest
from sqlalchemy.exc import IntegrityError
from app.repositories.user_repository import UserRepository
from app.repositories.friend_request_repository import FriendRequestRepository


@pytest.mark.asyncio
async def test_create_and_query_friend_request(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        fr_repo = FriendRequestRepository(db_session)

        a = await user_repo.create("test_provider", "provider_id_a", "a@test", "username_a", None)
        b = await user_repo.create("test_provider", "provider_id_b", "b@test", "username_b", None)

        fr = await fr_repo.create_friend_request(a.id, b.id)

        fetched = await fr_repo.get_friend_request(a.id, b.id)
        assert fetched is not None
        assert fetched.id == fr.id

        incoming = await fr_repo.get_incoming_requests(b.id)
        assert len(incoming) == 1

@pytest.mark.asyncio
async def test_duplicate_friend_request_violates_unique(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        fr_repo = FriendRequestRepository(db_session)

        a = await user_repo.create("test_provider", "provider_id_da", "da@test", "username_da", None)
        b = await user_repo.create("test_provider", "provider_id_db", "db@test", "username_db", None)

        await fr_repo.create_friend_request(a.id, b.id)
        # second attempt should raise IntegrityError due to UniqueConstraint
        with pytest.raises(IntegrityError):
            await fr_repo.create_friend_request(a.id, b.id)

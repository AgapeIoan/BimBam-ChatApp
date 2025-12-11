import pytest
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_create_friendship_pair_and_query(session_factory):
    async with session_factory() as db_session:
        user_repo = UserRepository(db_session)
        fs_repo = FriendshipRepository(db_session)

        u1 = await user_repo.create("test_provider", "provider_id_f1", "f1@test", "username_f1", None)
        u2 = await user_repo.create("test_provider", "provider_id_f2", "f2@test", "username_f2", None)

        f1, f2 = await fs_repo.create_friendship_pair(u1.id, u2.id)

        assert f1.user_id == u1.id
        assert f2.user_id == u2.id

        assert await fs_repo.are_friends(u1.id, u2.id)
        assert await fs_repo.are_friends(u2.id, u1.id)
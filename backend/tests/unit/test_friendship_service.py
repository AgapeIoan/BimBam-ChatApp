from typing import Dict, Tuple, cast
from uuid import UUID

import pytest

from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository
from app.services.friendship_service import FriendshipService


class FakeRepo:
    def __init__(self, friend_map: Dict[Tuple[str, str], bool]):
        """
        friend_map: dict[(user_id, friend_id)] -> bool
        We'll store UUIDs as strings to keep things hashable and simple.
        """
        self.friend_map = friend_map

    async def are_friends(self, user_id, friend_id):
        key = (str(user_id), str(friend_id))
        return self.friend_map.get(key, False)

    async def get_friends(self, user_id):
        # Not used in this test
        return []


class FakeUserRepo:
    async def get_by_id(self, user_id):
        # Minimal object with attributes needed by FriendshipService.get_friends
        return type(
            "User",
            (),
            {
                "id": user_id,
                "email": "x@example.com",
                "username": "x",
            },
        )()


@pytest.mark.asyncio
async def test_are_friends_true_and_false():
    u1 = UUID("00000000-0000-0000-0000-000000000001")
    u2 = UUID("00000000-0000-0000-0000-000000000002")
    u3 = UUID("00000000-0000-0000-0000-000000000003")

    friend_map = {
        (str(u1), str(u2)): True,
        (str(u2), str(u1)): True,
    }

    fake_repo = FakeRepo(friend_map)
    fake_user_repo = FakeUserRepo()

    service = FriendshipService(
        cast(FriendshipRepository, fake_repo),
        cast(UserRepository, fake_user_repo),
    )

    assert await service.are_friends(u1, u2) is True
    assert await service.are_friends(u1, u3) is False

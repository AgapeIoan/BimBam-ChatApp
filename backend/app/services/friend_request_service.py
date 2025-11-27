from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.friendship_repository import FriendshipRepository
from repositories.friend_request_repository import FriendRequestRepository
from repositories.user_repository import UserRepository
from models.enums import FriendRequestStatus


class FriendRequestService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def send_friend_request(
        self,
        from_user_id: int,
        to_email: str,
    ):
        user_repo = UserRepository(self._session)
        user_to = await user_repo.get_by_email(to_email)
        if not user_to:
            raise HTTPException(404, "User not found")
        to_user_id = user_to.id
        if from_user_id == to_user_id:
            raise HTTPException(400, "Cannot send request to yourself")
        friendship_repo = FriendshipRepository(self._session)
        if await friendship_repo.are_friends(from_user_id, to_user_id):
            raise HTTPException(400, "You are already friends")
        fr_repo = FriendRequestRepository(self._session)
        existing = await fr_repo.get_friend_request(from_user_id, to_user_id)
        if existing:
            raise HTTPException(400, "Friend request already sent")
        return await fr_repo.create_friend_request(from_user_id, to_user_id)

    async def accept_friend_request(self, request_id: int, current_user_id: int):
        fr_repo = FriendRequestRepository(self._session)
        fr = await fr_repo.get_friend_request_by_id(request_id)
        if not fr or fr.to_user_id != current_user_id:
            raise HTTPException(404, "Friend request not found")
        if fr.status != FriendRequestStatus.PENDING:
            raise HTTPException(400, "Friend request is not pending")
        await fr_repo.update_friend_request_status(fr, FriendRequestStatus.ACCEPTED)
        friendship_repo = FriendshipRepository(self._session)
        await friendship_repo.create_friendship_pair(fr.from_user_id, fr.to_user_id)
        return fr

    async def decline_friend_request(self, request_id: int, current_user_id: int):
        fr_repo = FriendRequestRepository(self._session)
        fr = await fr_repo.get_friend_request_by_id(request_id)
        if not fr or fr.to_user_id != current_user_id:
            raise HTTPException(404, "Friend request not found")
        if fr.status != FriendRequestStatus.PENDING:
            raise HTTPException(400, "Friend request is not pending")
        return await fr_repo.update_friend_request_status(fr, FriendRequestStatus.DECLINED)

    async def incoming_requests(self, user_id: int):
        fr_repo = FriendRequestRepository(self._session)
        return await fr_repo.get_incoming_requests(user_id)

    async def outgoing_requests(self, user_id: int):
        fr_repo = FriendRequestRepository(self._session)
        return await fr_repo.get_outgoing_requests(user_id)

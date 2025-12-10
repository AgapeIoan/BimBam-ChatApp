from uuid import UUID

from fastapi import HTTPException

from app.models.enums import FriendRequestStatus
from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository


class FriendRequestService:
    def __init__(
        self,
        user_repo: UserRepository,
        friendship_repo: FriendshipRepository,
        friend_request_repo: FriendRequestRepository,
    ):
        self.user_repo = user_repo
        self.friendship_repo = friendship_repo
        self.friend_request_repo = friend_request_repo

    async def send_friend_request(
        self,
        from_user_id: UUID,
        to_email: str,
    ):
        user_to = await self.user_repo.get_by_email(to_email)
        if not user_to:
            raise HTTPException(404, "User not found")

        to_user_id = user_to.id

        if from_user_id == to_user_id:
            raise HTTPException(400, "Cannot send request to yourself")

        if await self.friendship_repo.are_friends(from_user_id, to_user_id):
            raise HTTPException(400, "You are already friends")

        existing = await self.friend_request_repo.get_friend_request(
            from_user_id, to_user_id
        )
        if existing:
            raise HTTPException(400, "Friend request already sent")

        return await self.friend_request_repo.create_friend_request(
            from_user_id, to_user_id
        )

    async def accept_friend_request(self, request_id: UUID, current_user_id: UUID):
        fr = await self.friend_request_repo.get_friend_request_by_id(request_id)

        if not fr or fr.to_user_id != current_user_id:
            raise HTTPException(404, "Friend request not found")

        if fr.status != FriendRequestStatus.PENDING:
            raise HTTPException(400, "Friend request is not pending")

        await self.friend_request_repo.update_friend_request_status(
            fr, FriendRequestStatus.ACCEPTED
        )
        await self.friendship_repo.create_friendship_pair(
            fr.from_user_id, fr.to_user_id
        )
        return fr

    async def decline_friend_request(self, request_id: UUID, current_user_id: UUID):
        fr = await self.friend_request_repo.get_friend_request_by_id(request_id)

        if not fr or fr.to_user_id != current_user_id:
            raise HTTPException(404, "Friend request not found")

        if fr.status != FriendRequestStatus.PENDING:
            raise HTTPException(400, "Friend request is not pending")

        return await self.friend_request_repo.update_friend_request_status(
            fr, FriendRequestStatus.DECLINED
        )

    async def incoming_requests(self, user_id: UUID):
        return await self.friend_request_repo.get_incoming_requests(user_id)

    async def outgoing_requests(self, user_id: UUID):
        return await self.friend_request_repo.get_outgoing_requests(user_id)

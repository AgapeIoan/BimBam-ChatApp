from uuid import UUID

from app.models.enums import FriendRequestStatus
from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.friendship_repository import FriendshipRepository
from app.repositories.user_repository import UserRepository
from app.schemas.friend_request.friend_request_response import FriendRequestResponse
from app.schemas.user.user_response import UserResponse
from app.utils.errors.resource_not_found import ResourceNotFoundException
from app.utils.errors.user_not_found_exception import UserNotFoundException
from app.utils.errors.validation_exception import ValidationException


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

    FRIEND_REQUEST_NOT_FOUND = "Friend request not found"
    FRIEND_REQUEST_NOT_PENDING = "Friend request is not pending"

    def _map_to_friend_request_response(self, fr):
        response = FriendRequestResponse(
            id=fr.id,
            status=fr.status,
            createdAt=fr.created_at,
            fromUser=UserResponse(
                email=fr.sender.email,
                username=fr.sender.username,
                avatarUrl=fr.sender.avatar_url,
            ),
            toUser=UserResponse(
                email=fr.receiver.email,
                username=fr.receiver.username,
                avatarUrl=fr.receiver.avatar_url,
            ),
        )
        return response

    async def send_friend_request(
        self,
        from_user_id: UUID,
        to_email: str,
    ):
        user_to = await self.user_repo.get_by_email(to_email)
        if not user_to:
            raise UserNotFoundException(
                "The user you are trying to send a friend request to does not exist"
            )

        to_user_id = user_to.id

        if from_user_id == to_user_id:
            raise ValidationException("You cannot send a friend request to yourself")

        if await self.friendship_repo.are_friends(from_user_id, to_user_id):
            raise ValidationException("You are already friends")

        existing = await self.friend_request_repo.get_friend_request(
            from_user_id, to_user_id
        )
        if existing:
            if existing.status in [
                FriendRequestStatus.PENDING,
                FriendRequestStatus.ACCEPTED,
            ]:
                raise ValidationException("Friend request already sent or accepted")
            await self.friend_request_repo.delete_friend_request(existing.id)

        reverse = await self.friend_request_repo.get_friend_request(
            to_user_id, from_user_id
        )
        if reverse and reverse.status in [
            FriendRequestStatus.PENDING,
            FriendRequestStatus.ACCEPTED,
        ]:
            raise ValidationException(
                "The target user has already sent you a friend request"
            )

        result = await self.friend_request_repo.create_friend_request(
            from_user_id, to_user_id
        )
        return self._map_to_friend_request_response(result)

    async def accept_friend_request(self, request_id: UUID, current_user_id: UUID):
        fr = await self.friend_request_repo.get_friend_request_by_id(request_id)

        if not fr or fr.to_user_id != current_user_id:
            raise ResourceNotFoundException(self.FRIEND_REQUEST_NOT_FOUND)

        if fr.status != FriendRequestStatus.PENDING:
            raise ValidationException(self.FRIEND_REQUEST_NOT_PENDING)

        await self.friend_request_repo.update_friend_request_status(
            fr, FriendRequestStatus.ACCEPTED
        )
        await self.friendship_repo.create_friendship_pair(
            fr.from_user_id, fr.to_user_id
        )
        return self._map_to_friend_request_response(fr)

    async def decline_friend_request(self, request_id: UUID, current_user_id: UUID):
        fr = await self.friend_request_repo.get_friend_request_by_id(request_id)

        if not fr or fr.to_user_id != current_user_id:
            raise ResourceNotFoundException(self.FRIEND_REQUEST_NOT_FOUND)

        if fr.status != FriendRequestStatus.PENDING:
            raise ValidationException(self.FRIEND_REQUEST_NOT_PENDING)

        result = await self.friend_request_repo.update_friend_request_status(
            fr, FriendRequestStatus.DECLINED
        )
        return self._map_to_friend_request_response(result)

    async def cancel_friend_request(self, request_id: UUID, current_user_id: UUID):
        fr = await self.friend_request_repo.get_friend_request_by_id(request_id)

        if not fr or fr.from_user_id != current_user_id:
            raise ResourceNotFoundException(self.FRIEND_REQUEST_NOT_FOUND)

        if fr.status != FriendRequestStatus.PENDING:
            raise ValidationException(self.FRIEND_REQUEST_NOT_PENDING)

        result = await self.friend_request_repo.update_friend_request_status(
            fr, FriendRequestStatus.CANCELLED
        )
        return self._map_to_friend_request_response(result)

    async def incoming_requests(self, user_id: UUID):
        result = await self.friend_request_repo.get_incoming_requests(user_id)
        return [self._map_to_friend_request_response(fr) for fr in result]

    async def outgoing_requests(self, user_id: UUID):
        result = await self.friend_request_repo.get_outgoing_requests(user_id)
        return [self._map_to_friend_request_response(fr) for fr in result]

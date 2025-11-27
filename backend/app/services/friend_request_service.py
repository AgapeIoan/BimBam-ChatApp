from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories.friendship_repository import FriendshipRepository
from repositories.friend_request_repository import FriendRequestRepository
from repositories.user_repository import UserRepository
from models.enums import FriendRequestStatus


class FriendRequestService:

    @staticmethod
    def send_friend_request(
        db: Session,
        from_user_id: int,
        to_email: str,
    ):

        user_to = UserRepository.get_by_email(db, to_email)
        if not user_to:
            raise HTTPException(404, "User not found")

        to_user_id = user_to.id

        if from_user_id == to_user_id:
            raise HTTPException(400, "Cannot send request to yourself")

        if FriendshipRepository.are_friends(db, from_user_id, to_user_id):
            raise HTTPException(400, "You are already friends")

        existing = FriendRequestRepository.get_friend_request(
            db, from_user_id, to_user_id
        )
        if existing:
            raise HTTPException(400, "Friend request already sent")

        return FriendRequestRepository.create_friend_request(
            db, from_user_id, to_user_id
        )


    @staticmethod
    def accept_friend_request(db: Session, request_id: int, current_user_id: int):

        fr = FriendRequestRepository.get_friend_request_by_id(db, request_id)

        if not fr or fr.to_user_id != current_user_id:
            raise HTTPException(404, "Friend request not found")

        if fr.status != FriendRequestStatus.PENDING:
            raise HTTPException(400, "Friend request is not pending")

        FriendRequestRepository.update_friend_request_status(
            db, fr, FriendRequestStatus.ACCEPTED
        )

        # Create 2-way friendship
        FriendshipRepository.create_friendship_pair(
            db, fr.from_user_id, fr.to_user_id
        )

        return fr

    @staticmethod
    def decline_friend_request(db: Session, request_id: int, current_user_id: int):
        fr = FriendRequestRepository.get_friend_request_by_id(db, request_id)

        if not fr or fr.to_user_id != current_user_id:
            raise HTTPException(404, "Friend request not found")

        if fr.status != FriendRequestStatus.PENDING:
            raise HTTPException(400, "Friend request is not pending")

        return FriendRequestRepository.update_friend_request_status(
            db, fr, FriendRequestStatus.DECLINED
        )

    @staticmethod
    def incoming_requests(db: Session, user_id: int):
        return FriendRequestRepository.get_incoming_requests(db, user_id)

    @staticmethod
    def outgoing_requests(db: Session, user_id: int):
        return FriendRequestRepository.get_outgoing_requests(db, user_id)

from sqlalchemy.orm import Session
from typing import List, Optional

from models.friend_request import FriendRequest
from models.enums import FriendRequestStatus


class FriendRequestRepository:

    @staticmethod
    def get_friend_request_by_id(db: Session, request_id: int) -> Optional[FriendRequest]:
        return (
            db.query(FriendRequest)
            .filter(FriendRequest.id == request_id)
            .one_or_none()
        )

    @staticmethod
    def get_friend_request(
        db: Session,
        from_user_id: int,
        to_user_id: int,
    ) -> Optional[FriendRequest]:
        return (
            db.query(FriendRequest)
            .filter(
                FriendRequest.from_user_id == from_user_id,
                FriendRequest.to_user_id == to_user_id,
            )
            .one_or_none()
        )

    @staticmethod
    def create_friend_request(
        db: Session,
        from_user_id: int,
        to_user_id: int,
    ) -> FriendRequest:
        fr = FriendRequest(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status=FriendRequestStatus.PENDING,
        )
        db.add(fr)
        db.commit()
        db.refresh(fr)
        return fr

    @staticmethod
    def update_friend_request_status(
        db: Session,
        fr: FriendRequest,
        status: FriendRequestStatus,
    ) -> FriendRequest:
        fr.status = status
        db.commit()
        db.refresh(fr)
        return fr

    @staticmethod
    def get_incoming_requests(
        db: Session,
        user_id: int,
    ) -> List[FriendRequest]:
        return (
            db.query(FriendRequest)
            .filter(
                FriendRequest.to_user_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
            .order_by(FriendRequest.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_outgoing_requests(
        db: Session,
        user_id: int,
    ) -> List[FriendRequest]:
        return (
            db.query(FriendRequest)
            .filter(
                FriendRequest.from_user_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
            .order_by(FriendRequest.created_at.desc())
            .all()
        )



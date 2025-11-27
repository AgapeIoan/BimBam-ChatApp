from sqlalchemy.orm import Session
from typing import List

from models.friendship import Friendship


class FriendshipRepository:

    @staticmethod
    def are_friends(
        db: Session,
        user_id: int,
        friend_id: int,
    ) -> bool:
        row = (
            db.query(Friendship)
            .filter(
                Friendship.user_id == user_id,
                Friendship.friend_id == friend_id,
            )
            .one_or_none()
        )
        return row is not None

    @staticmethod
    def create_friendship_pair(
        db: Session,
        user_a: int,
        user_b: int,
    ):

        f1 = Friendship(user_id=user_a, friend_id=user_b)
        f2 = Friendship(user_id=user_b, friend_id=user_a)
        db.add_all([f1, f2])
        db.commit()
        return f1, f2

    @staticmethod
    def get_friends(db: Session, user_id: int) -> List[Friendship]:
        return (
            db.query(Friendship)
            .filter(Friendship.user_id == user_id)
            .order_by(Friendship.created_at.desc())
            .all()
        )

from sqlalchemy.orm import Session
from models.user import User


class UserRepository:

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).one_or_none()

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).one_or_none()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).one_or_none()

    @staticmethod
    def get_by_provider_id(db: Session, provider: str, provider_id: str) -> User | None:
        return (
            db.query(User)
              .filter(User.provider == provider)
              .filter(User.provider_id == provider_id)
              .one_or_none()
        )

    @staticmethod
    def create(db: Session, provider: str, provider_id: str, email: str, username: str, avatar_url: str | None) -> User:
        user = User(
            provider=provider,
            provider_id=provider_id,
            email=email,
            username=username,
            avatar_url=avatar_url
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_last_seen(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).one()
        from datetime import datetime
        user.last_seen = datetime.now()
        db.commit()
        return user

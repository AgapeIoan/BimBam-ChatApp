from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from core.redis_client import set_user_online, set_user_offline


class UserService:

    @staticmethod
    def get_by_id(db: Session, user_id: int):
        return UserRepository.get_by_id(db, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str):
        return UserRepository.get_by_email(db, email)
    
    @staticmethod
    def get_by_username(db: Session, username: str):
        return UserRepository.get_by_username(db, username)

    @staticmethod
    def login_or_register(db: Session, provider: str, provider_id: str, email: str, username: str, avatar_url: str | None):
        user = UserRepository.get_by_provider_id(db, provider, provider_id)
        if user:
            return user
        return UserRepository.create(db, provider, provider_id, email, username, avatar_url)
    
    @staticmethod
    async def set_online(user_id: int):
        await set_user_online(user_id)

    @staticmethod
    async def set_offline(user_id: int, db: Session):
        UserRepository.update_last_seen(db, user_id)
        await set_user_offline(user_id)

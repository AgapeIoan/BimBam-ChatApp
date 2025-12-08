from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.utils.jwt_utils import decode_access_token


async def get_current_user(acces_token: str = Cookie(default=None, alias="access_token"), session: AsyncSession = Depends(get_async_session)):
    if not acces_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    payload = decode_access_token(acces_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user

def get_user_service(session: AsyncSession = Depends(get_async_session)) -> UserService:
    repo = UserRepository(session)
    return UserService(repo)

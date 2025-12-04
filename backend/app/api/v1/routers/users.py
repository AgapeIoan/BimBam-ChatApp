from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.deps import get_current_user
from app.db.session import get_async_session
from app.models.user import User

import re

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me/username")

async def update_username(new_username: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    new_username = new_username.strip()

    if len(new_username) < 3 or not new_username.isalnum():
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long and alphanumeric.")
    
    if not re.match(r"^[a-zA-Z0-9_]+$", new_username):
        raise HTTPException(status_code=400, detail="Invalid username")

    result = await session.execute(select(User).where(User.username == new_username))
    existing_user = result.scalars().first()
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Username is already taken.")
    
    current_user.username = new_username
    await session.flush()
    await session.refresh(current_user)  

    return {"username": current_user.username}
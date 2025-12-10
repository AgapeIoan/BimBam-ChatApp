from fastapi import APIRouter, Depends, Query
from typing import List

from app.api.v1.deps import get_current_user, get_user_service
from app.models.user import User
from app.schemas.user.user_response import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me/username")
async def update_username(
    new_username: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    username = await user_service.update_username(current_user, new_username)
    return {"username": username}


@router.get(
    "/users/search-by-email",
    response_model=List[UserResponse],
    dependencies=[Depends(get_current_user)],
)
async def search_by_email(
    query: str = Query(..., min_length=1, alias="q"),
    user_service: UserService = Depends(get_user_service),
):
    users = await user_service.search_users_by_email(query)
    if not users:
        return []
    return users


@router.get(
    "/users/search-by-username",
    response_model=List[UserResponse],
    dependencies=[Depends(get_current_user)],
)
async def search_by_username(
    query: str = Query(..., min_length=1, alias="q"),
    user_service: UserService = Depends(get_user_service),
):
    users = await user_service.search_user_by_username(query)
    if not users:
        return []
    return users

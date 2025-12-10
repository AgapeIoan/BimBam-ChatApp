from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.deps import get_current_user, get_user_service
from app.models.user import User
from app.schemas.user.user_read import UserRead
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


@router.get("/search", response_model=list[UserRead])
async def search_users(
    query: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    try:
        users = await user_service.search_users(query, exclude_user_id=current_user.id, limit=20)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return [UserRead.model_validate(u) for u in users]

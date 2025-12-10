from app.api.v1.deps import get_current_user, get_user_service
from app.models.user import User
from app.services.user_service import UserService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me/username")

async def update_username(
    new_username: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    username = await user_service.update_username(current_user, new_username)
    return {"username": username}
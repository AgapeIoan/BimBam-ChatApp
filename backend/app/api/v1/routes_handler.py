from fastapi import APIRouter
from app.api.v1.routers import auth
from app.api.v1.routers import users
from app.api.v1.routers import friend_request

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(friend_request.router)

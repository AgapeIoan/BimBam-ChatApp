from fastapi import APIRouter

from app.api.v1.routers import auth, conversations_router, debug_router, users, friends

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(conversations_router.router)
api_router.include_router(debug_router.router)
api_router.include_router(friends.router)  

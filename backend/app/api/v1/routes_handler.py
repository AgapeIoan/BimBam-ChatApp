from fastapi import APIRouter

from app.api.v1.routers.conversations_router import router as conversations_router
from app.api.v1.routers.debug_router import router as debug_router

router = APIRouter()

router.include_router(conversations_router)

router.include_router(debug_router)

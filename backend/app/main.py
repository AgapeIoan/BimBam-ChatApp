import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from starlette.middleware.sessions import SessionMiddleware
except Exception:  # pragma: no cover - optional dependency in some test environments
    SessionMiddleware = None

from app.api.v1 import ws
from app.api.v1.routes_handler import api_router
from app.core.config import get_settings
from app.db.init_db import init_db

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    skip = os.getenv("SKIP_DB_INIT_ON_STARTUP", "").lower() in {"1", "true", "yes"}
    if not skip:
        await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.AUTH.JWT_SECRET_KEY,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.AUTH.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(ws.router)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

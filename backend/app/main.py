import os

from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .core.config import get_settings
from .api.v1.routes_handler import api_router

app = FastAPI()
settings = get_settings()

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

@app.on_event("startup")
async def startup_event():
    skip = os.getenv("SKIP_DB_INIT_ON_STARTUP", "").lower() in {"1", "true", "yes"}
    if skip:
        return

    await init_db()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(ws.router)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

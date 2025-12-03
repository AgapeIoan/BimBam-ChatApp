import os

from fastapi import FastAPI
import uvicorn

from .core.config import get_settings
from .api.v1 import ws
from app.db.init_db import init_db

app = FastAPI()
settings = get_settings()


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

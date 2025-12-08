import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.v1 import ws
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    skip = os.getenv("SKIP_DB_INIT_ON_STARTUP", "").lower() in {"1", "true", "yes"}
    if not skip:
        await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(ws.router)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

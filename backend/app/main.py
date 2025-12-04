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

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

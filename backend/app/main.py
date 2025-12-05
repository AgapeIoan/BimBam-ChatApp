from fastapi import FastAPI
import uvicorn
from .core.config import get_settings
from backend.app.api.v1.routes_handler import router as api_router

app = FastAPI()
settings = get_settings()

# Mount API v1 routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI
import uvicorn
from .core.config import get_settings

app = FastAPI()
settings = get_settings()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

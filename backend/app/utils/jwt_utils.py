from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt, JWTError

from app.core.config import get_settings

settings = get_settings()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.AUTH.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.AUTH.JWT_SECRET_KEY, algorithm=settings.AUTH.JWT_ALGORITHM)
   
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.AUTH.JWT_SECRET_KEY, algorithms=[settings.AUTH.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
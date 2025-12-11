import logging
from typing import Optional
from uuid import UUID

import jwt
from fastapi import WebSocket, status
from fastapi.exceptions import WebSocketException
from jwt import InvalidTokenError

import app.db.session as session_module
from app.core.config import get_settings
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
settings = get_settings()


def _extract_token(websocket: WebSocket) -> Optional[str]:
    """
    Try to locate the JWT provided by the user for WebSocket auth.

    Priority order:
    1) Explicit query param (?token=...)
    2) Authorization header (Bearer ...)
    3) access_token cookie (so HttpOnly session cookies work over WS)
    """
    token = websocket.query_params.get("token")
    auth_header = websocket.headers.get("Authorization")

    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return auth_header

    if token:
        return token

    # Fallback to session cookie so clients with HttpOnly cookies can connect without exposing the token to JS
    return websocket.cookies.get("access_token")


async def websocket_auth(
    websocket: WebSocket,
):
    token = _extract_token(websocket)
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    try:
        payload = jwt.decode(token, settings.AUTH.JWT_SECRET_KEY, algorithms=[settings.AUTH.JWT_ALGORITHM])
    except InvalidTokenError as exc:
        logger.warning("Invalid websocket token: %s", exc)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload"
        )

    try:
        user_id = UUID(str(user_id_raw))
    except ValueError:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token subject"
        )

    async with session_module.AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")

    return user

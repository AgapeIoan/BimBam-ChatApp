import asyncio
import logging
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """In-memory manager for active websocket connections keyed by user id."""

    def __init__(self) -> None:
        self._connections: Dict[UUID, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def add(self, user_id: UUID, websocket: WebSocket) -> None:
        """Register an accepted websocket for a user."""
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)
            logger.debug("WebSocket added for user %s (total=%s)", user_id, len(self._connections[user_id]))

    async def remove(self, user_id: UUID, websocket: WebSocket) -> None:
        """Remove a websocket for a user; cleanup empty buckets."""
        async with self._lock:
            sockets = self._connections.get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(user_id, None)
            logger.debug("WebSocket removed for user %s (remaining=%s)", user_id, len(sockets) if sockets else 0)

    async def disconnect_all(self, user_id: UUID) -> None:
        """Forcefully drop all sockets for a user."""
        async with self._lock:
            sockets = self._connections.pop(user_id, set())
        for ws in sockets:
            try:
                await ws.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error closing websocket for user %s: %s", user_id, exc)

    async def get_connections(self, user_id: UUID) -> Set[WebSocket]:
        """Return a shallow copy of active sockets for a user."""
        async with self._lock:
            sockets = self._connections.get(user_id, set()).copy()
        return sockets

    async def has_connections(self, user_id: UUID) -> bool:
        """Check if user has any active sockets."""
        async with self._lock:
            return user_id in self._connections and bool(self._connections[user_id])

    async def send_to_user(self, user_id: UUID, message) -> bool:
        """
        Send a payload to all active sockets for the user.
        Returns True if at least one send succeeds.
        """
        # Serialize UUIDs and other non-JSON-native types defensively
        serialized = None
        try:
            serialized = json.dumps(message, default=str)
        except TypeError:
            logger.warning("Failed to serialize message for user %s", user_id)
            return False

        sockets = await self.get_connections(user_id)
        if not sockets:
            return False

        delivered = False
        dead_sockets: Set[WebSocket] = set()

        for ws in sockets:
            try:
                if hasattr(ws, "send_text"):
                    await ws.send_text(serialized)
                    delivered = True
                else:
                    # Fallback for test doubles
                    await ws.send_json(json.loads(serialized))
                    delivered = True
            except WebSocketDisconnect:
                dead_sockets.add(ws)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error sending message to user %s websocket: %s", user_id, exc)
                dead_sockets.add(ws)

        # Cleanup dead sockets
        if dead_sockets:
            async with self._lock:
                active = self._connections.get(user_id, set())
                for ws in dead_sockets:
                    active.discard(ws)
                if not active:
                    self._connections.pop(user_id, None)

        return delivered

    async def broadcast(self, user_ids: Set[UUID], message) -> None:
        """Broadcast payload to a set of user ids."""
        for uid in user_ids:
            await self.send_to_user(uid, message)

    async def all_user_ids(self) -> Set[UUID]:
        """Return all user IDs that currently have active connections."""
        async with self._lock:
            return set(self._connections.keys())


# Singleton instance
connection_manager = ConnectionManager()

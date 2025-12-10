from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.enums import FriendRequestStatus
from app.models.friend_request import FriendRequest


class FriendRequestRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_friend_request_by_id(
        self, request_id: UUID
    ) -> Optional[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest)
            .options(
                joinedload(FriendRequest.sender),
                joinedload(FriendRequest.receiver),
            )
            .where(FriendRequest.id == request_id)
        )
        return result.scalars().one_or_none()

    async def get_friend_request(
        self,
        from_user_id: UUID,
        to_user_id: UUID,
    ) -> Optional[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest)
            .options(
                joinedload(FriendRequest.sender),
                joinedload(FriendRequest.receiver),
            )
            .where(
                FriendRequest.from_user_id == from_user_id,
                FriendRequest.to_user_id == to_user_id,
            )
        )
        return result.scalars().one_or_none()

    async def create_friend_request(
        self,
        from_user_id: UUID,
        to_user_id: UUID,
    ) -> FriendRequest:
        fr = FriendRequest(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status=FriendRequestStatus.PENDING,
        )
        self._session.add(fr)
        await self._session.flush()
        await self._session.refresh(fr)
        return await self.get_friend_request_by_id(fr.id)

    async def update_friend_request_status(
        self,
        fr: FriendRequest,
        status: FriendRequestStatus,
    ) -> FriendRequest:
        fr.status = status
        await self._session.flush()
        await self._session.refresh(fr)
        return fr

    async def get_incoming_requests(
        self,
        user_id: UUID,
    ) -> List[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest)
            .options(
                joinedload(FriendRequest.sender),
                joinedload(FriendRequest.receiver),
            )
            .where(
                FriendRequest.to_user_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
            .order_by(FriendRequest.created_at.desc())
        )
        return result.scalars().all()

    async def get_outgoing_requests(
        self,
        user_id: UUID,
    ) -> List[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest)
            .options(
                joinedload(FriendRequest.sender),
                joinedload(FriendRequest.receiver),
            )
            .where(
                FriendRequest.from_user_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
            .order_by(FriendRequest.created_at.desc())
        )
        return result.scalars().all()

    async def delete_friend_request(self, request_id: UUID) -> None:
        fr = await self.get_friend_request_by_id(request_id)
        if fr:
            await self._session.delete(fr)
            await self._session.flush()
        return None

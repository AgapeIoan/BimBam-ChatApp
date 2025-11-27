from typing import List, Optional
from models.friend_request import FriendRequest
from models.enums import FriendRequestStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class FriendRequestRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_friend_request_by_id(self, db: AsyncSession, request_id: int) -> Optional[FriendRequest]:
        result = await db.execute(select(FriendRequest).where(FriendRequest.id == request_id))
        return result.scalars().one_or_none()

    async def get_friend_request(
        self,
        from_user_id: int,
        to_user_id: int,
    ) -> Optional[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest).where(
                FriendRequest.from_user_id == from_user_id,
                FriendRequest.to_user_id == to_user_id,
            )
        )
        return result.scalars().one_or_none()


    async def create_friend_request(          
        self,
        from_user_id: int,
        to_user_id: int,
    ) -> FriendRequest:
        fr = FriendRequest(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status=FriendRequestStatus.PENDING,
        )
        self._session.add(fr)
        await self._session.commit()
        await self._session.refresh(fr)
        return fr

    async def update_friend_request_status(
        self,
        fr: FriendRequest,
        status: FriendRequestStatus,
    ) -> FriendRequest:
        fr.status = status
        await self._session.commit()
        await self._session.refresh(fr)
        return fr

    async def get_incoming_requests(
        self,
        user_id: int,
    ) -> List[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest)
            .where(
                FriendRequest.to_user_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
            .order_by(FriendRequest.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_outgoing_requests(
        self,
        user_id: int,
    ) -> List[FriendRequest]:
        result = await self._session.execute(
            select(FriendRequest)
            .where(
                FriendRequest.from_user_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
            .order_by(FriendRequest.created_at.desc())
        )
        return result.scalars().all()



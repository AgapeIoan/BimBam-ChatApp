from uuid import UUID

from app.api.v1.deps import get_current_user, get_friend_request_service
from app.schemas.friend_request.friend_request_create import \
    FriendRequestCreate
from app.schemas.friend_request.friend_request_response import \
    FriendRequestResponse
from app.services.friend_request_service import FriendRequestService
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/friend-requests",
    tags=["friend-requests"],
)


@router.post("", status_code=201, response_model=FriendRequestResponse)
async def send_friend_request(
    payload: FriendRequestCreate,
    current_user=Depends(get_current_user),
    friend_request_service: FriendRequestService = Depends(get_friend_request_service),
):
    """
    Send a friend request to a user by email (payload.toEmail).
    """
    fr = await friend_request_service.send_friend_request(
        from_user_id=current_user.id,
        to_email=payload.to_email,
    )
    return fr


@router.post(
    "/{request_id}/accept", status_code=201, response_model=FriendRequestResponse
)
async def accept_friend_request(
    request_id: UUID,
    current_user=Depends(get_current_user),
    friend_request_service: FriendRequestService = Depends(get_friend_request_service),
):
    """
    Accept an incoming friend request.
    """
    fr = await friend_request_service.accept_friend_request(
        request_id=request_id,
        current_user_id=current_user.id,
    )
    return fr


@router.post("/{request_id}/decline", response_model=FriendRequestResponse)
async def decline_friend_request(
    request_id: UUID,
    current_user=Depends(get_current_user),
    friend_request_service: FriendRequestService = Depends(get_friend_request_service),
):
    """
    Decline an incoming friend request.
    """
    fr = await friend_request_service.decline_friend_request(
        request_id=request_id,
        current_user_id=current_user.id,
    )
    return fr


@router.post("/{request_id}/cancel", response_model=FriendRequestResponse)
async def cancel_friend_request(
    request_id: UUID,
    current_user=Depends(get_current_user),
    friend_request_service: FriendRequestService = Depends(get_friend_request_service),
):
    """
    Cancel an outgoing friend request that the current user has sent.
    """
    fr = await friend_request_service.cancel_friend_request(
        request_id=request_id,
        current_user_id=current_user.id,
    )
    return fr


@router.get("/incoming", response_model=list[FriendRequestResponse])
async def list_incoming_friend_requests(
    current_user=Depends(get_current_user),
    friend_request_service: FriendRequestService = Depends(get_friend_request_service),
):
    """
    List pending friend requests received by the current user.
    """
    requests = await friend_request_service.incoming_requests(user_id=current_user.id)
    return requests


@router.get("/outgoing", response_model=list[FriendRequestResponse])
async def list_outgoing_friend_requests(
    current_user=Depends(get_current_user),
    friend_request_service: FriendRequestService = Depends(get_friend_request_service),
):
    """
    List pending friend requests sent by the current user.
    """
    requests = await friend_request_service.outgoing_requests(user_id=current_user.id)
    return requests

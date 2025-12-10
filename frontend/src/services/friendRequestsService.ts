import type {
  FriendRequestApi,
} from "../types/friendRequests/friendRequestApi";
import { apiClient } from "./apiClient";

const FRIEND_REQUESTS_BASE = "/api/v1/friend-requests";

export async function sendFriendRequest(
  toEmail: string
): Promise<FriendRequestApi> {
  return apiClient.post<FriendRequestApi>(FRIEND_REQUESTS_BASE, {
    toEmail,
  });
}

export async function acceptFriendRequest(
  requestId: string
): Promise<FriendRequestApi> {
  return apiClient.post<FriendRequestApi>(
    `${FRIEND_REQUESTS_BASE}/${requestId}/accept`,
    null
  );
}

export async function declineFriendRequest(
  requestId: string
): Promise<FriendRequestApi> {
  return apiClient.post<FriendRequestApi>(
    `${FRIEND_REQUESTS_BASE}/${requestId}/decline`,
    null
  );
}

export async function cancelFriendRequest(
  requestId: string
): Promise<FriendRequestApi> {
  return apiClient.post<FriendRequestApi>(
    `${FRIEND_REQUESTS_BASE}/${requestId}/cancel`,
    null
  );
}

export async function listIncomingRequests(): Promise<FriendRequestApi[]> {
  return apiClient.get<FriendRequestApi[]>(`${FRIEND_REQUESTS_BASE}/incoming`);
}

export async function listOutgoingRequests(): Promise<FriendRequestApi[]> {
  return apiClient.get<FriendRequestApi[]>(`${FRIEND_REQUESTS_BASE}/outgoing`);
}

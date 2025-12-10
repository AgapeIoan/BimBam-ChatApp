

import type { FriendRequestApi, UserSearchResult } from "../types/friendRequests";
import { mockUsers } from "../mock_data/mockUsers";

const API_BASE = "http://localhost:8000/api/v1/friend-requests";

export async function sendFriendRequest(toEmail: string): Promise<FriendRequestApi> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ toEmail: toEmail }),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to send friend request');
  return await res.json() as FriendRequestApi;
}

export async function acceptFriendRequest(requestId: string): Promise<FriendRequestApi> {
  const res = await fetch(`${API_BASE}/${requestId}/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to accept friend request');
  return await res.json() as FriendRequestApi;
}

export async function declineFriendRequest(requestId: string): Promise<FriendRequestApi> {
  const res = await fetch(`${API_BASE}/${requestId}/decline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to decline friend request');
  return await res.json() as FriendRequestApi;
}

export async function cancelFriendRequest(requestId: string): Promise<FriendRequestApi> {
  const res = await fetch(`${API_BASE}/${requestId}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to cancel friend request');
  return await res.json() as FriendRequestApi;
}

export async function listIncomingRequests(): Promise<FriendRequestApi[]> {
  const res = await fetch(`${API_BASE}/incoming`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch incoming requests');
  return await res.json() as FriendRequestApi[];
}

export async function listOutgoingRequests(): Promise<FriendRequestApi[]> {
  const res = await fetch(`${API_BASE}/outgoing`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch outgoing requests');
  return await res.json() as FriendRequestApi[];
}

// Example user search (adjust endpoint as needed)
export function searchUsers(query: string): UserSearchResult[] {
  // Mock search implementation
  const lowerQuery = query.toLowerCase();
  return mockUsers.filter(user =>
    user.username.toLowerCase().includes(lowerQuery) ||
    user.email.toLowerCase().includes(lowerQuery)
  );
}

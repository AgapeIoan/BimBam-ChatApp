import type { FriendListItem } from "../types/friend/friendListItem";
import { apiClient } from "./apiClient";

export async function listMyFriends(): Promise<FriendListItem[]> {
  return apiClient.get<FriendListItem[]>("/api/v1/friends/");
}
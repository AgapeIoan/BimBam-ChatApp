export interface UserResponse {
  email: string;
  username: string;
  avatarUrl?: string | null;
}

export interface FriendRequestApi {
  id: string;
  status: "pending" | "accepted" | "rejected" | "cancelled";
  createdAt: string;
  fromUser: UserResponse;
  toUser: UserResponse;
}

export interface FriendRequestApiSchema {
  toEmail: string;
}

export interface UserSearchResult {
  id: string;
  username: string;
  email: string;
  avatarUrl?: string | null;
  isFriend: boolean;
  hasPendingRequest: boolean;
}

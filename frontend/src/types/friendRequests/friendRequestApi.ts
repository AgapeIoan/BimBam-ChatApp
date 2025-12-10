import type { UserResponse } from "../user/userResponse";

export interface FriendRequestApi {
  id: string;
  status: "pending" | "accepted" | "rejected" | "cancelled";
  createdAt: string;
  fromUser: UserResponse;
  toUser: UserResponse;
}
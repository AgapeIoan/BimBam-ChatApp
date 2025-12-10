import type { UserRead } from "../user/userRead";

export interface FriendListItem {
  friend: UserRead;
  isOnline: boolean;
  lastReadMessageId?: string | null;
  unreadCount: number;
}
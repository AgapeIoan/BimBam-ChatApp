import type { UserRead } from "../user/userRead";

export type ConversationPreview = {
  id: string;
  isGroup: boolean;
  name?: string;
  lastMessage?: string;
  lastMessageAt?: string;
  otherUsers: UserRead[];
  unreadCount: number;
};

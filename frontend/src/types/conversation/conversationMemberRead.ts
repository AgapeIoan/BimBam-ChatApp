import type { UserRead } from "../user/userRead";

export interface ConversationMemberRead {
  id: string;
  conversationId: string;
  user: UserRead;
  joinedAt: string; // ISO date string
  lastReadMessageId?: string | null;
  unreadCount: number;
  isAdmin: boolean;
  isMuted: boolean;
}

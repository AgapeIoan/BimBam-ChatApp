import type { ConversationUser } from './conversationUser';

export type ConversationPreview = {
  id: string;
  isGroup: boolean;
  name?: string;
  lastMessage?: string;
  lastMessageAt?: string;
  otherUsers: ConversationUser[];
  unreadCount: number;
};

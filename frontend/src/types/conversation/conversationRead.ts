import type { ConversationMemberRead } from "./conversationMemberRead";

export interface ConversationRead {
  id: string;
  is_group: boolean;
  name?: string | null;
  created_at: string; // ISO date string
  members?: ConversationMemberRead[] | null;
}

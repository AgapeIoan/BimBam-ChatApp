import { apiClient } from "./apiClient";
import type { ConversationPreview } from "../types/conversation/conversationPreview";
import type { ConversationRead } from "../types/conversation/conversationRead";

export async function loadConversationPreviews(): Promise<ConversationPreview[]> {
  return apiClient.get<ConversationPreview[]>("/api/v1/conversations/");
}

export async function openOrCreateDirectConversation(friendId: string): Promise<ConversationRead> {
  return apiClient.get<ConversationRead>(`/api/v1/friends/${friendId}/conversation`);
}
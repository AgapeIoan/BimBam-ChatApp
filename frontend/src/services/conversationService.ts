import { apiClient } from "./apiClient";
import type { ConversationPreview } from "../types/conversation/conversationPreview";

export async function loadConversationPreviews(): Promise<ConversationPreview[]> {
  return apiClient.get<ConversationPreview[]>("/api/v1/conversations/");
}

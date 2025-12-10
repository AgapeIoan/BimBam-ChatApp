import type { ConversationPreview } from "../types/chat";



export async function loadConversationPreviews(): Promise<ConversationPreview[]> {
  const res = await fetch("/api/v1/conversations/", {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return await res.json();
}

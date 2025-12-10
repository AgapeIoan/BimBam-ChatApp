export interface ConversationUser {
    id: string;
    name: string;
    avatar: string;
}

export interface ConversationPreview {
  id: string;
  isGroup: boolean;
    name: string | null;
    lastMessage: string;
    lastMessageAt: string;
    otherUsers: ConversationUser[];
    unreadCount: number;
}

export async function listConversations(): Promise<ConversationPreview[]> {
  const res = await fetch('http://localhost:8000/api/v1/conversations', {
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return await res.json();
}

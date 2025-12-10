export type Message = {
  id: string;
  text: string;
  sender: 'me' | 'them';
  timestamp: Date;
  status?: 'sent' | 'delivered' | 'read' | 'failed';
};

export type Contact = {
  email: string;
  username: string;
  avatarUrl: string;
  provider: string;
  id : string;
  lastseenAt: Date | null;
};

export interface ConversationUser {
    email: string;
    username: string;
    avatarUrl: string;
    provider: string;
    id : string;
    lastseenAt: Date | null;
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

export type FriendRequest = {
  fromId: string;
  fromName: string;
  fromUsername: string;
  fromEmail: string;
  fromAvatar: string;
  timestamp: string;
  status: 'pending' | 'accepted' | 'rejected';
};

export type SentRequest = {
  toId: string;
  toName: string;
  toUsername: string;
  toEmail: string;
  toAvatar: string;
  timestamp: string;
  status: 'pending' | 'accepted' | 'rejected';
};

export type UserSearchResult = {
  id: string;
  name: string;
  username: string;
  email: string;
  avatar: string;
  isFriend: boolean;
  hasPendingRequest: boolean;
};

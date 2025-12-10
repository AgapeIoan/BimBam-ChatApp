export type Message = {
  id: string;
  text: string;
  sender: 'me' | 'them';
  timestamp: Date;
  status?: 'sent' | 'delivered' | 'read' | 'failed';
};

export type Contact = {
  id: string;
  name: string;
  avatar: string;
  lastMessage: string;
  timestamp: string;
  unread?: number;
  online?: boolean;
  isFriend?: boolean;
};

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

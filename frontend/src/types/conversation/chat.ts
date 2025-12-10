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
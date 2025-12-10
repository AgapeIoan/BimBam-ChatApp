export interface UserRead {
  id: string;
  provider: string;
  lastSeen: string;
  email: string;
  username: string;
  avatarUrl?: string | null;
}

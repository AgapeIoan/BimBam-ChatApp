export interface UserSearchResult {
  username: string;
  email: string;
  avatarUrl?: string | null;
  isFriend: boolean;
  hasPendingRequest: boolean; 
}
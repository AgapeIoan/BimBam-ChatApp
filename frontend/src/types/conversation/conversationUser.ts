export interface ConversationUser {
    email: string;
    username: string;
    avatarUrl: string;
    provider: string;
    id : string;
    lastseenAt: Date | null;
}
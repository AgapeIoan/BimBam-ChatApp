import { useCallback, useEffect, useRef, useState } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { ChatView } from './ChatView';
import { FriendRequestsModal } from './FriendRequestsModal';
import { AccountModal } from './AccountModal';
import { GroupModal } from './GroupModal';
import type { UserAccountDetails } from '../types/user/userAccountDetails';
import type { FriendListItem } from '../types/friend/friendListItem';
import ws from '../api/ws';
import type { AuthUser } from '../api/client';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Message {
  id: string;
  conversationId?: string;
  text: string;
  sender: 'me' | 'them';
  timestamp: Date;
  status?: 'sent' | 'delivered' | 'read' | 'failed';
  editedAt?: string | null;
  editedById?: string | null;
  reactions?: { emoji: string; count: number; reactedByMe?: boolean; users?: string[] }[];
  // When present, each reaction can also include usernames for tooltips
  // e.g., { emoji: "👍", count: 3, users: ["anna", "bob", "carol"] }
  // The UI reads these to show who reacted on hover.
  senderId?: string;
  senderName?: string;
  senderAvatarUrl?: string | null;
  senderOnline?: boolean;
}

export interface Contact {
  id: string;
  conversationId?: string;
  name: string;
  avatar: string;
  avatarUrl?: string | null;
  lastMessage: string;
  timestamp: string;
  unread?: number;
  online?: boolean;
  isFriend?: boolean;
  otherUserId?: string;
  username?: string;
  email?: string;
  isGroup?: boolean;
}

export interface FriendRequest {
  requestId?: string;
  fromId: string;
  fromUserId?: string;
  fromName: string;
  fromUsername: string;
  fromEmail: string;
  fromAvatar: string;
  timestamp: string;
  status: 'pending' | 'accepted' | 'rejected';
}

export interface SentRequest {
  requestId?: string;
  toId: string;
  toUserId?: string;
  toName: string;
  toUsername: string;
  toEmail: string;
  toAvatar: string;
  timestamp: string;
  status: 'pending' | 'accepted' | 'rejected';
}

export interface UserSearchResult {
  id: string;
  name: string;
  username: string;
  email: string;
  avatar: string;
  avatarUrl?: string | null;
  isFriend: boolean;
  hasPendingRequest: boolean;
}

interface ConversationPreviewResponse {
  id: string;
  is_group: boolean;
  name?: string | null;
  last_message?: string | null;
  last_message_at?: string | null;
  other_users?: UserPreview[];
  unread_count: number;
}

interface UserPreview {
  id: string;
  email: string;
  username: string;
  avatarUrl?: string | null;
}

const formatTimeLabel = (value?: string | Date | null) => {
  if (!value) return '';
  try {
    const dt = typeof value === 'string' ? new Date(value) : value;
    return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
};

const initials = (value?: string | null) => {
  if (!value) return '??';
  const parts = value.split(/[\s@._-]+/).filter(Boolean);
  if (!parts.length) return value.slice(0, 2).toUpperCase();
  return parts
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase();
};

const mapFriendApiEntry = (entry: any): FriendListItem => ({
  friend: entry.friend,
  isOnline: Boolean(entry.is_online),
  lastReadMessageId: entry.last_read_message_id ?? null,
  unreadCount: entry.unread_count ?? 0,
});

const getSenderDisplayName = (payload: any) =>
  payload?.senderName || payload?.senderUsername || payload?.senderEmail;

const mapPreviewToContact = (preview: ConversationPreviewResponse): Contact => {
  const isGroup = Boolean(preview.is_group);
  const other = preview.other_users?.[0];
  const baseName = isGroup
    ? preview.name || 'Group Conversation'
    : other?.username || preview.name || other?.email || 'Conversation';
  const avatarUrl = isGroup ? null : (other as any)?.avatar_url ?? (other as any)?.avatarUrl ?? null;
  return {
    id: String(preview.id),
    conversationId: String(preview.id),
    name: baseName,
    avatar: initials(baseName),
    avatarUrl,
    lastMessage: preview.last_message || '',
    timestamp: formatTimeLabel(preview.last_message_at),
    unread: preview.unread_count,
    online: false,
    isFriend: !isGroup,
    isGroup,
    otherUserId: isGroup ? undefined : other ? String(other.id) : undefined,
    username: isGroup ? undefined : other?.username,
    email: isGroup ? undefined : other?.email,
  };
};

const parseCookieToken = () => {
  if (typeof document === 'undefined') return undefined;
  const raw = document.cookie.split('; ').find((r) => r.startsWith('access_token='));
  if (!raw) return undefined;
  const [, v] = raw.split('=');
  return decodeURIComponent(v);
};

const safeId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

export function ChatApp({ onLogout, currentUser }: { onLogout: () => void; currentUser: AuthUser }) {
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showFriendRequests, setShowFriendRequests] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [friendsList, setFriendsList] = useState<Contact[]>([]);
  const [friendItems, setFriendItems] = useState<FriendListItem[]>([]);
  const [typingUsers, setTypingUsers] = useState<Record<string, number>>({});
  const [userAccount, setUserAccount] = useState<UserAccountDetails>({
    id: currentUser.id,
    username: currentUser.username || '',
    email: currentUser.email,
    avatar_url: currentUser.avatar_url || null,
  });
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [incomingRequests, setIncomingRequests] = useState<FriendRequest[]>([]);
  const [sentRequests, setSentRequests] = useState<SentRequest[]>([]);

  const pendingRef = useRef<Record<string, { conversationId: string; tempId: string }>>({});
  const selectedConversationRef = useRef<string | null>(null);
  const currentUserRef = useRef<string>(currentUser.id);
  const presenceMapRef = useRef<Record<string, boolean>>({});
  const historyAbortRef = useRef<AbortController | null>(null);
  const myReactionsRef = useRef<Record<string, Set<string>>>({});
  const getSenderOnline = (senderId?: string) =>
    senderId ? Boolean(presenceMapRef.current[senderId]) : undefined;

  const overlayMyReactions = useCallback(
    (reactions: { emoji: string; count: number; reactedByMe?: boolean }[] | undefined, messageId: string) => {
      const mine = myReactionsRef.current[messageId];
      if (!mine || !reactions) return reactions;
      return reactions.map((r) => (mine.has(r.emoji) ? { ...r, reactedByMe: true } : r));
    },
    []
  );

  useEffect(() => {
    selectedConversationRef.current = selectedContactId;
  }, [selectedContactId]);

  useEffect(() => {
    currentUserRef.current = currentUser.id;
  }, [currentUser.id]);

  const refreshConversations = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/conversations/`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!res.ok) {
        console.warn('Failed to load conversations', res.status);
        return null;
      }
      return (await res.json()) as ConversationPreviewResponse[];
    } catch (err) {
      console.error('Unable to fetch conversations', err);
      return null;
    }
  }, []);

  const fetchFriends = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/friends/`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!res.ok) {
        console.warn('Failed to load friends', res.status);
        return null;
      }
      const data = await res.json();
      return data as any[];
    } catch (err) {
      console.error('Unable to fetch friends', err);
      return null;
    }
  }, []);

  const mergeFriendsAndConversations = useCallback((friendsData: any[], previews: ConversationPreviewResponse[]) => {
    setFriendsList((prev) => {
      const prevById = new Map<string, Contact>(prev.map((c) => [c.id, c]));
      const convByUserId = new Map<string, ConversationPreviewResponse>();
      previews.forEach((p) => {
        p.other_users?.forEach((u) => convByUserId.set(String(u.id), p));
      });

      const contactsFromFriends: Contact[] = friendsData.map((f) => {
        const friendUser = f.friend || {};
        const friendId = String(friendUser.id || '');
        const conv = convByUserId.get(friendId);
        const name = friendUser.username || friendUser.email || 'Friend';
        const avatarUrl = friendUser.avatar_url || friendUser.avatarUrl || null;
        const existing = prevById.get(conv ? String(conv.id) : friendId);
        return {
          id: conv ? String(conv.id) : friendId,
          conversationId: conv ? String(conv.id) : undefined,
          name,
          avatar: initials(friendUser.username || friendUser.email || name),
          avatarUrl,
          lastMessage: conv?.last_message || '',
          timestamp: formatTimeLabel(conv?.last_message_at),
          unread: conv?.unread_count ?? f.unread_count ?? 0,
          online: Boolean(f.is_online) || Boolean(existing?.online),
          isFriend: true,
          isGroup: false,
          otherUserId: friendId,
          username: friendUser.username,
          email: friendUser.email,
        };
      });

      const contactsByKey = new Map<string, Contact>();
      contactsFromFriends.forEach((c) => contactsByKey.set(c.id, c));
      previews.forEach((p) => {
        const mapped = mapPreviewToContact(p);
        const existing = contactsByKey.get(mapped.id);
        if (existing) {
          contactsByKey.set(mapped.id, { ...mapped, online: existing.online || mapped.online });
        } else {
          contactsByKey.set(mapped.id, mapped);
        }
      });

      const merged = Array.from(contactsByKey.values()).map((c) => {
        const presence = presenceMapRef.current[c.otherUserId || ""];
        return presence === undefined ? c : { ...c, online: presence };
      });
      return merged;
    });
  }, []);

  const loadingContactsRef = useRef(false);
  const lastContactsLoadRef = useRef(0);

  const loadContacts = useCallback(
    async (options?: { force?: boolean }) => {
      const now = Date.now();
      if (loadingContactsRef.current) {
        // eslint-disable-next-line no-console
        console.log('loadContacts skipped (already loading)');
        return;
      }
      if (!options?.force && now - lastContactsLoadRef.current < 3000) {
        // eslint-disable-next-line no-console
        console.log('loadContacts skipped (throttled)');
        return;
      }
      loadingContactsRef.current = true;
      try {
      // eslint-disable-next-line no-console
      console.log('loadContacts fetch start');
      const [friendsData, previews] = await Promise.all([fetchFriends(), refreshConversations()]);
      if (friendsData === null && previews === null) {
        // eslint-disable-next-line no-console
        console.warn('loadContacts skipped update due to fetch errors');
        return;
      }
      setFriendItems(friendsData ? friendsData.map(mapFriendApiEntry) : []);
      mergeFriendsAndConversations(friendsData ?? [], previews ?? []);
      } finally {
        loadingContactsRef.current = false;
        lastContactsLoadRef.current = Date.now();
        // eslint-disable-next-line no-console
        console.log('loadContacts fetch end');
      }
    },
    [fetchFriends, mergeFriendsAndConversations, refreshConversations]
  );

  useEffect(() => {
    loadContacts({ force: true });
  }, [loadContacts]);

  // Periodically refresh friends/conversations so new accepts appear for both parties
  useEffect(() => {
    const timer = setInterval(() => {
      loadContacts();
    }, 15000);
    return () => clearInterval(timer);
  }, [loadContacts]);

  const refreshFriendRequests = useCallback(async () => {
    try {
      const [incomingRes, outgoingRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/friend-requests/incoming`, { method: 'GET', credentials: 'include' }),
        fetch(`${API_BASE}/api/v1/friend-requests/outgoing`, { method: 'GET', credentials: 'include' }),
      ]);

      if (incomingRes.ok) {
        const incoming = await incomingRes.json();
        setIncomingRequests(
          incoming.map((fr: any) => {
            const user = fr.fromUser || {};
            return {
              requestId: fr.id,
              fromId: fr.id,
              fromUserId: user.id ? String(user.id) : undefined,
              fromName: user.username || user.email || 'User',
              fromUsername: user.username || '',
              fromEmail: user.email || '',
              fromAvatar: initials(user.username || user.email || 'U'),
              timestamp: formatTimeLabel(fr.createdAt),
              status: 'pending',
            };
          })
        );
      }

      if (outgoingRes.ok) {
        const outgoing = await outgoingRes.json();
        setSentRequests(
          outgoing.map((fr: any) => {
            const user = fr.toUser || {};
            return {
              requestId: fr.id,
              toId: fr.id,
              toUserId: user.id ? String(user.id) : undefined,
              toName: user.username || user.email || 'User',
              toUsername: user.username || '',
              toEmail: user.email || '',
              toAvatar: initials(user.username || user.email || 'U'),
              timestamp: formatTimeLabel(fr.createdAt),
              status: 'pending',
            };
          })
        );
      }
    } catch (err) {
      console.error('Unable to fetch friend requests', err);
    }
  }, []);

  useEffect(() => {
    refreshFriendRequests();
  }, [refreshFriendRequests]);

  // Periodically refresh friend requests so incoming requests appear without reload
  useEffect(() => {
    const timer = setInterval(() => {
      refreshFriendRequests();
    }, 10000);
    return () => clearInterval(timer);
  }, [refreshFriendRequests]);

  // When opening the friend requests modal, fetch latest
  useEffect(() => {
    if (showFriendRequests) {
      refreshFriendRequests();
    }
  }, [showFriendRequests, refreshFriendRequests]);

  const markAsRead = useCallback((conversationId: string, beforeMessageId?: string) => {
    ws.send({
      type: 'message_read',
      data: {
        conversationId,
        ...(beforeMessageId ? { beforeMessageId } : {}),
      },
    });
  }, []);

  const handleDelivered = useCallback(
    (payload: any) => {
      if (!payload) return;
      const convId = String(payload.conversationId || '');
      if (!convId) return;

      const senderId = String(payload.senderId || payload.sender_id || '');
      const senderName = getSenderDisplayName(payload);
      const senderAvatarUrl =
        payload.senderAvatarUrl ?? payload.sender_avatar_url ?? null;
      const senderOnline = getSenderOnline(senderId);
      const msg: Message = {
        id: String(payload.messageId || payload.id || safeId()),
        conversationId: convId,
        text: payload.content,
        sender: senderId === currentUserRef.current ? 'me' : 'them',
        timestamp: payload.createdAt ? new Date(payload.createdAt) : new Date(),
        status: payload.read ? 'read' : payload.delivered ? 'delivered' : 'sent',
        editedAt: payload.editedAt,
        editedById: payload.editedById,
        senderId,
        senderName,
        senderAvatarUrl,
        senderOnline,
      };

      setMessages((prev) => ({
        ...prev,
        [convId]: [...(prev[convId] || []), msg],
      }));

      setFriendsList((prev) => {
        const exists = prev.some((c) => c.id === convId);
        const next = prev.map((c) =>
          c.id === convId
            ? {
                ...c,
                lastMessage: msg.text,
                timestamp: formatTimeLabel(msg.timestamp),
                unread:
                  selectedConversationRef.current === convId
                    ? 0
                    : (c.unread || 0) + 1,
              }
            : c
        );
        if (exists) {
          return next;
        }
        loadContacts();
        return next;
      });

      if (selectedConversationRef.current === convId && msg.sender === 'them') {
        markAsRead(convId, msg.id);
        setMessages((prev) => {
          const conv = prev[convId] || [];
          return {
            ...prev,
            [convId]: conv.map((m) => (m.id === msg.id ? { ...m, status: 'read' } : m)),
          };
        });
      }
    },
    [loadContacts, markAsRead]
  );

  const handleAck = useCallback((data: any) => {
    const correlationId = data?.correlationId;
    const ackMsg = data?.message;
    const delivered = Boolean(data?.delivered);
    const convId = ackMsg?.conversationId ? String(ackMsg.conversationId) : undefined;
    const pendingInfo = correlationId ? pendingRef.current[correlationId] : undefined;
    const targetConv = convId || pendingInfo?.conversationId;

    const realMessageId = ackMsg?.messageId || data?.messageId;
    const status: Message['status'] =
      data?.status === 'ok' ? (delivered ? 'delivered' : 'sent') : 'failed';

    setMessages((prev) => {
      // resolve conversation for reaction acks where convId is missing
      let resolvedConv = targetConv;
      if (!resolvedConv && realMessageId) {
        for (const cid of Object.keys(prev)) {
          if (prev[cid]?.some((m) => String(m.id) === String(realMessageId))) {
            resolvedConv = cid;
            break;
          }
        }
      }
      if (!resolvedConv) return prev;

      const conv = prev[resolvedConv] || [];
      const updated: Message[] = conv.map((msg) => {
        const matchesTemp = pendingInfo && msg.id === pendingInfo.tempId;
        const matchesReal = realMessageId && String(msg.id) === String(realMessageId);
        if (!matchesTemp && !matchesReal) return msg;

        const reactionsFromCounts = ackMsg?.counts
          ? overlayMyReactions(
              Object.keys(ackMsg.counts).map((emoji) => ({
                emoji,
                count: ackMsg.counts[emoji],
              })),
              targetConv || ''
            )
          : msg.reactions;

        const updatedSenderId = ackMsg?.senderId ? String(ackMsg.senderId) : msg.senderId;
        return {
          ...msg,
          id: realMessageId || msg.id,
          text: ackMsg?.content ?? msg.text,
          timestamp: ackMsg?.createdAt ? new Date(ackMsg.createdAt) : msg.timestamp,
          status,
          editedAt: ackMsg?.editedAt ?? msg.editedAt,
          editedById: ackMsg?.editedById ?? msg.editedById,
          senderId: updatedSenderId,
          senderName: getSenderDisplayName(ackMsg) ?? msg.senderName,
          senderAvatarUrl: ackMsg?.senderAvatarUrl ?? msg.senderAvatarUrl,
          senderOnline: getSenderOnline(updatedSenderId),
          reactions: reactionsFromCounts,
        };
      }) as Message[];
      return { ...prev, [resolvedConv]: updated };
    });

    if (targetConv) {
      setFriendsList((prev) =>
        prev.map((c) =>
          c.id === targetConv
            ? {
                ...c,
                lastMessage: ackMsg?.content ?? c.lastMessage,
                timestamp: formatTimeLabel(ackMsg?.createdAt || new Date()),
              }
            : c
        )
      );
    }

    if (correlationId) {
      const { [correlationId]: _, ...rest } = pendingRef.current;
      pendingRef.current = rest;
    }
  }, []);

  const handleEditEvent = useCallback((data: any) => {
    const convId = data?.conversationId ? String(data.conversationId) : null;
    const messageId = data?.messageId ? String(data.messageId) : null;
    if (!messageId) return;

    setMessages((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((cid) => {
        if (convId && cid !== convId) return;
        next[cid] = next[cid].map((m) =>
          String(m.id) === messageId ? { ...m, text: data.content, editedAt: data.editedAt } : m
        );
      });
      return next;
    });
  }, []);

  const handleReactionEvent = useCallback((data: any) => {
    const mid = String(data.messageId || data.message_id || '');
    const counts = data.counts || {};
    const usersByEmoji = data.users || {};
    // Build reactions with users list for hover tooltip
    const rawReactions = Object.keys(counts).map((emoji) => ({
      emoji,
      count: counts[emoji],
      users: Array.isArray(usersByEmoji[emoji]) ? usersByEmoji[emoji] : [],
    }));
    const reactions = overlayMyReactions(rawReactions, mid);
    setMessages((prev) => {
      const newPrev = { ...prev };
      for (const cid of Object.keys(newPrev)) {
        newPrev[cid] = newPrev[cid].map((m) => (String(m.id) === mid ? { ...m, reactions } : m));
      }
      return newPrev;
    });
  }, []);

  const handleReadEvent = useCallback((data: any) => {
    const convId = String(data.conversationId || '');
    const readerId = String(data.readerId || '');
    const msgId = data.messageId ? String(data.messageId) : undefined;
    if (!convId || !readerId) return;
    if (readerId === currentUserRef.current) return;

    setMessages((prev) => {
      const conv = prev[convId];
      if (!conv) return prev;
      const updated: Message[] = conv.map((m) => {
        if (m.sender !== 'me') return m;
        if (!msgId || m.id === msgId) {
          return { ...m, status: 'read' };
        }
        return m;
      }) as Message[];
      return { ...prev, [convId]: updated };
    });
  }, []);

  const handlePresence = useCallback(
    (data: any) => {
      const userId = String(data.userId || '');
      const isOnline = Boolean(data.isOnline);
      if (!userId) return;

      let seen = false;
      presenceMapRef.current = { ...presenceMapRef.current, [userId]: isOnline };
      setFriendsList((prev) =>
        prev.map((c) => {
          if (c.otherUserId === userId || c.id === userId) {
            seen = true;
            return { ...c, online: isOnline };
          }
          return c;
        })
      );

      setMessages((prev) => {
        let changed = false;
        const next: Record<string, Message[]> = {};
        for (const [convId, convMessages] of Object.entries(prev)) {
          let convChanged = false;
          const updatedMessages = convMessages.map((msg) => {
            if (msg.senderId !== userId) return msg;
            if (msg.senderOnline === isOnline) return msg;
            convChanged = true;
            return { ...msg, senderOnline: isOnline };
          });
          if (convChanged) {
            changed = true;
            next[convId] = updatedMessages;
          } else {
            next[convId] = convMessages;
          }
        }
        return changed ? next : prev;
      });

      if (!seen) {
        loadContacts();
      }
    },
    [loadContacts]
  );

  // Prune expired typing indicators periodically
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      setTypingUsers((prev) => {
        const next: Record<string, number> = {};
        Object.entries(prev).forEach(([uid, expiry]) => {
          if (expiry > now) next[uid] = expiry;
        });
        return next;
      });
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const token = parseCookieToken();
    ws.connect(token).catch((err) => console.warn('ws connect error', err));
    const unsub = ws.subscribe((env: any) => {
      const t = String(env.type || '').toLowerCase();
      const data = env.data || {};
      if (t === 'message_delivered') {
        handleDelivered(data);
      } else if (t === 'message_ack') {
        handleAck(data);
      } else if (t === 'message_edit') {
        handleEditEvent(data);
      } else if (t === 'message_reaction') {
        handleReactionEvent(data);
      } else if (t === 'message_read') {
        handleReadEvent(data);
      } else if (t === 'presence') {
        handlePresence(data);
      } else if (t === 'typing') {
        const fromId = String(data.fromUserId || data.from_user_id || '');
        const toId = String(data.toUserId || data.to_user_id || '');
        const convId = String(data.conversationId || data.conversation_id || '');
        const isTyping = Boolean(data.isTyping ?? data.is_typing);
        // For DMs: must be addressed to me; for groups: must match selected conversation
        const isDmForMe = toId && toId === currentUserRef.current;
        const isGroupForConv = convId && convId === selectedConversationRef.current;
        if (!fromId || (!isDmForMe && !isGroupForConv)) return;
        setTypingUsers((prev) => {
          if (isTyping) {
            return { ...prev, [fromId]: Date.now() + 4000 };
          }
          const { [fromId]: _, ...rest } = prev;
          return rest;
        });
      } else if (t === 'error') {
        console.warn('ws error', data);
      }
    });

    return () => {
      unsub();
      ws.disconnect();
    };
  }, [handleAck, handleDelivered, handleEditEvent, handlePresence, handleReactionEvent, handleReadEvent]);

  const selectedContact = friendsList.find((c) => c.id === selectedContactId);
  const currentMessages = selectedContactId ? messages[selectedContactId] || [] : [];

  useEffect(() => {
    if (!selectedContactId) return;
    const convMessages = messages[selectedContactId] || [];
    const hasUnread = convMessages.some((m) => m.sender === 'them' && m.status !== 'read');
    if (!convMessages.length || !hasUnread) return;
    const last = convMessages[convMessages.length - 1];
    markAsRead(selectedContactId, last.id);
    setMessages((prev) => ({
      ...prev,
      [selectedContactId]: convMessages.map((m) =>
        m.sender === 'them' ? { ...m, status: 'read' } : m
      ),
    }));
    setFriendsList((prev) => prev.map((c) => (c.id === selectedContactId ? { ...c, unread: 0 } : c)));
  }, [markAsRead, messages, selectedContactId]);

  const handleSendMessage = async (text: string) => {
    if (!selectedContactId) return;

    const correlationId = safeId();
    const tempId = `temp-${correlationId}`;
    const newMessage: Message = {
      id: tempId,
      conversationId: selectedContactId,
      text,
      sender: 'me',
      timestamp: new Date(),
      status: 'sent',
      senderId: currentUserRef.current,
      senderName: 'You',
      senderAvatarUrl: userAccount.avatar_url,
    };

    setMessages((prev) => ({
      ...prev,
      [selectedContactId]: [...(prev[selectedContactId] || []), newMessage],
    }));

    setFriendsList((prev) =>
      prev.map((c) =>
        c.id === selectedContactId
          ? { ...c, lastMessage: newMessage.text, timestamp: formatTimeLabel(newMessage.timestamp), unread: c.unread }
          : c
      )
    );

    pendingRef.current = {
      ...pendingRef.current,
      [correlationId]: { conversationId: selectedContactId, tempId },
    };

    const sent = await ws.send({
      type: 'message_send',
      data: { conversationId: selectedContactId, content: text },
      correlationId,
    });

    if (!sent) {
      setMessages((prev) => ({
        ...prev,
        [selectedContactId]: (prev[selectedContactId] || []).map((m) =>
          m.id === tempId ? { ...m, status: 'failed' } : m
        ),
      }));
    }
  };

  const ensureConversationForContact = useCallback(
    async (contact: Contact): Promise<string | null> => {
      if (contact.conversationId) return contact.conversationId;
      if (!contact.otherUserId) return null;
      try {
        const res = await fetch(`${API_BASE}/api/v1/friends/${contact.otherUserId}/conversation`, {
          method: 'GET',
          credentials: 'include',
        });
        if (!res.ok) {
          console.warn('Failed to open conversation', res.status);
          return null;
        }
        const data = await res.json();
        const convId = String(data.id || '');
        setFriendsList((prev) =>
          prev.map((c) =>
            c.otherUserId === contact.otherUserId
              ? { ...c, id: convId, conversationId: convId }
              : c
          )
        );
        return convId;
      } catch (err) {
        console.error('Error opening conversation', err);
        return null;
      }
    },
    []
  );

  const handleEditMessage = (messageId: string, newText: string) => {
    if (!selectedContactId) return;
    setMessages((prev) => ({
      ...prev,
      [selectedContactId]: prev[selectedContactId].map((m) =>
        m.id === messageId ? { ...m, text: newText, editedAt: new Date().toISOString() } : m
      ),
    }));

    ws.send({ type: 'message_edit', data: { messageId, content: newText } });
  };

  const handleReact = (messageId: string, emoji: string) => {
    if (!selectedContactId) return;
    setMessages((prev) => {
      const conv = prev[selectedContactId] || [];
      const newConv = conv.map((m) => {
        if (m.id !== messageId) return m;
        const reactions = m.reactions || [];
        const existing = reactions.find((r) => r.emoji === emoji);
        const mine = myReactionsRef.current[messageId]?.has(emoji) || existing?.reactedByMe;
        if (existing && mine) {
          const updatedReactions =
            existing.count > 1
              ? reactions.map((r) =>
                  r.emoji === emoji ? { ...r, count: r.count - 1, reactedByMe: false } : r
                )
              : reactions.filter((r) => r.emoji !== emoji);
          myReactionsRef.current[messageId]?.delete(emoji);
          return { ...m, reactions: updatedReactions };
        }
        const updated = existing
          ? reactions.map((r) =>
              r.emoji === emoji ? { ...r, count: r.count + 1, reactedByMe: true } : r
            )
          : [...reactions, { emoji, count: 1, reactedByMe: true }];
        myReactionsRef.current[messageId] = myReactionsRef.current[messageId] || new Set<string>();
        myReactionsRef.current[messageId].add(emoji);
        return { ...m, reactions: updated };
      });
      return { ...prev, [selectedContactId]: newConv };
    });

    const mineSet = myReactionsRef.current[messageId];
    const isMine = mineSet ? mineSet.has(emoji) : false;
    const action = isMine ? 'add' : 'remove';
    ws.send({ type: 'message_reaction', data: { messageId, emoji, action } });
  };

  const sendTyping = useCallback(
    (isTyping: boolean) => {
      if (!selectedContactId) return;
      const contact = friendsList.find((c) => c.id === selectedContactId);
      if (!contact) return;
      const basePayload: any = {
        fromUserId: currentUserRef.current,
        isTyping,
      };
      if (contact.isGroup) {
        basePayload.conversationId = selectedContactId;
      } else if (contact.otherUserId) {
        basePayload.toUserId = contact.otherUserId;
      } else {
        return;
      }
      ws.send({
        type: 'typing',
        data: basePayload,
      });
    },
    [friendsList, selectedContactId]
  );

  const loadHistory = useCallback(
    async (conversationId: string) => {
      if (!conversationId) return;
      // cancel any in-flight history fetch
      if (historyAbortRef.current) {
        historyAbortRef.current.abort();
      }
      const controller = new AbortController();
      historyAbortRef.current = controller;
      try {
        // eslint-disable-next-line no-console
        console.log('history: fetching', conversationId);
        const res = await fetch(
          `${API_BASE}/api/v1/conversations/${conversationId}/messages?limit=50`,
          {
            method: 'GET',
            credentials: 'include',
            signal: controller.signal,
          }
        );
        if (!res.ok) {
          console.warn('Failed to load history', res.status);
          return;
        }
        const body = await res.json();
        const items = (body?.messages || body || []) as any[];
        const normalized: Message[] = items.map((m) => {
          const counts = m.reactions || m.counts;
          const reactions = counts
            ? overlayMyReactions(
                Object.keys(counts).map((emoji) => ({ emoji, count: counts[emoji] })),
                String(m.id || m.messageId)
              )
            : undefined;
          return {
            id: String(m.id || m.messageId),
            conversationId: String(m.conversationId || conversationId),
            text: m.content || '',
            sender: String(m.senderId || m.sender_id || '') === currentUserRef.current ? 'me' : 'them',
            timestamp: m.createdAt ? new Date(m.createdAt) : new Date(),
            status: m.read ? 'read' : m.delivered ? 'delivered' : 'sent',
            editedAt: m.editedAt || null,
            editedById: m.editedById || null,
            senderId: String(m.senderId || m.sender_id || ''),
            senderName: m.sender?.username || m.sender?.email || undefined,
            senderAvatarUrl: m.sender?.avatarUrl ?? null,
            senderOnline: getSenderOnline(String(m.senderId || m.sender_id || '')),
            reactions,
          };
        });

        setMessages((prev) => {
          const existing = prev[conversationId] || [];
          const merged = new Map<string, Message>();
          [...existing, ...normalized].forEach((msg) => {
            merged.set(String(msg.id), msg);
          });
          const sorted = Array.from(merged.values()).sort(
            (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
          );
          return { ...prev, [conversationId]: sorted };
        });
      } catch (err) {
        if ((err as any)?.name !== 'AbortError') {
          console.error('History fetch failed', err);
        }
      }
    },
    [setMessages]
  );

  useEffect(() => {
    if (selectedContactId) {
      loadHistory(selectedContactId);
    }
    // cleanup any inflight history when unmounting
    return () => {
      if (historyAbortRef.current) {
        historyAbortRef.current.abort();
      }
    };
  }, [loadHistory, selectedContactId]);

  const handleCreateGroup = useCallback(
    async (groupName: string, memberIds: string[]) => {
      if (!groupName.trim() || memberIds.length === 0) return;
      try {
        const res = await fetch(`${API_BASE}/api/v1/conversations/group`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            groupName,
            participantIds: memberIds,
          }),
        });
        if (!res.ok) {
          console.warn('Failed to create group', res.status);
          return;
        }
        const data = await res.json();
        const convId = String(data.id);
        setSelectedContactId(convId);
        setMessages((prev) => ({
          ...prev,
          [convId]: prev[convId] || [],
        }));
        const createdAt = data.created_at ? new Date(data.created_at) : new Date();
        setFriendsList((prev) => [
          {
            id: convId,
            conversationId: convId,
            name: data.name || groupName,
            avatar: initials(data.name || groupName),
            avatarUrl: null,
            lastMessage: '',
            timestamp: formatTimeLabel(createdAt),
            unread: 0,
            online: false,
            isFriend: false,
            isGroup: true,
          },
          ...prev.filter((c) => c.id !== convId),
        ]);
        loadHistory(convId);
        loadContacts({ force: true });
      } catch (err) {
        console.error('Error creating group', err);
      }
    },
    [loadContacts, loadHistory]
  );

  const handleSelectContact = useCallback(
    async (id: string) => {
      const contact = friendsList.find((c) => c.id === id || c.otherUserId === id);
      if (!contact) return;
      const convId = await ensureConversationForContact(contact);
      if (convId) {
        setSelectedContactId(convId);
        loadHistory(convId);
      }
    },
    [ensureConversationForContact, friendsList, loadHistory]
  );

  const handleAcceptRequest = async (requestId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/friend-requests/${requestId}/accept`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) {
        console.warn('Failed to accept friend request', res.status);
      }
      setIncomingRequests((prev) => prev.filter((r) => r.fromId !== requestId));
      loadContacts();
      refreshFriendRequests();
    } catch (err) {
      console.error('Accept friend request failed', err);
    }
  };

  const handleDeclineRequest = async (requestId: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/friend-requests/${requestId}/decline`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Decline friend request failed', err);
    } finally {
      setIncomingRequests((prev) => prev.filter((r) => r.fromId !== requestId));
      refreshFriendRequests();
    }
  };

  const handleCancelRequest = async (requestId: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/friend-requests/${requestId}/cancel`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Cancel friend request failed', err);
    } finally {
      setSentRequests((prev) => prev.filter((r) => r.toId !== requestId));
      refreshFriendRequests();
    }
  };

  const handleSendRequest = async (email: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/friend-requests`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ toEmail: email }),
      });
      if (!res.ok) {
        console.warn('Failed to send friend request', res.status);
        return;
      }
      const fr = await res.json();
      const toUser = fr.toUser || {};
      const newRequest: SentRequest = {
        requestId: fr.id,
        toId: fr.id,
        toUserId: toUser.id ? String(toUser.id) : undefined,
        toName: toUser.username || toUser.email || 'User',
        toUsername: toUser.username || '',
        toEmail: toUser.email || email,
        toAvatar: initials(toUser.username || toUser.email || 'U'),
        timestamp: formatTimeLabel(fr.createdAt),
        status: 'pending',
      };
      setSentRequests((prev) => [...prev, newRequest]);
      // Refresh to pick up mirrored incoming on the other side (poller also runs)
      refreshFriendRequests();
    } catch (err) {
      console.error('Send friend request failed', err);
    }
  };

  const handleSearchUsers = useCallback(
    async (query: string): Promise<UserSearchResult[]> => {
      if (!query.trim()) return [];
      try {
        const res = await fetch(`${API_BASE}/api/v1/users/search?query=${encodeURIComponent(query)}`, {
          method: 'GET',
          credentials: 'include',
        });
        if (!res.ok) return [];
        const data = await res.json();
        return data.map((u: any) => {
          const isFriend = friendsList.some(
            (f) => f.otherUserId === String(u.id) || f.email === u.email
          );
          const hasPendingRequest =
            sentRequests.some((r) => r.toEmail === u.email || r.toUserId === String(u.id)) ||
            incomingRequests.some((r) => r.fromEmail === u.email || r.fromUserId === String(u.id));
          const avatarUrl = u.avatarUrl || u.avatar_url || null;
          return {
            id: String(u.id),
            name: u.username || u.email,
            username: u.username || '',
            email: u.email || '',
            avatar: initials(u.username || u.email || 'U'),
            avatarUrl,
            isFriend,
            hasPendingRequest,
          };
        });
      } catch (err) {
        console.error('Search users failed', err);
        return [];
      }
    },
    [friendsList, incomingRequests, sentRequests]
  );

  const handleSaveAccount = (account: UserAccountDetails) => {
    setUserAccount(account);
    console.log('Account updated:', account);
  };

  return (
    <div className="h-screen flex bg-gray-50">
      <ChatSidebar
        contacts={friendsList}
        selectedContactId={selectedContactId}
        onSelectContact={handleSelectContact}
        onLogout={onLogout}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        onOpenFriendRequests={() => setShowFriendRequests(true)}
        incomingRequestsCount={incomingRequests.length}
        onOpenGroupModal={() => setShowGroupModal(true)}
        onOpenAccount={() => setShowAccount(true)}
      />
      <ChatView
        contact={selectedContact}
        messages={currentMessages}
        onSendMessage={handleSendMessage}
        onEditMessage={handleEditMessage}
        onReact={handleReact}
        typingLabel={
          selectedContact
            ? selectedContact.isGroup
              ? Object.entries(typingUsers)
                  .filter(([uid, expiry]) => uid !== currentUserRef.current && expiry > Date.now())
                  .length > 0
                ? 'Someone is typing...'
                : undefined
              : selectedContact.otherUserId &&
                typingUsers[selectedContact.otherUserId] &&
                typingUsers[selectedContact.otherUserId] > Date.now()
              ? `${selectedContact.name} is typing...`
              : undefined
            : undefined
        }
        onTyping={sendTyping}
      />
      <FriendRequestsModal
        isOpen={showFriendRequests}
        onClose={() => setShowFriendRequests(false)}
        incomingRequests={incomingRequests}
        sentRequests={sentRequests}
        onAcceptRequest={handleAcceptRequest}
        onDeclineRequest={handleDeclineRequest}
        onCancelRequest={handleCancelRequest}
        onSendRequest={handleSendRequest}
        onSearchUsers={handleSearchUsers}
      />
      <AccountModal
        isOpen={showAccount}
        onClose={() => setShowAccount(false)}
        account={userAccount}
        onSave={handleSaveAccount}
      />
      <GroupModal
        isOpen={showGroupModal}
        mode="create"
        friends={friendItems}
        onClose={() => setShowGroupModal(false)}
        onSubmit={handleCreateGroup}
      />
    </div>
  );
}

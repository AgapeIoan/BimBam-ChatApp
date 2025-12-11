import { useCallback, useEffect, useRef, useState } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { ChatView } from './ChatView';
import { FriendRequestsModal } from './FriendRequestsModal';
import { AccountModal } from './AccountModal';
import type { UserAccountDetails } from '../types/user/userAccountDetails';
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
  reactions?: { emoji: string; count: number; reactedByMe?: boolean }[];
}

export interface Contact {
  id: string;
  conversationId?: string;
  name: string;
  avatar: string;
  lastMessage: string;
  timestamp: string;
  unread?: number;
  online?: boolean;
  isFriend?: boolean;
  otherUserId?: string;
  username?: string;
  email?: string;
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

const mapPreviewToContact = (preview: ConversationPreviewResponse): Contact => {
  const other = preview.other_users?.[0];
  const name = other?.username || preview.name || other?.email || 'Conversation';
  return {
    id: String(preview.id),
    conversationId: String(preview.id),
    name,
    avatar: initials(other?.username || other?.email || name),
    lastMessage: preview.last_message || '',
    timestamp: formatTimeLabel(preview.last_message_at),
    unread: preview.unread_count,
    online: false,
    isFriend: true,
    otherUserId: other ? String(other.id) : undefined,
    username: other?.username,
    email: other?.email,
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
  const [userAccount, setUserAccount] = useState<UserAccountDetails>({
    id: currentUser.id,
    username: currentUser.username || '',
    email: currentUser.email,
    avatar_url: currentUser.avatar_url || null,
  });
  const [incomingRequests, setIncomingRequests] = useState<FriendRequest[]>([]);
  const [sentRequests, setSentRequests] = useState<SentRequest[]>([]);

  const pendingRef = useRef<Record<string, { conversationId: string; tempId: string }>>({});
  const selectedConversationRef = useRef<string | null>(null);
  const currentUserRef = useRef<string>(currentUser.id);

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
        return [];
      }
      return (await res.json()) as ConversationPreviewResponse[];
    } catch (err) {
      console.error('Unable to fetch conversations', err);
      return [];
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
        return [];
      }
      const data = await res.json();
      return data as any[];
    } catch (err) {
      console.error('Unable to fetch friends', err);
      return [];
    }
  }, []);

  const mergeFriendsAndConversations = useCallback(
    (friendsData: any[], previews: ConversationPreviewResponse[]) => {
      const prevById = new Map<string, Contact>(friendsList.map((c) => [c.id, c]));
      const convByUserId = new Map<string, ConversationPreviewResponse>();
      previews.forEach((p) => {
        p.other_users?.forEach((u) => convByUserId.set(String(u.id), p));
      });

      const contactsFromFriends: Contact[] = friendsData.map((f) => {
        const friendUser = f.friend || {};
        const friendId = String(friendUser.id || '');
        const conv = convByUserId.get(friendId);
        const name = friendUser.username || friendUser.email || 'Friend';
        const existing = prevById.get(conv ? String(conv.id) : friendId);
        return {
          id: conv ? String(conv.id) : friendId,
          conversationId: conv ? String(conv.id) : undefined,
          name,
          avatar: initials(friendUser.username || friendUser.email || name),
          lastMessage: conv?.last_message || '',
          timestamp: formatTimeLabel(conv?.last_message_at),
          unread: conv?.unread_count ?? f.unread_count ?? 0,
          online: Boolean(f.is_online) || Boolean(existing?.online),
          isFriend: true,
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

      const merged = Array.from(contactsByKey.values());
      setFriendsList(merged);
    },
    [friendsList]
  );

  const loadContacts = useCallback(async () => {
    const [friendsData, previews] = await Promise.all([fetchFriends(), refreshConversations()]);
    mergeFriendsAndConversations(friendsData, previews);
  }, [fetchFriends, mergeFriendsAndConversations, refreshConversations]);

  useEffect(() => {
    loadContacts();
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
      const msg: Message = {
        id: String(payload.messageId || payload.id || safeId()),
        conversationId: convId,
        text: payload.content,
        sender: senderId === currentUserRef.current ? 'me' : 'them',
        timestamp: payload.createdAt ? new Date(payload.createdAt) : new Date(),
        status: payload.read ? 'read' : payload.delivered ? 'delivered' : 'sent',
        editedAt: payload.editedAt,
        editedById: payload.editedById,
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

    if (!targetConv) return;

    const realMessageId = ackMsg?.messageId || data?.messageId;
    const status: Message['status'] =
      data?.status === 'ok' ? (delivered ? 'delivered' : 'sent') : 'failed';

    setMessages((prev) => {
      const conv = prev[targetConv] || [];
      const updated: Message[] = conv.map((msg) => {
        const matchesTemp = pendingInfo && msg.id === pendingInfo.tempId;
        const matchesReal = realMessageId && msg.id === realMessageId;
        if (!matchesTemp && !matchesReal) return msg;

        const reactionsFromCounts = ackMsg?.counts
          ? Object.keys(ackMsg.counts).map((emoji) => ({
              emoji,
              count: ackMsg.counts[emoji],
            }))
          : msg.reactions;

        return {
          ...msg,
          id: realMessageId || msg.id,
          text: ackMsg?.content ?? msg.text,
          timestamp: ackMsg?.createdAt ? new Date(ackMsg.createdAt) : msg.timestamp,
          status,
          editedAt: ackMsg?.editedAt ?? msg.editedAt,
          editedById: ackMsg?.editedById ?? msg.editedById,
          reactions: reactionsFromCounts,
        };
      }) as Message[];
      return { ...prev, [targetConv]: updated };
    });

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
    const reactions = Object.keys(counts).map((k) => ({ emoji: k, count: counts[k] }));
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
      setFriendsList((prev) =>
        prev.map((c) => {
          if (c.otherUserId === userId) {
            seen = true;
            return { ...c, online: isOnline };
          }
          return c;
        })
      );

      if (!seen) {
        loadContacts();
      }
    },
    [loadContacts]
  );

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
        // eslint-disable-next-line no-console
        console.log('typing event', data);
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

  const handleSelectContact = useCallback(
    async (id: string) => {
      const contact = friendsList.find((c) => c.id === id || c.otherUserId === id);
      if (!contact) return;
      const convId = await ensureConversationForContact(contact);
      if (convId) {
        setSelectedContactId(convId);
      }
    },
    [ensureConversationForContact, friendsList]
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
        const existing = (m.reactions || []).find((r) => r.emoji === emoji);
        if (existing) {
          return { ...m, reactions: (m.reactions || []).filter((r) => r.emoji !== emoji) };
        }
        return { ...m, reactions: [...(m.reactions || []), { emoji, count: 1, reactedByMe: true }] };
      });
      return { ...prev, [selectedContactId]: newConv };
    });

    ws.send({ type: 'message_reaction', data: { messageId, emoji, action: 'add' } });
  };

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
          return {
            id: String(u.id),
            name: u.username || u.email,
            username: u.username || '',
            email: u.email || '',
            avatar: initials(u.username || u.email || 'U'),
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
        onOpenAccount={() => setShowAccount(true)}
      />
      <ChatView
        contact={selectedContact}
        messages={currentMessages}
        onSendMessage={handleSendMessage}
        onEditMessage={handleEditMessage}
        onReact={handleReact}
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
    </div>
  );
}

import { useState, useEffect } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { ChatView } from './ChatView';
import { FriendRequestsModal } from './FriendRequestsModal';
import { AccountModal } from './AccountModal';
import { GroupModal } from "./GroupModal";
import type { UserAccountDetails } from '../types/user/userAccountDetails';
import type { Message} from '../types/conversation/chat';
import type { ConversationPreview } from '../types/conversation/conversationPreview';
import type { FriendRequestApi } from '../types/friendRequests/friendRequestApi';
import type { UserSearchResult } from '../types/users/userSearchResult';
import { loadConversationPreviews } from '../services/conversationService';
import { getMe, searchUsers } from '../services/userService';
import {
  acceptFriendRequest,
  declineFriendRequest,
  cancelFriendRequest,
  sendFriendRequest,
  listIncomingRequests,
  listOutgoingRequests,
} from '../services/friendRequestsService';
import type { FriendListItem } from '../types/friend/friendListItem'; 
import { listMyFriends } from '../services/friendsService';

type GroupModalMode = "create" | "edit";
type SearchType = "username" | "email";


export function ChatApp({ onLogout }: Readonly<{ onLogout: () => void }>) {
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showFriendRequests, setShowFriendRequests] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [friendsList, setFriendsList] = useState<FriendListItem[]>([]);
  const [userAccount, setUserAccount] = useState<UserAccountDetails>({
    id: '',
    email: '',
    username: '',
    avatar_url: null,
  }
  )
  const [incomingRequests, setIncomingRequests] = useState<FriendRequestApi[]>([]);
  const [sentRequests, setSentRequests] = useState<FriendRequestApi[]>([]);
  const [conversations, setConversations] = useState<ConversationPreview[]>([]);
  // Group modal state
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [groupModalMode, setGroupModalMode] = useState<GroupModalMode>("create");
  const [editingGroup, setEditingGroup] = useState<ConversationPreview | null>(null);

  useEffect(() => {
    async function fetchConversations() {
      try {
        const previews = await loadConversationPreviews();
        setConversations(previews);
      } catch (e) {
        console.error('Failed to fetch conversations:', e);
      }
    }
    fetchConversations();

    async function fetchRequests() {
      try {
        const [incoming, sent] = await Promise.all([
          listIncomingRequests(),
          listOutgoingRequests(),
        ]);
        setIncomingRequests(incoming);
        setSentRequests(sent);
      } catch (e) {
        console.error('Failed to fetch friend requests:', e);
      }
    }
    fetchRequests();

    async function fetchUserAccount() {
      try {
        const me = await getMe();
        setUserAccount(me);
      } catch (e) {
        console.error('Failed to fetch user account:', e);
      }
    }
    fetchUserAccount();

    async function fetchFriendsList() {
      try {
        const friends = await listMyFriends();
        setFriendsList(friends);
      } catch (e) {
        console.error('Failed to fetch friends list:', e);
      } 
    }
    fetchFriendsList();
  }, []);

  const selectedContact = friendsList.find((c) => c.friend.id === selectedContactId);
  const currentMessages = selectedContactId ? messages[selectedContactId] || [] : [];

  const handleSendMessage = (text: string) => {
    if (!selectedContactId) return;

    const selectedFriend = friendsList.find((c) => c.friend.id === selectedContactId);
    if (!selectedFriend) {
      console.log('Cannot send message: contact not found');
      return;
    }

    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'me',
      timestamp: new Date(),
      status: 'sent',
    };

    setMessages((prev) => ({
      ...prev,
      [selectedContactId]: [...(prev[selectedContactId] || []), newMessage],
    }));

    // Simulate status progression
    setTimeout(() => {
      setMessages((prev) => ({
        ...prev,
        [selectedContactId]: prev[selectedContactId].map((msg) =>
          msg.id === newMessage.id ? { ...msg, status: 'delivered' } : msg
        ),
      }));
    }, 1000);

    setTimeout(() => {
      setMessages((prev) => ({
        ...prev,
        [selectedContactId]: prev[selectedContactId].map((msg) =>
          msg.id === newMessage.id ? { ...msg, status: 'read' } : msg
        ),
      }));
    }, 3000);
  };

  const handleAcceptRequest = async (id: string) => {
    try {
      await acceptFriendRequest(id);
      const friends = await listMyFriends();
      setFriendsList(friends);
      const incoming = await listIncomingRequests();
      setIncomingRequests(incoming);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeclineRequest = async (id: string) => {
    try {
      await declineFriendRequest(id);
      setIncomingRequests((prev) => prev.filter((r) => r.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleCancelRequest = async (id: string) => {
    try {
      await cancelFriendRequest(id);
      setSentRequests((prev) => prev.filter((r) => r.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendRequest = async (toEmail: string) => {
    try {
      const newRequest = await sendFriendRequest(toEmail);
      setSentRequests((prev) => [...prev, newRequest]);
      console.log('Sending friend request to:', toEmail);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSearchUsers = async (query: string, type: SearchType): Promise<UserSearchResult[]> => {
    const results = await searchUsers(query, type);
    return results.map(user => {
      const isFriend = friendsList.some(f => f.friend.id === user.id);
      const hasPendingRequest = incomingRequests.some(r => r.fromUser.username === user.username) ||
        sentRequests.some(r => r.toUser.username === user.username);
      return {
        username: user.username,
        email: user.email,
        avatarUrl: user.avatarUrl,
        isFriend: isFriend,
        hasPendingRequest: hasPendingRequest,
      };
    });
  };

  const handleSaveAccount = (account: UserAccountDetails) => {
    setUserAccount(account);
    console.log('Account updated:', account);
  };

  // Handler to open create group modal
  const handleOpenCreateGroup = () => {
    setGroupModalMode("create");
    setEditingGroup(null);
    setShowGroupModal(true);
  };

  // Handler to open edit group modal
  const handleOpenEditGroup = (conversationId: string) => {
    const conv = conversations.find((c) => c.id === conversationId && c.isGroup);
    if (!conv) return;
    setGroupModalMode("edit");
    setEditingGroup(conv);
    setShowGroupModal(true);
  };

  // Handler for group modal submit
  const handleGroupModalSubmit = (groupName: string, memberIds: string[]) => {
    if (groupModalMode === "create") {
      // Create new group
      const selectedMembers = friendsList.filter((f) => memberIds.includes(f.friend.id));
      const newGroup: ConversationPreview = {
        id: `group-${Date.now()}`,
        isGroup: true,
        name: groupName,
        lastMessage: "last message",
        lastMessageAt: "Just now",
        otherUsers: selectedMembers.map((member) => ({
          username: member.friend.username,
          email: member.friend.email,
          avatarUrl: member.friend.avatarUrl ?? "",
          lastseenAt: new Date(),
          provider: "email",
          id: member.friend.id,
        })),
        unreadCount: 0,
      };
      setConversations((prev) => [newGroup, ...prev]);
      setMessages((prev) => ({ ...prev, [newGroup.id]: [] }));
      setSelectedContactId(newGroup.id);
    } else if (groupModalMode === "edit" && editingGroup) {
      // Edit group
      const selectedMembers = friendsList.filter((f) => memberIds.includes(f.friend.id));
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === editingGroup.id
            ? {
                ...conv,
                name: groupName,
                other_users: selectedMembers.map((member) => ({
                  id: member.friend.id,
                  username: member.friend.username,
                  email: member.friend.email,
                  avatarUrl: member.friend.avatarUrl,
                  isOnline: false,
                })),
              }
            : conv
        )
      );
    }
    setShowGroupModal(false);
    setEditingGroup(null);
  };

  // Custom handler for selecting contact
  const handleSelectContact = async (contactId: string) => {
    // Verifică dacă există conversație cu mesaje pentru contactul selectat
    const hasConversation = conversations.some(
      (conv) => Array.isArray(conv.otherUsers) && conv.otherUsers.some((u) => u.id === contactId)
    );
    if (!hasConversation) {
      // Creează sau deschide conversația directă
      try {
        await import('../services/conversationService').then(m => m.openOrCreateDirectConversation(contactId));
        const previews = await loadConversationPreviews();
        setConversations(previews);
      } catch (e) {
        console.error('Failed to open or create direct conversation:', e);
      }
    }
    setSelectedContactId(contactId);
  };

  return (
    <div className="h-screen flex bg-gray-50">
      <ChatSidebar
        contacts={friendsList}
        conversations={conversations}
        selectedContactId={selectedContactId}
        onSelectContact={handleSelectContact}
        onLogout={onLogout}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        onOpenFriendRequests={() => setShowFriendRequests(true)}
        incomingRequestsCount={incomingRequests.length}
        onOpenAccount={() => setShowAccount(true)}
        onOpenCreateGroup={handleOpenCreateGroup}
      />
      <ChatView
        contact={selectedContact}
        messages={currentMessages}
        onSendMessage={handleSendMessage}
        onEditGroup={handleOpenEditGroup}
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
        mode={groupModalMode}
        onClose={() => {
          setShowGroupModal(false);
          setEditingGroup(null);
        }}
        friends={friendsList}
        initialName={groupModalMode === "edit" ? editingGroup?.name ?? "" : ""}
        initialMemberIds={groupModalMode === "edit" ? editingGroup?.otherUsers.map((u) => u.id) ?? [] : []}
        onSubmit={handleGroupModalSubmit}
      />
    </div>
  );
}
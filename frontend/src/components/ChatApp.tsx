import { useState, useEffect } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { ChatView } from './ChatView';
import { FriendRequestsModal } from './FriendRequestsModal';
import { AccountModal } from './AccountModal';
import { GroupModal } from "./GroupModal";
import { v4 as uuidv4 } from 'uuid';
import type { UserAccount } from './AccountModal';
import type { Message, ConversationUser, ConversationPreview } from '../types/chat';
import type { FriendRequestApi, UserSearchResult} from '../types/friendRequests';
import { loadConversationPreviews } from '../services/conversationService';

type GroupModalMode = "create" | "edit";
import {
  acceptFriendRequest,
  declineFriendRequest,
  cancelFriendRequest,
  sendFriendRequest,
  searchUsers,
  listIncomingRequests,
  listOutgoingRequests,
} from '../services/friendRequestsService';

export function ChatApp({ onLogout }: Readonly<{ onLogout: () => void }>) {
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showFriendRequests, setShowFriendRequests] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [friendsList, setFriendsList] = useState<ConversationUser[]>([]);
  const [userAccount, setUserAccount] = useState<UserAccount>({
    name: 'Alex Morgan',
    username: 'alexmorgan',
    email: 'alex.morgan@email.com',
    password: 'password123',
    signUpMethod: 'email',
  });
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
  }, []);

  const selectedContact = friendsList.find((c) => c.id === selectedContactId);
  const currentMessages = selectedContactId ? messages[selectedContactId] || [] : [];

  const handleSendMessage = (text: string) => {
    if (!selectedContactId) return;

    const selectedFriend = friendsList.find((c) => c.id === selectedContactId);
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
      const updated = await acceptFriendRequest(id);
      const newFriend: ConversationUser = {
        id: uuidv4(),
        username: updated.fromUser.username,
        email: updated.fromUser.email,
        avatarUrl: updated.fromUser.avatarUrl ?? "",
        provider:  'debug',
        lastseenAt: new Date(),
      };
      setFriendsList((prev) => [...prev, newFriend]);
      setIncomingRequests((prev) => prev.filter((r) => r.id !== id));
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

  const handleSearchUsers = (query: string): UserSearchResult[] => {
    const results = searchUsers(query);
    return results.map(user => {
      const isFriend = friendsList.some(f => f.username === user.username);
      const hasPendingRequest = sentRequests.some(r => r.toUser.username === user.username);
      return { ...user, isFriend, hasPendingRequest };
    });
  };

  const handleSaveAccount = (account: UserAccount) => {
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
      const selectedMembers = friendsList.filter((f) => memberIds.includes(f.id));
      const newGroup: ConversationPreview = {
        id: `group-${Date.now()}`,
        isGroup: true,
        name: groupName,
        lastMessage: "last message",
        lastMessageAt: "Just now",
        otherUsers: selectedMembers.map((member) => ({
          username: member.username,
          email: member.email,
          avatarUrl: member.avatarUrl,
          lastseenAt: new Date(),
          provider: "email",
          id: member.id,
        })),
        unreadCount: 0,
      };
      setConversations((prev) => [newGroup, ...prev]);
      setMessages((prev) => ({ ...prev, [newGroup.id]: [] }));
      setSelectedContactId(newGroup.id);
    } else if (groupModalMode === "edit" && editingGroup) {
      // Edit group
      const selectedMembers = friendsList.filter((f) => memberIds.includes(f.id));
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === editingGroup.id
            ? {
                ...conv,
                name: groupName,
                other_users: selectedMembers.map((member) => ({
                  id: member.id,
                  username: member.username,
                  email: member.email,
                  avatarUrl: member.avatarUrl,
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

  return (
    <div className="h-screen flex bg-gray-50">
      <ChatSidebar
        contacts={friendsList}
        conversations={conversations}
        selectedContactId={selectedContactId}
        onSelectContact={setSelectedContactId}
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
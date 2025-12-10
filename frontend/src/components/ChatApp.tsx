import { useState, useEffect } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { ChatView } from './ChatView';
import { FriendRequestsModal } from './FriendRequestsModal';
import { AccountModal } from './AccountModal';
import type { UserAccount } from './AccountModal';
import type { Message, Contact} from '../types/chat';
import type { FriendRequestApi, UserSearchResult} from '../types/friendRequests';
import { mockContacts, mockConversations } from '../mock_data/chat';
import {
  acceptFriendRequest,
  declineFriendRequest,
  cancelFriendRequest,
  sendFriendRequest,
  searchUsers,
  listIncomingRequests,
  listOutgoingRequests,
} from '../services/friendRequestsService';
const contacts = mockContacts;

const conversations: Record<string, Message[]> = mockConversations;

export function ChatApp({ onLogout }: Readonly<{ onLogout: () => void }>) {
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, Message[]>>(conversations);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showFriendRequests, setShowFriendRequests] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [friendsList, setFriendsList] = useState<Contact[]>(contacts);
  const [userAccount, setUserAccount] = useState<UserAccount>({
    name: 'Alex Morgan',
    username: 'alexmorgan',
    email: 'alex.morgan@email.com',
    password: 'password123',
    signUpMethod: 'email',
  });
  const [incomingRequests, setIncomingRequests] = useState<FriendRequestApi[]>([]);
  const [sentRequests, setSentRequests] = useState<FriendRequestApi[]>([]);

  useEffect(() => {
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
    if (!selectedFriend?.isFriend) {
      console.log('Cannot send message to non-friend');
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
      // Add to friends list
      const newFriend: Contact = {
        id: updated.fromUser.username,
        name: updated.fromUser.username,
        avatar: updated.fromUser.avatarUrl || '',
        lastMessage: '',
        timestamp: 'Just now',
        online: false,
        isFriend: true,
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
    // Folosește serviciul mock pentru search
    const results = searchUsers(query);
    return results.map(user => {
      const isFriend = friendsList.some(f => f.name === user.username);
      const hasPendingRequest = sentRequests.some(r => r.toUser.username === user.username);
      return { ...user, isFriend, hasPendingRequest };
    });
  };

  const handleSaveAccount = (account: UserAccount) => {
    setUserAccount(account);
    console.log('Account updated:', account);
  };

  return (
    <div className="h-screen flex bg-gray-50">
      <ChatSidebar
        contacts={friendsList}
        selectedContactId={selectedContactId}
        onSelectContact={setSelectedContactId}
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
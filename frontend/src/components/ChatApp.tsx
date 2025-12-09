import { useState } from 'react';
import { ChatSidebar } from './ChatSidebar';
import { ChatView } from './ChatView';
import { FriendRequestsModal } from './FriendRequestsModal';
import { AccountModal } from './AccountModal';
import type { UserAccount } from './AccountModal';

export interface Message {
  id: string;
  text: string;
  sender: 'me' | 'them';
  timestamp: Date;
  status?: 'sent' | 'delivered' | 'read' | 'failed';
}

export interface Contact {
  id: string;
  name: string;
  avatar: string;
  lastMessage: string;
  timestamp: string;
  unread?: number;
  online?: boolean;
  isFriend?: boolean;
}

export interface FriendRequest {
  fromId: string;
  fromName: string;
  fromUsername: string;
  fromEmail: string;
  fromAvatar: string;
  timestamp: string;
  status: 'pending' | 'accepted' | 'rejected';
}

export interface SentRequest {
  toId: string;
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

// Mock data
const contacts: Contact[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    avatar: 'SJ',
    lastMessage: 'See you tomorrow!',
    timestamp: '2m ago',
    unread: 2,
    online: true,
    isFriend: true,
  },
  {
    id: '2',
    name: 'Mike Chen',
    avatar: 'MC',
    lastMessage: 'Thanks for the help',
    timestamp: '1h ago',
    online: true,
    isFriend: true,
  },
  {
    id: '3',
    name: 'Emma Wilson',
    avatar: 'EW',
    lastMessage: 'Did you get my email?',
    timestamp: '3h ago',
    unread: 1,
    online: false,
    isFriend: true,
  },
  {
    id: '4',
    name: 'Alex Turner',
    avatar: 'AT',
    lastMessage: 'Perfect, sounds good',
    timestamp: 'Yesterday',
    online: false,
    isFriend: true,
  },
  {
    id: '5',
    name: 'Lisa Park',
    avatar: 'LP',
    lastMessage: 'Let me check and get back',
    timestamp: 'Yesterday',
    online: true,
    isFriend: true,
  },
  {
    id: '6',
    name: 'David Martinez',
    avatar: 'DM',
    lastMessage: 'Have a great weekend!',
    timestamp: '2 days ago',
    online: false,
    isFriend: true,
  },
];

const mockConversations: Record<string, Message[]> = {
  '1': [
    {
      id: '1',
      text: 'Hey! How are you doing?',
      sender: 'them',
      timestamp: new Date(Date.now() - 3600000),
    },
    {
      id: '2',
      text: "I'm doing great, thanks! How about you?",
      sender: 'me',
      timestamp: new Date(Date.now() - 3500000),
      status: 'read',
    },
    {
      id: '3',
      text: 'Pretty good! Are we still on for the meeting tomorrow?',
      sender: 'them',
      timestamp: new Date(Date.now() - 3400000),
    },
    {
      id: '4',
      text: 'Yes absolutely! 2pm works for me.',
      sender: 'me',
      timestamp: new Date(Date.now() - 3300000),
      status: 'read',
    },
    {
      id: '5',
      text: 'See you tomorrow!',
      sender: 'them',
      timestamp: new Date(Date.now() - 120000),
    },
  ],
  '2': [
    {
      id: '1',
      text: 'Could you help me with the project?',
      sender: 'them',
      timestamp: new Date(Date.now() - 7200000),
    },
    {
      id: '2',
      text: 'Sure! What do you need help with?',
      sender: 'me',
      timestamp: new Date(Date.now() - 7100000),
      status: 'read',
    },
    {
      id: '3',
      text: 'Thanks for the help',
      sender: 'them',
      timestamp: new Date(Date.now() - 3600000),
    },
  ],
  '3': [
    {
      id: '1',
      text: 'Did you get my email?',
      sender: 'them',
      timestamp: new Date(Date.now() - 10800000),
    },
  ],
  '4': [
    {
      id: '1',
      text: 'Want to grab lunch next week?',
      sender: 'them',
      timestamp: new Date(Date.now() - 86400000),
    },
    {
      id: '2',
      text: 'Perfect, sounds good',
      sender: 'them',
      timestamp: new Date(Date.now() - 86000000),
    },
  ],
  '5': [
    {
      id: '1',
      text: 'Can you review the document?',
      sender: 'them',
      timestamp: new Date(Date.now() - 86400000),
    },
    {
      id: '2',
      text: 'Let me check and get back',
      sender: 'them',
      timestamp: new Date(Date.now() - 85000000),
    },
  ],
  '6': [
    {
      id: '1',
      text: 'Have a great weekend!',
      sender: 'them',
      timestamp: new Date(Date.now() - 172800000),
    },
  ],
};

export function ChatApp({ onLogout }: { onLogout: () => void }) {
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, Message[]>>(mockConversations);
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
  const [incomingRequests, setIncomingRequests] = useState<FriendRequest[]>([
    {
      fromId: '1',
      fromName: 'John Doe',
      fromUsername: 'johndoe',
      fromEmail: 'john.doe@email.com',
      fromAvatar: 'JD',
      timestamp: '5m ago',
      status: 'pending',
    },
    {
      fromId: '2',
      fromName: 'Jane Smith',
      fromUsername: 'janesmith',
      fromEmail: 'jane.smith@email.com',
      fromAvatar: 'JS',
      timestamp: '1h ago',
      status: 'pending',
    },
  ]);
  const [sentRequests, setSentRequests] = useState<SentRequest[]>([
    {
      toId: '1',
      toName: 'Bob Wilson',
      toUsername: 'bobwilson',
      toEmail: 'bob.wilson@email.com',
      toAvatar: 'BW',
      timestamp: '2h ago',
      status: 'pending',
    },
  ]);

  // Mock user database for search
  const mockUsers: UserSearchResult[] = [
    {
      id: 'u1',
      name: 'Tom Anderson',
      username: 'tomanderson',
      email: 'tom.anderson@email.com',
      avatar: 'TA',
      isFriend: false,
      hasPendingRequest: false,
    },
    {
      id: 'u2',
      name: 'Rachel Green',
      username: 'rachelgreen',
      email: 'rachel.green@email.com',
      avatar: 'RG',
      isFriend: false,
      hasPendingRequest: false,
    },
    {
      id: 'u3',
      name: 'Monica Geller',
      username: 'monicageller',
      email: 'monica.geller@email.com',
      avatar: 'MG',
      isFriend: false,
      hasPendingRequest: false,
    },
    {
      id: 'u4',
      name: 'Ross Geller',
      username: 'rossgeller',
      email: 'ross.geller@email.com',
      avatar: 'RG',
      isFriend: false,
      hasPendingRequest: false,
    },
    {
      id: 'u5',
      name: 'Chandler Bing',
      username: 'chandlerbing',
      email: 'chandler.bing@email.com',
      avatar: 'CB',
      isFriend: false,
      hasPendingRequest: false,
    },
    {
      id: 'u6',
      name: 'Joey Tribbiani',
      username: 'joeytribbiani',
      email: 'joey.tribbiani@email.com',
      avatar: 'JT',
      isFriend: false,
      hasPendingRequest: false,
    },
    {
      id: 'u7',
      name: 'Phoebe Buffay',
      username: 'phoebebuffay',
      email: 'phoebe.buffay@email.com',
      avatar: 'PB',
      isFriend: false,
      hasPendingRequest: false,
    },
  ];

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

  const handleAcceptRequest = (id: string) => {
    const request = incomingRequests.find((r) => r.fromId === id);
    if (request) {
      // Add to friends list
      const newFriend: Contact = {
        id: Date.now().toString(),
        name: request.fromName,
        avatar: request.fromAvatar,
        lastMessage: '',
        timestamp: 'Just now',
        online: false,
        isFriend: true,
      };
      setFriendsList((prev) => [...prev, newFriend]);
      
      // Remove from incoming requests
      setIncomingRequests((prev) => prev.filter((r) => r.fromId !== id));
    }
  };

  const handleDeclineRequest = (id: string) => {
    setIncomingRequests((prev) => prev.filter((r) => r.fromId !== id));
  };

  const handleCancelRequest = (id: string) => {
    setSentRequests((prev) => prev.filter((r) => r.toId !== id));
  };

  const handleSendRequest = (usernameOrEmail: string) => {
    // Simulate sending a friend request
    const newRequest: SentRequest = {
      toId: Date.now().toString(),
      toName: usernameOrEmail,
      toUsername: usernameOrEmail.substring(0, 2).toUpperCase(),
      toEmail: usernameOrEmail + '@email.com',
      toAvatar: usernameOrEmail.substring(0, 2).toUpperCase(),
      timestamp: 'Just now',
      status: 'pending',
    };
    setSentRequests((prev) => [...prev, newRequest]);
    console.log('Sending friend request to:', usernameOrEmail);
  };

  const handleSearchUsers = (query: string): UserSearchResult[] => {
    // Search by username or email
    const lowerQuery = query.toLowerCase();
    const results = mockUsers.filter(user => {
      const matchesUsername = user.username.toLowerCase().includes(lowerQuery);
      const matchesEmail = user.email.toLowerCase().includes(lowerQuery);
      return matchesUsername || matchesEmail;
    });

    // Mark users who are already friends or have pending requests
    return results.map(user => {
      const isFriend = friendsList.some(f => f.name === user.name);
      const hasPendingRequest = sentRequests.some(r => r.toUsername === user.username);
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
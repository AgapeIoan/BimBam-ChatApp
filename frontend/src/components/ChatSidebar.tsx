import { Search, MessageCircle, MoreVertical, LogOut, UserPlus, UserCircle, Users } from 'lucide-react';
import type { Contact } from './ChatApp';
import { useMemo, useState } from 'react';

interface ChatSidebarProps {
  contacts: Contact[];
  selectedContactId: string | null;
  onSelectContact: (id: string) => void;
  onLogout: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onOpenFriendRequests: () => void;
  incomingRequestsCount: number;
  onOpenGroupModal: () => void;
  onOpenAccount: () => void;
}

export function ChatSidebar({ 
  contacts, 
  selectedContactId, 
  onSelectContact, 
  onLogout, 
  isCollapsed, 
  onToggleCollapse,
  onOpenFriendRequests,
  incomingRequestsCount,
  onOpenGroupModal,
  onOpenAccount
}: ChatSidebarProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const visible = contacts.filter((c) => c.isFriend || c.isGroup);
    if (!q) return visible;
    return visible.filter((c) => {
      return (
        c.name.toLowerCase().includes(q) ||
        (c.username && c.username.toLowerCase().includes(q)) ||
        (c.email && c.email.toLowerCase().includes(q))
      );
    });
  }, [contacts, search]);

  return (
    <div className={`bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ${isCollapsed ? 'w-20' : 'w-80'}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <button 
              onClick={onToggleCollapse}
              className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center hover:bg-blue-700 transition-colors flex-shrink-0"
            >
              <MessageCircle className="w-6 h-6 text-white" />
            </button>
            {!isCollapsed && <span className="text-gray-900">BimBam Chat</span>}
          </div>
          {!isCollapsed && (
            <div className="relative">
              <button 
                onClick={() => setShowMenu(!showMenu)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <MoreVertical className="w-5 h-5 text-gray-600" />
              </button>
              {showMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      onOpenAccount();
                    }}
                    className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <UserCircle className="w-4 h-4" />
                    Account
                  </button>
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      onLogout();
                    }}
                    className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Friend Request Button */}
        {!isCollapsed && (
          <button
            onClick={onOpenFriendRequests}
            className="w-full mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 relative"
          >
            <UserPlus className="w-4 h-4" />
            <span>Friend Requests</span>
            {incomingRequestsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {incomingRequestsCount}
              </span>
            )}
          </button>
        )}
        {!isCollapsed && (
          <button
            onClick={onOpenGroupModal}
            className="w-full mb-4 px-4 py-2 border border-gray-200 bg-white text-blue-700 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors flex items-center justify-center gap-2 shadow-sm"
          >
            <Users className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold tracking-wide">Create Group</span>
          </button>
        )}

        {isCollapsed && (
          <button
            onClick={onOpenFriendRequests}
            className="w-full mb-4 p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center relative"
            title="Friend Requests"
          >
            <UserPlus className="w-5 h-5" />
            {incomingRequestsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {incomingRequestsCount}
              </span>
            )}
          </button>
        )}
        {isCollapsed && (
          <button
            onClick={onOpenGroupModal}
            className="w-full mb-4 p-3 border border-gray-200 bg-white text-blue-700 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors flex items-center justify-center shadow-sm"
            title="Create Group"
          >
            <Users className="w-5 h-5 text-blue-600" />
          </button>
        )}

        {/* Search */}
        {!isCollapsed && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search conversations..."
              className="w-full pl-10 pr-4 py-2 bg-gray-100 border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}
      </div>

      {/* Contacts List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.map((contact) => (
          <button
            key={contact.id}
            onClick={() => onSelectContact(contact.id)}
            className={`w-full p-4 flex items-start gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100 ${
              selectedContactId === contact.id ? 'bg-blue-50' : ''
            }`}
            title={isCollapsed ? contact.name : undefined}
          >
            {/* Avatar */}
            <div className="relative flex-shrink-0">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white">
                {contact.avatar}
              </div>
              {contact.online && (
                <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
              )}
              {isCollapsed && (contact.unread ?? 0) > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                  {contact.unread}
                </div>
              )}
            </div>

            {/* Contact Info */}
            {!isCollapsed && (
              <div className="flex-1 min-w-0 text-left">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-gray-900 truncate">{contact.name}</span>
                  <span className="text-gray-500 text-xs flex-shrink-0 ml-2">{contact.timestamp}</span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-gray-600 text-sm truncate">{contact.lastMessage}</p>
                  {(contact.unread ?? 0) > 0 && (
                    <div className="flex-shrink-0 ml-2 w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                      {contact.unread}
                    </div>
                  )}
                </div>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

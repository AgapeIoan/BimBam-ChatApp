import { useState } from "react";
import {
  X,
  UserPlus,
  Mail,
  User as UserIcon,
  Check,
  XCircle,
  Clock,
} from "lucide-react";

export interface FriendRequest {
  fromId: string;
  fromName: string;
  fromUsername: string;
  fromEmail: string;
  fromAvatar: string;
  timestamp: string;
  status: "pending" | "accepted" | "rejected";
}

export interface SentRequest {
  toId: string;
  toName: string;
  toUsername: string;
  toEmail: string;
  toAvatar: string;
  timestamp: string;
  status: "pending" | "accepted" | "rejected";
}

interface FriendRequestsModalProps {
  isOpen: boolean;
  onClose: () => void;
  incomingRequests: FriendRequest[];
  sentRequests: SentRequest[];
  onAcceptRequest: (id: string) => void;
  onDeclineRequest: (id: string) => void;
  onCancelRequest: (id: string) => void;
  onSendRequest: (userId: string) => void;
  onSearchUsers: (query: string) => Promise<UserSearchResult[]> | UserSearchResult[];
}

export function FriendRequestsModal({
  isOpen,
  onClose,
  incomingRequests,
  sentRequests,
  onAcceptRequest,
  onDeclineRequest,
  onCancelRequest,
  onSendRequest,
  onSearchUsers,
}: FriendRequestsModalProps) {
  const [activeTab, setActiveTab] = useState<
    "send" | "incoming" | "sent"
  >("send");
  const [searchValue, setSearchValue] = useState("");
  const [searchType, setSearchType] = useState<
    "username" | "email"
  >("username");
  const [searchResults, setSearchResults] = useState<
    UserSearchResult[]
  >([]);

  if (!isOpen) return null;

  const handleSearchChange = async (value: string) => {
    setSearchValue(value);
    if (value.trim()) {
      const results = await onSearchUsers(value.trim());
      setSearchResults(results);
    } else {
      setSearchResults([]);
    }
  };

  const handleSendRequest = (userEmail: string) => {
    onSendRequest(userEmail);
    setSearchValue("");
    setSearchResults([]);
  };

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ background: "rgba(0,0,0,0.5)" }}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl h-[600px] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
          <h2 className="text-gray-900">Friend Requests</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 flex-shrink-0">
          <button
            onClick={() => setActiveTab("send")}
            className={`flex-1 px-6 py-3 transition-colors ${
              activeTab === "send"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <UserPlus className="w-4 h-4" />
              <span>Send Request</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab("incoming")}
            className={`flex-1 px-6 py-3 transition-colors ${
              activeTab === "incoming"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span>Incoming</span>
              {incomingRequests.length > 0 && (
                <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                  {incomingRequests.length}
                </span>
              )}
            </div>
          </button>
          <button
            onClick={() => setActiveTab("sent")}
            className={`flex-1 px-6 py-3 transition-colors ${
              activeTab === "sent"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span>Sent</span>
              {sentRequests.length > 0 && (
                <span className="bg-gray-400 text-white text-xs px-2 py-0.5 rounded-full">
                  {sentRequests.length}
                </span>
              )}
            </div>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Send Request Tab */}
          {activeTab === "send" && (
            <div className="space-y-4">
              <p className="text-gray-600">
                Add friends by their username or email address
              </p>

              {/* Search Type Toggle */}
              <div className="flex gap-2">
                <button
                  onClick={() => setSearchType("username")}
                  className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                    searchType === "username"
                      ? "bg-blue-50 border-blue-600 text-blue-600"
                      : "border-gray-300 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-center gap-2">
                    <UserIcon className="w-4 h-4" />
                    <span>Username</span>
                  </div>
                </button>
                <button
                  onClick={() => setSearchType("email")}
                  className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                    searchType === "email"
                      ? "bg-blue-50 border-blue-600 text-blue-600"
                      : "border-gray-300 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-center gap-2">
                    <Mail className="w-4 h-4" />
                    <span>Email</span>
                  </div>
                </button>
              </div>

              {/* Search Input */}
              <div className="relative">
                {searchType === "username" ? (
                  <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                ) : (
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                )}
                <input
                  type={
                    searchType === "email" ? "email" : "text"
                  }
                  value={searchValue}
                  onChange={(e) =>
                    handleSearchChange(e.target.value)
                  }
                  placeholder={
                    searchType === "username"
                      ? "Search by username..."
                      : "Search by email..."
                  }
                  className="w-full pl-11 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="space-y-2 max-h-96 overflow-y-auto animate-fadeIn">
                  <p className="text-gray-700 text-sm">
                    Search Results
                  </p>
                  {searchResults.map((user, index) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 animate-slideIn"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white flex-shrink-0">
                          {user.avatar}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-gray-900 truncate">
                            {user.name}
                          </p>
                          <p className="text-gray-600 text-sm truncate">
                            @{user.username}
                          </p>
                          <p className="text-gray-500 text-xs truncate">
                            {user.email}
                          </p>
                        </div>
                      </div>
                      <div className="ml-3 flex-shrink-0">
                        {user.isFriend ? (
                          <span className="px-4 py-2 text-gray-500 text-sm">
                            Already friends
                          </span>
                        ) : user.hasPendingRequest ? (
                          <span className="px-4 py-2 text-gray-500 text-sm">
                            Request sent
                          </span>
                        ) : (
                          <button
                            onClick={() =>
                              handleSendRequest(user.email)
                            }
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                          >
                            <UserPlus className="w-4 h-4" />
                            <span>Add</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {searchValue && searchResults.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">
                    No users found matching "{searchValue}"
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Incoming Requests Tab */}
          {activeTab === "incoming" && (
            <div className="space-y-3">
              {incomingRequests.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <UserPlus className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-gray-500">
                    No incoming friend requests
                  </p>
                </div>
              ) : (
                incomingRequests.map((request) => (
                  <div
                    key={request.fromId}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white">
                        {request.fromAvatar}
                      </div>
                      <div>
                        <p className="text-gray-900 truncate">
                          {request.fromName}
                        </p>
                        <p className="text-gray-600 text-sm truncate">
                          @{request.fromUsername}
                        </p>
                        <p className="text-gray-500 text-xs truncate">
                          {request.fromEmail}
                        </p>
                        <p className="text-gray-400 text-xs mt-1">
                          Requested {request.timestamp}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() =>
                          onAcceptRequest(request.fromId)
                        }
                        className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <Check className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() =>
                          onDeclineRequest(request.fromId)
                        }
                        className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
                      >
                        <XCircle className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Sent Requests Tab */}
          {activeTab === "sent" && (
            <div className="space-y-3">
              {sentRequests.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Clock className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-gray-500">
                    No pending sent requests
                  </p>
                </div>
              ) : (
                sentRequests.map((request) => (
                  <div
                    key={request.toId}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white flex-shrink-0">
                        {request.toAvatar}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-gray-900 truncate">
                          {request.toName}
                        </p>
                        <p className="text-gray-600 text-sm truncate">
                          @{request.toUsername}
                        </p>
                        <p className="text-gray-500 text-xs truncate">
                          {request.toEmail}
                        </p>
                        <p className="text-gray-400 text-xs mt-1">
                          Sent {request.timestamp}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() =>
                        onCancelRequest(request.toId)
                      }
                      className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors ml-3 flex-shrink-0"
                    >
                      Cancel
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export interface UserSearchResult {
  id: string;
  username: string;
  email: string;
  avatar: string;
  name: string;
  isFriend: boolean;
  hasPendingRequest: boolean;
}

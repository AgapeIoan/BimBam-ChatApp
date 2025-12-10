import { useState, useEffect } from "react";
import { X, Users } from "lucide-react";
import type { FriendListItem } from "../types/friend/friendListItem";

interface GroupModalProps {
  isOpen: boolean;
  mode: "create" | "edit";
  onClose: () => void;
  friends: FriendListItem[];
  initialName?: string;
  initialMemberIds?: string[];
  onSubmit: (name: string, memberIds: string[]) => void;
}

export function GroupModal({
  isOpen,
  mode,
  onClose,
  friends,
  initialName = "",
  initialMemberIds = [],
  onSubmit,
}: GroupModalProps) {
  const [groupName, setGroupName] = useState(initialName);
  const [selectedFriends, setSelectedFriends] = useState<
    Set<string>
  >(new Set(initialMemberIds));
  const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
    if (isOpen) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setGroupName(initialName);
      setSelectedFriends(new Set(initialMemberIds));
      setSearchQuery("");
    }
  }, [isOpen, initialName, initialMemberIds]);

  if (!isOpen) return null;

  const handleToggleFriend = (friendId: string) => {
    setSelectedFriends((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(friendId)) {
        newSet.delete(friendId);
      } else {
        newSet.add(friendId);
      }
      return newSet;
    });
  };

  const handleSubmit = () => {
    if (groupName.trim() && selectedFriends.size > 0) {
      onSubmit(groupName.trim(), Array.from(selectedFriends));
      onClose();
    }
  };

  const handleClose = () => {
    onClose();
  };

  const filteredFriends = friends
    .filter((friend) =>
      friend.friend.username
        .toLowerCase()
        .includes(searchQuery.toLowerCase()),
    )
    .sort((a, b) => {
      const aSelected = selectedFriends.has(a.friend.id);
      const bSelected = selectedFriends.has(b.friend.id);

      if (aSelected === bSelected) return 0;
      return aSelected ? -1 : 1;
    });

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 p-4" style={{ background: "rgba(0,0,0,0.5)" }}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl h-[600px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-gray-900">
              {mode === "create"
                ? "Create Group"
                : "Edit Group"}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
          {/* Group Name */}
          <div>
            <label className="block text-sm text-gray-700 mb-2">
              Group Name
            </label>
            <input
              type="text"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              placeholder="Enter group name"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Selected Count */}
          {selectedFriends.size > 0 && (
            <div className="px-4 py-2 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-700">
                {selectedFriends.size} member
                {selectedFriends.size !== 1 ? "s" : ""} selected
              </p>
            </div>
          )}

          {/* Search + Friends list */}
          <div>
            <label className="block text-sm text-gray-700 mb-2">
              {mode === "create"
                ? "Add Members"
                : "Edit Members"}
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search friends..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
            />

            <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-hide">
              {filteredFriends.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">
                    {searchQuery
                      ? "No friends found"
                      : "No friends to add"}
                  </p>
                </div>
              ) : (
                filteredFriends.map((friend) => {
                  const isSelected = selectedFriends.has(
                    friend.friend.id,
                  );
                  return (
                    <button
                      key={friend.friend.id}
                      onClick={() =>
                        handleToggleFriend(friend.friend.id)
                      }
                      className={`w-full p-3 rounded-lg border transition-all flex items-center gap-3 ${
                        isSelected
                          ? "bg-blue-50 border-blue-300"
                          : "bg-white border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      {/* Avatar */}
                      {friend.friend.avatarUrl ? (
                        <img
                          src={friend.friend.avatarUrl}
                          alt={friend.friend.username}
                          className="w-10 h-10 rounded-full object-cover flex-shrink-0"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white flex-shrink-0">
                          {friend.friend.username
                            .substring(0, 2)
                            .toUpperCase()}
                        </div>
                      )}

                      {/* Info */}
                      <div className="flex-1 text-left min-w-0">
                        <p className="text-gray-900 truncate">
                          {friend.friend.username}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {friend.friend.email}
                        </p>
                      </div>

                      {/* Checkbox vizual */}
                      <div
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ${
                          isSelected
                            ? "bg-blue-600 border-blue-600"
                            : "border-gray-300"
                        }`}
                      >
                        {isSelected && (
                          <span className="block w-3 h-3 bg-white rounded-sm" />
                        )}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex gap-3">
          <button
            onClick={handleClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={
              !groupName.trim() || selectedFriends.size === 0
            }
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mode === "create"
              ? "Create Group"
              : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

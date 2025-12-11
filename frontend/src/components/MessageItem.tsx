import { useMemo, useState, useRef } from 'react';
import ReactionPicker from './ReactionPicker';
import { fetchReactionUsers } from '../api';

interface Reaction {
  emoji: string;
  count: number;
  reactedByMe?: boolean;
  users?: string[];
}

interface MessageItemProps {
  message: any;
  onEdit: (messageId: string, newText: string) => void;
  onReact: (messageId: string, emoji: string) => void;
  showSenderName?: boolean;
}

const formatTime = (d: Date | null) =>
  d ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

export function MessageItem({ message, onEdit, onReact, showSenderName = false }: MessageItemProps) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(message.text || '');
  const [showPicker, setShowPicker] = useState(false);
  const [avatarError, setAvatarError] = useState(false);
  const isMine = message.sender === 'me';
  const displayName = message.senderName || (isMine ? 'You' : 'User');
  const avatarInitials = useMemo(() => {
    const source = displayName || 'User';
    const parts = String(source)
      .split(/[\s@._-]+/)
      .filter(Boolean)
      .slice(0, 2);
    if (!parts.length) return source.slice(0, 2).toUpperCase() || '??';
    return parts
      .map((p) => p[0])
      .join('')
      .toUpperCase();
  }, [displayName]);
  const showOnline = !isMine && Boolean(message.senderOnline);

  const reactions: Reaction[] = Array.isArray(message.reactions)
    ? message.reactions
    : message.reactions
    ? Object.keys(message.reactions).map((emoji) => ({ emoji, count: message.reactions[emoji] }))
    : [];

  const createdAt = useMemo(
    () => (message.timestamp ? new Date(message.timestamp) : null),
    [message.timestamp]
  );
  const editedAt = useMemo(
    () => (message.editedAt ? new Date(message.editedAt) : null),
    [message.editedAt]
  );

  const isEdited = useMemo(() => {
    if (!editedAt) return false;
    if (!createdAt) return true;
    return editedAt.getTime() > createdAt.getTime();
  }, [createdAt, editedAt]);

  const submitEdit = () => {
    if (text.trim() && text !== message.text) {
      onEdit(message.id, text.trim());
    }
    setEditing(false);
  };

  return (
    <div className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
      <div className="flex items-start gap-3">
        {!isMine && (
          <div className="relative inline-flex w-10 h-10 flex-shrink-0 items-center justify-center leading-none">
            {message.senderAvatarUrl && !avatarError ? (
              <img
                src={message.senderAvatarUrl}
                alt={displayName}
                className="w-full h-full rounded-full object-cover"
                onError={(e) => {
                  setAvatarError(true);
                }}
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white">
                {avatarInitials}
              </div>
            )}
            {showOnline && (
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
            )}
          </div>
        )}

        <div
          className={`max-w-md px-4 py-2 rounded-2xl ${
            isMine ? 'bg-blue-600 text-white' : 'bg-white text-gray-900 border border-gray-200'
          }`}
        >
          {!editing ? (
            <>
              {showSenderName && !isMine && displayName && (
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] text-gray-400 uppercase tracking-wide">
                    {displayName}
                  </span>
                </div>
              )}
              <p className="leading-relaxed">
                {message.text}
                {isEdited && (
                  <span
                    className="ml-2 text-xs opacity-70"
                    title={editedAt ? `Edited: ${editedAt.toLocaleString()}` : 'Edited'}
                  >
                    (edited)
                  </span>
                )}
              </p>
              <div className="flex items-center gap-2 mt-2 text-xs opacity-80">
                <span>{formatTime(createdAt)}</span>
                <div className="flex gap-2">
                  {reactions.map((r) => (
                    <ReactionPill
                      key={r.emoji}
                      emoji={r.emoji}
                      count={r.count}
                      users={r.users || []}
                      onReact={() => onReact(message.id, r.emoji)}
                      messageId={String(message.id)}
                      inverted={isMine}
                    />
                  ))}
                </div>
                <div className="ml-auto flex items-center gap-2 text-[11px]">
                  {isMine && (
                    <button onClick={() => setEditing(true)} className="text-xs text-gray-200/80 hover:underline">
                      Edit
                    </button>
                  )}
                  <button onClick={() => setShowPicker((s) => !s)} className="text-xs text-gray-200/80">
                    React
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex gap-2">
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="flex-1 rounded px-2 py-1"
              />
              <button onClick={submitEdit} className="text-sm px-2 py-1 bg-blue-500 text-white rounded">
                Save
              </button>
              <button onClick={() => setEditing(false)} className="text-sm px-2 py-1 bg-gray-200 rounded">
                Cancel
              </button>
            </div>
          )}

          {showPicker && (
            <div className="mt-2">
              <ReactionPicker
                onSelect={(emoji) => {
                  onReact(message.id, emoji);
                  setShowPicker(false);
                }}
                onClose={() => setShowPicker(false)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageItem;

type ReactionPillProps = {
  emoji: string;
  count: number;
  users: string[];
  onReact: () => void;
  messageId: string;
  inverted?: boolean; // if message is mine, adjust colors slightly
};

function ReactionPill({ emoji, count, users, onReact, messageId, inverted }: ReactionPillProps) {
  const [isHovering, setIsHovering] = useState(false);
  const [enterTimer, setEnterTimer] = useState<number | null>(null);
  const [leaveTimer, setLeaveTimer] = useState<number | null>(null);
  const [loadedUsers, setLoadedUsers] = useState<string[] | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={async () => {
        // small delay to avoid flicker when moving fast across reactions
        if (leaveTimer) {
          window.clearTimeout(leaveTimer);
          setLeaveTimer(null);
        }
        const t = window.setTimeout(() => setIsHovering(true), 100);
        setEnterTimer(t);
        // Always refetch on hover; no caching so updates reflect immediately
        try {
          setLoadedUsers(null);
          if (abortRef.current) {
            abortRef.current.abort();
          }
          const ctrl = new AbortController();
          abortRef.current = ctrl;
          const list = await fetchReactionUsers(messageId, emoji, { signal: ctrl.signal });
          setLoadedUsers(Array.isArray(list) ? list : []);
        } catch (e) {
          // ignore errors for hover fetch; keep tooltip empty
        }
      }}
      onMouseLeave={() => {
        if (enterTimer) {
          window.clearTimeout(enterTimer);
          setEnterTimer(null);
        }
        // small grace period to avoid flicker when moving between pills
        const t = window.setTimeout(() => setIsHovering(false), 120);
        setLeaveTimer(t);
        if (abortRef.current) {
          abortRef.current.abort();
          abortRef.current = null;
        }
        // Clear fetched users so next hover re-fetches
        setLoadedUsers(null);
      }}
      onFocus={() => setIsHovering(true)}
      onBlur={() => setIsHovering(false)}
    >
      <button
        onClick={onReact}
        aria-haspopup="dialog"
        aria-expanded={isHovering ? 'true' : 'false'}
        className={
          `text-sm px-2 py-1 rounded-full transition-colors ` +
          (inverted ? 'bg-blue-500/20 text-white hover:bg-blue-500/30' : 'bg-gray-100 text-gray-900 hover:bg-gray-200')
        }
      >
        {emoji} {count}
      </button>

      {isHovering && (users?.length || loadedUsers?.length) ? (
        <div
          className={
            `pointer-events-none absolute left-1/2 -translate-x-1/2 mt-2 z-50 w-max max-w-xs ` +
            `rounded-md shadow-lg border will-change-transform ` +
            (inverted ? 'bg-white text-gray-900 border-gray-200' : 'bg-white text-gray-900 border-gray-200')
          }
          role="tooltip"
        >
          <div className="px-3 py-2 text-xs leading-5 max-h-40 overflow-auto">
            {((loadedUsers && loadedUsers.length) ? loadedUsers : (users || [])).map((u, i) => (
              <div key={i}>{u}</div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

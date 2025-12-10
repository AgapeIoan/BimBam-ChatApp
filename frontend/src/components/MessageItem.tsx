import { useState } from 'react';
import ReactionPicker from './ReactionPicker';

interface Reaction {
  emoji: string;
  count: number;
  reactedByMe?: boolean;
}

interface MessageItemProps {
  message: any;
  onEdit: (messageId: string, newText: string) => void;
  onReact: (messageId: string, emoji: string) => void;
}

export function MessageItem({ message, onEdit, onReact }: MessageItemProps) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(message.text || '');
  const [showPicker, setShowPicker] = useState(false);

  const reactions: Reaction[] = message.reactions || [];

  const submitEdit = () => {
    if (text.trim() && text !== message.text) {
      onEdit(message.id, text.trim());
    }
    setEditing(false);
  };

  return (
    <div className={`flex ${message.sender === 'me' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-md px-4 py-2 rounded-2xl ${
          message.sender === 'me' ? 'bg-blue-600 text-white' : 'bg-white text-gray-900 border border-gray-200'
        }`}
      >
        {!editing ? (
          <>
            <p>{message.text}{message.editedAt ? ' · edited' : ''}</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="flex gap-2">
                {reactions.map((r) => (
                  <button
                    key={r.emoji}
                    onClick={() => onReact(message.id, r.emoji)}
                    className="text-sm bg-gray-100 px-2 py-1 rounded-full"
                  >
                    {r.emoji} {r.count}
                  </button>
                ))}
              </div>
              <div className="ml-auto flex items-center gap-2">
                {message.sender === 'me' && (
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
  );
}

export default MessageItem;

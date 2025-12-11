import { useState } from 'react';
import { MessageCircle } from 'lucide-react';

interface UsernameSetupModalProps {
  email: string;
  defaultUsername: string;
  onConfirm: (username: string) => void;
}

export function UsernameSetupModal({
  email,
  defaultUsername,
  onConfirm,
}: UsernameSetupModalProps) {
  const [username, setUsername] = useState(defaultUsername);
  const [error, setError] = useState('');

  const handleConfirm = () => {
    setError('');
    const trimmed = username.trim();

    if (!trimmed) {
      setError('Username is required');
      return;
    }
    if (trimmed.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }
    if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) {
      setError('Username can only contain letters, numbers, and underscores');
      return;
    }

    onConfirm(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleConfirm();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.5)" }}
    >
      <div className="w-full max-w-md rounded-2xl bg-white shadow-xl">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600">
            <MessageCircle className="h-8 w-8 text-white" />
          </div>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Choose Your Username
          </h2>
          <p className="text-sm text-gray-600">
            This is how others will find you on BimBam Chat
          </p>
        </div>

        {/* Content */}
        <div className="space-y-4 p-6">
          {/* Email display */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Signed in as
            </label>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
              {email}
            </div>
          </div>

          {/* Username input */}
          <div>
            <label
              htmlFor="username"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Username
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                @
              </span>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="username"
                autoFocus
                className="w-full rounded-lg border border-gray-300 pl-9 pr-4 py-3 text-sm text-gray-900 shadow-sm outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-6">
          <button
            onClick={handleConfirm}
            className="w-full rounded-lg bg-blue-600 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

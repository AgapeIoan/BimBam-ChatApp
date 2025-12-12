/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useRef, useEffect } from 'react';
import { Loader2, Send, Sparkles, X } from 'lucide-react';
import type { Contact, Message } from './ChatApp';
import { MessageItem } from './MessageItem';

interface ChatViewProps {
  contact?: Contact;
  messages: Message[];
  onSendMessage: (text: string) => void;
  onEditGroup?: (conversationId: string) => void;
  onEditMessage?: (messageId: string, newText: string) => void;
  onReact?: (messageId: string, emoji: string) => void;
  typingLabel?: string;
  onTyping?: (isTyping: boolean) => void;
}

const API_BASE = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function ChatView({ contact, messages, onSendMessage, onEditMessage, onReact, typingLabel, onTyping }: ChatViewProps) {
  const [inputValue, setInputValue] = useState('');
  const [summaryModalOpen, setSummaryModalOpen] = useState(false);
  const [summaryHours, setSummaryHours] = useState<number | null>(1);
  const [summaryText, setSummaryText] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setSummaryModalOpen(false);
    setSummaryError(null);
    setSummaryText(null);
    setSummaryLoading(false);
  }, [contact?.id, contact?.conversationId]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      if (onTyping) onTyping(false);
    }
  };

  const handleInputChange = (value: string) => {
    setInputValue(value);
    if (onTyping) {
      onTyping(true);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = window.setTimeout(() => {
        onTyping(false);
      }, 3000);
    }
  };

  const requestSummary = async (hours: number | null) => {
    if (!contact) return;
    const conversationId = contact.conversationId || contact.id;
    if (!conversationId) return;

    setSummaryHours(hours);
    setSummaryLoading(true);
    setSummaryError(null);
    setSummaryText(null);

    try {
      const res = await fetch(
        `${API_BASE}/api/v1/conversations/${conversationId}/summary`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ hours }),
        }
      );
      if (!res.ok) {
        let message = res.status === 503 ? 'Service unavailable' : 'Unable to generate summary right now.';
        try {
          const data = await res.json();
          message = data?.error || message;
        } catch {
          // ignore parse errors
        }
        setSummaryError(message);
      } else {
        const data = await res.json();
        setSummaryText(data?.summary || 'Nothing significant happened.');
      }
    } catch (err) {
      setSummaryError('Service unavailable');
    } finally {
      setSummaryLoading(false);
    }
  };

  const closeSummaryModal = () => {
    setSummaryModalOpen(false);
    setSummaryError(null);
  };

  // Message status rendering moved into MessageItem; helpers removed.

  if (!contact) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <Send className="w-10 h-10 text-gray-400" />
          </div>
          <p className="text-gray-500">Select a conversation to start chatting</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white">
              {contact.avatar}
            </div>
            {contact.online && (
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
            )}
          </div>
          <div>
            <h2 className="text-gray-900">{contact.name}</h2>
            {!contact.isGroup && (
              <p className="text-gray-500 text-sm">
                {contact.online ? 'Active now' : 'Offline'}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={!contact?.id || summaryLoading}
            onClick={() => {
              setSummaryModalOpen(true);
              setSummaryError(null);
              setSummaryText(null);
              setSummaryLoading(false);
            }}
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">Summary</span>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            showSenderName={Boolean(contact?.isGroup)}
            onEdit={(id, newText) => onEditMessage?.(id, newText)}
            onReact={(id, emoji) => onReact?.(id, emoji)}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        {typingLabel && (
          <div className="px-2 pb-2 text-sm text-gray-500 flex items-center gap-2">
            <span className="flex gap-1 items-end">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.2s]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.05s]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
            </span>
            {typingLabel}
          </div>
        )}
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => handleInputChange(e.target.value)}
            onBlur={() => onTyping?.(false)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-3 bg-gray-100 border-0 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

      {summaryModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
          onClick={closeSummaryModal}
        >
          <div
            className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-lg font-semibold text-gray-900">Chat Summary</p>
                <p className="text-sm text-gray-600">Summarize the last...</p>
              </div>
              <button
                type="button"
            onClick={closeSummaryModal}
            className="rounded-full bg-gray-100 p-2 text-gray-600 hover:bg-gray-200 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

            <div className="mt-4 grid grid-cols-3 gap-2">
              {[1, 12, 24].map((h) => (
                <button
                  key={h}
                  type="button"
                  disabled={summaryLoading}
                  onClick={() => requestSummary(h === 24 ? null : h)}
                  className="rounded-md px-4 py-2 text-sm font-semibold text-blue-700 bg-blue-100 hover:bg-blue-200 transition disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {h}h
                </button>
              ))}
            </div>

            <div className="mt-4 min-h-[140px] rounded-md border border-gray-100 bg-gray-50/60 p-3">
              <p className="mb-2 text-xs font-semibold text-gray-500">
                Interval: {summaryHours === null ? 'toate mesajele (buton 24h)' : `ultimele ${summaryHours}h`}
              </p>
              {summaryLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  AI is reading...
                </div>
              ) : summaryError ? (
                <p className="text-sm text-red-600">{summaryError}</p>
              ) : summaryText ? (
                <div className="text-sm text-gray-800 whitespace-pre-line leading-6">
                  {summaryText}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Pick a time window to generate a summary.</p>
              )}
            </div>

            <p className="mt-4 text-xs text-gray-400">
              AI skips spammy one-liners and highlights decisions, plans, and blockers.
            </p>

            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={closeSummaryModal}
                className="rounded-md bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-800 hover:bg-gray-200 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

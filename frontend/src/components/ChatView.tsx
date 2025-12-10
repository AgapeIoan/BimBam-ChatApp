import { useState, useRef, useEffect } from 'react';
import { Send, Check, CheckCheck, XCircle } from 'lucide-react';
import type { Contact, Message } from '../types/conversation/chat';

interface ChatViewProps {
  contact?: Contact;
  messages: Message[];
  onSendMessage: (text: string) => void;
  onEditGroup?: (conversationId: string) => void;
}

export function ChatView({ contact, messages, onSendMessage }: ChatViewProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  };

  const renderMessageStatus = (status?: 'sent' | 'delivered' | 'read' | 'failed') => {
    switch (status) {
      case 'sent':
        return <Check className="w-4 h-4 text-blue-100" />;
      case 'delivered':
        return <CheckCheck className="w-4 h-4 text-blue-100" />;
      case 'read':
        return <CheckCheck className="w-4 h-4 text-blue-300" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-300" />;
      default:
        return null;
    }
  };

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
              {contact. avatarUrl ? (
                <img
                  src={contact.avatarUrl}
                  alt={`${contact.username}'s avatar`}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                contact.username.charAt(0).toUpperCase()
              )}
            </div>
            {contact.lastseenAt && (
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
            )}
          </div>
          <div>
            <h2 className="text-gray-900">{contact.username}</h2>
            <p className="text-gray-500 text-sm">{contact.lastseenAt ? 'Active now' : 'Offline'}</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'me' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-md px-4 py-2 rounded-2xl ${
                message.sender === 'me'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-900 border border-gray-200'
              }`}
            >
              <p>{message.text}</p>
              <div className="flex items-center gap-1 mt-1">
                <span
                  className={`text-xs ${
                    message.sender === 'me' ? 'text-blue-100' : 'text-gray-500'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </span>
                {message.sender === 'me' && renderMessageStatus(message.status)}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
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
    </div>
  );
}
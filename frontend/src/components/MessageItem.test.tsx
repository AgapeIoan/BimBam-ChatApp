import '@testing-library/jest-dom';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageItem } from './MessageItem';

describe('MessageItem', () => {
  const baseMessage = {
    id: '1',
    text: 'Hello 🚀',
    sender: 'them',
    timestamp: new Date().toISOString(),
    editedAt: null,
    reactions: [{ emoji: '😆', count: 2 }],
  };

  it('renders emoji text and reactions', () => {
    render(
      <MessageItem
        message={baseMessage}
        onEdit={() => {}}
        onReact={() => {}}
      />
    );

    expect(screen.getByText('Hello 🚀')).toBeInTheDocument();
    expect(screen.getByText('😆 2')).toBeInTheDocument();
  });

  it('renders reactions loaded from counts map', () => {
    render(
      <MessageItem
        message={{ ...baseMessage, reactions: { '🔥': 3 } }}
        onEdit={() => {}}
        onReact={() => {}}
      />
    );
    expect(screen.getByText('🔥 3')).toBeInTheDocument();
  });

  it('shows edited label only when editedAt > createdAt', () => {
    const created = new Date('2024-01-01T10:00:00Z');
    const edited = new Date('2024-01-01T10:05:00Z');

    render(
      <MessageItem
        message={{ ...baseMessage, timestamp: created.toISOString(), editedAt: edited.toISOString() }}
        onEdit={() => {}}
        onReact={() => {}}
      />
    );

    expect(screen.getByText(/\(edited\)/i)).toBeInTheDocument();
  });
});

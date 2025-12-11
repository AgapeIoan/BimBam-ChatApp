import "@testing-library/jest-dom/vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll, beforeEach, vi } from "vitest";

import { ChatView } from "../../src/components/ChatView";

const scrollIntoViewMock = vi.fn();

vi.mock("../../src/components/MessageItem", () => ({
  MessageItem: ({ message, showSenderName }: any) => (
    <div
      data-testid="message-item"
      data-id={message.id}
      data-show-sender={showSenderName ? "true" : "false"}
    >
      {showSenderName && <span>{message.senderName}</span>}
      <span>{message.text}</span>
    </div>
  ),
}));

describe("ChatView (unit)", () => {
  beforeAll(() => {
    // mock scrollIntoView pentru toate elementele
    // @ts-expect-error
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;
  });

  beforeEach(() => {
    scrollIntoViewMock.mockClear();
  });

  const baseContact: any = {
    id: "c1",
    name: "Alice",
    avatar: "A",
    online: true,
    isGroup: false,
  };

  const baseMessages: any[] = [
    { id: "m1", text: "Hello", senderId: "u1", senderName: "Alice" },
    { id: "m2", text: "Hi", senderId: "u2", senderName: "Bob" },
  ];

  it("afișează placeholder când nu există contact selectat", () => {
    const onSendMessage = vi.fn();

    render(
      <ChatView
        contact={undefined}
        messages={[]}
        onSendMessage={onSendMessage}
      />
    );

    expect(
      screen.getByText("Select a conversation to start chatting")
    ).toBeInTheDocument();
  });

  it("afișează headerul cu numele contactului și statusul 'Active now' când contactul e online și nu e grup", () => {
    const onSendMessage = vi.fn();

    render(
      <ChatView
        contact={{ ...baseContact, online: true, isGroup: false }}
        messages={[]}
        onSendMessage={onSendMessage}
      />
    );

    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Active now")).toBeInTheDocument();
  });

  it("afișează statusul 'Offline' când contactul nu e online și nu e grup", () => {
    const onSendMessage = vi.fn();

    render(
      <ChatView
        contact={{ ...baseContact, online: false, isGroup: false }}
        messages={[]}
        onSendMessage={onSendMessage}
      />
    );

    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  it("nu afișează statusul online/offline pentru grup", () => {
    const onSendMessage = vi.fn();

    render(
      <ChatView
        contact={{ ...baseContact, isGroup: true }}
        messages={[]}
        onSendMessage={onSendMessage}
      />
    );

    expect(screen.queryByText("Active now")).not.toBeInTheDocument();
    expect(screen.queryByText("Offline")).not.toBeInTheDocument();
  });

  it("randază un MessageItem pentru fiecare mesaj și setează showSenderName în funcție de isGroup", () => {
    const onSendMessage = vi.fn();

    const { rerender } = render(
      <ChatView
        contact={{ ...baseContact, isGroup: false }}
        messages={baseMessages}
        onSendMessage={onSendMessage}
      />
    );

    const itemsForDirectChat = screen.getAllByTestId("message-item");
    expect(itemsForDirectChat).toHaveLength(2);
    itemsForDirectChat.forEach((item) =>
      expect(item).toHaveAttribute("data-show-sender", "false")
    );

    rerender(
      <ChatView
        contact={{ ...baseContact, isGroup: true }}
        messages={baseMessages}
        onSendMessage={onSendMessage}
      />
    );

    const itemsForGroup = screen.getAllByTestId("message-item");
    itemsForGroup.forEach((item) =>
      expect(item).toHaveAttribute("data-show-sender", "true")
    );
  });

  it("apelează scrollIntoView când lista de mesaje se schimbă", () => {
    const onSendMessage = vi.fn();
    const messages1 = [baseMessages[0]];
    const messages2 = [...baseMessages];

    const { rerender } = render(
      <ChatView
        contact={baseContact}
        messages={messages1}
        onSendMessage={onSendMessage}
      />
    );

    expect(scrollIntoViewMock).toHaveBeenCalled();

    scrollIntoViewMock.mockClear();

    rerender(
      <ChatView
        contact={baseContact}
        messages={messages2}
        onSendMessage={onSendMessage}
      />
    );

    expect(scrollIntoViewMock).toHaveBeenCalled();
  });

  it("afișează typingLabel și indicatorul de typing când typingLabel este setat", () => {
    const onSendMessage = vi.fn();

    render(
      <ChatView
        contact={baseContact}
        messages={[]}
        onSendMessage={onSendMessage}
        typingLabel="Alice is typing..."
      />
    );

    expect(screen.getByText("Alice is typing...")).toBeInTheDocument();
  });

  it("butonul de send este dezactivat când inputul este gol sau doar whitespace", () => {
    const onSendMessage = vi.fn();

    render(
      <ChatView
        contact={baseContact}
        messages={[]}
        onSendMessage={onSendMessage}
      />
    );

    const sendButton = screen.getByRole("button");
    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;

    expect(sendButton).toBeDisabled();

    input.value = "   ";
    expect(sendButton).toBeDisabled();
  });
});

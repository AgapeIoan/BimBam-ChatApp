/* eslint-disable @typescript-eslint/no-explicit-any */
import "@testing-library/jest-dom/vitest";
import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";

import { ChatView } from "../../src/components/ChatView";

vi.mock("../../src/components/MessageItem", () => ({
  MessageItem: ({ message, onEdit, onReact }: any) => (
    <div>
      <span>{message.text}</span>
      <button
        type="button"
        data-testid={`edit-${message.id}`}
        onClick={() => onEdit?.(message.id, "edited text")}
      >
        Edit
      </button>
      <button
        type="button"
        data-testid={`react-${message.id}`}
        onClick={() => onReact?.(message.id, "👍")}
      >
        React
      </button>
    </div>
  ),
}));

beforeAll(() => {
  (window.HTMLElement as any).prototype.scrollIntoView = vi.fn();
});

describe("ChatView (integration)", () => {
  const contact: any = {
    id: "c1",
    name: "Alice",
    avatar: "A",
    online: true,
    isGroup: false,
  };

  const messages: any[] = [
    {
      id: "m1",
      text: "Hello",
      senderId: "u1",
      senderName: "Alice",
    },
  ];

  let onSendMessage: ReturnType<typeof vi.fn>;
  let onEditMessage: ReturnType<typeof vi.fn>;
  let onReact: ReturnType<typeof vi.fn>;
  let onTyping: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onSendMessage = vi.fn();
    onEditMessage = vi.fn();
    onReact = vi.fn();
    onTyping = vi.fn();
  });

  it("trims the text, calls onSendMessage, and clears the input on submit", async () => {
    const user = userEvent.setup();

    render(
      <ChatView
        contact={contact}
        messages={messages}
        onSendMessage={onSendMessage}
        onTyping={onTyping}
      />
    );

    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;
    const sendButton = screen
      .getAllByRole("button")
      .find((btn) => (btn as HTMLButtonElement).type === "submit") as HTMLButtonElement;

    await user.type(input, "  hello world  ");
    expect(sendButton).not.toBeDisabled();

    await user.click(sendButton);

    expect(onSendMessage).toHaveBeenCalledTimes(1);
    expect(onSendMessage).toHaveBeenCalledWith("hello world");
    expect(input.value).toBe("");
    expect(onTyping).toHaveBeenCalledWith(false);
  });

  it("calls onTyping(true) on input change and onTyping(false) on blur", async () => {
    const user = userEvent.setup();

    render(
      <ChatView
        contact={contact}
        messages={messages}
        onSendMessage={onSendMessage}
        onTyping={onTyping}
      />
    );

    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;

    await user.type(input, "h");
    expect(onTyping).toHaveBeenCalledWith(true);

    await user.tab();
    expect(onTyping).toHaveBeenCalledWith(false);
  });

  it("calls onTyping(true) immediately and onTyping(false) after 3 seconds of inactivity", () => {
    vi.useFakeTimers();

    render(
      <ChatView
        contact={contact}
        messages={messages}
        onSendMessage={onSendMessage}
        onTyping={onTyping}
      />
    );

    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "hello" } });

    expect(onTyping).toHaveBeenCalledWith(true);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(onTyping).toHaveBeenCalledWith(false);

    vi.useRealTimers();
  });

  it("resets the typing timer if the user keeps typing", () => {
    vi.useFakeTimers();

    render(
      <ChatView
        contact={contact}
        messages={messages}
        onSendMessage={onSendMessage}
        onTyping={onTyping}
      />
    );

    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "h" } });
    fireEvent.change(input, { target: { value: "he" } });

    act(() => {
      vi.advanceTimersByTime(2500);
    });

    expect(onTyping).not.toHaveBeenCalledWith(false);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(onTyping).toHaveBeenCalledWith(false);

    vi.useRealTimers();
  });

  it("propagates onEdit from MessageItem to onEditMessage in props", async () => {
    const user = userEvent.setup();

    render(
      <ChatView
        contact={contact}
        messages={messages}
        onSendMessage={onSendMessage}
        onEditMessage={onEditMessage}
      />
    );

    const editButton = screen.getByTestId("edit-m1");
    await user.click(editButton);

    expect(onEditMessage).toHaveBeenCalledTimes(1);
    expect(onEditMessage).toHaveBeenCalledWith("m1", "edited text");
  });

  it("propagates onReact from MessageItem to onReact in props", async () => {
    const user = userEvent.setup();

    render(
      <ChatView
        contact={contact}
        messages={messages}
        onSendMessage={onSendMessage}
        onReact={onReact}
      />
    );

    const reactButton = screen.getByTestId("react-m1");
    await user.click(reactButton);

    expect(onReact).toHaveBeenCalledTimes(1);
    expect(onReact).toHaveBeenCalledWith("m1", "👍");
  });
});

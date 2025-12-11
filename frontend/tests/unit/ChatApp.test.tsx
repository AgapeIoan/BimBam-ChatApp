import "@testing-library/jest-dom";
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { ChatApp } from "../../src/components/ChatApp";
import type { AuthUser } from "../../src/api/client";
import ws from "../../src/api/ws";

let wsSubscribeCallback: ((env: any) => void) | null = null;

const mockWsConnect = vi.fn();
const mockWsDisconnect = vi.fn();
const mockWsSubscribe = vi.fn();
const mockWsSend = vi.fn();

const mockSidebarProps = vi.fn();
vi.mock("../../src/components/ChatSidebar", () => ({
  ChatSidebar: (props: any) => {
    mockSidebarProps(props);
    return (
      <div data-testid="sidebar">
        <div data-testid="contacts-count">{props.contacts.length}</div>
        {props.contacts.map((c: any) => (
          <button
            key={c.id}
            data-testid={`contact-${c.id}`}
            onClick={() => props.onSelectContact(c.id)}
          >
            {c.name}
          </button>
        ))}
        <button onClick={props.onOpenFriendRequests}>open-requests</button>
        <button onClick={props.onOpenAccount}>open-account</button>
        <button onClick={props.onOpenGroupModal}>open-group</button>
      </div>
    );
  },
}));

const mockChatViewProps = vi.fn();
vi.mock("../../src/components/ChatView", () => ({
  ChatView: (props: any) => {
    mockChatViewProps(props);
    return (
      <div data-testid="chat-view">
        <div data-testid="messages-count">{props.messages.length}</div>
        <div data-testid="typing-label">{props.typingLabel ?? ""}</div>
        <button onClick={() => props.onSendMessage("hello from test")}>
          send-from-test
        </button>
      </div>
    );
  },
}));

vi.mock("../../src/components/FriendRequestsModal", () => ({
  FriendRequestsModal: (props: any) =>
    props.isOpen ? (
      <div data-testid="friend-requests-modal">friend-requests</div>
    ) : null,
}));

vi.mock("../../src/components/AccountModal", () => ({
  AccountModal: (props: any) =>
    props.isOpen ? (
      <div data-testid="account-modal">account-modal</div>
    ) : null,
}));

vi.mock("../../src/components/GroupModal", () => ({
  GroupModal: (props: any) =>
    props.isOpen ? (
      <div data-testid="group-modal">group-modal</div>
    ) : null,
}));

const mockFetch = vi.fn();

function mockResponse(data: any, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  });
}

const baseUser: AuthUser = {
  id: "me-1",
  email: "me@example.com",
  username: "meuser",
  avatar_url: null,
  provider: "google",
  name: "Me User",
};

beforeEach(() => {
  mockWsConnect.mockReset();
  mockWsDisconnect.mockReset();
  mockWsSubscribe.mockReset();
  mockWsSend.mockReset();

  mockWsConnect.mockImplementation(() => Promise.resolve());
  mockWsDisconnect.mockImplementation(() => {});
  mockWsSubscribe.mockImplementation((cb: any) => {
    wsSubscribeCallback = cb;
    return vi.fn();
  });
  mockWsSend.mockResolvedValue(true);

  (ws as any).connect = mockWsConnect;
  (ws as any).disconnect = mockWsDisconnect;
  (ws as any).subscribe = mockWsSubscribe;
  (ws as any).send = mockWsSend;

  (globalThis as any).fetch = mockFetch;
  mockFetch.mockReset();

  mockFetch.mockImplementation((input: any) => {
    const url = String(input);
    if (url.endsWith("/api/v1/conversations/")) return mockResponse([]);
    if (url.endsWith("/api/v1/friends/")) return mockResponse([]);
    if (url.includes("/friend-requests/incoming")) return mockResponse([]);
    if (url.includes("/friend-requests/outgoing")) return mockResponse([]);
    if (url.includes("/api/v1/conversations/") && url.includes("/messages"))
      return mockResponse({ messages: [] });
    return mockResponse([]);
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ChatApp", () => {
  it("calls ws.connect with cookie token", async () => {
    document.cookie = "access_token=mytoken123";

    render(<ChatApp onLogout={vi.fn()} currentUser={baseUser} />);

    await waitFor(() => {
      expect(mockWsConnect).toHaveBeenCalled();
    });

    const firstCallArg = mockWsConnect.mock.calls[0][0];
    expect(firstCallArg).toBe("mytoken123");
  });

  it("loads friends and conversations and passes them to ChatSidebar", async () => {
    const now = new Date().toISOString();

    mockFetch.mockImplementation((input: any) => {
      const url = String(input);
      if (url.endsWith("/api/v1/friends/"))
        return mockResponse([
          {
            friend: { id: "u2", username: "Alice", email: "alice@example.com" },
            is_online: true,
            unread_count: 2,
          },
        ]);
      if (url.endsWith("/api/v1/conversations/"))
        return mockResponse([
          {
            id: "conv1",
            is_group: false,
            last_message: "hi",
            last_message_at: now,
            unread_count: 2,
            other_users: [
              {
                id: "u2",
                username: "Alice",
                email: "alice@example.com",
                avatarUrl: null,
              },
            ],
          },
        ]);
      if (url.includes("/friend-requests/incoming")) return mockResponse([]);
      if (url.includes("/friend-requests/outgoing")) return mockResponse([]);
      if (url.includes("/messages")) return mockResponse({ messages: [] });
      return mockResponse([]);
    });

    render(<ChatApp onLogout={vi.fn()} currentUser={baseUser} />);

    await waitFor(() => expect(mockSidebarProps).toHaveBeenCalled());

    const props = mockSidebarProps.mock.calls.at(-1)[0];
    expect(props.contacts).toHaveLength(1);
    expect(props.contacts[0].name).toBe("Alice");

    expect(screen.getByTestId("contacts-count")).toHaveTextContent("1");
  });

  it("selects a contact, loads history, and sends a message", async () => {
    const now = new Date().toISOString();

    mockFetch.mockImplementation((input: any) => {
      const url = String(input);
      if (url.endsWith("/api/v1/friends/"))
        return mockResponse([
          {
            friend: { id: "u2", username: "Alice", email: "alice@example.com" },
            is_online: true,
            unread_count: 0,
          },
        ]);
      if (url.endsWith("/api/v1/conversations/"))
        return mockResponse([
          {
            id: "conv1",
            is_group: false,
            last_message: "hello",
            last_message_at: now,
            unread_count: 0,
            other_users: [
              {
                id: "u2",
                username: "Alice",
                email: "alice@example.com",
              },
            ],
          },
        ]);
      if (url.includes("conv1/messages"))
        return mockResponse({
          messages: [
            {
              id: "m1",
              senderId: "u2",
              content: "from history",
              createdAt: now,
              delivered: true,
            },
          ],
        });
      if (url.includes("/friend-requests/incoming")) return mockResponse([]);
      if (url.includes("/friend-requests/outgoing")) return mockResponse([]);
      return mockResponse([]);
    });

    const user = userEvent.setup();
    render(<ChatApp onLogout={vi.fn()} currentUser={baseUser} />);

    const contact = await screen.findByTestId("contact-conv1");
    await user.click(contact);

    await waitFor(() =>
      expect(screen.getByTestId("messages-count")).toHaveTextContent("1")
    );

    await user.click(screen.getByText("send-from-test"));

    await waitFor(() =>
      expect(screen.getByTestId("messages-count")).toHaveTextContent("2")
    );

    expect(mockWsSend).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "message_send",
        data: { conversationId: "conv1", content: "hello from test" },
      })
    );
  });

  it("opens all modals triggered by ChatSidebar actions", async () => {
    const user = userEvent.setup();
    render(<ChatApp onLogout={vi.fn()} currentUser={baseUser} />);

    await user.click(screen.getByText("open-requests"));
    expect(
      await screen.findByTestId("friend-requests-modal")
    ).toBeInTheDocument();

    await user.click(screen.getByText("open-account"));
    expect(await screen.findByTestId("account-modal")).toBeInTheDocument();

    await user.click(screen.getByText("open-group"));
    expect(await screen.findByTestId("group-modal")).toBeInTheDocument();
  });

  it("displays 'Alice is typing...' when receiving a typing WebSocket event", async () => {
    const now = new Date().toISOString();

    mockFetch.mockImplementation((input: any) => {
      const url = String(input);
      if (url.endsWith("/api/v1/friends/"))
        return mockResponse([
          {
            friend: { id: "u2", username: "Alice", email: "alice@example.com" },
            is_online: true,
            unread_count: 0,
          },
        ]);
      if (url.endsWith("/api/v1/conversations/"))
        return mockResponse([
          {
            id: "conv1",
            is_group: false,
            last_message: "hello",
            last_message_at: now,
            unread_count: 0,
            other_users: [
              {
                id: "u2",
                username: "Alice",
                email: "alice@example.com",
              },
            ],
          },
        ]);
      if (url.includes("conv1/messages")) return mockResponse({ messages: [] });
      if (url.includes("/friend-requests/incoming")) return mockResponse([]);
      if (url.includes("/friend-requests/outgoing")) return mockResponse([]);
      return mockResponse([]);
    });

    const user = userEvent.setup();
    render(<ChatApp onLogout={vi.fn()} currentUser={baseUser} />);

    const contact = await screen.findByTestId("contact-conv1");
    await user.click(contact);

    expect(mockWsSubscribe).toHaveBeenCalled();
    expect(wsSubscribeCallback).not.toBeNull();

    wsSubscribeCallback?.({
      type: "typing",
      data: {
        fromUserId: "u2",
        toUserId: "me-1",
        isTyping: true,
      },
    });

    await waitFor(() => {
      expect(screen.getByTestId("typing-label")).toHaveTextContent(
        "Alice is typing..."
      );
    });
  });
});

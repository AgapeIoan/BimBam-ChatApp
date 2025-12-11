import "@testing-library/jest-dom";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ChatSidebar } from "../../src/components/ChatSidebar";
import type { Contact } from "../../src/components/ChatApp";

const baseContacts: Contact[] = [
  {
    id: "c1",
    conversationId: "c1",
    name: "Alice Johnson",
    avatar: "AJ",
    avatarUrl: null,
    lastMessage: "Hi there",
    timestamp: "10:00",
    unread: 2,
    online: true,
    isFriend: true,
    isGroup: false,
    otherUserId: "u1",
    username: "alice",
    email: "alice@example.com",
  },
  {
    id: "c2",
    conversationId: "c2",
    name: "Bob Smith",
    avatar: "BS",
    avatarUrl: "https://example.com/avatar-bob.png",
    lastMessage: "Hey!",
    timestamp: "11:00",
    unread: 0,
    online: false,
    isFriend: true,
    isGroup: false,
    otherUserId: "u2",
    username: "bob",
    email: "bob@example.com",
  },
];

function renderSidebar(overrides: Partial<React.ComponentProps<typeof ChatSidebar>> = {}) {
  const onSelectContact = vi.fn();
  const onLogout = vi.fn();
  const onToggleCollapse = vi.fn();
  const onOpenFriendRequests = vi.fn();
  const onOpenGroupModal = vi.fn();
  const onOpenAccount = vi.fn();

  const props: React.ComponentProps<typeof ChatSidebar> = {
    contacts: baseContacts,
    selectedContactId: null,
    onSelectContact,
    onLogout,
    isCollapsed: false,
    onToggleCollapse,
    onOpenFriendRequests,
    incomingRequestsCount: 3,
    onOpenGroupModal,
    onOpenAccount,
    ...overrides,
  };

  const result = render(<ChatSidebar {...props} />);

  return {
    ...result,
    props,
    onSelectContact,
    onLogout,
    onToggleCollapse,
    onOpenFriendRequests,
    onOpenGroupModal,
    onOpenAccount,
  };
}

describe("ChatSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders expanded sidebar with header, search, and contacts and handles selection", async () => {
    const user = userEvent.setup();
    const { onSelectContact } = renderSidebar({ isCollapsed: false });

    expect(screen.getByText("BimBam Chat")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search conversations...")).toBeInTheDocument();

    expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();

    const buttons = screen.getAllByRole("button");
    const toggleButton = buttons[0];
    await user.click(toggleButton);
    expect(toggleButton).toBeInTheDocument(); // sanity check that we found a button

    const aliceButton = screen.getByRole("button", { name: /Alice Johnson/i });
    await user.click(aliceButton);
    expect(onSelectContact).toHaveBeenCalledWith("c1");
  });

  it("shows menu and triggers account and logout actions", async () => {
    const user = userEvent.setup();
    const { onLogout, onOpenAccount } = renderSidebar({ isCollapsed: false });

    const buttons = screen.getAllByRole("button");
    const menuButton = buttons[1];

    await user.click(menuButton);

    const accountItem = await screen.findByText("Account");
    await user.click(accountItem);
    expect(onOpenAccount).toHaveBeenCalledTimes(1);

    await user.click(menuButton);

    const logoutItem = await screen.findByText("Sign out");
    await user.click(logoutItem);
    expect(onLogout).toHaveBeenCalledTimes(1);
    });


  it("renders friend requests and group buttons (expanded) and shows incoming count badge", async () => {
    const user = userEvent.setup();
    const { onOpenFriendRequests, onOpenGroupModal } = renderSidebar({
      isCollapsed: false,
      incomingRequestsCount: 5,
    });

    const friendBtn = screen.getByText("Friend Requests");
    const groupBtn = screen.getByText("Create Group");

    expect(friendBtn).toBeInTheDocument();
    expect(groupBtn).toBeInTheDocument();

    expect(screen.getByText("5")).toBeInTheDocument();

    await user.click(friendBtn);
    expect(onOpenFriendRequests).toHaveBeenCalledTimes(1);

    await user.click(groupBtn);
    expect(onOpenGroupModal).toHaveBeenCalledTimes(1);
  });

  it("renders collapsed sidebar, hides text UI, and shows unread badge on avatar", async () => {
    const user = userEvent.setup();
    const { onOpenFriendRequests, onOpenGroupModal } = renderSidebar({
      isCollapsed: true,
      incomingRequestsCount: 2,
    });

    expect(screen.queryByText("BimBam Chat")).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Search conversations...")).not.toBeInTheDocument();

    const friendBtn = screen.getByTitle("Friend Requests");
    const groupBtn = screen.getByTitle("Create Group");

    expect(friendBtn).toBeInTheDocument();
    expect(groupBtn).toBeInTheDocument();

    await user.click(friendBtn);
    expect(onOpenFriendRequests).toHaveBeenCalledTimes(1);

    await user.click(groupBtn);
    expect(onOpenGroupModal).toHaveBeenCalledTimes(1);

    const contactButtons = screen.getAllByRole("button");
    const sidebarContact = contactButtons.find((b) => b.getAttribute("title") === "Alice Johnson");
    expect(sidebarContact).toBeDefined();

    const badge = (sidebarContact as HTMLElement).querySelector(".w-5.h-5.bg-blue-600");
    expect(badge).not.toBeNull();
    expect(badge).toHaveTextContent("2");
  });

  it("filters contacts by search text using name / username / email", async () => {
    const user = userEvent.setup();
    renderSidebar({
      isCollapsed: false,
      contacts: baseContacts,
    });

    const searchInput = screen.getByPlaceholderText("Search conversations...");
    await user.type(searchInput, "bob");

    expect(screen.queryByText("Alice Johnson")).not.toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();

    await user.clear(searchInput);
    await user.type(searchInput, "alice@example.com");

    expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    expect(screen.queryByText("Bob Smith")).not.toBeInTheDocument();
  });

  it("falls back to initials when avatar image fails to load", () => {
    renderSidebar({
      isCollapsed: false,
      contacts: [
        {
          ...baseContacts[1],
          avatar: "BS",
          avatarUrl: "https://example.com/avatar-bob.png",
        },
      ],
    });

    const img = screen.getByAltText("Bob Smith") as HTMLImageElement;
    expect(img).toBeInTheDocument();

    fireEvent.error(img);

    const fallback = screen.getByText("BS");
    expect(fallback).toBeInTheDocument();
  });

  it("shows online indicator for online contacts", () => {
    renderSidebar({
      isCollapsed: false,
      contacts: [
        {
          ...baseContacts[0],
          online: true,
        },
      ],
    });

    const contactButton = screen.getByRole("button", { name: /Alice Johnson/i });
    const onlineDot = contactButton.querySelector(".bg-green-500");
    expect(onlineDot).not.toBeNull();
  });
});

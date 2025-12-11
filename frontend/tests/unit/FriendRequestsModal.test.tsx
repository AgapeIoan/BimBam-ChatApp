import "@testing-library/jest-dom";
import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, jest } from "@jest/globals";

import {
  FriendRequestsModal,
  type FriendRequest,
  type SentRequest,
  type UserSearchResult,
} from "../../src/components/FriendRequestsModal";

function createBaseProps(
  overrides: Partial<React.ComponentProps<typeof FriendRequestsModal>> = {}
) {
  const incomingRequests: FriendRequest[] = [
    {
      fromId: "req-1",
      fromName: "John Doe",
      fromUsername: "johndoe",
      fromEmail: "john@example.com",
      fromAvatar: "J",
      timestamp: "just now",
      status: "pending",
    },
  ];

  const sentRequests: SentRequest[] = [
    {
      toId: "req-2",
      toName: "Jane Smith",
      toUsername: "janesmith",
      toEmail: "jane@example.com",
      toAvatar: "J",
      timestamp: "yesterday",
      status: "pending",
    },
  ];

  return {
    isOpen: true,
    onClose: jest.fn(),
    incomingRequests,
    sentRequests,
    onAcceptRequest: jest.fn(),
    onDeclineRequest: jest.fn(),
    onCancelRequest: jest.fn(),
    onSendRequest: jest.fn(),
    onSearchUsers: jest.fn().mockResolvedValue([] as UserSearchResult[]),
    ...overrides,
  };
}

describe("FriendRequestsModal", () => {
  it("does not render when isOpen is false", () => {
    const props = createBaseProps({ isOpen: false });
    const { container } = render(<FriendRequestsModal {...props} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders header and tabs", () => {
    const props = createBaseProps();
    render(<FriendRequestsModal {...props} />);

    expect(screen.getByText("Friend Requests")).toBeInTheDocument();
    expect(screen.getByText("Send Request")).toBeInTheDocument();
    expect(screen.getByText("Incoming")).toBeInTheDocument();
    expect(screen.getByText("Sent")).toBeInTheDocument();
  });

  it("switches between tabs", async () => {
    const props = createBaseProps();
    render(<FriendRequestsModal {...props} />);

    expect(screen.getByText(/Add friends/i)).toBeInTheDocument();

    await userEvent.click(screen.getByText("Incoming"));
    expect(screen.getByText(/Requested just now/i)).toBeInTheDocument();

    await userEvent.click(screen.getByText("Sent"));
    expect(screen.getByText(/Sent yesterday/i)).toBeInTheDocument();
  });

  it("calls onSearchUsers and then onSendRequest", async () => {
    const result: UserSearchResult[] = [
      {
        id: "user-1",
        username: "miruna",
        email: "miruna@example.com",
        avatar: "M",
        name: "Miruna C",
        isFriend: false,
        hasPendingRequest: false,
      },
    ];

    const onSearchUsers = jest.fn().mockResolvedValue(result);
    const onSendRequest = jest.fn();
    const props = createBaseProps({ onSearchUsers, onSendRequest });

    render(<FriendRequestsModal {...props} />);

    const input = screen.getByPlaceholderText("Search by username...");
    await userEvent.type(input, "miruna");

    await waitFor(() => {
      expect(onSearchUsers).toHaveBeenCalledWith("miruna");
    });

    expect(screen.getByText("Miruna C")).toBeInTheDocument();
    expect(screen.getByText("@miruna")).toBeInTheDocument();
    expect(screen.getByText("miruna@example.com")).toBeInTheDocument();

    const addButton = screen.getByRole("button", { name: /add/i });
    await userEvent.click(addButton);

    expect(onSendRequest).toHaveBeenCalledWith("miruna@example.com");
  });

  it('shows "No users found" when search returns empty array', async () => {
    const onSearchUsers = jest.fn().mockResolvedValue([]);
    const props = createBaseProps({ onSearchUsers });

    render(<FriendRequestsModal {...props} />);

    const input = screen.getByPlaceholderText("Search by username...");
    await userEvent.type(input, "nobody");

    await waitFor(() => expect(onSearchUsers).toHaveBeenCalled());

    expect(
      screen.getByText('No users found matching "nobody"')
    ).toBeInTheDocument();
  });

  it("switches search type between username and email", async () => {
    const props = createBaseProps();
    render(<FriendRequestsModal {...props} />);

    const inputUsername = screen.getByPlaceholderText("Search by username...");
    expect(inputUsername).toHaveAttribute("type", "text");

    await userEvent.click(screen.getByText("Email"));

    const inputEmail = screen.getByPlaceholderText("Search by email...");
    expect(inputEmail).toHaveAttribute("type", "email");
  });

  it("shows empty state when no incoming requests", async () => {
    const props = createBaseProps({ incomingRequests: [] });
    render(<FriendRequestsModal {...props} />);

    await userEvent.click(screen.getByText("Incoming"));
    expect(
      screen.getByText("No incoming friend requests")
    ).toBeInTheDocument();
  });

  it("shows empty state when no sent requests", async () => {
    const props = createBaseProps({ sentRequests: [] });
    render(<FriendRequestsModal {...props} />);

    await userEvent.click(screen.getByText("Sent"));
    expect(
      screen.getByText("No pending sent requests")
    ).toBeInTheDocument();
  });

  it("calls Accept and Decline handlers", async () => {
    const onAcceptRequest = jest.fn();
    const onDeclineRequest = jest.fn();
    const props = createBaseProps({ onAcceptRequest, onDeclineRequest });

    render(<FriendRequestsModal {...props} />);

    await userEvent.click(screen.getByText("Incoming"));

    const buttons = screen.getAllByRole("button");
    const acceptButton = buttons[buttons.length - 2];
    const declineButton = buttons[buttons.length - 1];

    await userEvent.click(acceptButton);
    expect(onAcceptRequest).toHaveBeenCalledWith("req-1");

    await userEvent.click(declineButton);
    expect(onDeclineRequest).toHaveBeenCalledWith("req-1");
  });

  it("calls onCancelRequest for sent requests", async () => {
    const onCancelRequest = jest.fn();
    const props = createBaseProps({ onCancelRequest });

    render(<FriendRequestsModal {...props} />);

    await userEvent.click(screen.getByText("Sent"));

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await userEvent.click(cancelButton);

    expect(onCancelRequest).toHaveBeenCalledWith("req-2");
  });


  it("calls onClose when the X button is clicked", async () => {
  const user = userEvent.setup();
  const onClose = jest.fn();
  const props = createBaseProps({ onClose });

  render(<FriendRequestsModal {...props} />);

  const closeButton = screen
    .getAllByRole("button")
    .find((btn) => btn.textContent === "") as HTMLButtonElement;

  expect(closeButton).toBeDefined();

  await user.click(closeButton);

  expect(onClose).toHaveBeenCalledTimes(1);
});


  it('shows "Already friends" label for users that are already friends', async () => {
    const result: UserSearchResult[] = [
      {
        id: "user-friend",
        username: "bestie",
        email: "bestie@example.com",
        avatar: "B",
        avatarUrl: null,
        name: "Best Friend",
        isFriend: true,
        hasPendingRequest: false,
      },
    ];

    const onSearchUsers = jest.fn().mockResolvedValue(result);
    const props = createBaseProps({ onSearchUsers });

    render(<FriendRequestsModal {...props} />);

    const input = screen.getByPlaceholderText("Search by username...");
    await userEvent.type(input, "bestie");

    await waitFor(() => {
      expect(onSearchUsers).toHaveBeenCalledWith("bestie");
    });

    expect(screen.getByText("Best Friend")).toBeInTheDocument();
    expect(screen.getByText("@bestie")).toBeInTheDocument();
    expect(screen.getByText("bestie@example.com")).toBeInTheDocument();
    expect(screen.getByText("Already friends")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add/i })).not.toBeInTheDocument();
  });

  it('shows "Request sent" label for users with pending request', async () => {
    const result: UserSearchResult[] = [
      {
        id: "user-pending",
        username: "almostfriend",
        email: "almost@example.com",
        avatar: "A",
        avatarUrl: null,
        name: "Almost Friend",
        isFriend: false,
        hasPendingRequest: true,
      },
    ];

    const onSearchUsers = jest.fn().mockResolvedValue(result);
    const props = createBaseProps({ onSearchUsers });

    render(<FriendRequestsModal {...props} />);

    const input = screen.getByPlaceholderText("Search by username...");
    await userEvent.type(input, "almostfriend");

    await waitFor(() => {
      expect(onSearchUsers).toHaveBeenCalledWith("almostfriend");
    });

    expect(screen.getByText("Almost Friend")).toBeInTheDocument();
    expect(screen.getByText("@almostfriend")).toBeInTheDocument();
    expect(screen.getByText("almost@example.com")).toBeInTheDocument();
    expect(screen.getByText("Request sent")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add/i })).not.toBeInTheDocument();
  });

  it("renders avatar image when avatarUrl is provided and handles image error to show fallback avatar", async () => {
    const result: UserSearchResult[] = [
      {
        id: "user-img",
        username: "avataruser",
        email: "avatar@example.com",
        avatar: "A",
        avatarUrl: "http://example.com/avatar.png",
        name: "Avatar User",
        isFriend: false,
        hasPendingRequest: false,
      },
    ];

    const onSearchUsers = jest.fn().mockResolvedValue(result);
    const props = createBaseProps({ onSearchUsers });

    render(<FriendRequestsModal {...props} />);

    const input = screen.getByPlaceholderText("Search by username...");
    await userEvent.type(input, "avataruser");

    await waitFor(() => {
      expect(onSearchUsers).toHaveBeenCalledWith("avataruser");
    });

    const img = await screen.findByAltText("Avatar User");
    expect(img).toBeInTheDocument();

    fireEvent.error(img);
    expect(screen.getByText("Avatar User")).toBeTruthy();
  });
});

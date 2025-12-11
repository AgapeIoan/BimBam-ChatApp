import "@testing-library/jest-dom";
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, jest } from "@jest/globals";

import {
  FriendRequestsModal,
  type FriendRequest,
  type SentRequest,
} from "../../src/components/FriendRequestsModal";

import * as friendRequestsService from "../../src/services/friendRequestsService";
import * as userService from "../../src/services/userService";

jest.mock("../../src/services/friendRequestsService");
jest.mock("../../src/services/userService");

type UserSearchResult = Parameters<
  React.ComponentProps<typeof FriendRequestsModal>["onSearchUsers"]
>[0] extends string
  ? Awaited<ReturnType<React.ComponentProps<typeof FriendRequestsModal>["onSearchUsers"]>>
  : never;

function FriendRequestsContainer() {
  const incomingRequests: FriendRequest[] = [];
  const sentRequests: SentRequest[] = [];

  const handleSearchUsers = (query: string) =>
    userService.searchUsers(query, "username") as unknown as Promise<UserSearchResult[]>;

  const handleSendRequest = async (email: string) => {
    await friendRequestsService.sendFriendRequest(email);
  };

  return (
    <FriendRequestsModal
      isOpen={true}
      onClose={() => {}}
      incomingRequests={incomingRequests}
      sentRequests={sentRequests}
      onAcceptRequest={() => {}}
      onDeclineRequest={() => {}}
      onCancelRequest={() => {}}
      onSendRequest={handleSendRequest}
      onSearchUsers={handleSearchUsers}
    />
  );
}

describe("FriendRequestsModal integration-ish", () => {
  it("searches users via API and sends request, updating UI", async () => {
    const user = userEvent.setup();

    (userService.searchUsers as jest.Mock).mockResolvedValue([
      {
        id: "user-1",
        username: "miruna",
        email: "miruna@example.com",
        avatarUrl: null,
      },
    ]);

    (friendRequestsService.sendFriendRequest as jest.Mock).mockResolvedValue({
      id: "req-123",
      status: "pending",
      createdAt: new Date().toISOString(),
      fromUser: {
        id: "me",
        username: "meuser",
        email: "me@example.com",
        avatarUrl: null,
      },
      toUser: {
        id: "user-1",
        username: "miruna",
        email: "miruna@example.com",
        avatarUrl: null,
      },
    });

    render(<FriendRequestsContainer />);

    const input = screen.getByPlaceholderText("Search by username...");
    await user.type(input, "miruna");

    await waitFor(() => {
      expect(userService.searchUsers).toHaveBeenCalledWith("miruna", "username");
    });

    
    expect(screen.getByText("@miruna")).toBeInTheDocument();
    expect(screen.getByText("miruna@example.com")).toBeInTheDocument();

    const addButton = screen.getByRole("button", { name: /add/i });
    await user.click(addButton);

    expect(friendRequestsService.sendFriendRequest).toHaveBeenCalledWith("miruna@example.com");
  });
});

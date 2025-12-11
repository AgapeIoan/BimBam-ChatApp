import "@testing-library/jest-dom/vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { GroupModal } from "../../src/components/GroupModal";

function createFriend(id: string, overrides: Partial<any> = {}) {
  return {
    friend: {
      id,
      username: `user${id}`,
      email: `user${id}@example.com`,
      avatarUrl: null,
      ...overrides,
    },
  };
}

describe("GroupModal", () => {
  it("does not render anything when isOpen is false", () => {
    const { container } = render(
      <GroupModal
        isOpen={false}
        mode="create"
        onClose={vi.fn()}
        friends={[]}
        onSubmit={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("displays the correct title for mode=create and mode=edit", () => {
    const { rerender } = render(
      <GroupModal
        isOpen={true}
        mode="create"
        onClose={vi.fn()}
        friends={[]}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByRole("heading", { name: "Create Group" })).toBeInTheDocument();

    rerender(
      <GroupModal
        isOpen={true}
        mode="edit"
        onClose={vi.fn()}
        friends={[]}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByRole("heading", { name: "Edit Group" })).toBeInTheDocument();
  });

  it("submit button is disabled if the name is empty or no members are selected", async () => {
    const user = userEvent.setup();
    const friends = [createFriend("1"), createFriend("2")];

    render(
      <GroupModal
        isOpen={true}
        mode="create"
        onClose={vi.fn()}
        friends={friends}
        onSubmit={vi.fn()}
      />
    );

    const submitButton = screen.getByRole("button", { name: /create group/i });
    const nameInput = screen.getByPlaceholderText("Enter group name") as HTMLInputElement;

    expect(submitButton).toBeDisabled();

    await user.type(nameInput, "My Group");
    expect(submitButton).toBeDisabled();

    const firstFriendButton = screen.getByText("user1@example.com").closest("button")!;
    await user.click(firstFriendButton);

    expect(submitButton).not.toBeDisabled();
  });

  it("selects and deselects friends on click", async () => {
    const user = userEvent.setup();
    const friends = [createFriend("1"), createFriend("2")];

    render(
      <GroupModal
        isOpen={true}
        mode="create"
        onClose={vi.fn()}
        friends={friends}
        onSubmit={vi.fn()}
      />
    );

    const button1 = screen.getByText("user1@example.com").closest("button")!;
    const button2 = screen.getByText("user2@example.com").closest("button")!;

    await user.click(button1);
    await user.click(button2);

    expect(screen.getByText("2 members selected")).toBeInTheDocument();

    await user.click(button1);

    expect(screen.getByText("1 member selected")).toBeInTheDocument();
  });

  it("calls onSubmit with the name and member list and then onClose", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const onClose = vi.fn();
    const friends = [createFriend("1"), createFriend("2")];

    render(
      <GroupModal
        isOpen={true}
        mode="create"
        onClose={onClose}
        friends={friends}
        onSubmit={onSubmit}
      />
    );

    const nameInput = screen.getByPlaceholderText("Enter group name") as HTMLInputElement;
    await user.type(nameInput, "Test Group");

    const friend1Button = screen.getByText("user1@example.com").closest("button")!;
    const friend2Button = screen.getByText("user2@example.com").closest("button")!;

    await user.click(friend1Button);
    await user.click(friend2Button);

    const submitButton = screen.getByRole("button", { name: /create group/i });
    await user.click(submitButton);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const [submittedName, submittedMembers] = onSubmit.mock.calls[0];

    expect(submittedName).toBe("Test Group");
    expect(submittedMembers.sort()).toEqual(["1", "2"]);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("filters the friends list by searchQuery", async () => {
  const user = userEvent.setup();
  const friends = [
    createFriend("1", { username: "alice" }),
    createFriend("2", { username: "bob" }),
  ];

  render(
    <GroupModal
      isOpen={true}
      mode="create"
      onClose={vi.fn()}
      friends={friends}
      onSubmit={vi.fn()}
    />
  );

  const searchInput = screen.getByPlaceholderText("Search friends...") as HTMLInputElement;

  await user.type(searchInput, "ali");

  expect(await screen.findByText("alice")).toBeInTheDocument();
  expect(screen.queryByText("bob")).not.toBeInTheDocument();

  await user.clear(searchInput);
  await user.type(searchInput, "zzz");

  expect(screen.getByText("No friends found")).toBeInTheDocument();
});


  it("resets state when reopened with initialName and initialMemberIds", async () => {
    const user = userEvent.setup();
    const friends = [createFriend("1"), createFriend("2")];

    const { rerender } = render(
      <GroupModal
        isOpen={true}
        mode="edit"
        onClose={vi.fn()}
        friends={friends}
        initialName="Initial Group"
        initialMemberIds={["1"]}
        onSubmit={vi.fn()}
      />
    );

    const nameInput = screen.getByPlaceholderText("Enter group name") as HTMLInputElement;
    expect(nameInput.value).toBe("Initial Group");
    expect(screen.getByText("1 member selected")).toBeInTheDocument();

    await user.clear(nameInput);
    await user.type(nameInput, "Changed");

    const friend2Button = screen.getByText("user2@example.com").closest("button")!;
    await user.click(friend2Button); 

    rerender(
      <GroupModal
        isOpen={false}
        mode="edit"
        onClose={vi.fn()}
        friends={friends}
        initialName="Initial Group"
        initialMemberIds={["1"]}
        onSubmit={vi.fn()}
      />
    );

    rerender(
      <GroupModal
        isOpen={true}
        mode="edit"
        onClose={vi.fn()}
        friends={friends}
        initialName="Initial Group"
        initialMemberIds={["1"]}
        onSubmit={vi.fn()}
      />
    );

    const nameInput2 = screen.getByPlaceholderText("Enter group name") as HTMLInputElement;
    expect(nameInput2.value).toBe("Initial Group");
    expect(screen.getByText("1 member selected")).toBeInTheDocument();
  });

  it("uses fallback avatar when image fails to load", async () => {
    const user = userEvent.setup();
    const friends = [
      createFriend("1", {
        username: "avataruser",
        avatarUrl: "http://example.com/avatar.png",
      }),
    ];

    render(
      <GroupModal
        isOpen={true}
        mode="create"
        onClose={vi.fn()}
        friends={friends as any}
        onSubmit={vi.fn()}
      />
    );

    const img = screen.getByAltText("avataruser") as HTMLImageElement;
    expect(img).toBeInTheDocument();

    fireEvent.error(img);
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("calls onClose when Cancel or X is pressed", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <GroupModal
        isOpen={true}
        mode="create"
        onClose={onClose}
        friends={[]}
        onSubmit={vi.fn()}
      />
    );

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    const timesAfterCancel = onClose.mock.calls.length;

    const buttons = screen.getAllByRole("button");
    const xButton = buttons.find((btn) => btn !== cancelButton)!;

    await user.click(xButton);

    expect(onClose).toHaveBeenCalledTimes(timesAfterCancel + 1);
  });
});

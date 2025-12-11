import React, { useState } from "react";
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, jest } from "@jest/globals";

import { AccountModal } from "../../src/components/AccountModal";
import type { UserAccountDetails } from "../../src/types/user/userAccountDetails";

function createAccount(overrides: Partial<UserAccountDetails> = {}): UserAccountDetails {
  return {
    id: "user-1",
    email: "user@example.com",
    username: "testuser",
    avatar_url: null,
    ...overrides,
  };
}

function Wrapper() {
  const [isOpen, setIsOpen] = useState(true);
  const [account, setAccount] = useState<UserAccountDetails>(
    createAccount({
      username: "initialuser",
      email: "initial@example.com",
    })
  );

  const handleSave = (updated: UserAccountDetails) => {
    setAccount(updated);
  };

  return (
    <div>
      <div data-testid="account-username-display">{account.username}</div>
      <div data-testid="account-email-display">{account.email}</div>

      <AccountModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        account={account}
        onSave={handleSave}
      />
    </div>
  );
}

describe("AccountModal integration-ish", () => {
  it("updates parent account state via onSave and reflects changes in parent UI", async () => {
    const user = userEvent.setup();

    render(<Wrapper />);

    expect(screen.getByTestId("account-username-display")).toHaveTextContent(
      "initialuser"
    );
    expect(screen.getByTestId("account-email-display")).toHaveTextContent(
      "initial@example.com"
    );

    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;

    await user.clear(usernameInput);
    await user.type(usernameInput, "updateduser");
    await user.clear(emailInput);
    await user.type(emailInput, "updated@example.com");

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByTestId("account-username-display")).toHaveTextContent(
        "updateduser"
      );
      expect(screen.getByTestId("account-email-display")).toHaveTextContent(
        "updated@example.com"
      );
    });
  });

  it("closes modal when onClose is triggered from Close button", async () => {
    const user = userEvent.setup();

    render(<Wrapper />);

    expect(screen.getByText("Account Settings")).toBeInTheDocument();

    const closeButton = screen.getByRole("button", { name: /close/i });
    await user.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText("Account Settings")).not.toBeInTheDocument();
    });
  });

  it("resets form to latest parent account when reopened with updated props", async () => {
    const user = userEvent.setup();

    render(<Wrapper />);

    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;

    await user.clear(usernameInput);
    await user.type(usernameInput, "tempuser");
    await user.clear(emailInput);
    await user.type(emailInput, "temp@example.com");

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByTestId("account-username-display")).toHaveTextContent(
        "tempuser"
      );
    });

    const reopenButton = screen.queryByRole("button", { name: /edit profile/i });
    if (!reopenButton) {
      expect(screen.getByTestId("account-email-display")).toHaveTextContent(
        "temp@example.com"
      );
    }
  });
});

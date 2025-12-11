import React from "react";
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

function renderModal(
  propsOverrides: Partial<React.ComponentProps<typeof AccountModal>> = {}
) {
  const account = createAccount();
  const defaultProps: React.ComponentProps<typeof AccountModal> = {
    isOpen: true,
    onClose: jest.fn(),
    account,
    onSave: jest.fn(),
  };

  const props = { ...defaultProps, ...propsOverrides };

  const utils = render(<AccountModal {...props} />);

  return {
    ...utils,
    props,
  };
}

describe("AccountModal", () => {
  it("does not render when isOpen is false", () => {
    const { container } = render(
      <AccountModal
        isOpen={false}
        onClose={jest.fn()}
        account={createAccount()}
        onSave={jest.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("renders header, info text and fields when open", () => {
    renderModal();

    expect(screen.getByText("Account Settings")).toBeInTheDocument();
    expect(
      screen.getByText(/You signed up with/i)
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
  });

  it("shows avatar initial when avatar_url is null", () => {
    const account = createAccount({ username: "miruna", avatar_url: null });

    render(
      <AccountModal
        isOpen={true}
        onClose={jest.fn()}
        account={account}
        onSave={jest.fn()}
      />
    );

    // Inițiala username-ului în avatar
    expect(screen.getByText("M")).toBeInTheDocument();
  });

  it("shows avatar image when avatar_url is present", () => {
    const account = createAccount({
      username: "miruna",
      avatar_url: "https://example.com/avatar.png",
    });

    render(
      <AccountModal
        isOpen={true}
        onClose={jest.fn()}
        account={account}
        onSave={jest.fn()}
      />
    );

    const img = screen.getByAltText("avatar") as HTMLImageElement;
    expect(img).toBeInTheDocument();
    expect(img.src).toContain("https://example.com/avatar.png");
  });

  it("disables inputs by default and enables them in edit mode", async () => {
    const user = userEvent.setup();
    renderModal();

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;

    // implicit disabled
    expect(usernameInput).toBeDisabled();
    expect(emailInput).toBeDisabled();

    // intrăm în Edit Profile
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    expect(usernameInput).not.toBeDisabled();
    expect(emailInput).not.toBeDisabled();
  });

  it("shows validation error when username is empty on save", async () => {
    const user = userEvent.setup();
    const { props } = renderModal();

    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(usernameInput);

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    expect(screen.getByText("Username is required")).toBeInTheDocument();
    expect(props.onSave).not.toHaveBeenCalled();
  });

  it("shows validation error when email is empty on save", async () => {
    const user = userEvent.setup();
    const { props } = renderModal();

    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    await user.clear(emailInput);

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);
    
    expect(screen.getByText("Email is required")).toBeInTheDocument();
    expect(props.onSave).not.toHaveBeenCalled();
  });

  it("calls onSave with updated data and exits edit mode", async () => {
    const user = userEvent.setup();
    const onSave = jest.fn();
    const account = createAccount({
      username: "olduser",
      email: "old@example.com",
    });

    render(
      <AccountModal
        isOpen={true}
        onClose={jest.fn()}
        account={account}
        onSave={onSave}
      />
    );

    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;

    await user.clear(usernameInput);
    await user.type(usernameInput, "newuser");
    await user.clear(emailInput);
    await user.type(emailInput, "new@example.com");

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith({
      ...account,
      username: "newuser",
      email: "new@example.com",
    });

    // după save revine la mod non-edit (butonul Edit Profile reapare)
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /edit profile/i })
      ).toBeInTheDocument();
    });
  });

  it("resets form and error on Cancel", async () => {
    const user = userEvent.setup();
    const account = createAccount({
      username: "original",
      email: "original@example.com",
    });

    render(
      <AccountModal
        isOpen={true}
        onClose={jest.fn()}
        account={account}
        onSave={jest.fn()}
      />
    );

    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(usernameInput);
    await user.type(usernameInput, "changed");

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    expect(usernameInput.value).toBe("original");
    // nu trebuie să mai fie niciun mesaj de eroare
    expect(screen.queryByText(/required/)).toBeNull();
  });

  it("syncs formData with account when props.account changes while open", async () => {
    const user = userEvent.setup();
    const initialAccount = createAccount({
      username: "first",
      email: "first@example.com",
    });

    const { rerender } = render(
      <AccountModal
        isOpen={true}
        onClose={jest.fn()}
        account={initialAccount}
        onSave={jest.fn()}
      />
    );

    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    expect(usernameInput.value).toBe("first");

    const updatedAccount = createAccount({
      username: "second",
      email: "second@example.com",
    });

    rerender(
      <AccountModal
        isOpen={true}
        onClose={jest.fn()}
        account={updatedAccount}
        onSave={jest.fn()}
      />
    );

    await waitFor(() => {
      expect(usernameInput.value).toBe("second");
    });
  });

  it("calls onClose when Close button is clicked in non-edit mode", async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();

    render(
      <AccountModal
        isOpen={true}
        onClose={onClose}
        account={createAccount()}
        onSave={jest.fn()}
      />
    );

    const closeButton = screen.getByRole("button", { name: /close/i });
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

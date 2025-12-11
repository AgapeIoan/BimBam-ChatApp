import "@testing-library/jest-dom";
import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { UsernameSetupModal } from "../../src/components/UsernameSetupModal";

describe("UsernameSetupModal", () => {
  const baseProps = {
    email: "user@example.com",
    defaultUsername: "user123",
    onConfirm: vi.fn(),
  };

  const renderModal = (overrides: Partial<typeof baseProps> = {}) =>
    render(<UsernameSetupModal {...baseProps} {...overrides} />);

  it("renders email, default username and confirm button", () => {
    renderModal();

    expect(screen.getByText("Choose Your Username")).toBeInTheDocument();
    expect(
      screen.getByText("This is how others will find you on BimBam Chat")
    ).toBeInTheDocument();
    expect(screen.getByText("Signed in as")).toBeInTheDocument();
    expect(screen.getByText(baseProps.email)).toBeInTheDocument();

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    expect(input.value).toBe(baseProps.defaultUsername);

    expect(
      screen.getByRole("button", { name: /confirm/i })
    ).toBeInTheDocument();
  });

  it("updates username when typing", async () => {
    const user = userEvent.setup();
    renderModal({ defaultUsername: "oldname" });

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(input);
    await user.type(input, "newname");

    expect(input.value).toBe("newname");
  });

  it("shows error when username is empty", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ defaultUsername: "", onConfirm });

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(input);
    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(
      screen.getByText("Username is required")
    ).toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("shows error when username is shorter than 3 characters", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ defaultUsername: "ab", onConfirm });

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(input);
    await user.type(input, "ab");
    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(
      screen.getByText("Username must be at least 3 characters")
    ).toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("shows error when username has invalid characters", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ defaultUsername: "user!", onConfirm });

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(input);
    await user.type(input, "bad name!");
    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(
      screen.getByText("Username can only contain letters, numbers, and underscores")
    ).toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("calls onConfirm with trimmed valid username when clicking Confirm", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ defaultUsername: " initial ", onConfirm });

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(input);
    await user.type(input, "  valid_name  ");
    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm).toHaveBeenCalledWith("valid_name");
    expect(
      screen.queryByText(/Username is required/i)
    ).not.toBeInTheDocument();
  });

  it("submits when pressing Enter in the input", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ defaultUsername: "user_ok", onConfirm });

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    await user.clear(input);
    await user.type(input, "another_name{enter}");

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm).toHaveBeenCalledWith("another_name");
  });
});

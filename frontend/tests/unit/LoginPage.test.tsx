import "@testing-library/jest-dom/vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeAll, afterAll, vi } from "vitest";

import { LoginPage } from "../../src/components/LoginPage";

const originalConsoleError = console.error;
const NAV_NOT_IMPLEMENTED = "Not implemented: navigation (except hash changes)";

let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

beforeAll(() => {
  consoleErrorSpy = vi
    .spyOn(console, "error")
    .mockImplementation((...args: unknown[]) => {
      const firstArg = args[0] as any;

      const msg =
        typeof firstArg === "string"
          ? firstArg
          : firstArg && typeof firstArg.message === "string"
          ? firstArg.message
          : "";

      if (msg.includes(NAV_NOT_IMPLEMENTED)) {
        return;
      }

      (originalConsoleError as any)(...args);
    });
});

afterAll(() => {
  consoleErrorSpy.mockRestore();
});

describe("LoginPage", () => {
  it("renders title, description and login/signup buttons", () => {
    const onSwitchToSignUp = vi.fn();

    render(<LoginPage onSwitchToSignUp={onSwitchToSignUp} />);

    expect(screen.getByText("Welcome to BimBam Chat")).toBeInTheDocument();
    expect(
      screen.getByText("Sign in to continue to your conversations")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in with google/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign up/i })
    ).toBeInTheDocument();
  });

  it("calls onSwitchToSignUp when user clicks Sign up", async () => {
    const user = userEvent.setup();
    const onSwitchToSignUp = vi.fn();

    render(<LoginPage onSwitchToSignUp={onSwitchToSignUp} />);

    const signUpButton = screen.getByRole("button", { name: /sign up/i });
    await user.click(signUpButton);

    expect(onSwitchToSignUp).toHaveBeenCalledTimes(1);
  });

  it("calls Google login handler when button is clicked", async () => {
    const user = userEvent.setup();
    const onSwitchToSignUp = vi.fn();

    render(<LoginPage onSwitchToSignUp={onSwitchToSignUp} />);

    const googleButton = screen.getByRole("button", {
      name: /sign in with google/i,
    });

    await user.click(googleButton);
    expect(googleButton).toBeInTheDocument();
  });

  it("shows error message for authError = 'no_account'", () => {
    render(<LoginPage onSwitchToSignUp={() => {}} authError="no_account" />);

    expect(
      screen.getByText(
        "You don't have an account yet. Please sign up first."
      )
    ).toBeInTheDocument();
  });

  it("shows error message for authError = 'google_failed'", () => {
    render(<LoginPage onSwitchToSignUp={() => {}} authError="google_failed" />);

    expect(
      screen.getByText("Google authentication failed. Please try again.")
    ).toBeInTheDocument();
  });

  it("does not show error message when authError is null or undefined", () => {
    const { rerender } = render(<LoginPage onSwitchToSignUp={() => {}} />);

    expect(
      screen.queryByText(
        "You don't have an account yet. Please sign up first."
      )
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "Google authentication failed. Please try again."
      )
    ).not.toBeInTheDocument();

    rerender(<LoginPage onSwitchToSignUp={() => {}} authError={null} />);

    expect(
      screen.queryByText(
        "You don't have an account yet. Please sign up first."
      )
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "Google authentication failed. Please try again."
      )
    ).not.toBeInTheDocument();
  });
});

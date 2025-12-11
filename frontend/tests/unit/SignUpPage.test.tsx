import "@testing-library/jest-dom";
import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

import { SignUpPage } from "../../src/components/SignUpPage";

const originalEnv = { ...import.meta.env };
const originalLocation = window.location;

let hrefValue = originalLocation.href;

beforeAll(() => {
  delete (window as any).location;
  Object.defineProperty(window, "location", {
    configurable: true,
    enumerable: true,
    value: {
      ...originalLocation,
      get href() {
        return hrefValue;
      },
      set href(v: string) {
        hrefValue = v;
      },
    },
  });
});

afterAll(() => {
  Object.defineProperty(window, "location", {
    configurable: true,
    enumerable: true,
    value: originalLocation,
  });
  (import.meta as any).env = originalEnv;
});

beforeEach(() => {
  hrefValue = originalLocation.href;
  (import.meta as any).env = { ...originalEnv };
});

describe("SignUpPage", () => {
  it("renders title, description and UI elements", () => {
    const onSwitchToLogin = vi.fn();

    render(<SignUpPage onSwitchToLogin={onSwitchToLogin} />);

    expect(
      screen.getByText("Create your account")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Join BimBam Chat and start connecting")
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /sign up with google/i })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("redirects to Google signup using VITE_API_URL when defined", async () => {
    const user = userEvent.setup();
    const onSwitchToLogin = vi.fn();

    (import.meta as any).env.VITE_API_URL = "https://localhost:8000";

    render(<SignUpPage onSwitchToLogin={onSwitchToLogin} />);

    const googleButton = screen.getByRole("button", {
      name: /sign up with google/i,
    });

    await user.click(googleButton);

    expect(window.location.href).toBe(
      "http://localhost:8000/api/v1/auth/google/login?mode=signup"
    );
  });

  it("falls back to http://localhost:8000 when VITE_API_URL is not defined", async () => {
    const user = userEvent.setup();
    const onSwitchToLogin = vi.fn();

    delete (import.meta as any).env.VITE_API_URL;

    render(<SignUpPage onSwitchToLogin={onSwitchToLogin} />);

    const googleButton = screen.getByRole("button", {
      name: /sign up with google/i,
    });

    await user.click(googleButton);

    expect(window.location.href).toBe(
      "http://localhost:8000/api/v1/auth/google/login?mode=signup"
    );
  });

  it("calls onSwitchToLogin when clicking the Sign in button", async () => {
    const user = userEvent.setup();
    const onSwitchToLogin = vi.fn();

    render(<SignUpPage onSwitchToLogin={onSwitchToLogin} />);

    const signInButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(signInButton);

    expect(onSwitchToLogin).toHaveBeenCalledTimes(1);
  });
});

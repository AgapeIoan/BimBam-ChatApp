import "@testing-library/jest-dom";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import ReactionPicker from "../../src/components/ReactionPicker";

let lastOnEmojiClick: ((data: any) => void) | null = null;

vi.mock("emoji-picker-react", () => {
  const MockEmojiPicker = ({ onEmojiClick }: { onEmojiClick: (data: any) => void }) => {
    lastOnEmojiClick = onEmojiClick;
    return (
      <button type="button" data-testid="mock-emoji-button" onClick={() => onEmojiClick({ emoji: "😀", native: "😀" })}>
        Mock Emoji
      </button>
    );
  };

  return {
    __esModule: true,
    default: MockEmojiPicker,
  };
});

describe("ReactionPicker", () => {
  beforeEach(() => {
    lastOnEmojiClick = null;
  });

  it("renders with role dialog and optional className", () => {
    const onSelect = vi.fn();

    render(
      <ReactionPicker
        onSelect={onSelect}
        className="extra-class"
      />
    );

    const root = screen.getByRole("dialog", { name: "Reaction picker" });
    expect(root).toBeInTheDocument();
    expect(root).toHaveClass("inline-flex", "items-center");
    expect(root).toHaveClass("extra-class");

    expect(screen.getByTestId("mock-emoji-button")).toBeInTheDocument();
  });

  it("focuses the first button on mount", () => {
    const onSelect = vi.fn();

    render(<ReactionPicker onSelect={onSelect} />);

    const button = screen.getByTestId("mock-emoji-button");
    expect(button).toHaveFocus();
  });

  it("calls onSelect with chosen emoji and closes on click", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onClose = vi.fn();

    render(<ReactionPicker onSelect={onSelect} onClose={onClose} />);

    const button = screen.getByTestId("mock-emoji-button");
    await user.click(button);

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith("😀");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("supports unified/native fallback when emoji field is missing", () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();

    render(<ReactionPicker onSelect={onSelect} onClose={onClose} />);

    // Use the captured onEmojiClick to simulate a different payload shape
    expect(lastOnEmojiClick).not.toBeNull();

    // Case: only unified present, no emoji / native
    lastOnEmojiClick!({ unified: "1F600" });

    expect(onSelect).toHaveBeenCalledWith("1F600");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes when Escape key is pressed", () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();

    render(<ReactionPicker onSelect={onSelect} onClose={onClose} />);

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

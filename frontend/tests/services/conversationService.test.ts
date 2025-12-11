import { describe, it, expect, vi, beforeEach } from "vitest";

// Importăm funcțiile pe care le testăm
import {
  loadConversationPreviews,
  openOrCreateDirectConversation,
} from "../../src/services/conversationService"; // ajustează calea

// Mock pentru apiClient
import { apiClient } from "../../src/services/apiClient";

vi.mock("../../src/services/apiClient", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("conversationService", () => {
  it("loadConversationPreviews apelează apiClient.get cu endpoint corect și returnează datele", async () => {
    const mockResponse = [
      { id: "1", title: "Chat A", lastMessage: "Hello" },
      { id: "2", title: "Chat B", lastMessage: "Hi" },
    ];

    (apiClient.get as any).mockResolvedValue(mockResponse);

    const data = await loadConversationPreviews();

    expect(apiClient.get).toHaveBeenCalledWith("/api/v1/conversations/");
    expect(data).toEqual(mockResponse);
  });

  it("openOrCreateDirectConversation apelează apiClient.get cu friendId corect", async () => {
    const friendId = "friend-123";

    const mockResponse = {
      id: "conv-999",
      participants: ["me", friendId],
      messages: [],
    };

    (apiClient.get as any).mockResolvedValue(mockResponse);

    const data = await openOrCreateDirectConversation(friendId);

    expect(apiClient.get).toHaveBeenCalledWith(
      `/api/v1/friends/${friendId}/conversation`
    );
    expect(data).toEqual(mockResponse);
  });
});

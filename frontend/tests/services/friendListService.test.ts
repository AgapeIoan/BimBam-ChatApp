import { describe, it, expect, vi, beforeEach } from "vitest";
import { listMyFriends } from "../../src/services/friendsService"; // ajustează calea
import { apiClient } from "../../src/services/apiClient";

vi.mock("../../src/services/apiClient", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.clearAllMocks();
});

describe("friendListService", () => {
  it("listMyFriends apelează endpointul corect și returnează lista de prieteni", async () => {
    const mockFriends = [
      {
        id: "f1",
        name: "Alice",
        username: "alice123",
        avatarUrl: null,
        online: true,
      },
      {
        id: "f2",
        name: "Bob",
        username: "bobby",
        avatarUrl: "http://example.com/bob.png",
        online: false,
      },
    ];

    mockedGet.mockResolvedValue(mockFriends);

    const result = await listMyFriends();

    expect(mockedGet).toHaveBeenCalledWith("/api/v1/friends/");
    expect(result).toEqual(mockFriends);
  });
});

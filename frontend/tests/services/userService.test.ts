import { describe, it, expect, vi, beforeEach } from "vitest";
import { getMe, searchUsers } from "../../src/services/userService"; // ajustează calea
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

describe("userService", () => {
  it("getMe apelează endpointul corect și returnează userul", async () => {
    const mockUser = {
      id: "1",
      username: "miruna",
      email: "miruna@example.com",
      avatar_url: null,
    };

    mockedGet.mockResolvedValue(mockUser);

    const result = await getMe();

    expect(mockedGet).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(result).toEqual(mockUser);
  });

  it("searchUsers returnează [] dacă query este gol", async () => {
    const result = await searchUsers("", "username");

    expect(result).toEqual([]);
    expect(mockedGet).not.toHaveBeenCalled();
  });

  it("searchUsers returnează [] dacă query are lungimea < 2", async () => {
    const result = await searchUsers("a", "email");

    expect(result).toEqual([]);
    expect(mockedGet).not.toHaveBeenCalled();
  });

  it("searchUsers folosește endpointul username când type='username'", async () => {
    const mockResults = [
      {
        id: "u1",
        username: "miruna",
        email: "m@example.com",
      },
    ];

    mockedGet.mockResolvedValue(mockResults);

    const result = await searchUsers("mi", "username");

    expect(mockedGet).toHaveBeenCalledWith(
      "/api/v1/users/search-by-username",
      { q: "mi" }
    );
    expect(result).toEqual(mockResults);
  });

  it("searchUsers folosește endpointul email când type='email'", async () => {
    const mockResults = [
      {
        id: "u2",
        username: "john",
        email: "john@example.com",
      },
    ];

    mockedGet.mockResolvedValue(mockResults);

    const result = await searchUsers("jo", "email");

    expect(mockedGet).toHaveBeenCalledWith(
      "/api/v1/users/search-by-email",
      { q: "jo" }
    );
    expect(result).toEqual(mockResults);
  });
});

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  sendFriendRequest,
  acceptFriendRequest,
  declineFriendRequest,
  cancelFriendRequest,
  listIncomingRequests,
  listOutgoingRequests,
} from "../../src/services/friendRequestsService";
import { apiClient } from "../../src/services/apiClient";

// mock pentru apiClient
vi.mock("../../src/services/apiClient", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>;
const mockedPost = apiClient.post as unknown as ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.clearAllMocks();
});

describe("friendRequestsService", () => {
  it("sendFriendRequest apelează apiClient.post cu endpointul corect și body-ul potrivit", async () => {
    const response = { id: "req-1", status: "pending" };
    mockedPost.mockResolvedValue(response);

    const result = await sendFriendRequest("friend@example.com");

    expect(mockedPost).toHaveBeenCalledWith("/api/v1/friend-requests", {
      toEmail: "friend@example.com",
    });
    expect(result).toEqual(response);
  });

  it("acceptFriendRequest apelează endpointul /{id}/accept cu body null", async () => {
    const response = { id: "req-1", status: "accepted" };
    mockedPost.mockResolvedValue(response);

    const result = await acceptFriendRequest("req-1");

    expect(mockedPost).toHaveBeenCalledWith(
      "/api/v1/friend-requests/req-1/accept",
      null
    );
    expect(result).toEqual(response);
  });

  it("declineFriendRequest apelează endpointul /{id}/decline cu body null", async () => {
    const response = { id: "req-2", status: "declined" };
    mockedPost.mockResolvedValue(response);

    const result = await declineFriendRequest("req-2");

    expect(mockedPost).toHaveBeenCalledWith(
      "/api/v1/friend-requests/req-2/decline",
      null
    );
    expect(result).toEqual(response);
  });

  it("cancelFriendRequest apelează endpointul /{id}/cancel cu body null", async () => {
    const response = { id: "req-3", status: "canceled" };
    mockedPost.mockResolvedValue(response);

    const result = await cancelFriendRequest("req-3");

    expect(mockedPost).toHaveBeenCalledWith(
      "/api/v1/friend-requests/req-3/cancel",
      null
    );
    expect(result).toEqual(response);
  });

  it("listIncomingRequests folosește endpointul /incoming și întoarce lista", async () => {
    const response = [{ id: "req-in-1" }, { id: "req-in-2" }];
    mockedGet.mockResolvedValue(response);

    const result = await listIncomingRequests();

    expect(mockedGet).toHaveBeenCalledWith(
      "/api/v1/friend-requests/incoming"
    );
    expect(result).toEqual(response);
  });

  it("listOutgoingRequests folosește endpointul /outgoing și întoarce lista", async () => {
    const response = [{ id: "req-out-1" }];
    mockedGet.mockResolvedValue(response);

    const result = await listOutgoingRequests();

    expect(mockedGet).toHaveBeenCalledWith(
      "/api/v1/friend-requests/outgoing"
    );
    expect(result).toEqual(response);
  });
});

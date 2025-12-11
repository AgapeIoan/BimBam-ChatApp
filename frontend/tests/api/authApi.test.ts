/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  fetchCurrentUser,
  updateUsername,
  logout,
  type AuthUser,
} from "../../src/api/client"

const API_URL = "http://localhost:8000";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  (globalThis as any).fetch = fetchMock;
});

function createResponse(
  ok: boolean,
  status: number,
  body: any = {}
): any {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
  };
}

describe("fetchCurrentUser", () => {
  it("returns the user when the response is ok", async () => {
    const user: AuthUser = {
      id: "1",
      email: "test@example.com",
      username: "testuser",
      avatar_url: null,
      provider: "google",
      name: "Test User",
    };

    fetchMock.mockResolvedValue(createResponse(true, 200, user));

    const result = await fetchCurrentUser();

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/api/v1/auth/me`,
      {
        method: "GET",
        credentials: "include",
      }
    );
    expect(result).toEqual(user);
  });

  it("returns null when the response is not ok (e.g., 401)", async () => {
    fetchMock.mockResolvedValue(createResponse(false, 401, {}));

    const result = await fetchCurrentUser();

    expect(result).toBeNull();
  });

  it("returns null when fetch throws an error (network, etc.)", async () => {
    fetchMock.mockRejectedValue(new Error("network error"));

    const result = await fetchCurrentUser();

    expect(result).toBeNull();
  });
});

describe("updateUsername", () => {
  it("calls the correct endpoint and returns the updated username", async () => {
    const newUsername = "miruna";
    const responseBody = { username: newUsername };

    fetchMock.mockResolvedValue(createResponse(true, 200, responseBody));

    const result = await updateUsername(newUsername);

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/api/v1/users/me/username?new_username=${encodeURIComponent(
        newUsername
      )}`,
      {
        method: "PUT",
        credentials: "include",
      }
    );
    expect(result).toEqual(responseBody);
  });

  it("throws an error with the `detail` message when the response is not ok and has JSON with detail", async () => {
    fetchMock.mockResolvedValue(
      createResponse(false, 400, { detail: "Username already taken" })
    );

    await expect(updateUsername("taken")).rejects.toThrow(
      "Username already taken"
    );
  });

  it("throws a generic error when the response is not ok and does not have detail", async () => {
    // facem json să arunce, ca să intre în `.catch(() => ({}))`
    const res = {
      ok: false,
      status: 500,
      json: vi.fn().mockRejectedValue(new Error("bad json")),
    };
    fetchMock.mockResolvedValue(res as any);

    await expect(updateUsername("whatever")).rejects.toThrow(
      "Failed to update username"
    );
  });
});

describe("logout", () => {
  it("calls the logout endpoint with POST method and credentials include", async () => {
    fetchMock.mockResolvedValue(createResponse(true, 200, {}));

    await logout();

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_URL}/api/v1/auth/logout`,
      {
        method: "POST",
        credentials: "include",
      }
    );
  });

  it("does not throw an error if fetch fails (the error is only logged)", async () => {
    fetchMock.mockRejectedValue(new Error("network"));

    await expect(logout()).resolves.toBeUndefined();
  });
});

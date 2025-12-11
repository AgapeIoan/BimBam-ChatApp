import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "../../src/services/apiClient";
import type { RequestInit } from "node-fetch";

const BASE_URL = "http://localhost:8000";

const fetchMock = vi.fn();

global.fetch = fetchMock as unknown as typeof fetch;

beforeEach(() => {
  fetchMock.mockReset();
});

function mockResponse(status: number, data: any) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  };
}

describe("apiClient", () => {
  it("GET fără params apelează fetch cu URL corect", async () => {
    fetchMock.mockResolvedValue(mockResponse(200, { ok: true }));

    const result = await apiClient.get("/test");

    expect(fetchMock).toHaveBeenCalledWith(BASE_URL + "/test", {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });

    expect(result).toEqual({ ok: true });
  });

  it("GET cu query params construiește corect URL-ul", async () => {
    fetchMock.mockResolvedValue(mockResponse(200, { user: "test" }));

    await apiClient.get("/users", { page: 1, sort: "asc" });

    expect(fetchMock).toHaveBeenCalledWith(
      BASE_URL + "/users?page=1&sort=asc",
      expect.any(Object)
    );
  });

  it("POST trimite method=POST și body JSON", async () => {
    fetchMock.mockResolvedValue(mockResponse(200, { created: true }));

    const data = { name: "John" };
    const res = await apiClient.post("/users", data);

    expect(fetchMock).toHaveBeenCalledWith(BASE_URL + "/users", {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(data),
    });

    expect(res).toEqual({ created: true });
  });

  it("PUT trimite method=PUT și body JSON", async () => {
    fetchMock.mockResolvedValue(mockResponse(200, { updated: true }));

    const payload = { name: "John Updated" };

    await apiClient.put("/users/1", payload);

    expect(fetchMock).toHaveBeenCalledWith(BASE_URL + "/users/1", {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      method: "PUT",
      body: JSON.stringify(payload),
    });
  });

  it("DELETE trimite method=DELETE", async () => {
    fetchMock.mockResolvedValue(mockResponse(200, { deleted: true }));

    await apiClient.delete("/users/1");

    expect(fetchMock).toHaveBeenCalledWith(BASE_URL + "/users/1", {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      method: "DELETE",
    });
  });

  it("aruncă eroare când statusul nu este ok", async () => {
    fetchMock.mockResolvedValue(mockResponse(500, { error: true }));

    await expect(apiClient.get("/fail")).rejects.toThrow("API error: 500");
  });

  it("transmite headers custom din options", async () => {
    fetchMock.mockResolvedValue(mockResponse(200, { ok: true }));

    await apiClient.post("/headers", { a: 1 });

    const lastCall = fetchMock.mock.calls[0][1] as RequestInit;

    expect(lastCall.headers).toEqual({
      "Content-Type": "application/json",
    });
  });
});

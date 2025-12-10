/* eslint-disable @typescript-eslint/no-explicit-any */
const BASE_URL = "http://localhost:8000"; // schimbă după nevoie

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(BASE_URL + endpoint, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(endpoint: string, params?: Record<string, any>) => {
    const url =
      params
        ? endpoint + "?" + new URLSearchParams(params).toString()
        : endpoint;

    return apiFetch<T>(url);
  },

  post: <T>(endpoint: string, body: any) =>
    apiFetch<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  put: <T>(endpoint: string, body: any) =>
    apiFetch<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  delete: <T>(endpoint: string) =>
    apiFetch<T>(endpoint, { method: "DELETE" }),
};

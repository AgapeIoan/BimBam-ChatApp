const API_BASE = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || "";

export async function fetchReactionUsers(
  messageId: string,
  emoji: string,
  opts?: { signal?: AbortSignal }
) {
  const encEmoji = encodeURIComponent(emoji);
  const url = `${API_BASE}/api/v1/messages/${messageId}/reactions/${encEmoji}/users`;
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = localStorage.getItem("token") || localStorage.getItem("access_token");
  const res = await fetch(url, {
    credentials: "include",
    headers: token ? { ...headers, Authorization: `Bearer ${token}` } : headers,
    signal: opts?.signal,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch reactors (${res.status}): ${text}`);
  }
  const data = await res.json();
  return data as string[];
}

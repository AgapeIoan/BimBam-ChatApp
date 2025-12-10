import { apiClient } from "./apiClient";
import type { UserAccountDetails } from "../types/user/userAccountDetails";
import type { UserResponse } from "../types/user/userResponse";

export async function getMe(): Promise<UserAccountDetails> {
  return apiClient.get<UserAccountDetails>("/api/v1/auth/me");
}


export async function searchUsers(
  query: string,
  type: "username" | "email"
): Promise<UserResponse[]> {
  if (!query || query.length < 2) {
    return [];
  }

  const endpoint =
    type === "email" ? "/api/v1/users/search-by-email" : "/api/v1/users/search-by-username";

  return apiClient.get<UserResponse[]>(endpoint, { q: query });
}

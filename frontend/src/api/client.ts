const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface AuthUser {
  id: string;
  email: string;
  username: string | null;
  avatar_url: string | null;
  provider: string;
  name?: string | null;

}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/me`, {
      method: 'GET',
      credentials: 'include', 
    });

    console.log('fetchCurrentUser status:', res.status);

    if (!res.ok) {
      // 401 / 403 / 404 -> treat as "not logged in"
      return null;
    }

    const data = (await res.json()) as AuthUser;
    console.log('fetchCurrentUser data:', data);
    return data;
  } catch (err) {
    console.error('Error fetching current user:', err);
    return null;
  }
}

export async function updateUsername(newUsername: string): Promise<{ username: string }> {
  const res = await fetch(
    `${API_URL}/api/v1/users/me/username?new_username=${encodeURIComponent(newUsername)}`,
    {
      method: 'PUT',
      credentials: 'include',
    }
  );

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to update username');
  }

  return res.json();
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_URL}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',   // send cookie so backend can clear it
    });
  } catch (err) {
    console.error('Error during logout:', err);
  }
}

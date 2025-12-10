import type { UserAccountDetails } from '../types/userAccountDetails';

export async function getMe(): Promise<UserAccountDetails> {
  const response = await fetch('http://localhost:8000/api/v1/auth/me', {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch user info');
  }
  return response.json();
}

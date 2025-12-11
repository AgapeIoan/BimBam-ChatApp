import { useEffect, useState } from 'react';
import { ChatApp } from './components/ChatApp';
import { LoginPage } from './components/LoginPage';
import { SignUpPage } from './components/SignUpPage';
import { UsernameSetupModal } from './components/UsernameSetupModal';
import { fetchCurrentUser } from './api/client';
import { updateUsername } from './api/client';
import type { AuthUser } from './api/client';
import { logout } from './api/client';

function normalizeUsernameFromGoogle(name: string | null | undefined, email: string): string {
  if (name) {
    const normalized = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 20);

    if (normalized) return normalized;
  }

  return email.split('@')[0];
}

//const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  console.log(" App component rendered");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showSignUp, setShowSignUp] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [showUsernameSetup, setShowUsernameSetup] = useState(false);
  const [defaultUsername, setDefaultUsername] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const handleLogout = async () => {
    await logout();                     
    setUser(null);
    setIsAuthenticated(false);
    setShowUsernameSetup(false);
    window.history.replaceState({}, document.title, window.location.pathname);
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const error = params.get('auth_error');
    if (error) {
      setAuthError(error);
    }
  }, []);

  // Load current session from backend on initial mount
  useEffect(() => {
    console.log(' App useEffect: checking current user...');
    (async () => {
      try {
        const current = await fetchCurrentUser();
        console.log(' /auth/me returned:', current);

        if (!current) {
          setIsAuthenticated(false);
          setUser(null);
          setIsLoading(false);
          return;
        }

        setUser(current);
        setIsAuthenticated(true);
        setUserEmail(current.email);

        if (!current.username || current.username.trim() === '') {
          const guessed = normalizeUsernameFromGoogle(current.name ?? null, current.email);
          setDefaultUsername(guessed);
          setShowUsernameSetup(true);
        }
      } catch (e) {
        console.error('Error in session check:', e);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const handleUsernameConfirm = async (username: string) => {
    try {
      // persist to backend
      const result = await updateUsername(username);
      console.log('Username saved:', result.username);

      // update local state
      if (user) {
        setUser({ ...user, username: result.username });
      }
      setShowUsernameSetup(false);
      setIsAuthenticated(true);
    } catch (err: unknown) {
      console.error('Failed to save username:', err);
    }
  };

  if (isLoading) {

    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900 text-slate-100">
        <span className="text-sm text-slate-300">Loading...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (showSignUp) {
      return (
        <SignUpPage
          onSwitchToLogin={() => setShowSignUp(false)}
        />
      );
    }

    return (
      <LoginPage
        onSwitchToSignUp={() => setShowSignUp(true)}
        authError={authError}
      />
    );
  }

  return (
    <>
      {showUsernameSetup && (
        <UsernameSetupModal
          email={userEmail}
          defaultUsername={defaultUsername}
          onConfirm={handleUsernameConfirm}
        />
      )}

      {user && <ChatApp onLogout={handleLogout} currentUser={user} />}
    </>
  );
}

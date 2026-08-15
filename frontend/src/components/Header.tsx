import React, { useEffect, useState } from 'react';
import { RefreshCw, Settings as SettingsIcon, LogIn, LogOut, X } from 'lucide-react';
import { getCurrentUser, loginUser, logoutUser, registerUser } from '../api';
import { useTimeOfDay } from '../hooks/useTimeOfDay';
import BrandTitle from './BrandTitle';
import Settings from './Settings';

interface Props {
  onIngest: () => void;
  ingesting: boolean;
}

const Header: React.FC<Props> = ({ onIngest, ingesting }) => {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [user, setUser] = useState<{ id: number; email: string } | null>(null);
  const timePeriod = useTimeOfDay();

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => setUser(null));
  }, []);

  const handleAuthSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      if (authMode === 'register') {
        await registerUser(email, password);
        setAuthMessage('Account created. You are signed in.');
      } else {
        await loginUser(email, password);
        setAuthMessage('Signed in.');
      }
      const current = await getCurrentUser();
      setUser(current);
      setEmail('');
      setPassword('');
      setAuthOpen(false);
    } catch (error) {
      setAuthMessage(error instanceof Error ? error.message : 'Authentication failed');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
  };

  const openAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthMessage(null);
    setAuthOpen(true);
  };

  return (
    <>
      <header className="header">
        <div className="header__inner">
          <div className="header__brand">
            <BrandTitle className="header__title" />
          </div>

          <nav className="header__nav">
            <button className="btn btn-light" onClick={onIngest} disabled={ingesting}>
              <RefreshCw size={14} />
              {ingesting ? 'Refreshing…' : 'Refresh'}
            </button>
            {user ? (
              <>
                <button className="btn btn-subtle" onClick={() => setSettingsOpen(true)}>
                  <SettingsIcon size={16} />
                  Settings
                </button>
                <button className="btn btn-subtle" onClick={handleLogout}>
                  <LogOut size={16} />
                  Logout
                </button>
              </>
            ) : (
              <button className="btn btn-subtle" onClick={() => openAuth('login')}>
                <LogIn size={16} />
                Sign in
              </button>
            )}
          </nav>
        </div>
      </header>

      {settingsOpen && (
        <>
          <div className="settings-overlay" onClick={() => setSettingsOpen(false)} />
          <div className="settings-content">
            <Settings onClose={() => setSettingsOpen(false)} onSave={() => {}} />
          </div>
        </>
      )}

      {authOpen && (
        <>
          <div className="settings-overlay" onClick={() => setAuthOpen(false)} />
          <div className="settings-content auth-modal">
            <div className="auth-modal__brand" data-time={timePeriod}>
              <BrandTitle as="h1" className="auth-modal__brand-title" />
              <p className="auth-modal__tagline">Stories grouped by relevance, for you</p>
              <button className="btn btn-icon auth-modal__close" onClick={() => setAuthOpen(false)} aria-label="Close">
                <X size={18} />
              </button>
            </div>
            <div className="auth-modal__body">
              <div className="auth-modal__intro">
                <h2>{authMode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
                <p>Save topics, trusted publishers, and location preferences.</p>
              </div>
              <form className="auth-form" onSubmit={handleAuthSubmit}>
                <label>
                  Email
                  <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="you@example.com" />
                </label>
                <label>
                  Password
                  <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required placeholder="••••••••" />
                </label>
                {authMessage && <p className="auth-message">{authMessage}</p>}
                <div className="auth-actions">
                  <button className="btn btn-primary" type="submit" disabled={authLoading}>
                    {authLoading ? 'Working…' : authMode === 'login' ? 'Sign in' : 'Create account'}
                  </button>
                  <button className="btn btn-secondary" type="button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
                    {authMode === 'login' ? 'Need an account?' : 'Already have one?'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default Header;
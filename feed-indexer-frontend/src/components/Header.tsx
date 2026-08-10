import React, { useEffect, useState } from 'react';
import { RefreshCw, Settings as SettingsIcon, LogIn, LogOut } from 'lucide-react';
import { getCurrentUser, loginUser, logoutUser, registerUser } from '../api';
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
            <div className="header__brand-badge">FI</div>
            <div>
              <div className="header__title">Feed Indexer</div>
              <div className="header__subtitle">Live stories, grouped by relevance</div>
            </div>
          </div>

          <nav className="header__nav">
            <button className="header__nav-link header__nav-link--action" onClick={onIngest} disabled={ingesting}>
              <RefreshCw size={14} style={{ marginRight: 4 }} />
              {ingesting ? 'Refreshing…' : 'Refresh'}
            </button>
            {user ? (
              <>
                <button className="header__nav-link" onClick={() => setSettingsOpen(true)}>
                  <SettingsIcon size={16} style={{ marginRight: 4 }} />
                  Settings
                </button>
                <button className="header__nav-link" onClick={handleLogout}>
                  <LogOut size={16} style={{ marginRight: 4 }} />
                  Logout
                </button>
              </>
            ) : (
              <button className="header__nav-link" onClick={() => openAuth('login')}>
                <LogIn size={16} style={{ marginRight: 4 }} />
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
            <div className="auth-modal__header">
              <div>
                <h2>{authMode === 'login' ? 'Sign in' : 'Create account'}</h2>
                <p>Save your topics, publishers, and location preferences.</p>
              </div>
              <button className="btn-secondary" onClick={() => setAuthOpen(false)}>
                Close
              </button>
            </div>
            <form className="auth-form" onSubmit={handleAuthSubmit}>
              <label>
                Email
                <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              </label>
              <label>
                Password
                <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
              </label>
              {authMessage && <p className="auth-message">{authMessage}</p>}
              <div className="auth-actions">
                <button className="btn-primary" type="submit" disabled={authLoading}>
                  {authLoading ? 'Working…' : authMode === 'login' ? 'Sign in' : 'Create account'}
                </button>
                <button className="btn-secondary" type="button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
                  {authMode === 'login' ? 'Need an account?' : 'Already have one?'}
                </button>
              </div>
            </form>
          </div>
        </>
      )}
    </>
  );
};

export default Header;
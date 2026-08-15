import { useEffect, useState } from 'react';
import styles from '../styles/Header.module.css';
import {
  RefreshCw,
  Settings as SettingsIcon,
  LogIn,
  LogOut,
} from 'lucide-react';
import { getCurrentUser, logoutUser } from '../api';
import BrandTitle from './BrandTitle';
import Settings from './Settings';
import AuthPage from './AuthPage';

interface Props {
  onIngest: () => void;
  ingesting: boolean;
}

const Header: React.FC<Props> = ({ onIngest, ingesting }) => {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [user, setUser] = useState<{ id: number; email: string } | null>(null);

  useEffect(() => {
    getCurrentUser().then(setUser);
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <>
      <header className={styles.header}>
        <div className={styles.inner}>
          <div className={styles.brand}>
            <BrandTitle className={styles.title} />
          </div>

          <nav className={styles.nav}>
            <button
              className="btn btn-light"
              onClick={onIngest}
              disabled={ingesting}
            >
              <RefreshCw size={14} />
              {ingesting ? 'Refreshing…' : 'Refresh'}
            </button>

            {user ? (
              <>
                <button
                  className="btn btn-subtle"
                  onClick={() => setSettingsOpen(true)}
                >
                  <SettingsIcon size={16} />
                  Settings
                </button>

                <button
                  className="btn btn-subtle"
                  onClick={handleLogout}
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </>
            ) : (
              <button
                className="btn btn-subtle"
                onClick={() => setAuthOpen(true)}
              >
                <LogIn size={16} />
                Sign in
              </button>
            )}
          </nav>
        </div>
      </header>

      {settingsOpen && (
        <>
          <div
            className="overlay"
            onClick={() => setSettingsOpen(false)}
          />

          <div className="panel">
            <Settings
              onClose={() => setSettingsOpen(false)}
              onSave={() => {}}
            />
          </div>
        </>
      )}

      {authOpen && (
        <AuthPage
          onClose={() => setAuthOpen(false)}
          onAuthenticated={setUser}
        />
      )}
    </>
  );
};

export default Header;
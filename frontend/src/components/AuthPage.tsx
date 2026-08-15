import { useState } from 'react';
import {
  getCurrentUser,
  loginUser,
  registerUser,
} from '../api';
import { useTimeOfDay } from '../hooks/useTimeOfDay';
import styles from '../styles/AuthPage.module.css';
import BrandTitle from './BrandTitle';

interface Props {
  onClose: () => void;
  onAuthenticated: (user: { id: number; email: string }) => void;
}

const AuthPage: React.FC<Props> = ({
  onClose,
  onAuthenticated,
}) => {
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);

  const timePeriod = useTimeOfDay();

  const handleAuthSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    setAuthLoading(true);
    setAuthMessage(null);

    try {
      if (authMode === 'register') {
        await registerUser(email, password);
      } else {
        await loginUser(email, password);
      }

      const currentUser = await getCurrentUser();

      if (!currentUser) {
        throw new Error('Could not verify your session.');
      }

      onAuthenticated(currentUser);
      onClose();
    } catch (error) {
      setAuthMessage(
        error instanceof Error
          ? error.message
          : 'Authentication failed'
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const toggleAuthMode = () => {
    setAuthMode((current) =>
      current === 'login' ? 'register' : 'login'
    );

    setEmail('');
    setPassword('');
    setAuthMessage(null);
  };

  return (
    <>
      {/* Clicking anywhere outside the modal closes it */}
      <div
        className="overlay"
        onClick={onClose}
      />

      <div
        className={`glass-shell ${styles.authModal}`}
        onClick={(event) => event.stopPropagation()}>
        <div
          className={styles.authBrand}
          data-time={timePeriod}
        >
          <BrandTitle
            as="h1"
            className={styles.authBrandTitle}
          />

          <p className={styles.tagline}>
            Stories grouped by relevance, for you
          </p>
        </div>

        <div className={`glass-body ${styles.bodyInner}`}>
          <div className={styles.intro}>
            <h2>
              {authMode === 'login'
                ? 'Welcome back'
                : 'Create your account'}
            </h2>

            <p>
              Save topics, trusted publishers, and location preferences.
            </p>
          </div>

          <form
            className={styles.form}
            onSubmit={handleAuthSubmit}
          >
            <label>
              Email

              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </label>

            <label>
              Password

              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                autoComplete={
                  authMode === 'login'
                    ? 'current-password'
                    : 'new-password'
                }
                required
              />
            </label>

            {authMessage && (
              <p className={styles.message}>
                {authMessage}
              </p>
            )}

            <div className={styles.actions}>
              <button
                className="btn btn-primary"
                type="submit"
                disabled={authLoading}
              >
                {authLoading
                  ? 'Working…'
                  : authMode === 'login'
                    ? 'Sign in'
                    : 'Create account'}
              </button>

              <button
                className="btn btn-secondary"
                type="button"
                onClick={toggleAuthMode}
                disabled={authLoading}
              >
                {authMode === 'login'
                  ? 'Need an account?'
                  : 'Already have one?'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};

export default AuthPage;
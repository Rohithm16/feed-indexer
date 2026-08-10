import React, { useState } from 'react';
import { RefreshCw, Settings as SettingsIcon } from 'lucide-react';
import Settings from './Settings';

interface Props {
  onIngest: () => void;
  ingesting: boolean;
}

const Header: React.FC<Props> = ({ onIngest, ingesting }) => {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <>
      <header className="header">
        <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>Feed Indexer</span>
        <div className="header__spacer" />
        <nav className="header__nav">
          <button
            className="header__nav-link active"
            onClick={() => window.location.href = '/'}
          >
            Feed
          </button>
          <button
            className="header__nav-link"
            onClick={() => setSettingsOpen(true)}
          >
            <SettingsIcon size={16} style={{ marginRight: 4 }} />
            Settings
          </button>
          <button
            className="header__ingest-btn"
            onClick={onIngest}
            disabled={ingesting}
          >
            <RefreshCw size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            {ingesting ? 'Fetching…' : 'Fetch Now'}
          </button>
        </nav>
      </header>

      {settingsOpen && (
        <>
          <div className="settings-overlay" onClick={() => setSettingsOpen(false)} />
          <div className="settings-content">
            <Settings onClose={() => setSettingsOpen(false)} onSave={() => {}} />
          </div>
        </>
      )}
    </>
  );
};

export default Header;
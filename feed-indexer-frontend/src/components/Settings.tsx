import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { getPreferences, updatePreferences } from '../api';
import { DEFAULT_PREFS, type UserPreferences } from '../types';

const ALL_TOPICS = [
  'world', 'national', 'technology', 'business',
  'science', 'health', 'politics', 'finance'
];

const AVAILABLE_PUBLISHERS = [
  'AP News', 'BBC', 'Reuters', 'CNN', 'NYT', 'WP', 'FT', 'WSJ', 'Al Jazeera', 'The Guardian'
];

interface Props {
  onClose: () => void;
  onSave: () => void;
}

const Settings: React.FC<Props> = ({ onClose, onSave }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [prefs, setPrefs] = useState<UserPreferences>(DEFAULT_PREFS);

  useEffect(() => {
    async function load() {
      try {
        const data = await getPreferences();
        setPrefs({
          preferred_topics: data.preferred_topics || [],
          trusted_publishers: data.trusted_publishers || [],
          country: data.country || 'us',
          state: data.state || '',
          city: data.city || '',
        });
      } catch {
        setToast('Failed to load preferences.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const toggleTopic = (topic: string) => {
    setPrefs((prev) => ({
      ...prev,
      preferred_topics: prev.preferred_topics.includes(topic)
        ? prev.preferred_topics.filter((t) => t !== topic)
        : [...prev.preferred_topics, topic],
    }));
  };

  const togglePublisher = (pub: string) => {
    setPrefs((prev) => ({
      ...prev,
      trusted_publishers: prev.trusted_publishers.includes(pub)
        ? prev.trusted_publishers.filter((p) => p !== pub)
        : [...prev.trusted_publishers, pub],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updatePreferences(prefs);
      setToast('Preferences saved!');
      onSave();
      setTimeout(() => setToast(null), 3000);
    } catch {
      setToast('Failed to save preferences.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-6)', textAlign: 'center' }}>Loading preferences…</div>;
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Settings</h2>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-text-secondary)',
          }}
          aria-label="Close settings"
        >
          <X size={20} />
        </button>
      </div>

      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)' }}>
        Critical events always appear at the top regardless of your preferences.
      </p>

      <div className="settings-group">
        <label>Preferred Topics</label>
        <div className="hint">Events in these categories will be boosted.</div>
        <div className="pill-group">
          {ALL_TOPICS.map((topic) => (
            <span
              key={topic}
              className={`pill ${prefs.preferred_topics.includes(topic) ? 'selected' : ''}`}
              onClick={() => toggleTopic(topic)}
            >
              {topic.charAt(0).toUpperCase() + topic.slice(1)}
            </span>
          ))}
        </div>
      </div>

      <div className="settings-group">
        <label>Trusted Publishers</label>
        <div className="hint">Events covered by these will be prioritized.</div>
        <div className="pill-group">
          {AVAILABLE_PUBLISHERS.map((pub) => (
            <span
              key={pub}
              className={`pill ${prefs.trusted_publishers.includes(pub) ? 'selected' : ''}`}
              onClick={() => togglePublisher(pub)}
            >
              {pub}
            </span>
          ))}
        </div>
      </div>

      <div className="settings-group">
        <label>Location</label>
        <div className="hint">Used to surface local and national news.</div>
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Country code (e.g. us, in)"
            value={prefs.country}
            onChange={(e) => setPrefs({ ...prefs, country: e.target.value })}
            style={{ flex: 1, minWidth: 120 }}
          />
          <input
            type="text"
            placeholder="State (optional)"
            value={prefs.state}
            onChange={(e) => setPrefs({ ...prefs, state: e.target.value })}
            style={{ flex: 1, minWidth: 120 }}
          />
          <input
            type="text"
            placeholder="City (optional)"
            value={prefs.city}
            onChange={(e) => setPrefs({ ...prefs, city: e.target.value })}
            style={{ flex: 1, minWidth: 120 }}
          />
        </div>
      </div>

      <div className="settings-actions">
        <button className="btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving…' : 'Save Preferences'}
        </button>
        <button className="btn-secondary" onClick={onClose}>
          Cancel
        </button>
      </div>

      {toast && (
        <div className="toast show">
          {toast}
        </div>
      )}
    </>
  );
};

export default Settings;
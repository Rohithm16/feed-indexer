import { useState, useEffect } from 'react';
import type { UserPreferences } from '../types';
import { getPreferences, updatePreferences } from '../api';
import { DEFAULT_PREFS } from '../types';
import styles from '../styles/Settings.module.css';
import { useTimeOfDay } from '../hooks/useTimeOfDay';

interface Props {
  onClose: () => void;
  onSave?: () => void;
}

const SETTINGS_SECTIONS: Array<{ key: string; label: string }> = [
  { key: 'general', label: 'General' },
  { key: 'technology', label: 'Technology' },
  { key: 'business', label: 'Business' },
  { key: 'science', label: 'Science' },
  { key: 'health', label: 'Health' },
  { key: 'entertainment', label: 'Entertainment' },
  { key: 'sports', label: 'Sports' },
];

const Settings = ({ onClose, onSave }: Props) => {
  const [prefs, setPrefs] = useState<UserPreferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getPreferences()
      .then(setPrefs)
      .catch(() => setPrefs(DEFAULT_PREFS))
      .finally(() => setLoading(false));
  }, []);

  const toggleTopic = (topic: string) => {
    setPrefs((prev) => ({
      ...prev,
      preferred_topics: prev.preferred_topics.includes(topic)
        ? prev.preferred_topics.filter((t) => t !== topic)
        : [...prev.preferred_topics, topic],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updatePreferences(prefs);
      onSave?.();
      onClose();
    } catch {
      // Silently fail — user can retry
    } finally {
      setSaving(false);
    }
  };
  const timePeriod = useTimeOfDay();
  return (
    <div className={styles.body}>
      {loading ? (
        <p>Loading preferences…</p>
      ) : (
        <>
          <h2 className={styles.title} data-time={timePeriod}>
            Settings
          </h2>

          <div className={styles.group}>
            <label htmlFor="country">Country</label>
            <p className={styles.hint}>Filter stories relevant to your region.</p>
            <input
              id="country"
              type="text"
              value={prefs.country}
              onChange={(e) => setPrefs((prev) => ({ ...prev, country: e.target.value }))}
              placeholder="e.g. us"
            />
          </div>

          <div className={styles.group}>
            <label htmlFor="city">City</label>
            <p className={styles.hint}>Local news near you.</p>
            <input
              id="city"
              type="text"
              value={prefs.city}
              onChange={(e) => setPrefs((prev) => ({ ...prev, city: e.target.value }))}
              placeholder="e.g. New York"
            />
          </div>

          <div className={styles.group}>
            <label>Preferred topics</label>
            <p className={styles.hint}>Select topics you care about most.</p>
            <div className={styles.pillGroup}>
              {SETTINGS_SECTIONS.map((topic) => (
                <button
                  key={topic.key}
                  className={`${styles.pill} ${prefs.preferred_topics.includes(topic.key) ? styles.pillSelected : ''}`}
                  onClick={() => toggleTopic(topic.key)}
                >
                  {topic.label}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.actions}>
            <button className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save preferences'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default Settings;
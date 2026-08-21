import { useState, useEffect } from 'react';
import type { CountryCode, UserPreferences } from '../types';
import { getPreferences, updatePreferences } from '../api';
import { DEFAULT_PREFS, SUPPORTED_COUNTRIES, COUNTRY_INFO } from '../types';
import styles from '../styles/Settings.module.css';
import { useTimeOfDay } from '../hooks/useTimeOfDay';

interface Props {
  onClose: () => void;
  onSave?: () => void;
}

// "Health" removed (folds into World now), Technology + Science merged,
// Business renamed to Business & Finance -- matches the backend's
// current section names exactly (these keys are matched literally
// against the section names on the backend for real filtering, not just
// a ranking nudge -- unselected sections are hidden from the feed
// entirely, so don't add a key here that isn't a real backend section).
const SETTINGS_SECTIONS: Array<{ key: string; label: string }> = [
  { key: 'national', label: 'National' },
  { key: 'world', label: 'World' },
  { key: 'tech_science', label: 'Tech & Science' },
  { key: 'business_finance', label: 'Business & Finance' },
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

  const toggleCountry = (code: CountryCode) => {
    setPrefs((prev) => {
      const has = prev.countries.includes(code);
      const next = has ? prev.countries.filter((c) => c !== code) : [...prev.countries, code];
      // At least one country must stay selected -- falling back to the
      // default rather than letting the user save an empty selection.
      return { ...prev, countries: next.length > 0 ? next : DEFAULT_PREFS.countries };
    });
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
            <label>Country</label>
            <p className={styles.hint}>Choose one or both. Their stories appear under National.</p>
            <div className={styles.pillGroup}>
              {SUPPORTED_COUNTRIES.map((code) => (
                <button
                  key={code}
                  className={`${styles.pill} ${prefs.countries.includes(code) ? styles.pillSelected : ''}`}
                  onClick={() => toggleCountry(code)}
                >
                  <span style={{ marginRight: '6px' }}>{COUNTRY_INFO[code].flag}</span>
                  {COUNTRY_INFO[code].name}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.group}>
            <label>Preferred topics</label>
            <p className={styles.hint}>Only selected topics appear in your feed. Leave all unselected to see everything.</p>
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
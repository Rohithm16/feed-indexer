import { useState, useEffect, useCallback } from 'react';
import { getFeed } from './api';
import type { FeedData, Event } from './types';
import Header from './components/Header';
import Section from './components/Section';
import EventDetailModal from './components/EventDetailModal';
import styles from './styles/App.module.css';
import { useTimeOfDay } from './hooks/useTimeOfDay';
import { getTimePeriodLabel } from './utils/timeOfDay';

const SECTIONS: Array<{ key: keyof FeedData; label: string }> = [
  { key: 'critical', label: 'Breaking & Critical' },
  { key: 'local', label: 'Local' },
  { key: 'national', label: 'National' },
  { key: 'world', label: 'World' },
  { key: 'technology', label: 'Technology' },
  { key: 'business', label: 'Business' },
  { key: 'science', label: 'Science' },
];

function App() {
  const [feed, setFeed] = useState<FeedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const timePeriod = useTimeOfDay();

  const loadFeed = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFeed();
      setFeed(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadFeed();
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadFeed]);

  const handleIngest = async () => {
    await loadFeed();
  };

  const openEvent = (event: Event) => setSelectedEvent(event);
  const closeEvent = () => setSelectedEvent(null);

  return (
    <div className={styles.shell}>
      <Header onIngest={handleIngest} ingesting={loading} />
      <main className={styles.page}>
        <section className={styles.hero} data-time={timePeriod}>
          <div className={styles.content}>
            <p className={styles.title}>Updated x minutes ago. </p>
            <h1 className={styles.headline}>{getTimePeriodLabel(timePeriod)}</h1>
            <p className={styles.description}>
              Stories grouped by importance, location, and topic. 
            </p>
          </div>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <div className={styles.count}>{feed ? Object.values(feed).flat().length : 0}</div>
              <div className={styles.label}>events tracked</div>
            </div>
            <div className={styles.stat}>
              <div className={styles.count}>{feed ? feed.critical.length : 0}</div>
              <div className={styles.label}>critical stories</div>
            </div>
          </div>
        </section>

        {loading && <p className={styles.status}>Loading feed…</p>}
        {error && <p className={`${styles.status} ${styles.error}`}>Error: {error}</p>}
        {!loading && !error && !feed && (
          <div className={styles.empty}>
            <p>No events yet.</p>
            <p style={{ marginTop: 'var(--space-2)' }}>Refresh to pull the latest stories.</p>
          </div>
        )}
        {!loading && !error && feed && SECTIONS.map(({ key, label }) => (
          <Section key={key} title={label} events={feed[key]} onEventClick={openEvent} />
        ))}
      </main>
      <EventDetailModal event={selectedEvent} open={!!selectedEvent} onClose={closeEvent} />
    </div>
  );
}

export default App;
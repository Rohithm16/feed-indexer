import { useState, useEffect, useCallback } from 'react';
import { getFeed } from './api';
import type { FeedData, Event, CountryCode } from './types';
import { COUNTRY_INFO } from './types';
import Header from './components/Header';
import Section from './components/Section';
import EventDetailModal from './components/EventDetailModal';
import styles from './styles/App.module.css';
import { useTimeOfDay } from './hooks/useTimeOfDay';
import { getTimePeriodLabel } from './utils/timeOfDay';

// National is rendered separately below (grouped by country); these are
// the remaining flat sections, in display order.
const SECTIONS: Array<{ key: 'critical' | 'world' | 'tech_science' | 'business_finance'; label: string }> = [
  { key: 'critical', label: 'Breaking & Critical' },
];
const SECTIONS_AFTER_NATIONAL: Array<{ key: 'world' | 'tech_science' | 'business_finance'; label: string }> = [
  { key: 'world', label: 'World' },
  { key: 'tech_science', label: 'Tech & Science' },
  { key: 'business_finance', label: 'Business & Finance' },
];

function countAllEvents(feed: FeedData | null): number {
  if (!feed) return 0;
  const flatSections = feed.critical.length + feed.world.length + feed.tech_science.length + feed.business_finance.length;
  const nationalCount = Object.values(feed.national).reduce((sum, events) => sum + events.length, 0);
  return flatSections + nationalCount;
}

function formatUpdatedLabel(lastFetchedAt: Date | null, now: Date): string {
  if (!lastFetchedAt) return 'Not updated yet.';
  const diffMinutes = Math.max(0, Math.round((now.getTime() - lastFetchedAt.getTime()) / 60000));
  if (diffMinutes < 1) return 'Updated just now.';
  if (diffMinutes === 1) return 'Updated 1 minute ago.';
  if (diffMinutes < 60) return `Updated ${diffMinutes} minutes ago.`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours === 1) return 'Updated 1 hour ago.';
  return `Updated ${diffHours} hours ago.`;
}

function App() {
  const [feed, setFeed] = useState<FeedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [lastFetchedAt, setLastFetchedAt] = useState<Date | null>(null);
  const [now, setNow] = useState<Date>(new Date());
  const timePeriod = useTimeOfDay();

  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(interval);
  }, []);

  const loadFeed = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFeed();
      setFeed(data);
      setLastFetchedAt(new Date());
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
            <p className={styles.title}>{formatUpdatedLabel(lastFetchedAt, now)}</p>
            <h1 className={styles.headline}>{getTimePeriodLabel(timePeriod)}</h1>
            <p className={styles.description}>
              Stories grouped by importance, location, and topic. 
            </p>
          </div>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <div className={styles.count}>{countAllEvents(feed)}</div>
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
        {!loading && !error && feed && (
          <>
            {SECTIONS.map(({ key, label }) => (
              <Section key={key} title={label} events={feed[key]} onEventClick={openEvent} />
            ))}
            {(Object.entries(feed.national) as Array<[CountryCode, Event[]]>).map(([code, events]) => (
              <Section
                key={`national-${code}`}
                title={`${COUNTRY_INFO[code]?.flag ?? ''} National — ${COUNTRY_INFO[code]?.name ?? code}`}
                events={events}
                onEventClick={openEvent}
              />
            ))}
            {SECTIONS_AFTER_NATIONAL.map(({ key, label }) => (
              <Section key={key} title={label} events={feed[key]} onEventClick={openEvent} />
            ))}
          </>
        )}
      </main>
      <EventDetailModal event={selectedEvent} open={!!selectedEvent} onClose={closeEvent} />
    </div>
  );
}

export default App;
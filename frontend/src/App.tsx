import { useState, useEffect, useCallback } from 'react';
import { getFeed } from './api';
import type { FeedData, Event } from './types';
import Header from './components/Header';
import Section from './components/Section';
import EventDetailModal from './components/EventDetailModal';
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
    void loadFeed();
  }, [loadFeed]);

  const handleIngest = async () => {
    await loadFeed();
  };

  const openEvent = (event: Event) => setSelectedEvent(event);
  const closeEvent = () => setSelectedEvent(null);

  return (
    <div className="app-shell">
      <Header onIngest={handleIngest} ingesting={loading} />
      <main className="page-wrapper">
        <section className="hero-panel" data-time={timePeriod}>
          <div className="hero-panel__content">
            <p className="hero-panel__title">{getTimePeriodLabel(timePeriod)} · Today’s overview</p>
            <h1 className="hero-panel__headline">Stories grouped by importance, location, and topic.</h1>
            <p className="hero-panel__description">
              Breaking events stay prominent while local and sector sections keep the surrounding context visible.
            </p>
          </div>
          <div className="hero-panel__stats">
            <div className="hero-panel__stat">
              <div className="hero-panel__count">{feed ? Object.values(feed).flat().length : 0}</div>
              <div className="hero-panel__stat-label">events tracked</div>
            </div>
            <div className="hero-panel__stat">
              <div className="hero-panel__count">{feed ? feed.critical.length : 0}</div>
              <div className="hero-panel__stat-label">critical stories</div>
            </div>
          </div>
        </section>

        {loading && <p className="status-text">Loading feed…</p>}
        {error && <p className="status-text status-text--error">Error: {error}</p>}
        {!loading && !error && !feed && (
          <div className="empty-state">
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
import React, { useState, useEffect, useCallback } from 'react';
import { getFeed, triggerIngest } from './api';
import type { FeedData, Event } from './types';
import Header from './components/Header';
import Section from './components/Section';
import EventDetailModal from './components/EventDetailModal';

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
  const [ingesting, setIngesting] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

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
    loadFeed();
  }, [loadFeed]);

  const handleIngest = async () => {
    setIngesting(true);
    try {
      await triggerIngest();
      await loadFeed();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingest failed');
    } finally {
      setIngesting(false);
    }
  };

  const openEvent = (event: Event) => setSelectedEvent(event);
  const closeEvent = () => setSelectedEvent(null);

  if (loading) {
    return (
      <div className="page-wrapper">
        <Header onIngest={handleIngest} ingesting={ingesting} />
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading feed…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-wrapper">
        <Header onIngest={handleIngest} ingesting={ingesting} />
        <p style={{ color: 'var(--color-critical)' }}>Error: {error}</p>
      </div>
    );
  }

  if (!feed) {
    return (
      <div className="page-wrapper">
        <Header onIngest={handleIngest} ingesting={ingesting} />
        <div className="empty-state">
          <p>No events yet.</p>
          <p style={{ marginTop: 'var(--space-2)' }}>
            Click “Fetch Now” to pull the latest news.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <Header onIngest={handleIngest} ingesting={ingesting} />
      {SECTIONS.map(({ key, label }) => (
        <Section key={key} title={label} events={feed[key]} onEventClick={openEvent} />
      ))}
      <EventDetailModal event={selectedEvent} open={!!selectedEvent} onClose={closeEvent} />
    </div>
  );
}

export default App;
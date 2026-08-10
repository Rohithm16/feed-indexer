import React, { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { getEventDetail } from '../api';
import type { Event, EventDetailData } from '../types';

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

interface Props {
  event: Event | null;
  open: boolean;
  onClose: () => void;
}

const EventDetailModal: React.FC<Props> = ({ event, open, onClose }) => {
  const [detail, setDetail] = useState<EventDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !event) {
      setDetail(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getEventDetail(event.id)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        if (!cancelled) setError('Unable to load the full source list right now.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [event?.id, open]);

  if (!event) return null;

  const activeEvent = (detail ?? { ...event, articles: [] }) as EventDetailData;
  const articles = activeEvent.articles ?? [];

  return (
    <Dialog.Root open={open} onOpenChange={() => onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="settings-overlay" />
        <Dialog.Content className="settings-content" style={{ maxWidth: 700 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{activeEvent.title}</h2>
            <Dialog.Close asChild>
              <button
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--color-text-secondary)',
                  padding: '4px',
                }}
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </Dialog.Close>
          </div>

          <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            <span>{activeEvent.category || 'General'}</span>
            <span style={{ margin: '0 0.5rem' }}>·</span>
            <span>Importance: {Math.round(activeEvent.importance_score ?? 0)}</span>
            <span style={{ margin: '0 0.5rem' }}>·</span>
            <span>{timeAgo(activeEvent.last_updated_at)}</span>
            {activeEvent.is_critical && (
              <>
                <span style={{ margin: '0 0.5rem' }}>·</span>
                <span style={{ color: 'var(--color-critical)', fontWeight: 600 }}>⚠ Breaking</span>
              </>
            )}
          </div>

          {activeEvent.summary && (
            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Summary</h4>
              <p style={{ lineHeight: 1.7 }}>{activeEvent.summary}</p>
            </div>
          )}

          {activeEvent.why_it_matters && (
            <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--color-surface-2)', borderRadius: 'var(--radius-sm)' }}>
              <h4 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Why it matters</h4>
              <p style={{ lineHeight: 1.7 }}>{activeEvent.why_it_matters}</p>
            </div>
          )}

          <div style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
            <p>
              <strong>Sources:</strong> {activeEvent.source_count ?? 0}
              {activeEvent.primary_source_name && ` (via ${activeEvent.primary_source_name})`}
            </p>
            {loading && <p style={{ marginTop: '0.5rem' }}>Loading linked sources…</p>}
            {error && <p style={{ marginTop: '0.5rem', color: 'var(--color-critical)' }}>{error}</p>}
            {!loading && !error && articles.length > 0 && (
              <ul className="source-list" style={{ marginTop: '0.75rem' }}>
                {articles.map((article) => (
                  <li key={article.id}>
                    <a href={article.url} target="_blank" rel="noopener noreferrer">
                      {article.title || article.source_name}
                    </a>
                    <span> — {article.source_name}</span>
                  </li>
                ))}
              </ul>
            )}
            {!loading && !error && articles.length === 0 && (
              <p style={{ marginTop: '0.5rem' }}>No linked sources available yet.</p>
            )}
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
            <Dialog.Close asChild>
              <button className="btn-secondary" style={{ padding: '0.5rem 1.5rem' }}>
                Close
              </button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default EventDetailModal;
import React, { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ExternalLink, X } from 'lucide-react';
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

function badgeClass(score: number): string {
  if (score >= 65) return 'badge--high';
  if (score >= 35) return 'badge--mid';
  return 'badge--low';
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
  const score = Math.round(activeEvent.importance_score ?? 0);

  return (
    <Dialog.Root open={open} onOpenChange={() => onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="settings-overlay" />
        <Dialog.Content className="event-modal">
          <div className="event-modal__header">
            <div className="event-modal__meta">
              {activeEvent.is_critical && (
                <span className="badge badge--critical">Breaking</span>
              )}
              <span className="event-modal__chip">{activeEvent.category || 'General'}</span>
              <span className={`badge ${badgeClass(score)}`}>{score}</span>
              <span className="event-modal__chip">{timeAgo(activeEvent.last_updated_at)}</span>
            </div>
            <div className="event-modal__title-row">
              <Dialog.Title className="event-modal__title">{activeEvent.title}</Dialog.Title>
              <Dialog.Close asChild>
                <button className="btn btn-icon" aria-label="Close">
                  <X size={20} />
                </button>
              </Dialog.Close>
            </div>
          </div>

          <div className="event-modal__body">
            {activeEvent.summary && (
              <section className="event-modal__section">
                <h3 className="event-modal__section-title">Summary</h3>
                <p className="event-modal__text">{activeEvent.summary}</p>
              </section>
            )}

            {activeEvent.why_it_matters && (
              <section className="event-modal__section event-modal__section--highlight">
                <h3 className="event-modal__section-title">Why it matters</h3>
                <p className="event-modal__text">{activeEvent.why_it_matters}</p>
              </section>
            )}

            <section className="event-modal__section">
              <h3 className="event-modal__section-title">
                Sources
                <span className="event-modal__section-count">{activeEvent.source_count ?? 0}</span>
              </h3>
              {activeEvent.primary_source_name && (
                <p className="event-modal__source-lead">
                  Primary coverage via <strong>{activeEvent.primary_source_name}</strong>
                </p>
              )}
              {loading && <p className="event-modal__status">Loading linked sources…</p>}
              {error && <p className="event-modal__status event-modal__status--error">{error}</p>}
              {!loading && !error && articles.length > 0 && (
                <ul className="source-list source-list--modal">
                  {articles.map((article) => (
                    <li key={article.id}>
                      <a href={article.url} target="_blank" rel="noopener noreferrer">
                        <span>{article.title || article.source_name}</span>
                        <ExternalLink size={14} />
                      </a>
                      <span className="source-list__publisher">{article.source_name}</span>
                    </li>
                  ))}
                </ul>
              )}
              {!loading && !error && articles.length === 0 && (
                <p className="event-modal__status">No linked sources available yet.</p>
              )}
            </section>
          </div>

          <div className="event-modal__footer">
            <Dialog.Close asChild>
              <button className="btn btn-secondary">Close</button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default EventDetailModal;

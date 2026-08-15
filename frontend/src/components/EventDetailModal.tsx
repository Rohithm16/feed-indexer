import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import styles from '../styles/EventModal.module.css';
import { ExternalLink } from 'lucide-react';
import { getEventDetail } from '../api';
import type { Event, EventDetailData } from '../types';
import { useTimeOfDay } from '../hooks/useTimeOfDay';

interface Props {
  event: Event | null;
  open: boolean;
  onClose: () => void;
}

const EventDetailModal: React.FC<Props> = ({ event, open, onClose }) => {
  const [detail, setDetail] = useState<EventDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timePeriod = useTimeOfDay();
  useEffect(() => {
    let cancelled = false;

    if (!open || !event) {
      const resetTimer = window.setTimeout(() => {
        if (!cancelled) {
          setDetail(null);
          setError(null);
        }
      }, 0);

      return () => {
        cancelled = true;
        window.clearTimeout(resetTimer);
      };
    }

    const loadTimer = window.setTimeout(() => {
      if (cancelled) return;

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
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(loadTimer);
    };
  }, [event, open]);

  if (!event) return null;

  const activeEvent = (detail ?? { ...event, articles: [] }) as EventDetailData;
  const articles = activeEvent.articles ?? [];
  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => !isOpen && onClose()} modal={false}>
      <Dialog.Portal>
        <div className="overlay" onClick={onClose} />
        <div
          className={`glass-shell ${styles.modal}`}
          onClick={(event) => event.stopPropagation()}
        >
          <div className={styles.header} data-time={timePeriod}>
            {/* <div className="event-modal__meta">
              {activeEvent.is_critical && (
                <span className="badge badge--critical">Breaking</span>
              )}
              <span className="event-modal__chip">{activeEvent.category || 'General'}</span>
              <span className={`badge ${badgeClass(score)}`}>{score}</span>
              <span className="event-modal__chip">{timeAgo(activeEvent.last_updated_at)}</span>
            </div> */}
            <div className={styles.titleRow}>
              <Dialog.Title className={styles.title}>{activeEvent.title}</Dialog.Title>
            </div>
          </div>

          <div className={styles.body}>
            {activeEvent.summary && (
              <section>
                <h3 className={styles.sectionTitle}>Summary</h3>
                <p className={styles.text}>{activeEvent.summary}</p>
              </section>
            )}

            {activeEvent.why_it_matters && (
              <section className={styles.highlight}>
                <h3 className={styles.sectionTitle}>Why it matters</h3>
                <p className={styles.text}>{activeEvent.why_it_matters}</p>
              </section>
            )}

            <section>
              <h3 className={styles.sectionTitle}>
                Sources
                <span className={styles.sectionCount}>{activeEvent.source_count ?? 0}</span>
              </h3>
              {activeEvent.primary_source_name && (
                <p className={styles.sourceLead}>
                  Primary coverage via <strong>{activeEvent.primary_source_name}</strong>
                </p>
              )}
              {loading && <p className={styles.status}>Loading linked sources…</p>}
              {error && <p className={`${styles.status} ${styles.error}`}>{error}</p>}
              {!loading && !error && articles.length > 0 && (
                <ul className={styles.sourceList}>
                  {articles.map((article) => (
                    <li key={article.id}>
                      <a href={article.url} target="_blank" rel="noopener noreferrer">
                        <span>{article.title || article.source_name}</span>
                        <ExternalLink size={14} />
                      </a>
                      <span className={styles.publisher}>{article.source_name}</span>
                    </li>
                  ))}
                </ul>
              )}
              {!loading && !error && articles.length === 0 && (
                <p className={styles.status}>No linked sources available yet.</p>
              )}
            </section>
          </div>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default EventDetailModal;

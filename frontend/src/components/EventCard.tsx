import { Clock, FileText, Lightbulb, Newspaper } from 'lucide-react';
import type { Event } from '../types';
import ScoreRing from './ScoreRing';
import { ACCENT_VAR, type SectionAccent } from '../accentColors';
import styles from '../styles/EventCard.module.css';

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

interface Props {
  event: Event;
  onClick: (event: Event, accent: SectionAccent) => void;
  accent: SectionAccent;
}

const EventCard: React.FC<Props> = ({ event, onClick, accent }) => {
  const score = event.importance_score ?? 0;
  const isCritical = event.is_critical;
  const cardAccent: SectionAccent = isCritical ? 'critical' : accent;

  const handleClick = () => {
    onClick(event, cardAccent);
  };

  return (
    <div
      className={`${styles.card} ${isCritical ? styles.critical : ''}`}
      style={{ '--card-accent': ACCENT_VAR[cardAccent] } as React.CSSProperties}
      onClick={handleClick}
    >
      <div className={styles.meta}>
        <ScoreRing score={score} />
        <div className={styles.metaText}>
          {isCritical && <span className="badge badge--critical">⚠ Breaking</span>}
          <span className={styles.timeAgo}>
            <Clock size={12} />
            {timeAgo(event.last_updated_at)}
          </span>
        </div>
      </div>

      <h3 className={styles.title}>{event.title}</h3>

      {event.summary && (
        <div className={styles.block}>
          <span className={styles.blockLabel}>
            <FileText size={12} /> Summary
          </span>
          <p className={styles.summary}>{event.summary}</p>
        </div>
      )}

      {event.why_it_matters && (
        <div className={styles.why}>
          <span className={styles.blockLabel}>
            <Lightbulb size={12} /> Why it matters
          </span>
          <p className={styles.whyText}>{event.why_it_matters}</p>
        </div>
      )}

      <div className={styles.footer}>
        <span className={styles.footerItem}>
          <Newspaper size={13} />
          {event.source_count ?? 0} source{event.source_count !== 1 ? 's' : ''}
          {event.primary_source_name && ` · via ${event.primary_source_name}`}
        </span>
        {event.primary_source_url && (
          <a
            href={event.primary_source_url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.readLink}
            onClick={(e) => e.stopPropagation()}
          >
            Read original ↗
          </a>
        )}
      </div>
    </div>
  );
};

export default EventCard;
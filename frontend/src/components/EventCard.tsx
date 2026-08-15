import type { Event } from '../types';
import styles from '../styles/EventCard.module.css';

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
  event: Event;
  onClick: (event: Event) => void;
}

const EventCard: React.FC<Props> = ({ event, onClick }) => {
  const score = event.importance_score ?? 0;
  const isCritical = event.is_critical;

  const handleClick = () => {
    onClick(event);
  };

  return (
    <div
      className={`${styles.card} ${isCritical ? styles.critical : ''}`}
      onClick={handleClick}
    >
      <div className={styles.meta}>
        {isCritical && <span className="badge badge--critical">⚠ Breaking</span>}
        <span>{event.category || 'General'}</span>
        <span className={`badge ${badgeClass(score)}`}>{Math.round(score)}</span>
        <span>{timeAgo(event.last_updated_at)}</span>
      </div>

      <h3 className={styles.title}>{event.title}</h3>

      {event.summary && (
        <p className={styles.summary}>{event.summary}</p>
      )}

      {event.why_it_matters && (
        <div className={styles.why}>
          <span style={{ fontWeight: 600, fontStyle: 'normal' }}>Why it matters </span>
          {event.why_it_matters}
        </div>
      )}

      <div className={styles.footer}>
        <span>{event.source_count ?? 0} source{event.source_count !== 1 ? 's' : ''}</span>
        {event.primary_source_name && <span>via {event.primary_source_name}</span>}
        {event.primary_source_url && (
          <a
            href={event.primary_source_url}
            target="_blank"
            rel="noopener noreferrer"
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
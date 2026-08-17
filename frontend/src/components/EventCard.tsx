import type { Event } from '../types';
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

function scoreClass(score: number): string {
  if (score >= 65) return styles.ringHigh;
  if (score >= 35) return styles.ringMid;
  return styles.ringLow;
}

interface Props {
  event: Event;
  onClick: (event: Event) => void;
}

// Importance score as a circular progress ring with the number in the
// center, built from two stacked SVG circles: a dim full-circle track,
// and a colored circle whose stroke-dasharray is set to score% of the
// circumference so it reads as a partial ring.
const ScoreRing: React.FC<{ score: number }> = ({ score }) => {
  const clamped = Math.max(0, Math.min(100, score));
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);

  return (
    <div className={`${styles.ring} ${scoreClass(clamped)}`} aria-label={`Importance score ${Math.round(clamped)}`}>
      <svg viewBox="0 0 36 36" width="36" height="36">
        <circle className={styles.ringTrack} cx="18" cy="18" r={radius} fill="none" strokeWidth="3" />
        <circle
          className={styles.ringProgress}
          cx="18"
          cy="18"
          r={radius}
          fill="none"
          strokeWidth="3"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 18 18)"
        />
      </svg>
      <span className={styles.ringNumber}>{Math.round(clamped)}</span>
    </div>
  );
};

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
        <ScoreRing score={score} />
        <span className={styles.timeAgo}>{timeAgo(event.last_updated_at)}</span>
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
import styles from '../styles/ScoreRing.module.css';

function scoreClass(score: number): string {
  if (score >= 65) return styles.ringHigh;
  if (score >= 35) return styles.ringMid;
  return styles.ringLow;
}

interface Props {
  score: number;
  size?: number;
  light?: boolean;
}

// Importance score as a circular progress ring with the number centered,
// built from two stacked SVG circles: a dim full-circle track, and a
// colored circle whose stroke-dasharray is set to score% of the
// circumference so it reads as a partial ring. Shared between EventCard
// and EventDetailModal so the score reads identically in both places.
// `light` swaps track/number colors for use on a dark gradient header.
const ScoreRing: React.FC<Props> = ({ score, size = 44, light = false }) => {
  const clamped = Math.max(0, Math.min(100, score));
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);

  return (
    <div
      className={`${styles.ring} ${scoreClass(clamped)} ${light ? styles.light : ''}`}
      style={{ width: size, height: size }}
      aria-label={`Importance score ${Math.round(clamped)}`}
    >      <svg viewBox="0 0 36 36" width={size} height={size}>
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
      <span className={styles.ringNumber} style={{ fontSize: size <= 36 ? 11 : 13 }}>
        {Math.round(clamped)}
      </span>
    </div>
  );
};

export default ScoreRing;
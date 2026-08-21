import type { Event } from '../types';
import EventCard from './EventCard';
import type { SectionAccent } from '../accentColors';
import styles from '../styles/Section.module.css';

interface Props {
  title: string;
  events: Event[];
  onEventClick: (event: Event, accent: SectionAccent) => void;
  icon?: React.ReactNode;
  accent?: SectionAccent;
}

const Section: React.FC<Props> = ({ title, events, onEventClick, icon, accent = 'world' }) => {
  if (!events || events.length === 0) {
    return null;
  }

  return (
    <section className={styles.section}>
      <div className={`${styles.header} ${styles[accent]}`}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <h2 className={styles.title}>{title}</h2>
        <span className={styles.count}>{events.length}</span>
      </div>
      <div className={styles.grid}>
        {events.map((event) => (
          <EventCard key={event.id} event={event} onClick={onEventClick} accent={accent} />
        ))}
      </div>
    </section>
  );
};

export default Section;
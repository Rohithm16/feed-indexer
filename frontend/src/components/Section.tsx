import type { Event } from '../types';
import EventCard from './EventCard';
import styles from '../styles/Section.module.css';

interface Props {
  title: string;
  events: Event[];
  onEventClick: (event: Event) => void;
}

const Section: React.FC<Props> = ({ title, events, onEventClick }) => {
  if (!events || events.length === 0) {
    return (
      <section className={styles.section}>
        <div className={styles.header}>
          <h2 className={styles.title}>{title}</h2>
          <span className={styles.count}>0</span>
        </div>
        <div className="empty-state">No events in this section yet.</div>
      </section>
    );
  }

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>{title}</h2>
        <span className={styles.count}>{events.length}</span>
      </div>
      <div className={styles.grid}>
        {events.map((event) => (
          <EventCard key={event.id} event={event} onClick={onEventClick} />
        ))}
      </div>
    </section>
  );
};

export default Section;
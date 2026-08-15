import React from 'react';
import type { Event } from '../types';
import EventCard from './EventCard';

interface Props {
  title: string;
  events: Event[];
  onEventClick: (event: Event) => void;
}

const Section: React.FC<Props> = ({ title, events, onEventClick }) => {
  // Sections with no events are hidden entirely rather than showing
  // an empty-state message — the feed should only surface what's there.
  if (!events || events.length === 0) {
    return null;
  }

  return (
    <section className="section">
      <div className="section__header">
        <span className="section__eyebrow" aria-hidden="true" />
        <h2 className="section__title">{title}</h2>
        <span className="section__count">{events.length}</span>
      </div>
      <div className="section__grid">
        {events.map((event) => (
          <EventCard key={event.id} event={event} onClick={onEventClick} />
        ))}
      </div>
    </section>
  );
};

export default Section;
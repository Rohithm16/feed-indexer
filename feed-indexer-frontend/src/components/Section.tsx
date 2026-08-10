import React from 'react';
import type { Event } from '../types';
import EventCard from './EventCard';

interface Props {
  title: string;
  events: Event[];
  onEventClick: (event: Event) => void;
}

const Section: React.FC<Props> = ({ title, events, onEventClick }) => {
  if (!events || events.length === 0) {
    return (
      <section className="section">
        <div className="section__header">
          <h2 className="section__title">{title}</h2>
          <span className="section__count">0</span>
        </div>
        <div className="empty-state">No events in this section yet.</div>
      </section>
    );
  }

  return (
    <section className="section">
      <div className="section__header">
        <h2 className="section__title">{title}</h2>
        <span className="section__count">{events.length}</span>
      </div>
      {events.map((event) => (
        <EventCard key={event.id} event={event} onClick={onEventClick} />
      ))}
    </section>
  );
};

export default Section;
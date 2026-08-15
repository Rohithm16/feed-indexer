import { useEffect, useState } from 'react';
import { getTimePeriod, type TimePeriod } from '../utils/timeOfDay';

export function useTimeOfDay(): TimePeriod {
  const [period, setPeriod] = useState<TimePeriod>(() => getTimePeriod());

  useEffect(() => {
    const tick = () => setPeriod(getTimePeriod());
    tick();
    const id = window.setInterval(tick, 60_000);
    return () => window.clearInterval(id);
  }, []);

  return period;
}

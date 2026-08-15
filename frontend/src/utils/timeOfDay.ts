export type TimePeriod = 'night' | 'sunrise' | 'midday' | 'sunset';

export function getTimePeriod(date = new Date()): TimePeriod {
  const hour = date.getHours();

  if (hour >= 20 || hour < 5) return 'night';
  if (hour >= 5 && hour < 8) return 'sunrise';
  if (hour >= 8 && hour < 16) return 'midday';
  return 'sunset';
}

export function getTimePeriodLabel(period: TimePeriod): string {
  switch (period) {
    case 'night':
      return 'Night watch';
    case 'sunrise':
      return 'Sunrise';
    case 'midday':
      return 'Midday';
    case 'sunset':
      return 'Sunset';
  }
}

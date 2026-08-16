export type TimePeriod = 'night' | 'sunrise' | 'sunset';

export function getTimePeriod(date = new Date()): TimePeriod {  
  const hour = date.getHours();
  if (hour >= 20 || hour < 5) return 'night';
  if (hour >= 5 && hour < 15) return 'sunrise';
  return 'sunset';
}

export function getTimePeriodLabel(period: TimePeriod): string {
  const hour = new Date().getHours();
  switch (period) {
    case 'night':
      if (hour < 12) {
        return 'Good Morning';
      }
      return 'Good Evening';
    case 'sunrise':
      if (hour < 12) {
        return 'Good Morning';
      }
      return 'Good Afternoon';
    case 'sunset':
      if (hour < 17) {
        return 'Good Afternoon';
      }
      return 'Good Evening';
  }
}

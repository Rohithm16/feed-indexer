// Shared accent-color mapping so a card visually matches the section
// it's displayed in, using the same design tokens the app already
// defines in global.css (--color-national, --color-tech, etc.) rather
// than hardcoding hex values in multiple places.
export type SectionAccent = 'critical' | 'national' | 'world' | 'techScience' | 'businessFinance';

export const ACCENT_VAR: Record<SectionAccent, string> = {
  critical: 'var(--color-critical)',
  national: 'var(--color-national)',
  world: 'var(--color-world)',
  techScience: 'var(--color-tech)',
  businessFinance: 'var(--color-business)',
};
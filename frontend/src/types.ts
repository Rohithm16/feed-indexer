export interface Article {
  id: number;
  title: string;
  description: string | null;
  url: string;
  published_at: string | null;
  source_name: string;
  category: string | null;
  country: string | null;
}

export interface Event {
  id: number;
  title: string;
  summary: string | null;
  importance_score: number;
  is_critical: boolean;
  category: string | null;
  country: string | null;
  source_count: number;
  primary_source_name: string | null;
  primary_source_url: string | null;
  why_it_matters: string | null;
  last_updated_at: string;
}

export interface EventDetailData extends Event {
  articles: Article[];
}

export interface FeedData {
  critical: Event[];
  // Grouped by country code ("in" / "us") -- each selected country gets
  // its own capped sub-feed rather than one shared National list.
  national: Record<string, Event[]>;
  world: Event[];
  tech_science: Event[];
  business_finance: Event[];
}

// Only these two are supported for now. Adding a third means adding it
// here, adding a source feed tagged with that country code on the
// backend, and adding it to SUPPORTED_COUNTRIES in app/constants.py.
export const SUPPORTED_COUNTRIES = ['in', 'us'] as const;
export type CountryCode = (typeof SUPPORTED_COUNTRIES)[number];

export const COUNTRY_INFO: Record<CountryCode, { name: string; flag: string }> = {
  in: { name: 'India', flag: '🇮🇳' },
  us: { name: 'United States', flag: '🇺🇸' },
};

export interface UserPreferences {
  preferred_topics: string[];
  trusted_publishers: string[];
  countries: CountryCode[];
}

export const DEFAULT_PREFS: UserPreferences = {
  preferred_topics: [],
  trusted_publishers: [],
  countries: ['in'],
};

export interface ApiError {
  message: string;
}
export interface Event {
  id: number;
  title: string;
  summary: string | null;
  importance_score: number;
  is_critical: boolean;
  category: string | null;
  source_count: number;
  primary_source_name: string | null;
  primary_source_url: string | null;
  why_it_matters: string | null;
  last_updated_at: string;
}

export interface FeedData {
  critical: Event[];
  local: Event[];
  national: Event[];
  world: Event[];
  technology: Event[];
  business: Event[];
  science: Event[];
}

export interface UserPreferences {
  preferred_topics: string[];
  trusted_publishers: string[];
  country: string;
  state: string;
  city: string;
  show_minor_news: boolean;
}

export const DEFAULT_PREFS: UserPreferences = {
  preferred_topics: [],
  trusted_publishers: [],
  country: 'us',
  state: '',
  city: '',
  show_minor_news: false,
};

export interface ApiError {
  message: string;
}
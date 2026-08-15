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
  city: string;
}

export const DEFAULT_PREFS: UserPreferences = {
  preferred_topics: [],
  trusted_publishers: [],
  country: 'us',
  city: '',
};

export interface ApiError {
  message: string;
}
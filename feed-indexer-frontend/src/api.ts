import type { FeedData, UserPreferences } from './types.ts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export function getFeed(country?: string): Promise<FeedData> {
  const url = country ? `/api/events/?country=${country}` : '/api/events/';
  return request<FeedData>(url);
}

export function triggerIngest(): Promise<void> {
  return request<void>('/api/ingest', { method: 'POST' });
}

export function getPreferences(): Promise<UserPreferences> {
  return request<UserPreferences>('/api/preferences/');
}

export function updatePreferences(prefs: UserPreferences): Promise<UserPreferences> {
  return request<UserPreferences>('/api/preferences/', {
    method: 'PUT',
    body: JSON.stringify(prefs),
  });
}
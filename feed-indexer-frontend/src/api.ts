import type { EventDetailData, FeedData, UserPreferences } from './types.ts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export function getFeed(): Promise<FeedData> {
  return request<FeedData>('/api/events/');
}

export function getEventDetail(eventId: number): Promise<EventDetailData> {
  return request<EventDetailData>(`/api/events/${eventId}`);
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

export function registerUser(email: string, password: string): Promise<{ id: number; email: string }> {
  return request<{ id: number; email: string }>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function loginUser(email: string, password: string): Promise<{ id: number; email: string }> {
  return request<{ id: number; email: string }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function logoutUser(): Promise<void> {
  return request<void>('/api/auth/logout', { method: 'POST' });
}

export function getCurrentUser(): Promise<{ id: number; email: string } | null> {
  return request<{ id: number; email: string }>('/api/auth/me').catch(() => null);
}
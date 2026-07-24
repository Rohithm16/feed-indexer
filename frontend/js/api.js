/**
 * api.js — thin wrapper around fetch() for all backend calls.
 *
 * All functions return a parsed JSON object, or throw on error.
 * The BASE_URL is the only thing you need to change if you deploy elsewhere.
 */

const BASE_URL = "https://feed-indexer.onrender.com";

/**
 * Generic fetch wrapper. Throws an Error with a readable message on failure.
 */
async function apiFetch(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }

  return response.json();
}

/** Returns the full sectioned feed for the homepage. */
export async function getFeed() {
  return apiFetch("/api/events/");
}

/** Returns full event detail including all articles. */
export async function getEvent(id) {
  return apiFetch(`/api/events/${id}`);
}

/** Trigger a manual ingestion run. */
export async function triggerIngest() {
  return apiFetch("/api/ingest", { method: "POST" });
}

/** List all registered providers and their feeds. */
export async function getProviders() {
  return apiFetch("/api/feeds/");
}

/** Get the current user preferences. */
export async function getPreferences() {
  return apiFetch("/api/preferences/");
}

/** Update user preferences. Pass the full preferences object. */
export async function updatePreferences(prefs) {
  return apiFetch("/api/preferences/", {
    method: "PUT",
    body: JSON.stringify(prefs),
  });
}

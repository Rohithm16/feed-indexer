/**
 * settings.js — user preferences UI.
 *
 * Loads current preferences from the API, renders pill selectors
 * for topics and publishers, and saves changes back via PUT.
 */

import { getPreferences, updatePreferences, getProviders } from "./api.js";

// Available topics (shown as pills)
const ALL_TOPICS = [
  "world", "national", "technology", "business",
  "science", "health", "politics", "finance",
];

// ── State ────────────────────────────────────────────────────────────────────
let selectedTopics = new Set();
let selectedPublishers = new Set();

// ── Toast ────────────────────────────────────────────────────────────────────
function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast toast--${type} show`;
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// ── Topic Pills ──────────────────────────────────────────────────────────────

function renderTopics() {
  const container = document.getElementById("topic-pills");
  container.innerHTML = ALL_TOPICS.map(topic => `
    <button
      class="pill${selectedTopics.has(topic) ? " selected" : ""}"
      data-topic="${topic}"
      type="button"
    >
      ${topic.charAt(0).toUpperCase() + topic.slice(1)}
    </button>
  `).join("");

  container.querySelectorAll(".pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const topic = pill.dataset.topic;
      if (selectedTopics.has(topic)) {
        selectedTopics.delete(topic);
        pill.classList.remove("selected");
      } else {
        selectedTopics.add(topic);
        pill.classList.add("selected");
      }
    });
  });
}

// ── Publisher Pills ──────────────────────────────────────────────────────────

function renderPublishers(providers) {
  const container = document.getElementById("publisher-pills");
  container.innerHTML = providers.map(p => `
    <button
      class="pill${selectedPublishers.has(p.name) ? " selected" : ""}"
      data-publisher="${p.name}"
      type="button"
    >
      ${p.name}
    </button>
  `).join("");

  container.querySelectorAll(".pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const name = pill.dataset.publisher;
      if (selectedPublishers.has(name)) {
        selectedPublishers.delete(name);
        pill.classList.remove("selected");
      } else {
        selectedPublishers.add(name);
        pill.classList.add("selected");
      }
    });
  });
}

// ── Save ─────────────────────────────────────────────────────────────────────

async function savePreferences() {
  const country = document.getElementById("input-country").value.trim() || "us";
  const state = document.getElementById("input-state").value.trim() || null;
  const city = document.getElementById("input-city").value.trim() || null;

  const payload = {
    preferred_topics: [...selectedTopics],
    trusted_publishers: [...selectedPublishers],
    country,
    state,
    city,
  };

  try {
    await updatePreferences(payload);
    showToast("Preferences saved!", "success");
  } catch (err) {
    showToast("Failed to save. Is the backend running?", "error");
    console.error(err);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  try {
    // Load current prefs and available providers in parallel
    const [prefs, providers] = await Promise.all([getPreferences(), getProviders()]);

    // Populate state from saved prefs
    selectedTopics = new Set(prefs.preferred_topics || []);
    selectedPublishers = new Set(prefs.trusted_publishers || []);

    document.getElementById("input-country").value = prefs.country || "us";
    document.getElementById("input-state").value = prefs.state || "";
    document.getElementById("input-city").value = prefs.city || "";

    renderTopics();
    renderPublishers(providers);

  } catch (err) {
    showToast("Could not load preferences. Is the backend running?", "error");
    // Still render topics even if backend is down
    renderTopics();
    renderPublishers([]);
  }

  document.getElementById("btn-save").addEventListener("click", savePreferences);
}

main();

/**
 * home.js — homepage rendering.
 * 
 * Fetches the sectioned feed and renders event cards per section.
 * Handles loading states and empty sections gracefully.
 */

import { getFeed, triggerIngest } from "./api.js";

// ── Helpers ─────────────────────────────────────────────────────────────────

/** Format a date string into a human-readable relative time. */
function timeAgo(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1)  return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

/** Map an importance score (0-100) to a CSS modifier class. */
function importanceBadgeClass(score) {
  if (score >= 65) return "importance-badge--high";
  if (score >= 35) return "importance-badge--mid";
  return "importance-badge--low";
}

/** Map a score to a short label. */
function importanceLabel(score) {
  if (score >= 85) return "Critical";
  if (score >= 65) return "Major";
  if (score >= 45) return "Notable";
  if (score >= 25) return "Moderate";
  return "Minor";
}

/** Map category name to a CSS modifier. */
function categoryClass(category) {
  const map = {
    world: "world", technology: "technology", business: "business",
    science: "science", national: "national", local: "local",
    health: "health", politics: "politics", finance: "business",
  };
  return map[category?.toLowerCase()] || "world";
}

// ── Card builder ─────────────────────────────────────────────────────────────

/**
 * Build the HTML for a single event card.
 * isCritical controls extra visual treatment.
 */
function buildEventCard(event, isCritical = false) {
  const cat = categoryClass(event.category);
  const score = event.importance_score || 0;
  const badgeClass = importanceBadgeClass(score);
  const ago = timeAgo(event.last_updated_at);
  const tags = (event.tags || []).slice(0, 3);

  const tagsHtml = tags.length
    ? `<div class="tags">${tags.map(t => `<span class="tag">${t}</span>`).join("")}</div>`
    : "";

  const whyHtml = event.why_it_matters
    ? `<div class="event-card__why">
         <span class="event-card__why-label">Why it matters</span>
         ${event.why_it_matters}
       </div>`
    : "";

  const reasonHtml = event.recommendation_reason
    ? `<span class="reason-chip">✦ ${event.recommendation_reason}</span>`
    : "";

  const readBtn = event.primary_source_url
    ? `<a href="${event.primary_source_url}" target="_blank" rel="noopener noreferrer"
          class="btn-read" onclick="event.stopPropagation()">
          Read original ↗
       </a>`
    : "";

  const criticalBadge = isCritical
    ? `<span class="badge badge--critical">⚠ Breaking</span>`
    : "";

  return `
    <article
      class="event-card event-card--${cat}${isCritical ? " event-card--critical" : ""}"
      onclick="window.location.href='event.html?id=${event.id}'"
      role="button"
      tabindex="0"
      aria-label="View event: ${event.title}"
    >
      <div class="event-card__meta">
        ${criticalBadge}
        <span class="badge badge--category">${event.category || "General"}</span>
        <span class="importance-badge ${badgeClass}">
          ${importanceLabel(score)} · ${Math.round(score)}
        </span>
        <span class="timestamp">${ago}</span>
        ${reasonHtml}
      </div>

      <h2 class="event-card__title">${event.title || "Loading analysis…"}</h2>

      ${event.summary
        ? `<p class="event-card__summary">${event.summary}</p>`
        : ""}

      ${whyHtml}
      ${tagsHtml}

      <div class="event-card__footer">
        <div class="event-card__footer-left">
          <div class="source-info">
            <span class="source-count">${event.source_count} source${event.source_count !== 1 ? "s" : ""}</span>
            ${event.primary_source_name
              ? `<span>via ${event.primary_source_name}</span>`
              : ""}
          </div>
        </div>
        ${readBtn}
      </div>
    </article>
  `;
}

// ── Section builder ──────────────────────────────────────────────────────────

const SECTION_META = {
  critical:   { label: "Breaking & Critical",  color: "var(--color-critical)",  emoji: "⚠" },
  local:      { label: "Local",                color: "var(--color-local)",     emoji: "📍" },
  national:   { label: "National",             color: "var(--color-national)",  emoji: "🏛" },
  world:      { label: "World",                color: "var(--color-world)",     emoji: "🌐" },
  technology: { label: "Technology",           color: "var(--color-tech)",      emoji: "💻" },
  business:   { label: "Business",             color: "var(--color-business)",  emoji: "📈" },
  science:    { label: "Science",              color: "var(--color-science)",   emoji: "🔬" },
};

/** Render a section of events into the DOM. */
function renderSection(containerId, events, sectionKey) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const meta = SECTION_META[sectionKey];
  const isCritical = sectionKey === "critical";

  if (!events || events.length === 0) {
    // Hide the whole section wrapper if empty (except critical — it just stays gone)
    const wrapper = container.closest(".section");
    if (wrapper) wrapper.style.display = "none";
    return;
  }

  // Show section wrapper (it may have been hidden on a previous render)
  const wrapper = container.closest(".section");
  if (wrapper) wrapper.style.display = "";

  // Render a critical banner if this is the critical section
  const bannerHtml = isCritical
    ? `<div class="critical-banner">
         <div class="critical-banner__dot"></div>
         <span class="critical-banner__text">
           ${events.length} critical event${events.length !== 1 ? "s" : ""} requiring your attention
         </span>
       </div>`
    : "";

  container.innerHTML = bannerHtml + events
    .map(event => buildEventCard(event, isCritical))
    .join("");
}

// ── Skeleton loader ──────────────────────────────────────────────────────────

function showSkeletons() {
  const sections = ["world", "technology", "business", "science"];
  sections.forEach(key => {
    const el = document.getElementById(`section-${key}`);
    if (!el) return;
    el.innerHTML = Array(3).fill(`
      <div class="event-card" style="pointer-events:none">
        <div class="skeleton" style="height:12px;width:40%;margin-bottom:12px;"></div>
        <div class="skeleton" style="height:20px;width:90%;margin-bottom:8px;"></div>
        <div class="skeleton" style="height:14px;width:75%;margin-bottom:4px;"></div>
        <div class="skeleton" style="height:14px;width:60%;"></div>
      </div>
    `).join("");
  });
}

// ── Toast notification ───────────────────────────────────────────────────────

function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast toast--${type} show`;
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  showSkeletons();

  try {
    const feed = await getFeed();

    Object.keys(SECTION_META).forEach(key => {
      renderSection(`section-${key}`, feed[key] || [], key);
    });

    // Show "no events yet" state if everything is empty
    const total = Object.values(feed).reduce((sum, arr) => sum + arr.length, 0);
    if (total === 0) {
      document.getElementById("empty-state").style.display = "block";
    }

  } catch (err) {
    console.error("Failed to load feed:", err);
    showToast("Could not connect to the backend. Is it running?", "error");
    document.getElementById("empty-state").style.display = "block";
  }
}

// ── Ingest button ────────────────────────────────────────────────────────────

document.getElementById("btn-ingest")?.addEventListener("click", async function () {
  this.disabled = true;
  this.textContent = "Fetching…";
  showToast("Fetching latest news…");

  try {
    const result = await triggerIngest();
    showToast(
      `Done! ${result.new_articles} new articles, ${result.events_analyzed} events analyzed.`,
      "success"
    );
    // Refresh the feed after ingestion
    await main();
  } catch (err) {
    showToast("Ingestion failed. Check the console.", "error");
  } finally {
    this.disabled = false;
    this.textContent = "Fetch Now";
  }
});

// ── Keyboard nav for event cards ─────────────────────────────────────────────

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.classList.contains("event-card")) {
    e.target.click();
  }
});

main();

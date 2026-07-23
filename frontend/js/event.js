/**
 * event.js — event detail page.
 *
 * Reads ?id=N from the URL, fetches full event detail,
 * and renders the title, summary, why-it-matters, and all articles.
 */

import { getEvent } from "./api.js";

// ── Helpers ─────────────────────────────────────────────────────────────────

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
  return `${Math.floor(diffHours / 24)}d ago`;
}

function importanceBadgeClass(score) {
  if (score >= 65) return "importance-badge--high";
  if (score >= 35) return "importance-badge--mid";
  return "importance-badge--low";
}

function importanceLabel(score) {
  if (score >= 85) return "Critical";
  if (score >= 65) return "Major";
  if (score >= 45) return "Notable";
  if (score >= 25) return "Moderate";
  return "Minor";
}

// ── Renderers ────────────────────────────────────────────────────────────────

function renderDetail(event) {
  document.title = `${event.title} — Feed Indexer`;

  const score = event.importance_score || 0;
  const badgeClass = importanceBadgeClass(score);
  const tags = (event.tags || []).map(t => `<span class="tag">${t}</span>`).join("");

  // Meta row
  document.getElementById("detail-meta").innerHTML = `
    ${event.is_critical ? '<span class="badge badge--critical">⚠ Breaking</span>' : ""}
    <span class="badge badge--category">${event.category || "General"}</span>
    <span class="importance-badge ${badgeClass}">${importanceLabel(score)} · ${Math.round(score)}</span>
    <span class="timestamp">${timeAgo(event.last_updated_at)}</span>
    ${event.recommendation_reason
      ? `<span class="reason-chip">✦ ${event.recommendation_reason}</span>`
      : ""}
  `;

  // Title
  document.getElementById("detail-title").textContent = event.title || "Untitled Event";

  // Summary
  document.getElementById("detail-summary").textContent = event.summary || "";

  // Why it matters
  const whyBlock = document.getElementById("detail-why");
  if (event.why_it_matters) {
    document.getElementById("detail-why-text").textContent = event.why_it_matters;
  } else {
    whyBlock.style.display = "none";
  }

  // Tags
  const tagsEl = document.getElementById("detail-tags");
  tagsEl.innerHTML = tags;
  if (!tags) tagsEl.style.display = "none";

  // Source count
  document.getElementById("detail-source-count").textContent =
    `Reported by ${event.source_count || event.articles?.length || 0} source(s)`;

  // Articles list
  renderSources(event.articles || []);
}

function renderSources(articles) {
  const container = document.getElementById("detail-sources");
  if (!articles.length) {
    container.innerHTML = '<p class="text-muted text-sm">No articles found.</p>';
    return;
  }

  container.innerHTML = articles.map(article => `
    <div class="source-item">
      <div class="source-item__body">
        <div class="source-item__publisher">${article.source_name}</div>
        <div class="source-item__title">${article.title}</div>
        <div class="text-xs text-muted" style="margin-bottom:8px">
          ${timeAgo(article.published_at)} · ${article.category || ""}
        </div>
        ${article.description
          ? `<p class="text-sm text-secondary" style="line-height:1.6;margin-bottom:8px">${article.description}</p>`
          : ""}
        <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="source-item__link">
          Read full article ↗
        </a>
      </div>
    </div>
  `).join("");
}

function showError(message) {
  document.getElementById("detail-loading").style.display = "none";
  document.getElementById("detail-error").style.display = "block";
  document.getElementById("detail-error").textContent = message;
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");

  if (!id) {
    showError("No event ID provided.");
    return;
  }

  try {
    const event = await getEvent(id);
    document.getElementById("detail-loading").style.display = "none";
    document.getElementById("detail-content").style.display = "block";
    renderDetail(event);
  } catch (err) {
    showError(`Could not load event: ${err.message}`);
  }
}

main();

/* =============================================================
   Analyzing Islam — Random catalog-fact footer
   -------------------------------------------------------------
   Replaces the static "Built from the Saheeh International
   translation…" line on community pages with a single-sentence
   pull from the catalog plus a "Read more →" link to that
   entry. Picks a random entry from /assets/data/catalog-entries.json
   on every page load. Fails silently and leaves the original
   footer text in place if the fetch breaks.
   ============================================================= */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  function entryHref(entry) {
    // Catalog rows already carry a relative URL like
    // "catalog/abu-dawud.html#<entry-id>". Use it verbatim — it
    // resolves against the current page (community pages live at
    // site root alongside catalog/).
    if (entry && entry.url) return entry.url;
    if (entry && entry.source && entry.id) {
      return "catalog/" + entry.source + ".html#" + entry.id;
    }
    return "catalog.html";
  }

  function pickRandom(entries) {
    if (!Array.isArray(entries) || !entries.length) return null;
    return entries[Math.floor(Math.random() * entries.length)];
  }

  async function loadEntries() {
    // Cache the parsed list across calls in the same page load.
    if (window.__catalogEntries) return window.__catalogEntries;
    try {
      const res = await fetch("assets/data/catalog-entries.json", { cache: "force-cache" });
      if (!res.ok) return null;
      const data = await res.json();
      window.__catalogEntries = data;
      return data;
    } catch (_) {
      return null;
    }
  }

  async function paint() {
    const footer = document.querySelector(".site-footer");
    if (!footer) return;
    const entries = await loadEntries();
    const entry = pickRandom(entries);
    if (!entry || !entry.title) return;
    footer.innerHTML =
      '<span class="cf-footer-fact">' +
        '<strong>Did you know?</strong> ' +
        esc(entry.title) +
        ' <a href="' + esc(entryHref(entry)) + '">Read more &rarr;</a>' +
      '</span>';
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", paint);
  } else {
    paint();
  }
})();

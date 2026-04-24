// community-search-bar.js — shared across every community page.
// Injects a fuzzy search bar with a live-suggestions dropdown directly
// under the site nav. Enter or clicking "See all results" navigates to
// community-search.html?q=... Uses the search_all RPC (trigram fuzzy
// matching, so partial words and typos still surface results).
(function () {
  "use strict";

  // Don't inject on the search results page itself — it has its own UI.
  if (location.pathname.endsWith("community-search.html")) return;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  let wrap, input, dropdown;
  let debounceT = null;
  let lastQuery = "";

  function mount() {
    if (document.querySelector(".cf-search-global")) return;
    const nav = document.querySelector("nav.site-nav");
    if (!nav) return;

    wrap = document.createElement("div");
    wrap.className = "cf-search-global";
    wrap.innerHTML = `
      <div class="cf-search" style="margin: 14px auto 0; max-width: 1400px; padding: 0 16px;">
        <span class="cf-search-icon">🔍</span>
        <input type="search" id="cf-global-search" placeholder="Search communities and posts…" autocomplete="off">
        <div class="cf-search-dropdown" id="cf-global-search-dropdown"></div>
      </div>
    `;
    nav.parentNode.insertBefore(wrap, nav.nextSibling);

    input = wrap.querySelector("input");
    dropdown = wrap.querySelector(".cf-search-dropdown");

    // Preserve query when navigating between community pages (?q=... is never
    // actually written to the URL on non-search pages, so this is just UX)
    const existingQ = new URLSearchParams(location.search).get("q");
    if (existingQ) input.value = existingQ;

    input.addEventListener("input", onInput);
    input.addEventListener("focus", () => { if (input.value.trim()) runSearch(input.value.trim()); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const q = input.value.trim();
        if (!q) return;
        location.href = "community-search.html?q=" + encodeURIComponent(q);
      } else if (e.key === "Escape") {
        dropdown.classList.remove("open");
      }
    });

    document.addEventListener("click", (e) => {
      if (!wrap.contains(e.target)) dropdown.classList.remove("open");
    });
  }

  function onInput() {
    const q = input.value.trim();
    clearTimeout(debounceT);
    if (!q) { dropdown.classList.remove("open"); dropdown.innerHTML = ""; return; }
    debounceT = setTimeout(() => runSearch(q), 180);
  }

  async function runSearch(q) {
    if (q === lastQuery) { dropdown.classList.add("open"); return; }
    lastQuery = q;
    dropdown.innerHTML = `<div class="cf-search-empty">Searching…</div>`;
    dropdown.classList.add("open");

    if (!window.COMMUNITY_API) return; // not loaded yet on this page
    const { data, error } = await COMMUNITY_API.search(q, 10);
    if (lastQuery !== q) return; // newer query came in

    if (error) {
      dropdown.innerHTML = `<div class="cf-search-empty">Search failed.</div>`;
      return;
    }
    const rows = data || [];
    if (!rows.length) {
      dropdown.innerHTML = `<div class="cf-search-empty">No matches for "${esc(q)}".</div>`;
      return;
    }

    const html = rows.map((r) => {
      const href = r.kind === "community"
        ? `community-view.html?c=${encodeURIComponent(r.id)}`
        : `community-post.html?p=${encodeURIComponent(r.id)}`;
      const kind = r.kind === "community" ? "Community" : "Post";
      return `
        <a class="cf-search-result" href="${href}">
          <span class="cf-search-result-kind">${kind}</span>
          <div class="cf-search-result-title">
            <strong>${esc(r.title || "(untitled)")}</strong>
            <span>${esc(r.community_name ? "in " + r.community_name : "")}${r.subtitle ? (r.community_name ? " · " : "") + esc(r.subtitle.slice(0, 120)) : ""}</span>
          </div>
        </a>`;
    }).join("");

    dropdown.innerHTML = html + `
      <a class="cf-search-result" href="community-search.html?q=${encodeURIComponent(q)}" style="justify-content:center; color:var(--accent);">
        <span>See all results for "${esc(q)}" →</span>
      </a>`;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();

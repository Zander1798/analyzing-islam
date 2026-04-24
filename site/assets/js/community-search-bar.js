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
        <input type="search" id="cf-global-search" placeholder="Search communities, posts, and @usernames…" autocomplete="off">
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

    // Strip a leading "@" so users can type "@alice" and still get a
    // username-only search.
    const needle = q.replace(/^@/, "");

    const [searchResult, profilesResult] = await Promise.all([
      COMMUNITY_API.search(q, 10),
      COMMUNITY_API.searchProfiles(needle, { limit: 5 }),
    ]);

    if (lastQuery !== q) return; // newer query came in

    if (searchResult.error) {
      dropdown.innerHTML = `<div class="cf-search-empty">Search failed.</div>`;
      return;
    }
    // Dropdown is a quick-jump to users + communities only. Post hits
    // stay reachable via the "See all results" link at the bottom so
    // the typeahead doesn't get noisy.
    const communities = (searchResult.data || []).filter((r) => r.kind === "community");
    const users = profilesResult.data || [];

    if (!communities.length && !users.length) {
      dropdown.innerHTML = `
        <div class="cf-search-empty">No users or communities match "${esc(q)}".</div>
        <a class="cf-search-result" href="community-search.html?q=${encodeURIComponent(q)}" style="justify-content:center; color:var(--accent);">
          <span>Search posts for "${esc(q)}" →</span>
        </a>`;
      return;
    }

    const communityHtml = communities.map((r) => {
      const href = `community-view.html?c=${encodeURIComponent(r.id)}`;
      return `
        <a class="cf-search-result" href="${href}">
          <span class="cf-search-result-kind">Community</span>
          <div class="cf-search-result-title">
            <strong>${esc(r.title || r.community_name || "(untitled)")}</strong>
            ${r.subtitle ? `<span>${esc(r.subtitle.slice(0, 120))}</span>` : ""}
          </div>
        </a>`;
    }).join("");

    const userHtml = users.map((u) => {
      const href = `user-profile.html?u=${encodeURIComponent(u.username)}`;
      const avatar = u.avatar_url
        ? `<img src="${esc(u.avatar_url)}" alt="">`
        : `<span>${esc((u.username || "?")[0].toUpperCase())}</span>`;
      return `
        <a class="cf-search-result" href="${href}">
          <span class="cf-search-result-kind">User</span>
          <span class="cf-search-user-avatar">${avatar}</span>
          <div class="cf-search-result-title">
            <strong>@${esc(u.username)}</strong>
          </div>
        </a>`;
    }).join("");

    dropdown.innerHTML = communityHtml + userHtml + `
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

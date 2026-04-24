// community-search.js — full search results page.
// URL: community-search.html?q=<query>&tab=all|communities|posts
// Uses the search_all RPC (trigram similarity) so partial terms and minor
// typos still surface results.
(function () {
  "use strict";

  const shell = document.getElementById("cf-search-shell");
  const params = new URLSearchParams(location.search);
  const state = {
    q: (params.get("q") || "").trim(),
    tab: params.get("tab") || "all",
    results: [],
    users: [],
    loading: false,
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }
  function fmt(n) {
    const v = Number(n) || 0;
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
    if (v >= 1000) return (v / 1000).toFixed(1).replace(/\.0$/, "") + "k";
    return String(v);
  }

  function renderShell() {
    if (!state.q) {
      shell.innerHTML = `
        <h1 style="font-family:var(--sans); font-size:22px; font-weight:600; margin:0 0 20px;">Search communities &amp; posts</h1>
        <form id="cf-search-form">
          <div class="cf-search">
            <span class="cf-search-icon">🔍</span>
            <input type="search" id="cf-search-input" placeholder="Try 'warfare', 'aisha', 'apologetics'…" autocomplete="off" autofocus>
          </div>
        </form>
      `;
      document.getElementById("cf-search-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const v = document.getElementById("cf-search-input").value.trim();
        if (!v) return;
        location.href = "community-search.html?q=" + encodeURIComponent(v);
      });
      return;
    }

    shell.innerHTML = `
      <h1 style="font-family:var(--sans); font-size:22px; font-weight:600; margin:0 0 8px;">Results for "${esc(state.q)}"</h1>
      <p style="color:var(--text-muted); font-size:13px; margin:0 0 20px;">Fuzzy match on name, slug, description, and post title.</p>

      <form id="cf-search-form" style="margin-bottom:18px;">
        <div class="cf-search">
          <span class="cf-search-icon">🔍</span>
          <input type="search" id="cf-search-input" placeholder="Refine your search…" autocomplete="off" value="${esc(state.q)}">
        </div>
      </form>

      <div class="cf-search-tabs">
        <a data-tab="all"         class="${state.tab === "all" ? "active" : ""}"         href="community-search.html?q=${encodeURIComponent(state.q)}&tab=all">All</a>
        <a data-tab="communities" class="${state.tab === "communities" ? "active" : ""}" href="community-search.html?q=${encodeURIComponent(state.q)}&tab=communities">Communities</a>
        <a data-tab="posts"       class="${state.tab === "posts" ? "active" : ""}"       href="community-search.html?q=${encodeURIComponent(state.q)}&tab=posts">Posts</a>
        <a data-tab="users"       class="${state.tab === "users" ? "active" : ""}"       href="community-search.html?q=${encodeURIComponent(state.q)}&tab=users">Users</a>
      </div>

      <div id="cf-search-results">${state.loading ? `<div class="cf-search-empty">Searching…</div>` : renderResults()}</div>
    `;

    document.getElementById("cf-search-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const v = document.getElementById("cf-search-input").value.trim();
      if (!v) return;
      location.href = "community-search.html?q=" + encodeURIComponent(v) + "&tab=" + state.tab;
    });
  }

  function renderUserRow(u) {
    const href = `user-profile.html?u=${encodeURIComponent(u.username)}`;
    const avatar = u.avatar_url
      ? `<img src="${esc(u.avatar_url)}" alt="" style="width:100%;height:100%;object-fit:cover;">`
      : `<span>${esc((u.username || "?")[0].toUpperCase())}</span>`;
    return `
      <a class="cf-post" href="${href}" style="text-decoration:none; grid-template-columns: 68px minmax(0,1fr);">
        <div class="cf-post-votes" style="justify-content:center; align-items:center;">
          <span class="cf-search-user-avatar" style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:#0a0a0a;display:inline-flex;align-items:center;justify-content:center;font-weight:700;overflow:hidden;">${avatar}</span>
        </div>
        <div class="cf-post-body">
          <h2 class="cf-post-title" style="font-size:16px;">@${esc(u.username)}</h2>
          <div class="cf-post-meta">User profile</div>
        </div>
      </a>`;
  }

  function renderResults() {
    let rows = state.results || [];
    if (state.tab === "communities") rows = rows.filter((r) => r.kind === "community");
    if (state.tab === "posts") rows = rows.filter((r) => r.kind === "post");
    if (state.tab === "users") rows = [];

    const users = (state.tab === "all" || state.tab === "users") ? (state.users || []) : [];

    if (!rows.length && !users.length) {
      return `<div class="cf-search-empty">No ${state.tab === "all" ? "" : state.tab + " "}results for "${esc(state.q)}".</div>`;
    }

    const usersHtml = users.length
      ? (state.tab === "all"
          ? `<div style="margin:8px 0 4px; font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--text-dim);">Users</div>`
          : "") + users.map(renderUserRow).join("")
      : "";

    const postsHtml = rows
      .map((r) => {
        const href = r.kind === "community"
          ? `community-view.html?c=${encodeURIComponent(r.id)}`
          : `community-post.html?p=${encodeURIComponent(r.id)}`;
        const kind = r.kind === "community" ? "Community" : "Post";
        const subtitle = r.kind === "community"
          ? `${fmt(r.score)} members${r.subtitle ? " · " + esc(r.subtitle.slice(0, 200)) : ""}`
          : `in ${esc(r.community_name || "")}${r.subtitle ? " · " + esc(r.subtitle.slice(0, 200)) : ""}`;
        return `
          <a class="cf-post" href="${href}" style="text-decoration:none; grid-template-columns: 68px minmax(0,1fr);">
            <div class="cf-post-votes" style="justify-content:center;">
              <span class="cf-search-result-kind">${kind}</span>
            </div>
            <div class="cf-post-body">
              <h2 class="cf-post-title" style="font-size:16px;">${esc(r.title || "(untitled)")}</h2>
              <div class="cf-post-meta">${subtitle}</div>
            </div>
          </a>`;
      })
      .join("");

    const postsSectionLabel = (state.tab === "all" && rows.length && users.length)
      ? `<div style="margin:18px 0 4px; font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--text-dim);">Communities &amp; posts</div>`
      : "";

    return usersHtml + postsSectionLabel + postsHtml;
  }

  async function runSearch() {
    state.loading = true;
    renderShell();
    // Strip a leading "@" so users searching for "@alice" find users.
    const needle = state.q.replace(/^@/, "");
    const [resA, resB] = await Promise.all([
      COMMUNITY_API.search(state.q, 50),
      COMMUNITY_API.searchProfiles(needle, { limit: 20 }),
    ]);
    state.loading = false;
    if (resA.error) {
      shell.innerHTML = `<div class="cf-error">${esc(resA.error.message || resA.error)}</div>`;
      return;
    }
    state.results = resA.data || [];
    state.users = resB.data || [];
    renderShell();
  }

  function paint() {
    if (!state.q) { renderShell(); return; }
    runSearch();
  }

  function onReady() {
    if (window.__authReady) window.__authReady.then(paint);
    else paint();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();

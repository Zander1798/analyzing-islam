/* =============================================================
   Analyzing Islam — Shared community left sidebar
   -------------------------------------------------------------
   Self-mounts on any page that has <aside id="cf-left">. Renders:
     - My profile card (avatar + @username + Edit profile)
     - Nav links: Home / Popular / Explore / Create community
     - Your communities (owned)
     - Joined communities (member/admin)

   Highlights the current page based on location. Re-renders on
   auth-state and profile-state events so username / avatar edits
   update everywhere immediately.
   ============================================================= */
(function () {
  "use strict";

  const state = {
    user: null,
    myCommunities: [],
    lastSignedIn: null,
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  // Determine which sidebar row should show an "active" highlight
  // based on the URL. The community-home page uses ?sort=top to mean
  // Popular; community-view uses ?c=<slug> to identify which community.
  function currentContext() {
    const path = location.pathname;
    const params = new URLSearchParams(location.search);
    if (path.endsWith("/community.html") || path.endsWith("community.html")) {
      const sort = params.get("sort");
      if (sort === "top") return { page: "popular" };
      return { page: "home" };
    }
    if (path.endsWith("community-view.html")) {
      return { slug: (params.get("c") || "").trim() };
    }
    return {};
  }

  function iconFor(c) {
    if (c && c.icon_url) return `<span class="cf-side-icon"><img src="${esc(c.icon_url)}" alt=""></span>`;
    const letter = c && c.name ? c.name[0].toUpperCase() : "?";
    return `<span class="cf-side-icon">${esc(letter)}</span>`;
  }

  function myProfileCardHtml() {
    const me = window.__profile || null;
    if (!state.user) {
      return `
        <div class="cf-my-profile-card cf-my-profile-card--signedout">
          <a href="login.html?return=${encodeURIComponent(location.pathname + location.search)}">Sign in</a> to manage your community profile.
        </div>`;
    }
    const avatar = me && me.avatar_url
      ? `<img src="${esc(me.avatar_url)}" alt="">`
      : (me && me.username ? esc(me.username[0].toUpperCase()) : esc((state.user.email || "?")[0].toUpperCase()));
    const name = (me && me.username) ? ("@" + me.username) : "(set a username)";
    return `
      <div class="cf-my-profile-card">
        <div class="cf-my-profile-card-head">
          <span class="cf-my-profile-avatar">${avatar}</span>
          <span class="cf-my-profile-name">${esc(name)}</span>
        </div>
        <a class="cf-my-profile-edit" href="community-profile.html">Edit profile</a>
      </div>`;
  }

  function partition(memberships) {
    const owned = [];
    const joined = [];
    (memberships || []).forEach((m) => {
      if (!m || !m.communities) return;
      if (m.role === "owner") owned.push(m.communities);
      else joined.push(m.communities);
    });
    const byName = (a, b) => (a.name || "").localeCompare(b.name || "");
    owned.sort(byName);
    joined.sort(byName);
    return { owned, joined };
  }

  function sideRow(c, ctx) {
    const isActive = ctx.slug && c.slug === ctx.slug;
    return `
      <a class="cf-side-link ${isActive ? "active" : ""}"
         href="community-view.html?c=${encodeURIComponent(c.slug)}">
        ${iconFor(c)}
        <span>${esc(c.name)}</span>
      </a>`;
  }

  function render() {
    const left = document.getElementById("cf-left");
    if (!left) return;

    const ctx = currentContext();
    const { owned, joined } = partition(state.myCommunities);

    const ownedHtml = owned.length
      ? owned.map((c) => sideRow(c, ctx)).join("")
      : `<div class="cf-side-empty">You haven't created any communities.</div>`;
    const joinedHtml = joined.length
      ? joined.map((c) => sideRow(c, ctx)).join("")
      : `<div class="cf-side-empty">You haven't joined any communities.</div>`;

    left.innerHTML = `
      ${myProfileCardHtml()}

      <div class="cf-side-section">
        <a class="cf-side-link ${ctx.page === "home" ? "active" : ""}" href="community.html">
          <span class="cf-side-icon">☰</span><span>Home</span>
        </a>
        <a class="cf-side-link ${ctx.page === "popular" ? "active" : ""}" href="community.html?sort=top">
          <span class="cf-side-icon">★</span><span>Popular</span>
        </a>
        <a class="cf-side-link" href="community.html?view=explore">
          <span class="cf-side-icon">◎</span><span>Explore</span>
        </a>
        <a class="cf-side-link" href="community-create.html">
          <span class="cf-side-icon">+</span><span>Create community</span>
        </a>
      </div>

      <div class="cf-side-section">
        <p class="cf-side-label">Your communities</p>
        ${ownedHtml}
      </div>

      <div class="cf-side-section">
        <p class="cf-side-label">Joined communities</p>
        ${joinedHtml}
      </div>
    `;
  }

  async function loadMyCommunities() {
    state.myCommunities = [];
    if (!state.user) return;
    if (!window.COMMUNITY_API) return;
    const { data } = await window.COMMUNITY_API.listMyCommunities();
    state.myCommunities = data || [];
  }

  async function refresh() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    // Reload the community list only when the signed-in status flipped.
    // On a plain profile-state event (username / avatar edit) we skip
    // this and just re-render — the my-profile card picks up changes.
    const needFetch = (state.lastSignedIn !== isIn);
    state.user = user;
    state.lastSignedIn = isIn;
    if (needFetch) await loadMyCommunities();
    render();
  }

  function init() {
    if (window.__authReady) window.__authReady.then(refresh);
    else refresh();
    window.addEventListener("auth-state", refresh);
    // Re-render on profile changes (avatar / username) without reloading
    // the whole community list.
    window.addEventListener("profile-state", () => { try { render(); } catch (_) {} });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose a manual trigger in case another script wants to force a
  // render (e.g., after a join / leave action elsewhere on the page).
  window.CF_SIDEBAR = { render };
})();

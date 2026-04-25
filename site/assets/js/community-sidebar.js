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
    notifCount: 0,       // combined unseen requests + unread threads
    notifTimer: null,
    notifChannel: null,  // realtime channel that nudges loadNotifCount
    isRendering: false,
    isRefreshing: false,
    notifInFlight: false,
    pendingNotifRefresh: false,
    // Map<communityId, number> — pending join-request count per community
    // the viewer owns or admins. Drives the red badge on each "Your
    // communities" sidebar row. Auto-decreases as admins approve / deny
    // requests on the manage screen (status leaves 'pending').
    pendingByCommunity: new Map(),
    pendingChannel: null,
    pendingInFlight: false,
    pendingPending: false,
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
    if (path.endsWith("messages.html")) {
      return { page: "messages" };
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

  function sideRow(c, ctx, opts) {
    const isActive = ctx.slug && c.slug === ctx.slug;
    const pending = opts && opts.pending ? Number(opts.pending) : 0;
    const badge = pending > 0
      ? `<span class="cf-notif-badge" aria-label="${pending} pending join request${pending === 1 ? "" : "s"}">${pending > 99 ? "99+" : pending}</span>`
      : "";
    return `
      <a class="cf-side-link ${isActive ? "active" : ""}"
         href="community-view.html?c=${encodeURIComponent(c.slug)}">
        ${iconFor(c)}
        <span>${esc(c.name)}</span>
        ${badge}
      </a>`;
  }

  function render() {
    // Re-entrancy guard. render() writes to #cf-left and events
    // like profile-state / cf-messages-notif-change can fire during
    // that write — without this flag, a second render() can start
    // before the first returns, which in the worst case cascades
    // into an infinite paint loop and freezes the tab.
    if (state.isRendering) return;
    const left = document.getElementById("cf-left");
    if (!left) return;

    state.isRendering = true;
    try { actuallyRender(left); }
    finally { state.isRendering = false; }
  }

  function actuallyRender(left) {
    const ctx = currentContext();
    const { owned, joined } = partition(state.myCommunities);

    const pendingMap = state.pendingByCommunity || new Map();
    const ownedHtml = owned.length
      ? owned.map((c) => sideRow(c, ctx, { pending: pendingMap.get(c.id) || 0 })).join("")
      : `<div class="cf-side-empty">You haven't created any communities.</div>`;
    const joinedHtml = joined.length
      ? joined.map((c) => sideRow(c, ctx, { pending: pendingMap.get(c.id) || 0 })).join("")
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
        <a class="cf-side-link ${ctx.page === "messages" ? "active" : ""}" href="messages.html">
          <span class="cf-side-icon">✉</span>
          <span>Messages</span>
          ${state.notifCount > 0
            ? `<span class="cf-notif-badge" aria-label="${state.notifCount} unread notifications">${state.notifCount > 99 ? "99+" : state.notifCount}</span>`
            : ""}
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

  // Pending join-request counts for every community the viewer owns or
  // admins. Re-entrancy guarded so cascaded events (auth-state +
  // realtime + cf-community-pending-change) coalesce instead of stacking.
  async function loadPendingByCommunity() {
    if (state.pendingInFlight) {
      state.pendingPending = true;
      return;
    }
    if (!state.user || !window.COMMUNITY_API ||
        typeof COMMUNITY_API.countMyAdminPending !== "function") {
      if (state.pendingByCommunity.size) {
        state.pendingByCommunity = new Map();
        render();
      }
      return;
    }
    state.pendingInFlight = true;
    try {
      const map = await COMMUNITY_API.countMyAdminPending();
      // Only re-render when the totals actually changed.
      const next = map instanceof Map ? map : new Map();
      let changed = next.size !== state.pendingByCommunity.size;
      if (!changed) {
        for (const [k, v] of next) {
          if (state.pendingByCommunity.get(k) !== v) { changed = true; break; }
        }
      }
      if (changed) {
        state.pendingByCommunity = next;
        render();
      }
    } catch (_) { /* best-effort */ }
    finally {
      state.pendingInFlight = false;
      if (state.pendingPending) {
        state.pendingPending = false;
        setTimeout(loadPendingByCommunity, 0);
      }
    }
  }

  // Fetch the combined notification count (unseen friend requests +
  // unread direct-message threads) and re-render if it changed.
  // Guarded against concurrent calls so stacked events (auth-state
  // + profile-state + cf-messages-notif-change firing together) can't
  // spin into a tight loop of re-queries.
  async function loadNotifCount() {
    if (state.notifInFlight) {
      state.pendingNotifRefresh = true;
      return;
    }
    if (!state.user || !window.COMMUNITY_API ||
        typeof COMMUNITY_API.countMessagesNotifications !== "function") {
      if (state.notifCount !== 0) {
        state.notifCount = 0;
        render();
      }
      return;
    }
    state.notifInFlight = true;
    try {
      const { count } = await COMMUNITY_API.countMessagesNotifications();
      if (count !== state.notifCount) {
        state.notifCount = count;
        render();
      }
    } catch (_) { /* best-effort */ }
    finally {
      state.notifInFlight = false;
      if (state.pendingNotifRefresh) {
        state.pendingNotifRefresh = false;
        // One coalesced follow-up, scheduled async so events that
        // triggered us don't recurse on the stack.
        setTimeout(loadNotifCount, 0);
      }
    }
  }

  function startNotifPoll() {
    stopNotifPoll();
    if (!state.user || document.hidden) return;
    // Keep a 60s safety net even with realtime in case the WebSocket
    // drops mid-session and the user has no live tab to recover from.
    state.notifTimer = setInterval(loadNotifCount, 60000);
  }

  function stopNotifPoll() {
    if (state.notifTimer) { clearInterval(state.notifTimer); state.notifTimer = null; }
  }

  // Subscribe to direct_messages / direct_threads / friendships so the
  // unread badge ticks up the instant a peer messages or friend-requests
  // the viewer. RLS already restricts these tables to participants /
  // addressees, so the channel only ever delivers events the viewer
  // is allowed to see.
  function startNotifRealtime() {
    stopNotifRealtime();
    if (!state.user || !window.__supabase) return;
    state.notifChannel = window.__supabase
      .channel("notif-" + state.user.id)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "direct_messages" },
        () => { loadNotifCount(); }
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "direct_threads" },
        () => { loadNotifCount(); }
      )
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "friendships", filter: "addressee_id=eq." + state.user.id },
        () => { loadNotifCount(); }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "friendships", filter: "addressee_id=eq." + state.user.id },
        () => { loadNotifCount(); }
      )
      .subscribe();
  }

  function stopNotifRealtime() {
    if (state.notifChannel && window.__supabase) {
      try { window.__supabase.removeChannel(state.notifChannel); } catch (_) {}
    }
    state.notifChannel = null;
  }

  // Realtime channel for community_join_requests so the per-community
  // pending badge ticks the moment a request is created or resolved
  // (status leaves 'pending'). RLS limits these events to communities
  // the viewer admins, so we don't need a per-community filter here.
  function startPendingRealtime() {
    stopPendingRealtime();
    if (!state.user || !window.__supabase) return;
    state.pendingChannel = window.__supabase
      .channel("pending-" + state.user.id)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "community_join_requests" },
        () => { loadPendingByCommunity(); }
      )
      .subscribe();
  }

  function stopPendingRealtime() {
    if (state.pendingChannel && window.__supabase) {
      try { window.__supabase.removeChannel(state.pendingChannel); } catch (_) {}
    }
    state.pendingChannel = null;
  }

  async function refresh() {
    if (state.isRefreshing) return;
    state.isRefreshing = true;
    try {
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
      await Promise.all([loadNotifCount(), loadPendingByCommunity()]);
      if (isIn) { startNotifPoll(); startNotifRealtime(); startPendingRealtime(); }
      else { stopNotifPoll(); stopNotifRealtime(); stopPendingRealtime(); }
    } finally {
      state.isRefreshing = false;
    }
  }

  function init() {
    if (window.__authReady) window.__authReady.then(refresh);
    else refresh();
    window.addEventListener("auth-state", refresh);
    // Re-render on profile changes (avatar / username) without reloading
    // the whole community list.
    window.addEventListener("profile-state", () => { try { render(); } catch (_) {} });

    // messages.js dispatches this when a thread is read, a request is
    // accepted/declined, or the Requests panel is opened — refresh
    // the badge immediately instead of waiting for the poller.
    window.addEventListener("cf-messages-notif-change", () => { loadNotifCount(); });

    // community-manage.js dispatches this after approve / deny so the
    // per-community pending badges drop right away instead of waiting
    // for the realtime channel to redeliver the row update.
    window.addEventListener("cf-community-pending-change", () => { loadPendingByCommunity(); });

    // Pause polling when the tab is hidden; resume when visible.
    // Realtime channel stays open across visibility changes so the
    // badge is already up to date by the time the user returns.
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) stopNotifPoll();
      else if (state.user) { loadNotifCount(); startNotifPoll(); }
    });
    window.addEventListener("beforeunload", () => {
      stopNotifRealtime();
      stopPendingRealtime();
    });
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

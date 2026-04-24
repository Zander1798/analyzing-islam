// community-view.js — single community page (community-view.html?c=<slug>).
// Renders banner + header, Join/Request-to-Join button, post list with sort
// tabs, and About sidebar. RLS enforces private-post visibility; non-members
// of a private community see only the header + "Request to join" CTA.
(function () {
  "use strict";

  const $left = document.getElementById("cf-left");
  const $center = document.getElementById("cf-center");
  const $right = document.getElementById("cf-right");

  const params = new URLSearchParams(location.search);
  const slug = (params.get("c") || "").trim();

  const state = {
    user: null,
    community: null,
    membership: null,
    joinRequest: null,
    members: [],
    myCommunities: [],
    posts: [],
    myVotes: {},
    sort: params.get("sort") || "new",
    error: null,
    pendingCount: 0,          // for this community (admin-only)
    pendingByCommunity: null, // Map<communityId, number> for sidebar
  };

  // ------------------------------------------------------------------
  // Helpers (mirrors community-home.js; duplicated on purpose to keep
  // each page self-contained and small.)
  // ------------------------------------------------------------------
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
  function ago(ts) {
    if (!ts) return "";
    const d = new Date(ts);
    const s = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
    if (s < 60) return s + "s ago";
    if (s < 3600) return Math.floor(s / 60) + "m ago";
    if (s < 86400) return Math.floor(s / 3600) + "h ago";
    if (s < 2592000) return Math.floor(s / 86400) + "d ago";
    return d.toLocaleDateString();
  }
  function iconFor(c) {
    if (c && c.icon_url) return `<span class="cf-side-icon"><img src="${esc(c.icon_url)}" alt=""></span>`;
    const letter = c && c.name ? c.name[0].toUpperCase() : "?";
    return `<span class="cf-side-icon">${esc(letter)}</span>`;
  }
  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return tmp.textContent || "";
  }
  // Pull the first <img> / <video> out of body_html so the feed card can
  // show a small thumbnail. Returns { type, src } or null.
  function firstMediaFrom(html) {
    if (!html) return null;
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    const el = tmp.querySelector("img[src], video[src]");
    if (!el) return null;
    const src = el.getAttribute("src");
    if (!src) return null;
    return { type: el.tagName.toLowerCase() === "video" ? "video" : "image", src };
  }

  // ------------------------------------------------------------------
  // Left sidebar (same shape as home)
  // ------------------------------------------------------------------
  // Split memberships: "Your communities" = role owner (the user created
  // it), "Joined communities" = role member or admin. The currently-
  // viewed community gets an "active" class in whichever list it lands.
  function sideRowHtml(c) {
    const pendingMap = state.pendingByCommunity;
    const n = pendingMap && pendingMap.get ? pendingMap.get(c.id) : 0;
    const badge = n ? `<span class="cf-notify-badge" title="${n} pending join request${n === 1 ? "" : "s"}">${n}</span>` : "";
    return `
      <a class="cf-side-link ${c.slug === slug ? "active" : ""}"
         href="community-view.html?c=${encodeURIComponent(c.slug)}">
        ${iconFor(c)}
        <span>${esc(c.name)}</span>
        ${badge}
      </a>`;
  }

  function myProfileCardHtml() {
    const me = window.__profile || null;
    if (!state.user) {
      return `
        <div class="cf-my-profile-card cf-my-profile-card--signedout">
          <a href="login.html?return=community-view.html${location.search}">Sign in</a> to manage your community profile.
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

  function renderLeft() {
    const owned = [];
    const joined = [];
    (state.myCommunities || []).forEach((m) => {
      if (!m || !m.communities) return;
      if (m.role === "owner") owned.push(m.communities);
      else joined.push(m.communities);
    });
    const byName = (a, b) => a.name.localeCompare(b.name);
    owned.sort(byName);
    joined.sort(byName);

    const ownedHtml = owned.length
      ? owned.map(sideRowHtml).join("")
      : `<div class="cf-side-empty">You haven't created any communities.</div>`;

    const joinedHtml = joined.length
      ? joined.map(sideRowHtml).join("")
      : `<div class="cf-side-empty">You haven't joined any communities.</div>`;

    $left.innerHTML = `
      ${myProfileCardHtml()}
      <div class="cf-side-section">
        <a class="cf-side-link" href="community.html">
          <span class="cf-side-icon">☰</span><span>Home</span>
        </a>
        <a class="cf-side-link" href="community.html?sort=top">
          <span class="cf-side-icon">★</span><span>Popular</span>
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

  // ------------------------------------------------------------------
  // Right sidebar — About card, stats, admin actions
  // ------------------------------------------------------------------
  function renderRight() {
    if (!state.community) { $right.innerHTML = ""; return; }
    const c = state.community;
    const isAdmin = state.membership && (state.membership.role === "owner" || state.membership.role === "admin");
    $right.innerHTML = `
      <div class="cf-panel">
        <h3>About community</h3>
        <p style="color:var(--text-muted); font-size:13px; margin:0 0 6px;">${esc(c.description || "No description.")}</p>
        ${c.is_private ? `<p><span class="cf-badge cf-badge-private">Private community</span></p>` : ""}
        <div class="cf-about-stats">
          <div class="cf-about-stat"><strong>${fmt(c.member_count)}</strong><span>Members</span></div>
          <div class="cf-about-stat"><strong>${fmt(c.post_count)}</strong><span>Posts</span></div>
        </div>
        <div style="font-size:12px; color:var(--text-dim);">Created ${ago(c.created_at)}</div>
        ${isAdmin ? `
          <div style="margin-top:14px;">
            <a class="cf-btn" href="community-manage.html?c=${encodeURIComponent(c.slug)}" style="width:100%; justify-content:center;">
              Manage community${state.pendingCount ? `<span class="cf-notify-badge" title="${state.pendingCount} pending join request${state.pendingCount === 1 ? "" : "s"}">${state.pendingCount}</span>` : ""}
            </a>
          </div>` : ""}
      </div>
    `;
  }

  // ------------------------------------------------------------------
  // Header — banner, icon, title, Join/Leave/Request button
  // ------------------------------------------------------------------
  function headerButtonHtml() {
    const c = state.community;
    if (!state.user) {
      return `<a class="cf-btn cf-btn-primary" href="login.html?return=${encodeURIComponent(location.pathname + location.search)}">Sign in to join</a>`;
    }
    if (state.membership) {
      const label = state.membership.role === "owner" ? "Owner" : (state.membership.role === "admin" ? "Admin" : "Joined");
      const leaveText = state.membership.role === "owner" ? "" : `<button class="cf-btn cf-btn-joined" data-action="leave">${esc(label)} ▾</button>`;
      return leaveText || `<span class="cf-btn cf-btn-joined">${esc(label)}</span>`;
    }
    if (c.is_private) {
      if (state.joinRequest && state.joinRequest.status === "pending") {
        return `<button class="cf-btn" data-action="cancel-request" title="Withdraw your join request">Cancel request</button>`;
      }
      if (state.joinRequest && state.joinRequest.status === "denied") {
        return `<button class="cf-btn" data-action="request-join">Request to join</button>
                <div style="font-size:12px; color:var(--strong); margin-left:10px;">Previous request denied</div>`;
      }
      return `<button class="cf-btn cf-btn-primary" data-action="request-join">Request to join</button>`;
    }
    return `<button class="cf-btn cf-btn-primary" data-action="join">Join</button>`;
  }

  function renderHeader() {
    const c = state.community;
    const banner = c.banner_url
      ? `background-image: url('${esc(c.banner_url)}');`
      : "";
    const icon = c.icon_url
      ? `<img src="${esc(c.icon_url)}" alt="">`
      : (c.name || "?")[0].toUpperCase();

    return `
      <div class="cf-community-banner" style="${banner}"></div>
      <div class="cf-community-header">
        <div class="cf-community-icon">${c.icon_url ? icon : esc(icon)}</div>
        <div class="cf-community-title">
          <h1>${esc(c.name)}</h1>
          <p class="cf-community-slug">
            <span>${esc(c.slug)}</span>
            ${c.is_private ? `<span class="cf-badge cf-badge-private">Private</span>` : ""}
            <span>·</span>
            <span>${fmt(c.member_count)} members</span>
          </p>
        </div>
        <div class="cf-community-actions">
          ${state.membership ? `<a class="cf-btn cf-btn-primary" href="community-new-post.html?c=${encodeURIComponent(c.slug)}">+ Create Post</a>` : ""}
          ${headerButtonHtml()}
        </div>
      </div>
    `;
  }

  // ------------------------------------------------------------------
  // Center
  // ------------------------------------------------------------------
  function renderSortBar() {
    const base = "community-view.html?c=" + encodeURIComponent(slug);
    return `
      <div class="cf-main-bar">
        <nav class="cf-sort-tabs" data-sort-nav>
          <a data-sort="new" class="${state.sort === "new" ? "active" : ""}" href="${base}&sort=new">New</a>
          <a data-sort="top" class="${state.sort === "top" ? "active" : ""}" href="${base}&sort=top">Top</a>
        </nav>
      </div>`;
  }

  function renderPost(p) {
    const c = state.community;
    const myVote = state.myVotes[p.id] || 0;
    const snippetRaw = stripHtml(p.body_html).slice(0, 280);
    const snippet = snippetRaw ? esc(snippetRaw) + (snippetRaw.length >= 280 ? "…" : "") : "";
    const buildBadge = p.build_id
      ? `<div class="cf-post-badge-build">📎 <span>Attached build: <strong>${esc(
          (p.build_snapshot && p.build_snapshot.name) || "build"
        )}</strong></span></div>`
      : "";
    const permalink = `community-post.html?p=${p.id}`;
    const media = firstMediaFrom(p.body_html);
    const mediaBlock = media
      ? (media.type === "video"
          ? `<div class="cf-post-media">
               <video src="${esc(media.src)}" controls preload="metadata" playsinline></video>
             </div>`
          : `<a class="cf-post-media" href="${permalink}" aria-label="Open post">
               <img src="${esc(media.src)}" alt="" loading="lazy">
             </a>`)
      : "";

    return `
      <article class="cf-post" data-post-id="${p.id}">
        <div class="cf-post-body">
          <div class="cf-post-meta">
            <span>Posted by ${authorLink(p.author)}</span>
            <span class="cf-dot">·</span>
            <span>${ago(p.created_at)}</span>
          </div>
          <h2 class="cf-post-title"><a href="${permalink}">${esc(p.title)}</a></h2>
          ${buildBadge}
          ${snippet ? `<div class="cf-post-snippet">${snippet}</div>` : ""}
          ${mediaBlock}
          <div class="cf-post-actions">
            <div class="cf-post-votes-inline" aria-label="Votes">
              <button class="cf-vote-btn up ${myVote === 1 ? "active" : ""}" data-vote="1" aria-label="Upvote">▲</button>
              <span class="cf-vote-score">${fmt(p.score)}</span>
              <button class="cf-vote-btn down ${myVote === -1 ? "active" : ""}" data-vote="-1" aria-label="Downvote">▼</button>
            </div>
            <a href="${permalink}">💬 ${fmt(p.comment_count)} comments</a>
            <button data-action="share">🔗 Share</button>
          </div>
        </div>
      </article>`;
  }

  function renderPrivateGate() {
    const c = state.community;
    const header = renderHeader();
    const req = state.joinRequest;
    const reqMsg = req && req.status === "pending"
      ? `<p>Your request is pending the admin's review.</p>`
      : (req && req.status === "denied" ? `<p>Your previous request was denied.</p>` : "");
    $center.innerHTML = `
      ${header}
      <div class="cf-empty">
        <h2>This community is private</h2>
        <p>Only members can see posts here. ${state.user ? "" : "Sign in and then request to join."}</p>
        ${reqMsg}
      </div>
    `;
    wireHeaderButtons();
  }

  function renderCenter() {
    const c = state.community;
    // Non-member on a private community -> gated view.
    if (c.is_private && !state.membership) {
      renderPrivateGate();
      return;
    }
    const posts = state.posts.length
      ? state.posts.map(renderPost).join("")
      : `<div class="cf-empty">
           <h2>No posts yet</h2>
           <p>Be the first to post in this community.</p>
           ${state.membership ? `<a class="cf-btn cf-btn-primary" href="community-new-post.html?c=${encodeURIComponent(c.slug)}">+ Create the first post</a>` : ""}
         </div>`;
    $center.innerHTML = `
      ${renderHeader()}
      ${renderSortBar()}
      ${posts}
    `;
    wireHeaderButtons();
    wireSortTabs();
    wireVotes();
    wireShare();
  }

  // ------------------------------------------------------------------
  // Interactions
  // ------------------------------------------------------------------
  function wireHeaderButtons() {
    $center.querySelectorAll("[data-action]").forEach((btn) => {
      const action = btn.getAttribute("data-action");
      if (action === "join") btn.addEventListener("click", handleJoin);
      if (action === "leave") btn.addEventListener("click", handleLeave);
      if (action === "request-join") btn.addEventListener("click", handleRequestJoin);
      if (action === "cancel-request") btn.addEventListener("click", handleCancelRequest);
    });
  }

  async function handleJoin() {
    if (!state.user) { location.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search); return; }
    const { error } = await COMMUNITY_API.joinCommunity(state.community.id);
    if (error) { alert("Could not join: " + (error.message || error)); return; }
    await reloadCore();
  }

  async function handleLeave() {
    if (!confirm("Leave this community?")) return;
    const { error } = await COMMUNITY_API.leaveCommunity(state.community.id);
    if (error) { alert("Could not leave: " + (error.message || error)); return; }
    await reloadCore();
  }

  async function handleRequestJoin() {
    if (!state.user) { location.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search); return; }
    const msg = prompt("Message to the admin (optional):", "") || "";
    const { error } = await COMMUNITY_API.requestToJoin(state.community.id, msg);
    if (error) { alert("Could not send request: " + (error.message || error)); return; }
    await reloadCore();
  }

  async function handleCancelRequest() {
    if (!state.joinRequest) return;
    if (!confirm("Cancel your join request?")) return;
    const { error } = await COMMUNITY_API.cancelRequest(state.joinRequest.id);
    if (error) { alert("Could not cancel request: " + (error.message || error)); return; }
    state.joinRequest = null;
    await reloadCore();
  }

  function wireSortTabs() {
    $center.querySelectorAll("[data-sort-nav] a").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        state.sort = a.getAttribute("data-sort");
        const url = new URL(location.href);
        url.searchParams.set("sort", state.sort);
        history.replaceState(null, "", url.toString());
        loadPosts();
      });
    });
  }

  function wireVotes() {
    $center.querySelectorAll(".cf-post").forEach((post) => {
      const postId = Number(post.getAttribute("data-post-id"));
      post.querySelectorAll(".cf-vote-btn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.preventDefault();
          if (!state.user) { location.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search); return; }
          const v = Number(btn.getAttribute("data-vote"));
          const existing = state.myVotes[postId] || 0;
          const next = existing === v ? 0 : v;
          const scoreEl = post.querySelector(".cf-vote-score");
          const p = state.posts.find((x) => x.id === postId);
          if (p) { p.score = p.score - existing + next; scoreEl.textContent = fmt(p.score); }
          state.myVotes[postId] = next;
          post.querySelectorAll(".cf-vote-btn").forEach((b) => {
            const bv = Number(b.getAttribute("data-vote"));
            b.classList.toggle("active", next !== 0 && bv === next);
          });
          await COMMUNITY_API.votePost(postId, next);
        });
      });
    });
  }

  function wireShare() {
    $center.querySelectorAll('[data-action="share"]').forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        const post = btn.closest(".cf-post");
        const id = post.getAttribute("data-post-id");
        const url = new URL(`community-post.html?p=${id}`, location.href).toString();
        if (navigator.share) { try { await navigator.share({ url }); return; } catch (_) {} }
        try {
          await navigator.clipboard.writeText(url);
          btn.textContent = "✓ Copied";
          setTimeout(() => (btn.textContent = "🔗 Share"), 1800);
        } catch { prompt("Copy this link:", url); }
      });
    });
  }

  // ------------------------------------------------------------------
  // Data loads
  // ------------------------------------------------------------------
  async function loadCommunity() {
    const { data, error } = await COMMUNITY_API.getCommunity(slug);
    if (error) { state.error = error; state.community = null; return; }
    if (!data) { state.error = new Error("Community not found"); state.community = null; return; }
    state.community = data;
  }

  async function loadMembership() {
    if (!state.user || !state.community) { state.membership = null; return; }
    const { data } = await COMMUNITY_API.getMembership(state.community.id);
    state.membership = data || null;
    if (!state.membership && state.community.is_private) {
      const { data: jr } = await COMMUNITY_API.getMyJoinRequest(state.community.id);
      state.joinRequest = jr || null;
    }
  }

  async function loadMyCommunities() {
    if (!state.user) { state.myCommunities = []; state.pendingByCommunity = null; return; }
    const { data } = await COMMUNITY_API.listMyCommunities();
    state.myCommunities = data || [];
    try {
      state.pendingByCommunity = await COMMUNITY_API.countMyAdminPending();
    } catch (_) {
      state.pendingByCommunity = null;
    }
  }

  async function loadPendingCount() {
    state.pendingCount = 0;
    if (!state.community || !state.membership) return;
    const role = state.membership.role;
    if (role !== "owner" && role !== "admin") return;
    const { count } = await COMMUNITY_API.countPendingRequests(state.community.id);
    state.pendingCount = count || 0;
  }

  async function loadPosts() {
    if (!state.community) return;
    if (state.community.is_private && !state.membership) {
      state.posts = [];
      renderCenter();
      return;
    }
    const { data, error } = await COMMUNITY_API.listPosts(state.community.id, { sort: state.sort, limit: 30 });
    if (error) {
      $center.innerHTML = `${renderHeader()}<div class="cf-error">${esc(error.message || error)}</div>`;
      wireHeaderButtons();
      return;
    }
    state.posts = data || [];
    if (state.posts.length) {
      const ids = state.posts.map((p) => p.id);
      state.myVotes = await COMMUNITY_API.getMyPostVotes(ids);
      await COMMUNITY_API.attachAuthors(state.posts);
    }
    renderCenter();
  }

  async function reloadCore() {
    await loadCommunity();
    await loadMembership();
    await loadPosts();
    renderRight();
    renderLeft();
  }

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  // Supabase fires auth-state on token refresh, not just sign-in/out.
  // Skip repaint when the signed-in status hasn't changed so the view
  // doesn't flicker and re-issue network requests on a token refresh.
  let lastSignedIn = null;

  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    if (!slug) {
      $center.innerHTML = `<div class="cf-empty"><h2>No community specified</h2><p>Go back to <a href="community.html">the community home</a>.</p></div>`;
      return;
    }
    await Promise.all([loadCommunity(), loadMyCommunities()]);
    if (!state.community) {
      $center.innerHTML = `<div class="cf-empty"><h2>Community not found</h2><p>No community with slug "<code>${esc(slug)}</code>" exists. <a href="community.html">Back to community home</a>.</p></div>`;
      renderLeft();
      return;
    }
    await loadMembership();
    await loadPendingCount();
    renderLeft();
    renderRight();
    await loadPosts();
  }

  function onReady() {
    if (window.__authReady) window.__authReady.then(paint);
    else paint();
    window.addEventListener("auth-state", paint);
    window.addEventListener("profile-state", () => { try { renderLeft(); } catch (_) {} });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();

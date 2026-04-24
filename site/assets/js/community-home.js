// community-home.js — renders the Community home page (merged feed from all
// communities the current user has joined). Three columns: left nav, center
// feed, right popular-communities panel.
//
// Page shell (#cf-left, #cf-center, #cf-right) is in community.html.
// All DB calls go through window.COMMUNITY_API.
(function () {
  "use strict";

  const $left = document.getElementById("cf-left");
  const $center = document.getElementById("cf-center");
  const $right = document.getElementById("cf-right");

  const state = {
    user: null,
    myCommunities: [],
    popular: [],
    feed: [],
    myVotes: {},
    sort: new URL(location.href).searchParams.get("sort") || "new",
    loading: true,
    error: null,
  };

  // ------------------------------------------------------------------
  // Helpers
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

  function iconFor(community) {
    if (community && community.icon_url) {
      return `<span class="cf-side-icon"><img src="${esc(community.icon_url)}" alt=""></span>`;
    }
    const letter = community && community.name ? community.name[0].toUpperCase() : "?";
    return `<span class="cf-side-icon">${esc(letter)}</span>`;
  }

  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return tmp.textContent || "";
  }

  // ------------------------------------------------------------------
  // Left sidebar
  // ------------------------------------------------------------------
  function renderLeft() {
    const myList = (state.myCommunities || [])
      .map((m) => m.communities)
      .filter(Boolean)
      .sort((a, b) => a.name.localeCompare(b.name));

    const myListHtml = myList.length
      ? myList
          .map(
            (c) => `
          <a class="cf-side-link" href="community-view.html?c=${encodeURIComponent(c.slug)}">
            ${iconFor(c)}
            <span>${esc(c.name)}</span>
          </a>`
          )
          .join("")
      : `<div class="cf-side-empty">You haven't joined any communities yet.</div>`;

    $left.innerHTML = `
      <div class="cf-side-section">
        <a class="cf-side-link active" href="community.html">
          <span class="cf-side-icon">☰</span><span>Home</span>
        </a>
        <a class="cf-side-link" href="community.html?sort=top">
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
        ${myListHtml}
      </div>
    `;
  }

  // ------------------------------------------------------------------
  // Right sidebar
  // ------------------------------------------------------------------
  function renderRight() {
    const rows = (state.popular || [])
      .slice(0, 8)
      .map(
        (c) => `
      <a class="cf-panel-row" href="community-view.html?c=${encodeURIComponent(c.slug)}">
        ${iconFor(c)}
        <div class="cf-panel-row-name">
          <strong>${esc(c.name)}</strong>
          <span>${fmt(c.member_count)} members${c.is_private ? " · private" : ""}</span>
        </div>
      </a>`
      )
      .join("");

    $right.innerHTML = `
      <div class="cf-panel">
        <h3>Popular communities</h3>
        ${rows || '<div class="cf-side-empty">No communities yet.</div>'}
        <div style="padding: 10px 0 0;">
          <a class="cf-btn" href="community-create.html" style="width:100%; justify-content:center;">Create a community</a>
        </div>
      </div>
    `;
  }

  // ------------------------------------------------------------------
  // Center
  // ------------------------------------------------------------------
  function renderSortBar(heading) {
    return `
      <div class="cf-main-bar">
        <h1 class="cf-page-title">${esc(heading)}</h1>
        <nav class="cf-sort-tabs" data-sort-nav>
          <a data-sort="new" class="${state.sort === "new" ? "active" : ""}" href="community.html?sort=new">New</a>
          <a data-sort="top" class="${state.sort === "top" ? "active" : ""}" href="community.html?sort=top">Top</a>
        </nav>
      </div>`;
  }

  function renderPost(p) {
    const com = p.communities || {};
    const myVote = state.myVotes[p.id] || 0;
    const snippetRaw = stripHtml(p.body_html).slice(0, 280);
    const snippet = snippetRaw ? esc(snippetRaw) + (snippetRaw.length >= 280 ? "…" : "") : "";
    const buildBadge = p.build_id
      ? `<div class="cf-post-badge-build">📎 <span>Attached build: <strong>${esc(
          (p.build_snapshot && p.build_snapshot.name) || "build"
        )}</strong></span></div>`
      : "";

    const permalink = `community-post.html?p=${p.id}`;

    return `
      <article class="cf-post" data-post-id="${p.id}">
        <div class="cf-post-votes">
          <button class="cf-vote-btn up ${myVote === 1 ? "active" : ""}" data-vote="1" aria-label="Upvote">▲</button>
          <span class="cf-vote-score">${fmt(p.score)}</span>
          <button class="cf-vote-btn down ${myVote === -1 ? "active" : ""}" data-vote="-1" aria-label="Downvote">▼</button>
        </div>
        <div class="cf-post-body">
          <div class="cf-post-meta">
            ${iconFor(com)}
            <a href="community-view.html?c=${encodeURIComponent(com.slug || "")}">${esc(com.name || com.slug || "community")}</a>
            <span class="cf-dot">·</span>
            <span>${ago(p.created_at)}</span>
            ${com.is_private ? `<span class="cf-dot">·</span><span class="cf-badge cf-badge-private">Private</span>` : ""}
          </div>
          <h2 class="cf-post-title"><a href="${permalink}">${esc(p.title)}</a></h2>
          ${buildBadge}
          ${snippet ? `<div class="cf-post-snippet">${snippet}</div>` : ""}
          <div class="cf-post-actions">
            <a href="${permalink}">💬 ${fmt(p.comment_count)} comments</a>
            <button data-action="share">🔗 Share</button>
          </div>
        </div>
      </article>
    `;
  }

  function renderSignedOut() {
    $center.innerHTML = `
      <div class="cf-empty">
        <h2>Community is for members</h2>
        <p>Sign in to join communities, post builds, and reply to discussions.</p>
        <p>
          <a class="cf-btn cf-btn-primary" href="login.html?return=community.html">Sign in</a>
          <a class="cf-btn" href="signup.html">Create an account</a>
        </p>
      </div>
      <div class="cf-main-bar" style="margin-top:32px;">
        <h1 class="cf-page-title">Browse communities</h1>
      </div>
      <div id="cf-browse-grid"></div>
    `;
    renderBrowseGrid();
  }

  function renderBrowseGrid() {
    const wrap = document.getElementById("cf-browse-grid");
    if (!wrap) return;
    if (!state.popular.length) {
      wrap.innerHTML = `<div class="cf-empty"><p>No communities exist yet. <a href="community-create.html">Be the first to create one.</a></p></div>`;
      return;
    }
    wrap.innerHTML = state.popular
      .map(
        (c) => `
      <a class="cf-post" href="community-view.html?c=${encodeURIComponent(c.slug)}" style="grid-template-columns: 56px minmax(0,1fr); text-decoration:none;">
        <div class="cf-post-votes" style="justify-content:center;">
          ${iconFor(c)}
        </div>
        <div class="cf-post-body">
          <div class="cf-post-meta">
            <a>${esc(c.name)}</a>
            <span class="cf-dot">·</span>
            <span>${fmt(c.member_count)} members</span>
            ${c.is_private ? `<span class="cf-dot">·</span><span class="cf-badge cf-badge-private">Private</span>` : ""}
          </div>
          ${c.description ? `<div class="cf-post-snippet">${esc(c.description)}</div>` : ""}
        </div>
      </a>`
      )
      .join("");
  }

  function renderNoJoinedView() {
    $center.innerHTML = `
      ${renderSortBar("Home")}
      <div class="cf-empty">
        <h2>Your feed is empty</h2>
        <p>Join some communities to see their posts here.</p>
        <p>
          <a class="cf-btn cf-btn-primary" href="community-create.html">Create a community</a>
        </p>
      </div>
      <div class="cf-main-bar" style="margin-top:32px;">
        <h2 class="cf-page-title" style="font-size:18px;">Popular right now</h2>
      </div>
      <div id="cf-browse-grid"></div>
    `;
    renderBrowseGrid();
    wireSortTabs();
  }

  function renderFeed() {
    const postsHtml = state.feed.map(renderPost).join("");
    $center.innerHTML = `
      ${renderSortBar("Home")}
      ${postsHtml || '<div class="cf-empty"><p>No posts yet in your communities. Try creating one.</p></div>'}
    `;
    wireSortTabs();
    wireVotes();
    wireShare();
  }

  // ------------------------------------------------------------------
  // Interactions
  // ------------------------------------------------------------------
  function wireSortTabs() {
    $center.querySelectorAll("[data-sort-nav] a").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        state.sort = a.getAttribute("data-sort");
        const url = new URL(location.href);
        url.searchParams.set("sort", state.sort);
        history.replaceState(null, "", url.toString());
        loadFeed();
      });
    });
  }

  function wireVotes() {
    $center.querySelectorAll(".cf-post").forEach((post) => {
      const postId = Number(post.getAttribute("data-post-id"));
      post.querySelectorAll(".cf-vote-btn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.preventDefault();
          if (!state.user) {
            location.href = "login.html?return=community.html";
            return;
          }
          const v = Number(btn.getAttribute("data-vote"));
          const existing = state.myVotes[postId] || 0;
          const next = existing === v ? 0 : v;
          // Optimistic
          const scoreEl = post.querySelector(".cf-vote-score");
          const p = state.feed.find((x) => x.id === postId);
          if (p) {
            p.score = p.score - existing + next;
            scoreEl.textContent = fmt(p.score);
          }
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
        if (navigator.share) {
          try { await navigator.share({ url }); return; } catch (_) {}
        }
        try {
          await navigator.clipboard.writeText(url);
          btn.textContent = "✓ Copied";
          setTimeout(() => (btn.textContent = "🔗 Share"), 1800);
        } catch {
          prompt("Copy this link:", url);
        }
      });
    });
  }

  // ------------------------------------------------------------------
  // Data loads
  // ------------------------------------------------------------------
  async function loadPopular() {
    const { data, error } = await COMMUNITY_API.listCommunities({
      orderBy: "member_count",
      orderDir: "desc",
      limit: 15,
    });
    if (error) {
      console.warn("[community-home] popular fetch error", error);
      state.popular = [];
    } else {
      state.popular = data || [];
    }
    renderRight();
  }

  async function loadMyCommunities() {
    if (!state.user) {
      state.myCommunities = [];
      renderLeft();
      return;
    }
    const { data, error } = await COMMUNITY_API.listMyCommunities();
    if (error) {
      console.warn("[community-home] my communities error", error);
      state.myCommunities = [];
    } else {
      state.myCommunities = data || [];
    }
    renderLeft();
  }

  async function loadFeed() {
    if (!state.user) { renderSignedOut(); return; }
    if (!state.myCommunities.length) { renderNoJoinedView(); return; }

    $center.innerHTML = `${renderSortBar("Home")}<div class="cf-empty">Loading…</div>`;
    wireSortTabs();

    const { data, error } = await COMMUNITY_API.listFeed({ sort: state.sort, limit: 30 });
    if (error) {
      $center.innerHTML = `${renderSortBar("Home")}<div class="cf-error">${esc(error.message || error)}</div>`;
      wireSortTabs();
      return;
    }
    state.feed = data || [];
    if (state.feed.length) {
      const ids = state.feed.map((p) => p.id);
      state.myVotes = await COMMUNITY_API.getMyPostVotes(ids);
    }
    renderFeed();
  }

  // ------------------------------------------------------------------
  // Paint cycle
  // ------------------------------------------------------------------
  // Supabase fires auth-state on token refresh, not just sign-in/out.
  // Skip repaint when the signed-in status hasn't changed so a token
  // refresh doesn't flicker the feed and re-issue network requests.
  let lastSignedIn = null;

  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    renderLeft();
    await Promise.all([loadPopular(), loadMyCommunities()]);
    await loadFeed();
  }

  function onReady() {
    if (window.__authReady) {
      window.__authReady.then(paint);
    } else {
      paint();
    }
    window.addEventListener("auth-state", paint);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();

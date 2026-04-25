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
    pendingByCommunity: null, // Map<communityId, number>
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
  // Left sidebar
  // ------------------------------------------------------------------
  // Split memberships into two lists: "Your communities" = ones the user
  // created (role === "owner"), "Joined communities" = ones they joined
  // but did not create (role member or admin).
  function sideRowHtml(c, activeSlug) {
    const pendingMap = state.pendingByCommunity;
    const n = pendingMap && pendingMap.get ? pendingMap.get(c.id) : 0;
    // cf-notif-badge matches the styled red badge used elsewhere
    // (Messages tab); cf-notify-badge was a typo with no CSS rule.
    const badge = n
      ? `<span class="cf-notif-badge" aria-label="${n} pending join request${n === 1 ? "" : "s"}">${n > 99 ? "99+" : n}</span>`
      : "";
    return `
      <a class="cf-side-link ${activeSlug && c.slug === activeSlug ? "active" : ""}"
         href="community-view.html?c=${encodeURIComponent(c.slug)}">
        ${iconFor(c)}
        <span>${esc(c.name)}</span>
        ${badge}
      </a>`;
  }

  function partitionMemberships(memberships) {
    const owned = [];
    const joined = [];
    (memberships || []).forEach((m) => {
      if (!m || !m.communities) return;
      if (m.role === "owner") owned.push(m.communities);
      else joined.push(m.communities);
    });
    const byName = (a, b) => a.name.localeCompare(b.name);
    owned.sort(byName);
    joined.sort(byName);
    return { owned, joined };
  }

  function myProfileCardHtml() {
    const me = window.__profile || null;
    if (!state.user) {
      return `
        <div class="cf-my-profile-card cf-my-profile-card--signedout">
          <a href="login.html?return=community.html">Sign in</a> to manage your community profile.
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
    const { owned, joined } = partitionMemberships(state.myCommunities);

    const ownedHtml = owned.length
      ? owned.map((c) => sideRowHtml(c)).join("")
      : `<div class="cf-side-empty">You haven't created any communities yet.</div>`;

    const joinedHtml = joined.length
      ? joined.map((c) => sideRowHtml(c)).join("")
      : `<div class="cf-side-empty">You haven't joined any communities yet.</div>`;

    $left.innerHTML = `
      ${myProfileCardHtml()}

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
        <a class="cf-side-link" href="messages.html">
          <span class="cf-side-icon">✉</span><span>Messages</span>
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
            ${iconFor(com)}
            <a href="community-view.html?c=${encodeURIComponent(com.slug || "")}">${esc(com.name || com.slug || "community")}</a>
            <span class="cf-dot">·</span>
            <span>Posted by ${authorLink(p.author)}</span>
            <span class="cf-dot">·</span>
            <span>${ago(p.created_at)}</span>
            ${com.is_private ? `<span class="cf-dot">·</span><span class="cf-badge cf-badge-private">Private</span>` : ""}
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
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const post = btn.closest(".cf-post");
        const id = post.getAttribute("data-post-id");
        const titleEl = post.querySelector(".cf-post-title a");
        const title = titleEl ? titleEl.textContent.trim() : "";
        if (window.CF_SHARE) {
          window.CF_SHARE.open(btn, id, title);
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
      state.pendingByCommunity = null;
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
    await loadPendingByCommunity();
  }

  // Refresh the per-community pending-request totals and re-render the
  // left sidebar. Called on initial load, on realtime events from
  // community_join_requests, and whenever the manage screen dispatches
  // cf-community-pending-change after an approve / deny.
  async function loadPendingByCommunity() {
    if (!state.user) {
      state.pendingByCommunity = null;
      renderLeft();
      return;
    }
    try {
      state.pendingByCommunity = await COMMUNITY_API.countMyAdminPending();
    } catch (_) {
      state.pendingByCommunity = null;
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
      await COMMUNITY_API.attachAuthors(state.feed);
    }
    renderFeed();
  }

  // ------------------------------------------------------------------
  // Live sync — Supabase realtime channel for new posts in the user's
  // joined communities. RLS already filters out posts in private
  // communities the viewer doesn't belong to, but for the merged
  // home feed we additionally check community_id against the joined
  // list so unrelated public-community posts don't bleed in.
  // ------------------------------------------------------------------
  let realtimeChannel = null;

  function startRealtime() {
    stopRealtime();
    if (!state.user || !window.__supabase) return;
    const joinedIds = new Set(
      (state.myCommunities || [])
        .map((m) => m.communities && m.communities.id)
        .filter(Boolean)
    );
    realtimeChannel = window.__supabase
      .channel("home-feed-" + state.user.id)
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "community_posts" },
        async (payload) => {
          const p = payload.new;
          if (!p || p.is_deleted) return;
          if (!joinedIds.has(p.community_id)) return;
          if (state.feed.some((x) => x.id === p.id)) return;
          // Refetch the row with its joined community block (the
          // realtime payload doesn't carry it) and pop it onto the
          // top of the feed.
          const { data } = await COMMUNITY_API.getPost(p.id).catch(() => ({ data: null }));
          if (!data) return;
          await COMMUNITY_API.attachAuthors([data]);
          if (state.sort === "new") state.feed.unshift(data);
          else state.feed.push(data);
          renderFeed();
        }
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "community_join_requests" },
        () => { loadPendingByCommunity(); }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "community_posts" },
        (payload) => {
          const p = payload.new;
          if (!p) return;
          const i = state.feed.findIndex((x) => x.id === p.id);
          if (i === -1) return;
          if (p.is_deleted) {
            state.feed.splice(i, 1);
            renderFeed();
            return;
          }
          // Patch in score / comment_count without disturbing the
          // attached community + author blocks the feed renderer needs.
          state.feed[i] = { ...state.feed[i], ...p, communities: state.feed[i].communities, author: state.feed[i].author };
          // Update the score / comments badge in place to avoid blowing
          // away listeners on the rest of the feed.
          const card = $center.querySelector('.cf-post[data-post-id="' + p.id + '"]');
          if (card) {
            const sc = card.querySelector(".cf-vote-score");
            if (sc) sc.textContent = fmt(p.score);
            const cm = card.querySelector('.cf-post-actions a[href^="community-post.html?p="]');
            if (cm) cm.textContent = "💬 " + fmt(p.comment_count) + " comments";
          }
        }
      )
      .subscribe();
  }

  function stopRealtime() {
    if (realtimeChannel && window.__supabase) {
      try { window.__supabase.removeChannel(realtimeChannel); } catch (_) {}
    }
    realtimeChannel = null;
  }

  window.addEventListener("beforeunload", stopRealtime);

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
    startRealtime();
  }

  function onReady() {
    if (window.__authReady) {
      window.__authReady.then(paint);
    } else {
      paint();
    }
    window.addEventListener("auth-state", paint);
    // Re-render the sidebar when the cached profile changes (username
    // save, avatar/banner upload) so the My profile card stays current.
    window.addEventListener("profile-state", () => { try { renderLeft(); } catch (_) {} });
    // community-manage.js dispatches this after approve / deny, so the
    // home-page sidebar's red badge counts down right away instead of
    // waiting for realtime to redeliver the row update.
    window.addEventListener("cf-community-pending-change", () => { loadPendingByCommunity(); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();

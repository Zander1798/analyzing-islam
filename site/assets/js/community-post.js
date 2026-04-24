// community-post.js — single-post page: renders one post, its attached
// build (if any), vote controls, share, and the threaded comment tree.
//
// Usage: community-post.html?p=<post-id>
// Enforcement: Supabase RLS policies already block viewing posts/comments
// on private communities you aren't a member of; this file just mirrors
// that outcome in the UI.
(function () {
  "use strict";

  const $left = document.getElementById("cf-left");
  const $center = document.getElementById("cf-center");
  const $right = document.getElementById("cf-right");

  const params = new URLSearchParams(location.search);
  const postId = Number(params.get("p") || 0);

  const state = {
    user: null,
    post: null,
    community: null,
    membership: null,
    myCommunities: [],
    comments: [],
    myPostVote: 0,
    myCommentVotes: {},
    replyingTo: null, // comment id currently being replied to
    pendingByCommunity: null, // Map<communityId, number>
  };

  // ------------------------------------------------------------------
  // Shared helpers (mirrors other community pages)
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

  // ------------------------------------------------------------------
  // Sidebars
  // ------------------------------------------------------------------
  function renderLeft() {
    const myList = (state.myCommunities || [])
      .map((m) => m.communities)
      .filter(Boolean)
      .sort((a, b) => a.name.localeCompare(b.name));
    const currentSlug = state.community && state.community.slug;
    const pendingMap = state.pendingByCommunity;
    const myListHtml = myList.length
      ? myList.map((c) => {
          const n = pendingMap && pendingMap.get ? pendingMap.get(c.id) : 0;
          const badge = n ? `<span class="cf-notify-badge" title="${n} pending join request${n === 1 ? "" : "s"}">${n}</span>` : "";
          return `
          <a class="cf-side-link ${c.slug === currentSlug ? "active" : ""}" href="community-view.html?c=${encodeURIComponent(c.slug)}">
            ${iconFor(c)}<span>${esc(c.name)}</span>${badge}
          </a>`;
        }).join("")
      : `<div class="cf-side-empty">You haven't joined any communities.</div>`;

    $left.innerHTML = `
      <div class="cf-side-section">
        <a class="cf-side-link" href="community.html"><span class="cf-side-icon">☰</span><span>Home</span></a>
        <a class="cf-side-link" href="community.html?sort=top"><span class="cf-side-icon">★</span><span>Popular</span></a>
        <a class="cf-side-link" href="community-create.html"><span class="cf-side-icon">+</span><span>Create community</span></a>
      </div>
      <div class="cf-side-section">
        <p class="cf-side-label">Your communities</p>
        ${myListHtml}
      </div>`;
  }

  function renderRight() {
    if (!state.community) { $right.innerHTML = ""; return; }
    const c = state.community;
    $right.innerHTML = `
      <div class="cf-panel">
        <h3>About ${esc(c.name)}</h3>
        <p style="color:var(--text-muted); font-size:13px; margin:0 0 8px;">${esc(c.description || "No description.")}</p>
        ${c.is_private ? `<p><span class="cf-badge cf-badge-private">Private</span></p>` : ""}
        <div class="cf-about-stats">
          <div class="cf-about-stat"><strong>${fmt(c.member_count)}</strong><span>Members</span></div>
          <div class="cf-about-stat"><strong>${fmt(c.post_count)}</strong><span>Posts</span></div>
        </div>
        <div style="margin-top:10px;">
          <a class="cf-btn" href="community-view.html?c=${encodeURIComponent(c.slug)}" style="width:100%; justify-content:center;">Go to community</a>
        </div>
      </div>`;
  }

  // ------------------------------------------------------------------
  // Center — the post
  // ------------------------------------------------------------------
  function renderNotFound(kind = "Post") {
    $center.innerHTML = `
      <div class="cf-empty">
        <h2>${esc(kind)} not found</h2>
        <p>It may have been deleted, or you might not have permission to view it.</p>
        <a class="cf-btn" href="community.html">Back to community home</a>
      </div>`;
  }

  function renderPostHtml() {
    const p = state.post;
    const c = state.community;
    const v = state.myPostVote || 0;
    const buildBlock = p.build_snapshot
      ? `<div class="cf-attached-build">
           <div class="cf-attached-build-header">
             <h4>Attached build</h4>
             <strong>${esc(p.build_snapshot.name || "Build")}</strong>
           </div>
           <div class="cf-attached-build-body ql-snow">
             <div class="ql-editor" style="padding:0;">${p.build_snapshot.content_html || ""}</div>
           </div>
         </div>`
      : "";
    const canDelete =
      state.user && (
        state.user.id === p.author_id ||
        (state.membership && (state.membership.role === "owner" || state.membership.role === "admin"))
      );

    return `
      <article class="cf-post-full" data-post-id="${p.id}">
        <div class="cf-post-votes">
          <button class="cf-vote-btn up ${v === 1 ? "active" : ""}" data-vote="1" aria-label="Upvote">▲</button>
          <span class="cf-vote-score">${fmt(p.score)}</span>
          <button class="cf-vote-btn down ${v === -1 ? "active" : ""}" data-vote="-1" aria-label="Downvote">▼</button>
        </div>
        <div class="cf-post-body">
          <div class="cf-post-meta">
            ${iconFor(c)}
            <a href="community-view.html?c=${encodeURIComponent(c.slug)}">${esc(c.name)}</a>
            <span class="cf-dot">·</span>
            <span>Posted ${ago(p.created_at)}</span>
            ${c.is_private ? `<span class="cf-dot">·</span><span class="cf-badge cf-badge-private">Private</span>` : ""}
          </div>
          <h1 class="cf-post-title">${esc(p.title)}</h1>
          ${p.body_html ? `<div class="cf-post-full-content ql-snow"><div class="ql-editor" style="padding:0;">${p.body_html}</div></div>` : ""}
          ${buildBlock}
          <div class="cf-post-actions">
            <span data-role="comment-count">💬 ${fmt((state.comments || []).length)} comments</span>
            <button data-action="share">🔗 Share</button>
            ${state.user ? `<button data-action="report">⚑ Report</button>` : ""}
            ${canDelete ? `<button data-action="delete" class="cf-btn-danger" style="color:var(--strong);">🗑 Delete</button>` : ""}
          </div>
        </div>
      </article>
    `;
  }

  function renderCommentComposer() {
    if (!state.user) {
      return `<div class="cf-comments-section">
        <h3>Comments</h3>
        <p style="color:var(--text-muted); font-size:14px;">
          <a href="login.html?return=${encodeURIComponent(location.pathname + location.search)}">Sign in</a> to comment.
        </p>
      </div>`;
    }
    if (!state.membership) {
      return `<div class="cf-comments-section">
        <h3>Comments</h3>
        <p style="color:var(--text-muted); font-size:14px;">
          Join <a href="community-view.html?c=${encodeURIComponent(state.community.slug)}">${esc(state.community.name)}</a> to comment.
        </p>
        ${renderCommentTree()}
      </div>`;
    }
    return `
      <div class="cf-comments-section">
        <h3>Comments</h3>
        <div class="cf-comment-composer" data-parent="">
          <textarea placeholder="What are your thoughts?" maxlength="10000"></textarea>
          <div class="cf-comment-composer-actions">
            <button class="cf-btn cf-btn-primary" data-action="submit-comment">Comment</button>
          </div>
        </div>
        ${renderCommentTree()}
      </div>
    `;
  }

  // Build a tree from the flat comment list.
  function buildTree() {
    const byId = {};
    const roots = [];
    (state.comments || []).forEach((c) => {
      byId[c.id] = { ...c, children: [] };
    });
    Object.values(byId).forEach((c) => {
      if (c.parent_comment_id && byId[c.parent_comment_id]) {
        byId[c.parent_comment_id].children.push(c);
      } else {
        roots.push(c);
      }
    });
    return roots;
  }

  function renderCommentNode(c) {
    const myVote = state.myCommentVotes[c.id] || 0;
    const canDelete =
      state.user && (
        state.user.id === c.author_id ||
        (state.membership && (state.membership.role === "owner" || state.membership.role === "admin"))
      );
    const children = (c.children || []).map(renderCommentNode).join("");
    const depth = Math.min(Number(c.depth) || 0, 5);
    const canReply = state.user && state.membership && depth < 5;

    const replyBox =
      state.replyingTo === c.id
        ? `<div class="cf-comment-composer" data-parent="${c.id}" style="margin-top:10px;">
             <textarea placeholder="Reply…" maxlength="10000"></textarea>
             <div class="cf-comment-composer-actions">
               <button class="cf-btn" data-action="cancel-reply">Cancel</button>
               <button class="cf-btn cf-btn-primary" data-action="submit-reply">Reply</button>
             </div>
           </div>`
        : "";

    return `
      <div class="cf-comment" data-depth="${depth}" data-comment-id="${c.id}">
        <div class="cf-comment-head">
          <strong>user</strong>
          <span>· ${ago(c.created_at)}</span>
        </div>
        <div class="cf-comment-body">${esc(c.body)}</div>
        <div class="cf-comment-actions">
          <button class="cf-vote-btn up ${myVote === 1 ? "active" : ""}" data-vote="1" aria-label="Upvote">▲</button>
          <span class="cf-vote-score">${fmt(c.score)}</span>
          <button class="cf-vote-btn down ${myVote === -1 ? "active" : ""}" data-vote="-1" aria-label="Downvote">▼</button>
          ${canReply ? `<button data-action="reply">💬 Reply</button>` : ""}
          ${state.user ? `<button data-action="report">⚑ Report</button>` : ""}
          ${canDelete ? `<button data-action="delete" style="color:var(--strong);">🗑 Delete</button>` : ""}
        </div>
        ${replyBox}
        ${children}
      </div>`;
  }

  function renderCommentTree() {
    const tree = buildTree();
    if (!tree.length) {
      return `<div class="cf-comment-tree"><div class="cf-manage-empty">No comments yet. Be the first.</div></div>`;
    }
    return `<div class="cf-comment-tree">${tree.map(renderCommentNode).join("")}</div>`;
  }

  // ------------------------------------------------------------------
  // Paint
  // ------------------------------------------------------------------
  function renderAll() {
    renderLeft();
    renderRight();
    if (!state.post || !state.community) { renderNotFound(); return; }
    $center.innerHTML = `
      ${renderPostHtml()}
      ${renderCommentComposer()}
    `;
    wireAll();
  }

  // Re-render ONLY the comments section (used after local delete/submit
  // and by the poller when another user's comment activity changes the
  // list). Preserves any draft text the user has typed into composers.
  function renderCommentsSection() {
    const section = $center.querySelector(".cf-comments-section");
    if (!section) { renderAll(); return; }

    // Snapshot draft text + which composers are open so we can restore.
    const drafts = {};
    $center.querySelectorAll(".cf-comment-composer").forEach((c) => {
      const parent = c.getAttribute("data-parent") || "";
      const ta = c.querySelector("textarea");
      if (ta && ta.value.trim()) drafts[parent] = ta.value;
    });

    section.outerHTML = renderCommentComposer();

    // Restore drafts.
    Object.entries(drafts).forEach(([parent, value]) => {
      const c = $center.querySelector('.cf-comment-composer[data-parent="' + parent + '"] textarea');
      if (c) c.value = value;
    });

    // Update the displayed count on the post-actions bar.
    const countEl = $center.querySelector('[data-role="comment-count"]');
    if (countEl) countEl.textContent = "💬 " + fmt((state.comments || []).length) + " comments";

    wireComments();
  }

  // ------------------------------------------------------------------
  // Interactions
  // ------------------------------------------------------------------
  function wireAll() {
    // Post-level vote
    $center.querySelectorAll(".cf-post-full .cf-vote-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!state.user) { location.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search); return; }
        const v = Number(btn.getAttribute("data-vote"));
        const next = state.myPostVote === v ? 0 : v;
        const post = $center.querySelector(".cf-post-full");
        state.post.score = state.post.score - state.myPostVote + next;
        state.myPostVote = next;
        post.querySelector(".cf-vote-score").textContent = fmt(state.post.score);
        post.querySelectorAll(".cf-vote-btn").forEach((b) => {
          const bv = Number(b.getAttribute("data-vote"));
          b.classList.toggle("active", next !== 0 && bv === next);
        });
        await COMMUNITY_API.votePost(state.post.id, next);
      });
    });

    // Post share / report / delete
    const postEl = $center.querySelector(".cf-post-full");
    if (postEl) {
      const shareBtn = postEl.querySelector('[data-action="share"]');
      const reportBtn = postEl.querySelector('[data-action="report"]');
      const deleteBtn = postEl.querySelector('[data-action="delete"]');
      if (shareBtn) shareBtn.addEventListener("click", sharePost);
      if (reportBtn) reportBtn.addEventListener("click", reportPost);
      if (deleteBtn) deleteBtn.addEventListener("click", deletePost);
    }

    wireComments();
  }

  // Split out so renderCommentsSection() can re-wire the comment listeners
  // without rebinding the post-level vote/share/delete handlers.
  function wireComments() {
    // Top-level comment submit
    const topComposer = $center.querySelector('.cf-comment-composer[data-parent=""]');
    if (topComposer) {
      topComposer.querySelector('[data-action="submit-comment"]').addEventListener("click", () => submitComment(null, topComposer));
    }

    // Per-comment actions
    $center.querySelectorAll(".cf-comment").forEach((node) => {
      const cid = Number(node.getAttribute("data-comment-id"));

      node.querySelectorAll(":scope > .cf-comment-actions .cf-vote-btn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.preventDefault();
          e.stopPropagation();
          if (!state.user) { location.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search); return; }
          const v = Number(btn.getAttribute("data-vote"));
          const existing = state.myCommentVotes[cid] || 0;
          const next = existing === v ? 0 : v;
          const scoreEl = node.querySelector(":scope > .cf-comment-actions > .cf-vote-score");
          const c = state.comments.find((x) => x.id === cid);
          if (c) { c.score = c.score - existing + next; scoreEl.textContent = fmt(c.score); }
          state.myCommentVotes[cid] = next;
          node.querySelectorAll(":scope > .cf-comment-actions .cf-vote-btn").forEach((b) => {
            const bv = Number(b.getAttribute("data-vote"));
            b.classList.toggle("active", next !== 0 && bv === next);
          });
          await COMMUNITY_API.voteComment(cid, next);
        });
      });

      const replyBtn = node.querySelector(':scope > .cf-comment-actions [data-action="reply"]');
      if (replyBtn) replyBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        state.replyingTo = state.replyingTo === cid ? null : cid;
        renderAll();
      });

      const cancelReplyBtn = node.querySelector(':scope > .cf-comment-composer [data-action="cancel-reply"]');
      if (cancelReplyBtn) cancelReplyBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        state.replyingTo = null;
        renderAll();
      });

      const submitReplyBtn = node.querySelector(':scope > .cf-comment-composer [data-action="submit-reply"]');
      if (submitReplyBtn) submitReplyBtn.addEventListener("click", () => {
        const composer = node.querySelector(":scope > .cf-comment-composer");
        submitComment(cid, composer);
      });

      const reportBtn = node.querySelector(':scope > .cf-comment-actions [data-action="report"]');
      if (reportBtn) reportBtn.addEventListener("click", () => reportComment(cid));

      const deleteBtn = node.querySelector(':scope > .cf-comment-actions [data-action="delete"]');
      if (deleteBtn) deleteBtn.addEventListener("click", () => deleteComment(cid));
    });
  }

  async function submitComment(parentId, composerEl) {
    const textarea = composerEl.querySelector("textarea");
    const body = textarea.value.trim();
    if (!body) return;
    textarea.disabled = true;
    const { data, error } = await COMMUNITY_API.createComment({
      postId: state.post.id,
      parentCommentId: parentId,
      body,
    });
    textarea.disabled = false;
    if (error) { alert("Comment failed: " + (error.message || error)); return; }
    state.comments.push(data);
    state.post.comment_count = (state.post.comment_count || 0) + 1;
    state.replyingTo = null;
    renderAll();
  }

  async function sharePost() {
    const url = new URL(`community-post.html?p=${state.post.id}`, location.href).toString();
    if (navigator.share) { try { await navigator.share({ url }); return; } catch (_) {} }
    try {
      await navigator.clipboard.writeText(url);
      const btn = $center.querySelector('.cf-post-full [data-action="share"]');
      if (btn) {
        btn.textContent = "✓ Copied";
        setTimeout(() => (btn.textContent = "🔗 Share"), 1800);
      }
    } catch { prompt("Copy this link:", url); }
  }

  async function reportPost() {
    const reason = prompt("Reason (grotesque / violent / sexual / spam / harassment / other):", "other");
    if (!reason) return;
    const ok = ["grotesque","violent","sexual","spam","harassment","other"].includes(reason);
    if (!ok) { alert("Unknown reason."); return; }
    const detail = prompt("Extra detail (optional):", "") || "";
    const { error } = await COMMUNITY_API.reportPost(state.post.id, reason, detail);
    if (error) { alert("Report failed: " + (error.message || error)); return; }
    alert("Thanks — the admin will review this.");
  }

  async function reportComment(commentId) {
    const reason = prompt("Reason (grotesque / violent / sexual / spam / harassment / other):", "other");
    if (!reason) return;
    const ok = ["grotesque","violent","sexual","spam","harassment","other"].includes(reason);
    if (!ok) { alert("Unknown reason."); return; }
    const detail = prompt("Extra detail (optional):", "") || "";
    const { error } = await COMMUNITY_API.reportComment(commentId, reason, detail);
    if (error) { alert("Report failed: " + (error.message || error)); return; }
    alert("Thanks — the admin will review this.");
  }

  async function deletePost() {
    if (!confirm("Delete this post? This can't be undone.")) return;
    const { error } = await COMMUNITY_API.softDeletePost(state.post.id);
    if (error) { alert("Delete failed: " + (error.message || error)); return; }
    location.href = "community-view.html?c=" + encodeURIComponent(state.community.slug);
  }

  async function deleteComment(commentId) {
    if (!confirm("Delete this comment?")) return;
    const { error } = await COMMUNITY_API.softDeleteComment(commentId);
    if (error) { alert("Delete failed: " + (error.message || error)); return; }
    state.comments = state.comments.filter((c) => c.id !== commentId);
    if (state.post) {
      state.post.comment_count = Math.max(0, (state.post.comment_count || 0) - 1);
    }
    renderCommentsSection();
  }

  // ------------------------------------------------------------------
  // Loads
  // ------------------------------------------------------------------
  async function loadPost() {
    const { data, error } = await COMMUNITY_API.getPost(postId);
    if (error || !data) { state.post = null; state.community = null; return; }
    state.post = data;
    state.community = data.communities || null;
  }

  async function loadMembership() {
    state.membership = null;
    if (!state.user || !state.community) return;
    const { data } = await COMMUNITY_API.getMembership(state.community.id);
    state.membership = data || null;
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

  async function loadComments() {
    if (!state.post) { state.comments = []; return; }
    const { data } = await COMMUNITY_API.listComments(state.post.id);
    state.comments = data || [];
  }

  async function loadMyVotes() {
    if (!state.user || !state.post) { state.myPostVote = 0; state.myCommentVotes = {}; return; }
    state.myPostVote = await COMMUNITY_API.getMyPostVote(state.post.id);
    const commentIds = state.comments.map((c) => c.id);
    state.myCommentVotes = await COMMUNITY_API.getMyCommentVotes(commentIds);
  }

  // ------------------------------------------------------------------
  // Live sync (poll for deletes/inserts by other users)
  // ------------------------------------------------------------------
  // Every ~10 s while the tab is visible, refetch the comment list. If
  // the set has changed (a comment was deleted or added by someone in
  // another tab / browser), re-render just the comments section so the
  // current view updates without the user having to refresh.
  const COMMENT_POLL_MS = 10000;
  let commentPollTimer = null;

  function startCommentPoll() {
    stopCommentPoll();
    if (!state.post) return;
    if (document.hidden) return;
    commentPollTimer = setInterval(syncCommentsIfChanged, COMMENT_POLL_MS);
  }

  function stopCommentPoll() {
    if (commentPollTimer) {
      clearInterval(commentPollTimer);
      commentPollTimer = null;
    }
  }

  async function syncCommentsIfChanged() {
    if (!state.post) return;
    const { data, error } = await COMMUNITY_API.listComments(state.post.id);
    if (error) return;
    const next = data || [];
    // Cheap fingerprint over (id, score) — detects deletes, inserts,
    // and vote-count drift without needing a deep diff.
    const signature = (arr) =>
      arr.map((c) => c.id + ":" + (c.score || 0)).join(",");
    if (signature(state.comments) === signature(next)) return;

    state.comments = next;
    // Refresh my vote map so any new comments don't appear unvoted
    // forever and existing votes stay highlighted.
    if (state.user) {
      const ids = next.map((c) => c.id);
      state.myCommentVotes = await COMMUNITY_API.getMyCommentVotes(ids);
    }
    if (state.post) {
      state.post.comment_count = next.length;
    }
    renderCommentsSection();
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopCommentPoll();
    else startCommentPoll();
  });
  window.addEventListener("beforeunload", stopCommentPoll);

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  // Supabase fires auth-state on token refresh, not just sign-in/out.
  // Skip repaint when the signed-in status hasn't changed so the in-
  // progress comment draft isn't wiped on a token refresh.
  let lastSignedIn = null;

  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    if (!postId) { renderNotFound(); return; }
    await loadPost();
    if (!state.post) { renderAll(); return; }
    await Promise.all([loadMembership(), loadMyCommunities(), loadComments()]);
    await loadMyVotes();
    renderAll();
    startCommentPoll();
  }

  function onReady() {
    if (window.__authReady) window.__authReady.then(paint);
    else paint();
    window.addEventListener("auth-state", paint);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();

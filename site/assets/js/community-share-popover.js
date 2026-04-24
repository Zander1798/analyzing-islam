/* =============================================================
   Analyzing Islam — Share-to-friend popover
   -------------------------------------------------------------
   Replaces the legacy clipboard-only share button on community
   posts. Clicking 🔗 Share now opens a small popover anchored
   to the button containing:
     - search box (filter friends by username)
     - friend list (avatar + @username + Send button)
     - "Copy link" fallback
   Sending a friend the post creates / opens a DM thread with
   them and posts the post URL into it.

   Public API:
     CF_SHARE.open(button, postId, postTitle?)
     CF_SHARE.close()
   ============================================================= */
(function () {
  "use strict";

  let popover = null;       // root element
  let anchor = null;        // current anchor button
  let postUrl = null;
  let postTitle = "";
  let friendsCache = null;  // lazy-loaded list

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  function buildPopover() {
    const el = document.createElement("div");
    el.className = "cf-share-popover";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "Share post");
    el.innerHTML = `
      <input type="search" class="cf-share-search" placeholder="Search friends…" autocomplete="off">
      <div class="cf-share-list" data-role="list">
        <div class="cf-share-empty">Loading friends…</div>
      </div>
      <button type="button" class="cf-share-copy" data-role="copy">🔗 Copy link</button>`;
    document.body.appendChild(el);
    return el;
  }

  function position() {
    if (!popover || !anchor) return;
    const r = anchor.getBoundingClientRect();
    const pad = 8;
    const docW = document.documentElement.clientWidth;
    const docH = document.documentElement.clientHeight;
    // Place below by default; flip above if no room.
    popover.style.visibility = "hidden";
    popover.style.display = "block";
    const pw = popover.offsetWidth;
    const ph = popover.offsetHeight;
    let top = r.bottom + window.scrollY + pad;
    if (r.bottom + ph + pad > docH) top = r.top + window.scrollY - ph - pad;
    let left = r.left + window.scrollX;
    if (left + pw > docW + window.scrollX - pad) left = docW + window.scrollX - pw - pad;
    if (left < window.scrollX + pad) left = window.scrollX + pad;
    popover.style.top = top + "px";
    popover.style.left = left + "px";
    popover.style.visibility = "";
  }

  async function loadFriends() {
    if (!window.COMMUNITY_API || typeof COMMUNITY_API.listMyFriends !== "function") {
      return [];
    }
    const { data } = await COMMUNITY_API.listMyFriends();
    return (data || [])
      .filter((r) => r.peer && r.peer.username)
      .sort((a, b) => a.peer.username.localeCompare(b.peer.username));
  }

  function renderList(query) {
    const list = popover.querySelector('[data-role="list"]');
    const friends = friendsCache || [];
    const needle = (query || "").trim().toLowerCase();
    const filtered = needle
      ? friends.filter((f) => f.peer.username.toLowerCase().includes(needle))
      : friends;
    if (!friends.length) {
      list.innerHTML = `<div class="cf-share-empty">You don't have any friends yet. <a href="community.html">Find some →</a></div>`;
      return;
    }
    if (!filtered.length) {
      list.innerHTML = `<div class="cf-share-empty">No friend matches "${esc(query || "")}".</div>`;
      return;
    }
    list.innerHTML = filtered.map((f) => {
      const u = f.peer;
      const avatar = u.avatar_url
        ? `<img src="${esc(u.avatar_url)}" alt="">`
        : esc((u.username || "?")[0].toUpperCase());
      return `
        <div class="cf-share-row" data-peer-id="${esc(u.id)}" data-username="${esc(u.username)}">
          <span class="cf-share-avatar">${avatar}</span>
          <span class="cf-share-name">@${esc(u.username)}</span>
          <button type="button" class="cf-share-send" data-role="send">Send</button>
        </div>`;
    }).join("");
  }

  async function sendToPeer(peerId, peerUsername, rowEl) {
    const sendBtn = rowEl.querySelector('[data-role="send"]');
    if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = "Sending…"; }
    try {
      const { threadId, error: tErr } = await COMMUNITY_API.startOrGetDM(peerId);
      if (tErr || !threadId) throw tErr || new Error("Couldn't open thread.");
      const body = postTitle ? `${postTitle}\n${postUrl}` : postUrl;
      const { error: mErr } = await COMMUNITY_API.sendMessage({ threadId, body });
      if (mErr) throw mErr;
      if (sendBtn) {
        sendBtn.textContent = "✓ Sent";
        sendBtn.classList.add("is-sent");
      }
      // Tell the sidebar badge / messages.js something changed.
      window.dispatchEvent(new CustomEvent("cf-messages-notif-change"));
    } catch (e) {
      if (sendBtn) {
        sendBtn.disabled = false;
        sendBtn.textContent = "Retry";
      }
      alert("Couldn't share with @" + peerUsername + ": " + (e.message || e));
    }
  }

  async function copyLink(btn) {
    btn.disabled = true;
    try {
      await navigator.clipboard.writeText(postUrl);
      btn.textContent = "✓ Link copied";
    } catch {
      try { prompt("Copy this link:", postUrl); } catch (_) {}
      btn.textContent = "🔗 Copy link";
    }
    setTimeout(() => {
      if (!popover) return;
      btn.disabled = false;
      btn.textContent = "🔗 Copy link";
    }, 1600);
  }

  function wirePopoverEvents() {
    const search = popover.querySelector(".cf-share-search");
    search.addEventListener("input", () => renderList(search.value));
    search.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });

    popover.addEventListener("click", (e) => {
      const sendBtn = e.target.closest('[data-role="send"]');
      if (sendBtn) {
        const row = sendBtn.closest(".cf-share-row");
        const peerId = row.getAttribute("data-peer-id");
        const username = row.getAttribute("data-username");
        sendToPeer(peerId, username, row);
        return;
      }
      const copyBtn = e.target.closest('[data-role="copy"]');
      if (copyBtn) copyLink(copyBtn);
    });
  }

  function onDocClick(e) {
    if (!popover) return;
    if (popover.contains(e.target)) return;
    if (anchor && anchor.contains(e.target)) return;
    close();
  }

  function onKey(e) {
    if (e.key === "Escape") close();
  }

  function onResize() { position(); }

  async function open(btn, postId, title) {
    if (popover && anchor === btn) { close(); return; }
    close();
    anchor = btn;
    postUrl = new URL(`community-post.html?p=${postId}`, location.href).toString();
    postTitle = title || "";

    popover = buildPopover();
    wirePopoverEvents();
    position();
    setTimeout(() => {
      document.addEventListener("click", onDocClick, true);
      document.addEventListener("keydown", onKey);
      window.addEventListener("resize", onResize);
      window.addEventListener("scroll", onResize, true);
    }, 0);

    if (friendsCache === null) {
      friendsCache = await loadFriends();
    }
    if (popover) renderList("");
    const search = popover && popover.querySelector(".cf-share-search");
    if (search) search.focus();
  }

  function close() {
    if (!popover) return;
    document.removeEventListener("click", onDocClick, true);
    document.removeEventListener("keydown", onKey);
    window.removeEventListener("resize", onResize);
    window.removeEventListener("scroll", onResize, true);
    popover.remove();
    popover = null;
    anchor = null;
  }

  // Refresh cached friends on auth changes / when a friendship is
  // accepted while the page is open.
  window.addEventListener("auth-state", () => { friendsCache = null; });

  window.CF_SHARE = { open, close };
})();

/* =============================================================
   Analyzing Islam — Direct messenger
   -------------------------------------------------------------
   Two-pane inbox. Left column: thread list. Right column: active
   chat. A Requests panel in the header shows pending incoming
   friend requests with Accept / Decline.

   Threads and messages are gated to accepted friends by RLS +
   start_or_get_dm RPC (see supabase/messenger-schema.sql).
   ============================================================= */
(function () {
  "use strict";

  const shell = document.getElementById("cf-messages-shell");
  const urlParams = new URLSearchParams(location.search);

  const state = {
    user: null,
    threads: [],
    activeThreadId: urlParams.get("t") ? Number(urlParams.get("t")) : null,
    activeThread: null,
    messages: [],
    requestsOpen: false,
    requests: [],             // pending incoming
    reqProfiles: {},           // user_id -> { username, avatar_url }
    draftAttachments: [],      // uploads queued on the composer
    pollTimer: null,
  };

  // ---------- Utilities ----------
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }
  function ago(ts) {
    if (!ts) return "";
    const d = new Date(ts);
    const s = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
    if (s < 60) return s + "s";
    if (s < 3600) return Math.floor(s / 60) + "m";
    if (s < 86400) return Math.floor(s / 3600) + "h";
    if (s < 604800) return Math.floor(s / 86400) + "d";
    return d.toLocaleDateString();
  }
  function fmtTime(ts) {
    try {
      return new Date(ts).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
    } catch { return ""; }
  }
  function urlRe() {
    // Naive URL matcher — good enough for auto-linking message text.
    return /\bhttps?:\/\/[^\s<]+/gi;
  }
  function linkify(text) {
    if (!text) return "";
    const safe = esc(text);
    return safe.replace(urlRe(), (m) =>
      `<a href="${m}" target="_blank" rel="noopener noreferrer">${m}</a>`
    );
  }

  // ---------- Renderers ----------
  function renderSignedOut() {
    shell.innerHTML = `
      <div class="cf-messages-empty">
        <h1>Messages</h1>
        <p>Sign in to see your direct messages and friend requests.</p>
        <div style="margin-top:14px; display:flex; gap:10px; justify-content:center;">
          <a class="cf-btn cf-btn-primary" href="login.html?return=messages.html">Sign in</a>
          <a class="cf-btn" href="signup.html">Create account</a>
        </div>
      </div>`;
  }

  function renderShell() {
    shell.innerHTML = `
      <div class="cf-messages">
        <aside class="cf-messages-inbox">
          <div class="cf-messages-inbox-head">
            <h1>Messages</h1>
            <button type="button" class="cf-btn cf-messages-requests-btn" data-action="open-requests">
              Requests <span class="cf-requests-count" data-role="req-count">0</span>
            </button>
          </div>
          <div class="cf-messages-thread-list" data-role="thread-list">
            <div class="cf-empty" style="padding:20px;">Loading threads…</div>
          </div>
        </aside>
        <section class="cf-messages-chat" data-role="chat">
          <div class="cf-messages-chat-empty">
            <p>Select a conversation to start messaging.</p>
          </div>
        </section>
      </div>

      <div class="cf-requests-panel" data-role="requests-panel" hidden>
        <div class="cf-requests-panel-inner">
          <div class="cf-requests-panel-head">
            <h2>Friend requests</h2>
            <button type="button" class="cf-btn" data-action="close-requests">Close</button>
          </div>
          <div class="cf-requests-list" data-role="requests-list">
            <div class="cf-empty" style="padding:20px;">Loading requests…</div>
          </div>
        </div>
      </div>
    `;

    shell.querySelector('[data-action="open-requests"]').addEventListener("click", openRequests);
    shell.querySelector('[data-action="close-requests"]').addEventListener("click", closeRequests);
  }

  function renderThreadList() {
    const list = shell.querySelector('[data-role="thread-list"]');
    if (!list) return;
    if (!state.threads.length) {
      list.innerHTML = `
        <div class="cf-messages-threads-empty">
          <p><strong>No conversations yet.</strong></p>
          <p>Add a friend and click <em>Message</em> on their profile to start chatting.</p>
        </div>`;
      return;
    }
    list.innerHTML = state.threads.map((t) => {
      const p = t.peer || {};
      const name = p.username ? "@" + p.username : "(user)";
      const avatar = p.avatar_url
        ? `<img src="${esc(p.avatar_url)}" alt="">`
        : `<span>${esc((p.username || "?")[0].toUpperCase())}</span>`;
      const preview = t.last_message_preview || (t.last_message_at ? "[attachment]" : "Start a conversation");
      const time = t.last_message_at ? ago(t.last_message_at) : "";
      const active = t.id === state.activeThreadId ? "is-active" : "";
      const unreadDot = t.unread ? '<span class="cf-thread-dot" aria-label="Unread"></span>' : "";
      return `
        <button type="button" class="cf-thread-row ${active}" data-thread-id="${t.id}">
          <span class="cf-thread-avatar">${avatar}</span>
          <span class="cf-thread-body">
            <span class="cf-thread-row-top">
              <span class="cf-thread-name">${esc(name)}</span>
              <span class="cf-thread-time">${time}</span>
            </span>
            <span class="cf-thread-preview">${esc(preview.slice(0, 90))}</span>
          </span>
          ${unreadDot}
        </button>`;
    }).join("");

    list.querySelectorAll(".cf-thread-row").forEach((row) => {
      row.addEventListener("click", () => openThread(Number(row.getAttribute("data-thread-id"))));
    });
  }

  function renderChat() {
    const pane = shell.querySelector('[data-role="chat"]');
    if (!pane) return;
    if (!state.activeThread) {
      pane.innerHTML = `
        <div class="cf-messages-chat-empty">
          <p>Select a conversation to start messaging.</p>
        </div>`;
      return;
    }
    const p = state.activeThread.peer || {};
    const username = p.username || "user";
    const avatar = p.avatar_url
      ? `<img src="${esc(p.avatar_url)}" alt="">`
      : `<span>${esc(username[0].toUpperCase())}</span>`;

    pane.innerHTML = `
      <header class="cf-chat-head">
        <a class="cf-thread-avatar" href="user-profile.html?u=${encodeURIComponent(username)}">${avatar}</a>
        <div class="cf-chat-head-text">
          <a class="cf-chat-head-name" href="user-profile.html?u=${encodeURIComponent(username)}">@${esc(username)}</a>
        </div>
      </header>
      <div class="cf-chat-messages" data-role="chat-messages">
        <div class="cf-empty" style="padding:20px;">Loading messages…</div>
      </div>
      <form class="cf-chat-composer" data-role="composer" autocomplete="off">
        <div class="cf-chat-attachments" data-role="attach-previews"></div>
        <div class="cf-chat-composer-row">
          <label class="cf-chat-attach-btn" title="Attach image or video">
            📎
            <input type="file" accept="image/*,video/*" multiple style="display:none;" data-role="attach-input">
          </label>
          <textarea class="cf-chat-input" data-role="chat-input" rows="1" placeholder="Message @${esc(username)}…"></textarea>
          <button type="submit" class="cf-btn cf-btn-primary" data-role="send-btn">Send</button>
        </div>
      </form>
    `;

    wireChat();
    renderMessages();
  }

  function renderMessages() {
    const box = shell.querySelector('[data-role="chat-messages"]');
    if (!box) return;
    if (!state.messages.length) {
      box.innerHTML = `<div class="cf-chat-empty"><p>No messages yet. Say hi.</p></div>`;
      return;
    }
    const me = state.user.id;
    box.innerHTML = state.messages.map((m) => {
      const mine = m.sender_id === me;
      const attach = (m.attachments || []).map(attachmentHtml).join("");
      const bodyHtml = m.body ? `<div class="cf-chat-body">${linkify(m.body)}</div>` : "";
      return `
        <div class="cf-chat-msg ${mine ? "is-mine" : ""}" data-message-id="${m.id}">
          <div class="cf-chat-bubble">
            ${bodyHtml}
            ${attach}
          </div>
          <div class="cf-chat-msg-meta">${fmtTime(m.created_at)}</div>
        </div>`;
    }).join("");
    // Scroll to bottom after DOM settles.
    setTimeout(() => { box.scrollTop = box.scrollHeight; }, 0);
  }

  function attachmentHtml(a) {
    if (!a || !a.url) return "";
    if (a.type === "video") {
      return `
        <div class="cf-chat-attach">
          <video src="${esc(a.url)}" controls preload="metadata" playsinline></video>
        </div>`;
    }
    // default: image
    return `
      <div class="cf-chat-attach">
        <img src="${esc(a.url)}" alt="${esc(a.name || "")}" loading="lazy">
      </div>`;
  }

  // ---------- Chat wiring ----------
  function wireChat() {
    const form = shell.querySelector('[data-role="composer"]');
    const input = shell.querySelector('[data-role="chat-input"]');
    const file = shell.querySelector('[data-role="attach-input"]');

    // Auto-grow textarea.
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 180) + "px";
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form.requestSubmit();
      }
    });

    file.addEventListener("change", async () => {
      const files = Array.from(file.files || []);
      file.value = "";
      if (!files.length) return;
      for (const f of files) {
        const preview = showUploadingPreview(f);
        const { data, error } = await COMMUNITY_API.uploadDMAttachment(f);
        if (error) {
          preview.remove();
          alert("Upload failed: " + (error.message || error));
          continue;
        }
        state.draftAttachments.push(data);
        preview.remove();
        renderAttachmentPreview(data);
      }
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const body = input.value;
      if (!body.trim() && !state.draftAttachments.length) return;
      const sendBtn = shell.querySelector('[data-role="send-btn"]');
      sendBtn.disabled = true;
      const { data, error } = await COMMUNITY_API.sendMessage({
        threadId: state.activeThreadId,
        body,
        attachments: state.draftAttachments.slice(),
      });
      sendBtn.disabled = false;
      if (error) {
        alert("Send failed: " + (error.message || error));
        return;
      }
      input.value = "";
      input.style.height = "auto";
      state.draftAttachments = [];
      shell.querySelector('[data-role="attach-previews"]').innerHTML = "";
      state.messages.push(data);
      renderMessages();
      // Move the thread to the top of the inbox optimistically.
      bumpThreadToTop(state.activeThreadId, body, data.attachments);
    });
  }

  function showUploadingPreview(file) {
    const wrap = shell.querySelector('[data-role="attach-previews"]');
    const node = document.createElement("div");
    node.className = "cf-attach-chip";
    node.innerHTML = `<span>Uploading ${esc(file.name)}…</span>`;
    wrap.appendChild(node);
    return node;
  }

  function renderAttachmentPreview(a) {
    const wrap = shell.querySelector('[data-role="attach-previews"]');
    const node = document.createElement("div");
    node.className = "cf-attach-chip";
    const thumb = a.type === "video"
      ? `<video src="${esc(a.url)}" muted></video>`
      : `<img src="${esc(a.url)}" alt="">`;
    node.innerHTML = `${thumb}<button type="button" data-action="remove">✕</button>`;
    node.querySelector('[data-action="remove"]').addEventListener("click", () => {
      state.draftAttachments = state.draftAttachments.filter((x) => x.url !== a.url);
      node.remove();
    });
    wrap.appendChild(node);
  }

  function bumpThreadToTop(threadId, previewText, attachments) {
    const idx = state.threads.findIndex((t) => t.id === threadId);
    if (idx === -1) return;
    const t = state.threads[idx];
    const preview = (previewText || "").trim() ||
      (attachments && attachments.length ? "[attachment]" : t.last_message_preview);
    const updated = { ...t, last_message_at: new Date().toISOString(), last_message_preview: preview, last_sender_id: state.user.id, unread: false };
    state.threads.splice(idx, 1);
    state.threads.unshift(updated);
    renderThreadList();
  }

  // ---------- Requests panel ----------
  async function openRequests() {
    state.requestsOpen = true;
    const panel = shell.querySelector('[data-role="requests-panel"]');
    panel.hidden = false;
    await loadRequests();
    renderRequests();
    // Opening the panel counts as "reading" the requests — mark
    // them all seen so the red notification badge on the Messages
    // tab decreases even if the user doesn't accept/decline.
    if (window.COMMUNITY_API && COMMUNITY_API.markIncomingRequestsSeen) {
      try { await COMMUNITY_API.markIncomingRequestsSeen(); } catch (_) {}
      broadcastNotifChange();
    }
  }

  function closeRequests() {
    state.requestsOpen = false;
    const panel = shell.querySelector('[data-role="requests-panel"]');
    panel.hidden = true;
  }

  async function loadRequests() {
    const { data } = await COMMUNITY_API.listIncomingFriendRequests();
    state.requests = data || [];
    const ids = state.requests.map((r) => r.requester_id);
    if (ids.length) {
      const { data: profiles } = await COMMUNITY_API.listProfiles(ids);
      state.reqProfiles = {};
      (profiles || []).forEach((p) => { state.reqProfiles[p.id] = p; });
    } else {
      state.reqProfiles = {};
    }
    // Update the badge count on the Requests button.
    const countEl = shell.querySelector('[data-role="req-count"]');
    if (countEl) {
      countEl.textContent = String(state.requests.length);
      countEl.classList.toggle("is-zero", state.requests.length === 0);
    }
  }

  function renderRequests() {
    const list = shell.querySelector('[data-role="requests-list"]');
    if (!list) return;
    if (!state.requests.length) {
      list.innerHTML = `<div class="cf-empty">No pending friend requests.</div>`;
      return;
    }
    list.innerHTML = state.requests.map((r) => {
      const p = state.reqProfiles[r.requester_id] || {};
      const name = p.username ? "@" + p.username : "(user)";
      const href = p.username ? "user-profile.html?u=" + encodeURIComponent(p.username) : "#";
      const avatar = p.avatar_url
        ? `<img src="${esc(p.avatar_url)}" alt="">`
        : `<span>${esc((p.username || "?")[0].toUpperCase())}</span>`;
      return `
        <div class="cf-request-row" data-request-id="${r.id}" data-requester-id="${r.requester_id}">
          <a class="cf-thread-avatar" href="${href}">${avatar}</a>
          <div class="cf-request-text">
            <a href="${href}"><strong>${esc(name)}</strong></a>
            <span class="cf-request-time">· ${ago(r.created_at)} ago</span>
          </div>
          <div class="cf-request-actions">
            <button type="button" class="cf-btn cf-btn-primary" data-action="accept">Accept</button>
            <button type="button" class="cf-btn" data-action="decline">Decline</button>
          </div>
        </div>`;
    }).join("");

    list.querySelectorAll(".cf-request-row").forEach((row) => {
      const id = Number(row.getAttribute("data-request-id"));
      const requesterId = row.getAttribute("data-requester-id");
      row.querySelector('[data-action="accept"]').addEventListener("click", async () => {
        row.querySelectorAll("button").forEach((b) => (b.disabled = true));
        const { error } = await COMMUNITY_API.acceptFriendRequest(id);
        if (error) { alert("Accept failed: " + (error.message || error)); return; }
        // Spin up a DM thread for the new friendship so a chat box
        // appears in the inbox immediately, clickable to start
        // messaging. startOrGetDM is idempotent — returns an
        // existing thread if one somehow already exists.
        const { error: tErr } = await COMMUNITY_API.startOrGetDM(requesterId);
        if (tErr) console.warn("[messages] startOrGetDM failed", tErr);
        state.requests = state.requests.filter((r) => r.id !== id);
        renderRequests();
        updateReqBadge();
        await loadThreads();
        broadcastNotifChange();
      });
      row.querySelector('[data-action="decline"]').addEventListener("click", async () => {
        row.querySelectorAll("button").forEach((b) => (b.disabled = true));
        const { error } = await COMMUNITY_API.declineFriendRequest(id);
        if (error) { alert("Decline failed: " + (error.message || error)); return; }
        state.requests = state.requests.filter((r) => r.id !== id);
        renderRequests();
        updateReqBadge();
        broadcastNotifChange();
      });
    });
  }

  function updateReqBadge() {
    const countEl = shell.querySelector('[data-role="req-count"]');
    if (!countEl) return;
    countEl.textContent = String(state.requests.length);
    countEl.classList.toggle("is-zero", state.requests.length === 0);
  }

  // Tell the sidebar badge / any listener that unseen-request or
  // unread-thread counts may have changed, so it can re-query.
  function broadcastNotifChange() {
    window.dispatchEvent(new CustomEvent("cf-messages-notif-change"));
  }

  // ---------- Boot ----------
  async function loadThreads() {
    const { data } = await COMMUNITY_API.listMyThreads();
    state.threads = data || [];
    renderThreadList();
  }

  async function openThread(threadId) {
    state.activeThreadId = threadId;
    // Write to URL so the thread is shareable and survives refresh.
    const q = new URLSearchParams(location.search);
    q.set("t", String(threadId));
    history.replaceState(null, "", location.pathname + "?" + q.toString());
    // Update the active highlight.
    shell.querySelectorAll(".cf-thread-row").forEach((r) => {
      r.classList.toggle("is-active", Number(r.getAttribute("data-thread-id")) === threadId);
    });
    const { data } = await COMMUNITY_API.getThread(threadId);
    state.activeThread = data || null;
    state.messages = [];
    renderChat();
    const { data: msgs } = await COMMUNITY_API.listMessages(threadId);
    state.messages = msgs || [];
    renderMessages();
    // Mark-as-read so the unread dot clears.
    await COMMUNITY_API.markThreadRead(threadId);
    // Locally mark the thread read.
    const t = state.threads.find((x) => x.id === threadId);
    if (t) { t.unread = false; renderThreadList(); }
    broadcastNotifChange();
  }

  async function pollActive() {
    if (document.hidden || !state.activeThreadId) return;
    const { data: msgs } = await COMMUNITY_API.listMessages(state.activeThreadId);
    const next = msgs || [];
    // Only re-render if the last id changed.
    const lastNow = state.messages.length ? state.messages[state.messages.length - 1].id : 0;
    const lastNext = next.length ? next[next.length - 1].id : 0;
    if (lastNow !== lastNext) {
      state.messages = next;
      renderMessages();
      await COMMUNITY_API.markThreadRead(state.activeThreadId);
    }
    // Also refresh the inbox to pick up other threads' activity.
    loadThreads();
  }

  function startPolling() {
    stopPolling();
    state.pollTimer = setInterval(pollActive, 6000);
  }
  function stopPolling() {
    if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; }
  }
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopPolling();
    else startPolling();
  });
  window.addEventListener("beforeunload", stopPolling);

  let lastSignedIn = null;
  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    if (!user) { renderSignedOut(); stopPolling(); return; }
    renderShell();
    await Promise.all([loadThreads(), loadRequests()]);
    if (state.activeThreadId) {
      await openThread(state.activeThreadId);
    }
    startPolling();
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

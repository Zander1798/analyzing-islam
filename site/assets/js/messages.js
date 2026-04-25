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
    replyTo: null,             // { id, body, attachments, sender_id } — the message currently being quoted
    threadChannel: null,       // realtime channel for the active thread's messages
    inboxChannel: null,        // realtime channel for the inbox + friend requests
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
        <div class="cf-chat-reply" data-role="reply-chip" hidden></div>
        <div class="cf-chat-attachments" data-role="attach-previews"></div>
        <div class="cf-chat-composer-row">
          <button type="button" class="cf-chat-attach-btn" data-role="attach-btn" title="Attach photo, video, or file" aria-label="Attach">
            📎
          </button>
          <button type="button" class="cf-chat-emoji-btn" data-role="emoji-btn" title="Insert emoji" aria-label="Insert emoji">
            😊
          </button>
          <input type="file" accept="image/*,video/*" multiple style="display:none;" data-role="attach-input-media">
          <input type="file" multiple style="display:none;" data-role="attach-input-file">
          <textarea class="cf-chat-input" data-role="chat-input" rows="1" placeholder="Message @${esc(username)}…"></textarea>
          <button type="submit" class="cf-btn cf-btn-primary" data-role="send-btn">Send</button>
        </div>
      </form>
    `;

    wireChat();
    renderMessages();
  }

  // One-line preview of a message — body if any, else first attachment
  // type. Used by the quoted-reply chip on the composer and on bubbles.
  function messagePreview(m) {
    if (!m) return "";
    const body = (m.body || "").trim();
    if (body) return body.length > 140 ? body.slice(0, 140) + "…" : body;
    const a = (m.attachments || [])[0];
    if (a) return a.type === "video" ? "[video]" : "[image]";
    return "";
  }

  // Lookup helper — peer username for a message's sender, used in
  // the quoted-reply chip's header line.
  function senderLabel(senderId) {
    if (!state.user) return "user";
    if (senderId === state.user.id) return "You";
    const peer = state.activeThread && state.activeThread.peer;
    return peer && peer.username ? "@" + peer.username : "user";
  }

  // Render the small quoted-reply block that sits inside a bubble
  // when the message is a reply. Tappable to scroll back to the
  // original; missing originals (deleted, hadn't loaded yet) render
  // as a faded "Original message unavailable" placeholder.
  function quotedHtml(m) {
    if (!m || !m.reply_to_id) return "";
    const orig = state.messages.find((x) => x.id === m.reply_to_id);
    if (!orig) {
      return `<button type="button" class="cf-chat-quote cf-chat-quote--missing" disabled>
                <span class="cf-chat-quote-name">Reply</span>
                <span class="cf-chat-quote-body">Original message unavailable</span>
              </button>`;
    }
    return `
      <button type="button" class="cf-chat-quote" data-jump-to="${orig.id}">
        <span class="cf-chat-quote-name">${esc(senderLabel(orig.sender_id))}</span>
        <span class="cf-chat-quote-body">${esc(messagePreview(orig))}</span>
      </button>`;
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
            ${quotedHtml(m)}
            ${bodyHtml}
            ${attach}
          </div>
          <div class="cf-chat-msg-meta">${fmtTime(m.created_at)}</div>
        </div>`;
    }).join("");
    wireMessageInteractions(box);
    // Scroll to bottom after DOM settles.
    setTimeout(() => { box.scrollTop = box.scrollHeight; }, 0);
  }

  // Per-message interactions:
  //   - right-click → "Reply" context menu (desktop)
  //   - swipe-left ≥ 56px → start a reply (mobile / touch)
  //   - tap on a quoted-reply chip → scroll to and flash the original
  function wireMessageInteractions(box) {
    box.querySelectorAll(".cf-chat-msg").forEach((node) => {
      const id = Number(node.getAttribute("data-message-id"));

      node.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        openMessageContextMenu(e.clientX, e.clientY, id);
      });

      // Touch: track horizontal swipe on the bubble. Negative deltaX
      // (right→left) starts a reply once it crosses the threshold.
      let startX = null, startY = null, decided = false;
      node.addEventListener("touchstart", (e) => {
        if (e.touches.length !== 1) return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        decided = false;
        node.style.transition = "";
      }, { passive: true });
      node.addEventListener("touchmove", (e) => {
        if (startX == null) return;
        const dx = e.touches[0].clientX - startX;
        const dy = e.touches[0].clientY - startY;
        if (!decided) {
          if (Math.abs(dy) > Math.abs(dx)) {
            // Vertical scroll — abandon this gesture.
            startX = null;
            return;
          }
          decided = true;
        }
        const drag = Math.max(-80, Math.min(0, dx));
        node.style.transform = `translateX(${drag}px)`;
      }, { passive: true });
      function endTouch() {
        if (startX == null) return;
        const m = state.messages.find((x) => x.id === id);
        const tr = node.style.transform;
        const match = /translateX\((-?\d+(?:\.\d+)?)px\)/.exec(tr || "");
        const dx = match ? Number(match[1]) : 0;
        node.style.transition = "transform 160ms ease-out";
        node.style.transform = "";
        if (m && dx <= -56) startReplyTo(m);
        startX = null;
      }
      node.addEventListener("touchend", endTouch);
      node.addEventListener("touchcancel", endTouch);
    });

    box.querySelectorAll("[data-jump-to]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = Number(btn.getAttribute("data-jump-to"));
        scrollToMessage(targetId);
      });
    });
  }

  // Build a small one-action context menu at the click coordinates.
  // Closes on outside click, Escape, or scroll.
  function openMessageContextMenu(x, y, messageId) {
    closeMessageContextMenu();
    const menu = document.createElement("div");
    menu.className = "cf-chat-ctx-menu";
    menu.setAttribute("role", "menu");
    menu.innerHTML = `<button type="button" data-action="reply">↩ Reply</button>`;
    document.body.appendChild(menu);
    // Position, clamping to the viewport so the menu doesn't clip.
    const r = menu.getBoundingClientRect();
    const left = Math.min(x, window.innerWidth - r.width - 8);
    const top = Math.min(y, window.innerHeight - r.height - 8);
    menu.style.left = left + "px";
    menu.style.top = top + "px";
    menu.querySelector('[data-action="reply"]').addEventListener("click", () => {
      const m = state.messages.find((x) => x.id === messageId);
      if (m) startReplyTo(m);
      closeMessageContextMenu();
    });
    setTimeout(() => {
      document.addEventListener("click", closeMessageContextMenu, { once: true });
      document.addEventListener("keydown", escClose);
      window.addEventListener("scroll", closeMessageContextMenu, { once: true, capture: true });
    }, 0);
  }
  function escClose(e) {
    if (e.key === "Escape") closeMessageContextMenu();
  }
  function closeMessageContextMenu() {
    document.querySelectorAll(".cf-chat-ctx-menu").forEach((n) => n.remove());
    document.removeEventListener("keydown", escClose);
  }

  // Attach sheet: tiny popup anchored above the paperclip with two
  // entries that each kick off the corresponding file input. Adding
  // a third option later (catalog / verse / build picker — task #4)
  // is just one more entry in the sheet.
  function openAttachSheet(anchorEl, handlers) {
    closePopover();
    const sheet = document.createElement("div");
    sheet.className = "cf-chat-popover cf-chat-attach-sheet";
    sheet.innerHTML = `
      <button type="button" data-action="media">📷 Photo or video</button>
      <button type="button" data-action="file">📎 File</button>
    `;
    document.body.appendChild(sheet);
    anchorPopover(sheet, anchorEl);
    sheet.querySelector('[data-action="media"]').addEventListener("click", () => {
      closePopover();
      try { handlers.media(); } catch (_) {}
    });
    sheet.querySelector('[data-action="file"]').addEventListener("click", () => {
      closePopover();
      try { handlers.file(); } catch (_) {}
    });
    armPopoverDismiss();
  }

  // Emoji picker: an inline grid keyed by category. ~150 emojis, no
  // dependency. Clicking one inserts the codepoint at the textarea's
  // current cursor position and re-focuses so typing continues
  // without an extra tap.
  const EMOJI_CATEGORIES = [
    { label: "Smileys", emoji: "😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘😗☺😚😙🥲😋😛😜🤪😝🤑🤗🤭🤫🤔🤐🤨😐😑😶😏😒🙄😬😮😯😲🥱😴🤤😪😵🤐🥴🥺😢😭😤😠😡🤬🤯😳😱🥵🥶😨😰😥😓🤗🤔🤭" },
    { label: "Gestures", emoji: "👍👎👌🤌🤏✌🤞🤟🤘🤙👈👉👆🖕👇☝👋🤚🖐✋🖖👌🤛🤜👊✊🤝🙏✍💅🤳💪🦾🦵🦶👂🦻👃🧠🦷🦴👀👁👅👄💋" },
    { label: "Hearts", emoji: "❤🧡💛💚💙💜🖤🤍🤎💔❣💕💞💓💗💖💘💝💟" },
    { label: "Animals", emoji: "🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐽🐸🐵🙈🙉🙊🐒🐔🐧🐦🐤🦆🦅🦉🐺🐗🐴🦄🐝🐛🦋🐌🐞🐜🦂🦗🕷🐢🐍🦎🦖🐙🐠🐟🐬🐳🐋🦈🐊🐅🐆🦓🦍🦧🐘🦏🦛🐪🐫🦒🦘🐃🐂🐄🐎🐖🐏🐑🦙🐐🦌🐕🐩🐈🦃🦚🦜🦢🦩🐇🐀🐁🐿🦔" },
    { label: "Food", emoji: "🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🥦🥬🥒🌶🫑🌽🥕🫒🧄🧅🥔🍠🥐🥯🍞🥖🥨🧀🥚🍳🧈🥞🧇🥓🥩🍗🍖🦴🌭🍔🍟🍕🥪🥙🧆🌮🌯🫔🥗🥘🫕🍝🍜🍲🍛🍣🍱🥟🦪🍤🍙🍚🍘🍥🥠🥮🍢🍡🍧🍨🍦🥧🧁🍰🎂🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯☕🍵🍶🍾🍷🍸🍹🍺🍻🥂🥃🥤🧋🧃🧉🧊" },
    { label: "Travel", emoji: "🚗🚕🚙🚌🚎🏎🚓🚑🚒🚐🛻🚚🚛🚜🦯🦽🦼🛴🚲🛵🏍🛺🚨🚔🚍🚘🚖🚡🚠🚟🚃🚋🚞🚝🚄🚅🚈🚂🚆🚇🚊🚉✈🛫🛬🛩💺🛰🚀🛸🚁🛶⛵🚤🛥🛳⛴🚢⚓🪝⛽🚧🚦🚥🚏🗺🗿🗽🗼🏰🏯🏟🎡🎢🎠⛲⛱🏖🏝🏜🌋⛰🏔🗻🏕⛺🏠🏡🏘🏚🏗🏭🏢🏬🏣🏤🏥🏦🏨🏪🏫🏩💒🏛⛪🕌🛕🕍⛩🕋⛩🛤🛣🗾🎑🏞🌅🌄🌠🎇🎆🌇🌆🏙🌃🌌🌉🌁" },
    { label: "Symbols", emoji: "✅❌⭕🚫⛔📛🚭❗❓❔❕💯🔔🔕🔇🔈🔉🔊📣📢👁‍🗨💬💭🗯♨💈🛑🚸⚠☢☣⬆↗➡↘⬇↙⬅↖↕↔↩↪⤴⤵🔃🔄🔙🔚🔛🔜🔝🛐⚛🕉✡☸☯✝☦☪☮🕎🔯♈♉♊♋♌♍♎♏♐♑♒♓⛎🆔🈳🈹Ⓜ🉐㊙㊗🈴🈲🅰🅱🆎🅾💠♻⚜🔱📛🔰⭕✅☑✔❌❎➕➖➗✖💲💱©®™" },
  ];

  function openEmojiPicker(anchorEl, textarea) {
    closePopover();
    const wrap = document.createElement("div");
    wrap.className = "cf-chat-popover cf-chat-emoji-picker";
    const tabs = EMOJI_CATEGORIES.map((cat, i) =>
      `<button type="button" class="cf-emoji-tab ${i === 0 ? 'is-active' : ''}" data-tab="${i}" title="${esc(cat.label)}">${Array.from(cat.emoji)[0]}</button>`
    ).join("");
    wrap.innerHTML = `
      <div class="cf-emoji-tabs">${tabs}</div>
      <div class="cf-emoji-grid" data-role="emoji-grid"></div>
    `;
    document.body.appendChild(wrap);
    const grid = wrap.querySelector('[data-role="emoji-grid"]');
    function paintGrid(idx) {
      const chars = Array.from(EMOJI_CATEGORIES[idx].emoji);
      grid.innerHTML = chars.map((ch) => `<button type="button" class="cf-emoji-cell">${ch}</button>`).join("");
      grid.querySelectorAll(".cf-emoji-cell").forEach((b) => {
        b.addEventListener("click", () => insertAtCursor(textarea, b.textContent));
      });
    }
    wrap.querySelectorAll(".cf-emoji-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        wrap.querySelectorAll(".cf-emoji-tab").forEach((t) => t.classList.remove("is-active"));
        tab.classList.add("is-active");
        paintGrid(Number(tab.getAttribute("data-tab")));
      });
    });
    paintGrid(0);
    anchorPopover(wrap, anchorEl);
    armPopoverDismiss();
  }

  // Insert a string at the textarea's selection point and grow the
  // textarea so the row reflows. Mirrors the auto-grow handler.
  function insertAtCursor(textarea, text) {
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const v = textarea.value;
    textarea.value = v.slice(0, start) + text + v.slice(end);
    const cursor = start + text.length;
    textarea.setSelectionRange(cursor, cursor);
    textarea.focus();
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 180) + "px";
  }

  // Position a popover above its anchor button and clamp into the
  // viewport. Used for both the attach sheet and the emoji picker.
  function anchorPopover(popover, anchor) {
    const r = anchor.getBoundingClientRect();
    const pr = popover.getBoundingClientRect();
    let left = r.left;
    if (left + pr.width > window.innerWidth - 8) left = window.innerWidth - pr.width - 8;
    if (left < 8) left = 8;
    let top = r.top - pr.height - 8;
    if (top < 8) top = r.bottom + 8;
    popover.style.left = left + "px";
    popover.style.top  = top  + "px";
  }

  function armPopoverDismiss() {
    setTimeout(() => {
      document.addEventListener("click", outsidePopoverClose, true);
      document.addEventListener("keydown", escPopover);
    }, 0);
  }
  function escPopover(e) { if (e.key === "Escape") closePopover(); }
  function outsidePopoverClose(e) {
    const p = document.querySelector(".cf-chat-popover");
    if (!p) return;
    if (p.contains(e.target)) return;
    // Don't close if the click was on the anchor button — the click
    // handler there will close + reopen on its own.
    if (e.target.closest('[data-role="attach-btn"], [data-role="emoji-btn"]')) return;
    closePopover();
  }
  function closePopover() {
    document.querySelectorAll(".cf-chat-popover").forEach((n) => n.remove());
    document.removeEventListener("click", outsidePopoverClose, true);
    document.removeEventListener("keydown", escPopover);
  }

  // Scroll the chat pane so the target message is centred, then
  // briefly highlight it so the eye can land on it after the jump.
  function scrollToMessage(id) {
    const node = shell.querySelector(`.cf-chat-msg[data-message-id="${id}"]`);
    if (!node) return;
    node.scrollIntoView({ behavior: "smooth", block: "center" });
    node.classList.add("cf-chat-msg--flash");
    setTimeout(() => node.classList.remove("cf-chat-msg--flash"), 1600);
  }

  function startReplyTo(message) {
    state.replyTo = {
      id: message.id,
      body: message.body || "",
      attachments: message.attachments || [],
      sender_id: message.sender_id,
    };
    renderReplyChip();
    const input = shell.querySelector('[data-role="chat-input"]');
    if (input) input.focus();
  }

  function clearReplyTo() {
    state.replyTo = null;
    renderReplyChip();
  }

  function renderReplyChip() {
    const chip = shell.querySelector('[data-role="reply-chip"]');
    if (!chip) return;
    if (!state.replyTo) {
      chip.hidden = true;
      chip.innerHTML = "";
      return;
    }
    chip.hidden = false;
    chip.innerHTML = `
      <div class="cf-chat-reply-bar"></div>
      <div class="cf-chat-reply-text">
        <strong>Replying to ${esc(senderLabel(state.replyTo.sender_id))}</strong>
        <span>${esc(messagePreview(state.replyTo))}</span>
      </div>
      <button type="button" class="cf-chat-reply-close" aria-label="Cancel reply">✕</button>`;
    chip.querySelector(".cf-chat-reply-close").addEventListener("click", clearReplyTo);
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
    const fileMedia = shell.querySelector('[data-role="attach-input-media"]');
    const fileAny   = shell.querySelector('[data-role="attach-input-file"]');
    const attachBtn = shell.querySelector('[data-role="attach-btn"]');
    const emojiBtn  = shell.querySelector('[data-role="emoji-btn"]');

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

    // Both file inputs feed the same upload pipeline. We split them so
    // the system picker can default to the camera roll for media and
    // a generic file picker for everything else (matters most on iOS).
    async function handleFileSelection(files) {
      if (!files || !files.length) return;
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
    }
    fileMedia.addEventListener("change", () => {
      const files = Array.from(fileMedia.files || []);
      fileMedia.value = "";
      handleFileSelection(files);
    });
    fileAny.addEventListener("change", () => {
      const files = Array.from(fileAny.files || []);
      fileAny.value = "";
      handleFileSelection(files);
    });

    // Tapping the paperclip opens a tiny sheet: "Photo or video" (uses
    // the media-only input so the OS opens the photo library / camera
    // first) and "File" (uses the unrestricted input).
    attachBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openAttachSheet(attachBtn, {
        media: () => fileMedia.click(),
        file:  () => fileAny.click(),
      });
    });

    emojiBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openEmojiPicker(emojiBtn, input);
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const body = input.value;
      if (!body.trim() && !state.draftAttachments.length) return;
      const sendBtn = shell.querySelector('[data-role="send-btn"]');
      sendBtn.disabled = true;
      const replyToId = state.replyTo ? state.replyTo.id : null;
      const { data, error } = await COMMUNITY_API.sendMessage({
        threadId: state.activeThreadId,
        body,
        attachments: state.draftAttachments.slice(),
        replyToId,
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
      clearReplyTo();
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
    // Reset reply draft when navigating between conversations — a
    // reply target only makes sense within its own thread.
    state.replyTo = null;
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
    // Subscribe to incoming messages on this thread.
    subscribeThread(threadId);
    // Mark-as-read so the unread dot clears.
    await COMMUNITY_API.markThreadRead(threadId);
    // Locally mark the thread read.
    const t = state.threads.find((x) => x.id === threadId);
    if (t) { t.unread = false; renderThreadList(); }
    broadcastNotifChange();
  }

  // ---------- Realtime ----------
  // Subscribes to the active thread's direct_messages so a peer's
  // send pops into view without a refresh. RLS already restricts
  // SELECT on direct_messages to the two participants, so the
  // channel only ever delivers events the viewer is allowed to see.
  function subscribeThread(threadId) {
    unsubscribeThread();
    if (!threadId || !window.__supabase) return;
    const channel = window.__supabase
      .channel("dm-thread-" + threadId)
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "direct_messages", filter: "thread_id=eq." + threadId },
        (payload) => {
          const msg = payload.new;
          if (!msg || msg.is_deleted) return;
          if (state.messages.some((m) => m.id === msg.id)) return;
          state.messages.push(msg);
          renderMessages();
          // If the new message is from the peer, mark the thread read
          // so the unread dot doesn't reappear when the inbox refreshes.
          if (state.user && msg.sender_id !== state.user.id) {
            COMMUNITY_API.markThreadRead(threadId).catch(() => {});
            broadcastNotifChange();
          }
        }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "direct_messages", filter: "thread_id=eq." + threadId },
        (payload) => {
          const msg = payload.new;
          if (!msg) return;
          // Soft-delete clears the row from view; otherwise replace in place.
          if (msg.is_deleted) {
            state.messages = state.messages.filter((m) => m.id !== msg.id);
          } else {
            const i = state.messages.findIndex((m) => m.id === msg.id);
            if (i !== -1) state.messages[i] = msg;
          }
          renderMessages();
        }
      )
      .subscribe();
    state.threadChannel = channel;
  }

  function unsubscribeThread() {
    if (state.threadChannel && window.__supabase) {
      try { window.__supabase.removeChannel(state.threadChannel); } catch (_) {}
    }
    state.threadChannel = null;
  }

  // Subscribes to direct_threads so the inbox preview / unread dot
  // updates the moment a peer sends a message in any thread, and to
  // friendships so the Requests badge counts incoming requests live.
  function subscribeInbox() {
    unsubscribeInbox();
    if (!state.user || !window.__supabase) return;
    const channel = window.__supabase
      .channel("dm-inbox-" + state.user.id)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "direct_threads" },
        () => { loadThreads(); broadcastNotifChange(); }
      )
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "friendships", filter: "addressee_id=eq." + state.user.id },
        () => { if (state.requestsOpen) loadRequests().then(renderRequests); broadcastNotifChange(); }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "friendships", filter: "addressee_id=eq." + state.user.id },
        () => { if (state.requestsOpen) loadRequests().then(renderRequests); broadcastNotifChange(); }
      )
      .subscribe();
    state.inboxChannel = channel;
  }

  function unsubscribeInbox() {
    if (state.inboxChannel && window.__supabase) {
      try { window.__supabase.removeChannel(state.inboxChannel); } catch (_) {}
    }
    state.inboxChannel = null;
  }

  function teardownRealtime() {
    unsubscribeThread();
    unsubscribeInbox();
  }
  window.addEventListener("beforeunload", teardownRealtime);

  let lastSignedIn = null;
  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    if (!user) { renderSignedOut(); teardownRealtime(); return; }
    renderShell();
    await Promise.all([loadThreads(), loadRequests()]);
    if (state.activeThreadId) {
      await openThread(state.activeThreadId);
    }
    subscribeInbox();
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

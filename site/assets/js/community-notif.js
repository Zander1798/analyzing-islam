/* =============================================================
   Analyzing Islam — Messages notification badge decorator
   -------------------------------------------------------------
   Adds / keeps the red unread-count badge on any sidebar row that
   links to messages.html. Works on pages whose sidebar is rendered
   by community-home.js / community-view.js / community-post.js
   (they don't inject the badge themselves). Complements
   community-sidebar.js, which renders its own badge inline — this
   decorator simply updates whatever badge span it finds.

   Count source: COMMUNITY_API.countMessagesNotifications(), which
   already combines unseen friend requests + unread direct-message
   threads. The badge ticks down automatically as each thread is
   opened or the Requests panel is viewed (messages.js dispatches
   `cf-messages-notif-change` at those moments).
   ============================================================= */
(function () {
  "use strict";

  let notifCount = 0;
  let pollTimer = null;
  let obs = null;
  let isApplying = false;

  function currentUser() {
    return window.AI_AUTH ? window.AI_AUTH.getUser() : null;
  }

  // Find every Messages sidebar row on the page and make sure each
  // has a .cf-notif-badge child reflecting the current count (or no
  // badge at all when count is zero).
  //
  // CRITICAL: this mutates #cf-left, and the MutationObserver below
  // watches #cf-left with subtree:true. If we don't disconnect the
  // observer around our own writes, every write retriggers the
  // observer -> applyBadges -> writes again -> infinite loop that
  // freezes the tab with no console output. So we disconnect, guard
  // re-entrancy, and skip no-op writes entirely.
  function applyBadges() {
    if (isApplying) return;
    isApplying = true;
    if (obs) obs.disconnect();
    try {
      const links = document.querySelectorAll('a.cf-side-link[href="messages.html"]');
      const text = notifCount > 99 ? "99+" : String(notifCount);
      const label = notifCount + " unread notification" + (notifCount === 1 ? "" : "s");
      links.forEach((a) => {
        let badge = a.querySelector('.cf-notif-badge');
        if (notifCount > 0) {
          if (!badge) {
            badge = document.createElement('span');
            badge.className = 'cf-notif-badge';
            badge.textContent = text;
            badge.setAttribute('aria-label', label);
            a.appendChild(badge);
          } else {
            // Skip no-op writes so we don't churn the DOM for nothing.
            if (badge.textContent !== text) badge.textContent = text;
            if (badge.getAttribute('aria-label') !== label) {
              badge.setAttribute('aria-label', label);
            }
          }
        } else if (badge) {
          badge.remove();
        }
      });
    } finally {
      // Reconnect on the next microtask so our just-issued mutations
      // have already been flushed and can't feed back into the observer.
      Promise.resolve().then(() => {
        isApplying = false;
        const left = document.getElementById('cf-left');
        if (obs && left) obs.observe(left, { childList: true, subtree: true });
      });
    }
  }

  async function loadNotifCount() {
    const u = currentUser();
    if (!u || !window.COMMUNITY_API ||
        typeof COMMUNITY_API.countMessagesNotifications !== "function") {
      notifCount = 0;
      applyBadges();
      return;
    }
    try {
      const { count } = await COMMUNITY_API.countMessagesNotifications();
      notifCount = count || 0;
    } catch (_) {
      notifCount = 0;
    }
    applyBadges();
  }

  function startPoll() {
    stopPoll();
    if (!currentUser() || document.hidden) return;
    pollTimer = setInterval(loadNotifCount, 30000);
  }

  function stopPoll() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  function init() {
    // Watch the left sidebar for re-renders so the badge is re-applied
    // whenever the host page wipes and re-injects the sidebar HTML.
    const left = document.getElementById('cf-left');
    if (left) {
      obs = new MutationObserver(() => {
        if (!isApplying) applyBadges();
      });
      obs.observe(left, { childList: true, subtree: true });
    }

    // Initial fetch + start polling.
    if (window.__authReady) window.__authReady.then(loadNotifCount);
    else loadNotifCount();
    startPoll();

    window.addEventListener('auth-state', () => { loadNotifCount(); startPoll(); });
    // messages.js fires this when a thread is opened, a request is
    // accepted/declined, or the Requests panel is opened — refresh
    // immediately rather than wait for the poller.
    window.addEventListener('cf-messages-notif-change', loadNotifCount);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stopPoll();
      else { loadNotifCount(); startPoll(); }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose a manual trigger so a host page can force a refresh after
  // mutating state (opening a thread, etc.) without waiting 30s.
  window.CF_NOTIF = { applyBadges, refresh: loadNotifCount };
})();

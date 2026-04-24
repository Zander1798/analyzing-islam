// Auth UI: injects a "Sign in" button into .site-nav-inner on every page,
// immediately to the left of the goat button. Re-renders when the session
// changes (via the `auth-state` event fired by auth.js).
(function () {
  "use strict";

  function assetPrefix() {
    const el = document.querySelector('link[href*="assets/"], script[src*="assets/"]');
    if (el) {
      const attr = el.getAttribute("href") || el.getAttribute("src");
      const idx = attr.indexOf("assets/");
      return attr.slice(0, idx);
    }
    const parts = location.pathname.split("/").filter(Boolean);
    const depth = Math.max(0, parts.length - 1);
    return depth > 0 ? "../".repeat(depth) : "";
  }

  function session() {
    return (typeof window !== "undefined" && window.__session) || null;
  }

  function buildLoggedOutButton(prefix) {
    const btn = document.createElement("a");
    btn.className = "auth-button auth-button--signin";
    btn.href = prefix + "login.html";
    btn.textContent = "Sign in";
    btn.setAttribute("aria-label", "Sign in or create an account");
    return btn;
  }

  function avatarMarkup(profile, email) {
    if (profile && profile.avatar_url) {
      return '<span class="auth-avatar auth-avatar--img" aria-hidden="true">' +
             '<img src="' + escapeHtml(profile.avatar_url) + '" alt=""></span>';
    }
    const seed = (profile && profile.username) || email || "";
    const letter = (seed[0] || "?").toUpperCase();
    return '<span class="auth-avatar" aria-hidden="true">' + escapeHtml(letter) + '</span>';
  }

  function buildLoggedInControl(prefix, sess) {
    const email = (sess.user && sess.user.email) || "";
    const profile = (typeof window !== "undefined" && window.__profile) || null;
    const username = (profile && profile.username) || "";
    const displayLabel = username ? "@" + username : "Account";

    // A wrapper that holds the trigger pill + the dropdown menu.
    const wrap = document.createElement("div");
    wrap.className = "auth-button auth-button--account";

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "auth-trigger";
    trigger.setAttribute("aria-haspopup", "true");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-label", "Account menu for " + (username || email));
    trigger.innerHTML =
      avatarMarkup(profile, email) +
      '<span class="auth-label">' + escapeHtml(displayLabel) + "</span>";
    wrap.appendChild(trigger);

    const menu = document.createElement("div");
    menu.className = "auth-menu";
    menu.setAttribute("role", "menu");
    menu.innerHTML =
      (username
        ? '<div class="auth-menu-handle">@' + escapeHtml(username) + "</div>"
        : "") +
      '<div class="auth-menu-email">' + escapeHtml(email) + "</div>" +
      '<a href="' + prefix + 'saved.html" class="auth-menu-item" role="menuitem">My saved entries</a>' +
      '<a href="' + prefix + 'profile.html" class="auth-menu-item" role="menuitem">Profile</a>' +
      '<button type="button" class="auth-menu-item auth-signout" role="menuitem">Sign out</button>';
    wrap.appendChild(menu);

    trigger.addEventListener("click", function (e) {
      e.stopPropagation();
      const open = wrap.classList.toggle("auth-open");
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
    });

    document.addEventListener("click", function (e) {
      if (!wrap.contains(e.target)) {
        wrap.classList.remove("auth-open");
        trigger.setAttribute("aria-expanded", "false");
      }
    });

    menu.querySelector(".auth-signout").addEventListener("click", async function () {
      if (!window.AI_AUTH) return;
      try {
        trigger.disabled = true;
        trigger.querySelector(".auth-label").textContent = "Signing out…";
        await window.AI_AUTH.signOut();
        // auth-state event fires on change and will re-render the button.
      } catch (err) {
        console.error("[auth] sign out failed", err);
      }
    });

    return wrap;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // The MutationObserver below watches the nav for external scripts
  // that rebuild it (goat.js, etc.). Since render() itself mutates the
  // nav, we have to pause the observer around our own mutations or we
  // trigger ourselves in an infinite loop, freezing the tab.
  let navObserver = null;
  let isRendering = false;

  function render() {
    const navInner = document.querySelector(".site-nav-inner");
    if (!navInner) return;
    if (isRendering) return; // hard guard against re-entrancy
    isRendering = true;
    if (navObserver) navObserver.disconnect();
    try {
      const prev = navInner.querySelector(".auth-button");
      if (prev) prev.remove();

      const prefix = assetPrefix();
      const sess = session();
      const node = sess ? buildLoggedInControl(prefix, sess) : buildLoggedOutButton(prefix);

      // Insert before the goat so the auth control sits to the goat's LEFT.
      const goat = navInner.querySelector(".goat-scream");
      if (goat) {
        navInner.insertBefore(node, goat);
      } else {
        navInner.appendChild(node);
      }
    } finally {
      // Reconnect on the next microtask so our just-issued DOM mutation
      // has been flushed — otherwise the observer sees it and re-triggers.
      Promise.resolve().then(() => {
        isRendering = false;
        if (navObserver) navObserver.observe(navInner, { childList: true });
      });
    }
  }

  function init() {
    // Wait for the first auth check so we render the correct state without flicker.
    if (window.__authReady && typeof window.__authReady.then === "function") {
      window.__authReady.then(render);
    } else {
      render();
    }

    // Re-render when auth state changes or the cached profile updates
    // (username change, avatar upload, avatar removal).
    window.addEventListener("auth-state", render);
    window.addEventListener("profile-state", render);

    // If goat.js or some other script mutates .site-nav-inner after us, re-inject.
    const navInner = document.querySelector(".site-nav-inner");
    if (navInner) {
      navObserver = new MutationObserver(function () {
        if (isRendering) return;
        const navInner2 = document.querySelector(".site-nav-inner");
        if (navInner2 && !navInner2.querySelector(".auth-button")) {
          render();
        }
      });
      navObserver.observe(navInner, { childList: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

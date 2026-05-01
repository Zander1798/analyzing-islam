// Entry actions — injects a Save button and Share button into every
// <div class="entry"> on catalog and category pages. Only visible when
// the user is signed in.
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function entryMetadata(entryEl) {
    const id = entryEl.id;
    const titleEl = entryEl.querySelector(".entry-title");
    const title = titleEl ? titleEl.textContent.trim() : "";
    const refEl = entryEl.querySelector(".ref");
    let ref = "";
    let url = "";
    if (refEl) {
      ref = refEl.textContent.trim();
      const a = refEl.querySelector("a");
      if (a) {
        url = a.href;
      }
    }
    const categories = (entryEl.getAttribute("data-category") || "").split(/\s+/).filter(Boolean);
    const strength = entryEl.getAttribute("data-strength") || "";
    // Source = the current catalog slug (e.g., "quran", "bukhari").
    // Primary: extract from the catalog page URL (/catalog/<source>.html).
    // Fallback: infer from the entry's ref link URL (/read/<source>.html),
    // which is present on category pages and other non-catalog views.
    let source = null;
    const m = location.pathname.match(/\/catalog\/([^/.]+)\.html/);
    if (m) {
      source = m[1];
    } else if (url) {
      try {
        const rm = new URL(url, location.href).pathname.match(/\/read\/([^/.]+)\.html/);
        if (rm) source = rm[1];
      } catch (_) {}
    }
    return {
      entry_id: id,
      entry_title: title,
      entry_ref: ref,
      entry_url: url || (location.origin + location.pathname + "#" + id),
      source,
      strength,
      categories,
    };
  }

  function renderSaveButton(entryEl, isSaved) {
    let btn = entryEl.querySelector(".entry-save-btn");
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button";
      btn.className = "entry-save-btn";
      const header = entryEl.querySelector(".entry-header");
      if (header) header.appendChild(btn);
      else entryEl.insertBefore(btn, entryEl.firstChild);

      btn.addEventListener("click", async function () {
        if (!window.AI_BOOKMARKS) return;
        btn.disabled = true;
        const result = await window.AI_BOOKMARKS.toggle(entryMetadata(entryEl));
        btn.disabled = false;
        if (result === "added") {
          renderSaveButton(entryEl, true);
        } else if (result === "removed") {
          renderSaveButton(entryEl, false);
        } else {
          btn.textContent = "Error";
          setTimeout(() => renderSaveButton(entryEl, isSaved), 1500);
        }
      });
    }
    btn.textContent = isSaved ? "★ Saved" : "☆ Save";
    btn.classList.toggle("is-saved", !!isSaved);
    btn.setAttribute("aria-pressed", isSaved ? "true" : "false");
  }

  function renderShareButton(entryEl) {
    if (!entryEl.id) return;
    if (entryEl.querySelector(".entry-share-btn")) return;

    const header = entryEl.querySelector(".entry-header");
    if (!header) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "entry-share-btn";
    btn.textContent = "Share";
    btn.title = "Copy a direct link to this entry";
    header.appendChild(btn);

    btn.addEventListener("click", async function () {
      // The direct URL to this entry is the current page + its anchor.
      const shareUrl = location.origin + location.pathname + "#" + entryEl.id;

      let ok = false;
      try {
        await navigator.clipboard.writeText(shareUrl);
        ok = true;
      } catch {
        // Fallback for browsers/contexts without clipboard API.
        try {
          const ta = document.createElement("textarea");
          ta.value = shareUrl;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.select();
          ok = document.execCommand("copy");
          document.body.removeChild(ta);
        } catch {
          ok = false;
        }
      }

      const originalLabel = "Share";
      btn.textContent = ok ? "Copied" : "Copy failed";
      btn.classList.add("just-copied");
      setTimeout(function () {
        btn.textContent = originalLabel;
        btn.classList.remove("just-copied");
      }, 1500);
    });
  }

  async function hydrate() {
    const entries = document.querySelectorAll("div.entry");
    if (!entries.length) return;

    // The Share button is visible for everyone — no auth required.
    entries.forEach(function (entryEl) {
      renderShareButton(entryEl);
    });

    const signedIn = !!(window.__session && window.__session.user);
    if (!signedIn) {
      // Remove stale signed-in-only widgets if the user signed out mid-session.
      entries.forEach((e) => {
        e.querySelectorAll(".entry-save-btn")
          .forEach((el) => el.remove());
      });
      return;
    }

    if (!window.AI_BOOKMARKS) return;

    const set = await window.AI_BOOKMARKS.loadSet(true);
    entries.forEach((entryEl) => {
      if (!entryEl.id) return;
      renderSaveButton(entryEl, set.has(entryEl.id));
    });
  }

  ready(function () {
    // Wait for the first auth check to resolve so we render the right state.
    if (window.__authReady && window.__authReady.then) {
      window.__authReady.then(hydrate);
    } else {
      setTimeout(hydrate, 200);
    }

    window.addEventListener("auth-state", hydrate);
    window.addEventListener("bookmarks-changed", function (e) {
      // When a bookmark is added/removed elsewhere (e.g., from saved.html),
      // update the button on this page too.
      if (!e.detail || !e.detail.entry_id) return;
      const el = document.getElementById(e.detail.entry_id);
      if (!el) return;
      if (e.detail.action === "added") renderSaveButton(el, true);
      else if (e.detail.action === "removed") renderSaveButton(el, false);
    });
  });
})();

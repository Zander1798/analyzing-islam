// Entry actions — injects a Save button and Note toggle into every
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
    // Fall back to "catalog" on category pages.
    let source = null;
    const m = location.pathname.match(/\/catalog\/([^/.]+)\.html/);
    if (m) source = m[1];
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

  function renderNoteToggle(entryEl) {
    if (entryEl.querySelector(".entry-note-toggle")) return;

    const header = entryEl.querySelector(".entry-header");
    if (!header) return;

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "entry-note-toggle";
    toggle.textContent = "✎ Note";
    toggle.setAttribute("aria-expanded", "false");
    header.appendChild(toggle);

    // Panel hidden by default, appears after the <section>
    const panel = document.createElement("div");
    panel.className = "entry-note-panel";
    panel.hidden = true;
    panel.innerHTML =
      '<textarea placeholder="Your private notes about this entry — only you can see them."></textarea>' +
      '<div class="entry-note-actions">' +
      '  <button type="button" class="entry-note-save">Save note</button>' +
      '  <button type="button" class="entry-note-delete">Delete</button>' +
      '  <span class="entry-note-status"></span>' +
      "</div>";
    entryEl.appendChild(panel);

    const textarea = panel.querySelector("textarea");
    const saveBtn = panel.querySelector(".entry-note-save");
    const deleteBtn = panel.querySelector(".entry-note-delete");
    const status = panel.querySelector(".entry-note-status");
    let loaded = false;

    toggle.addEventListener("click", async function () {
      const opening = panel.hidden;
      panel.hidden = !opening;
      toggle.setAttribute("aria-expanded", opening ? "true" : "false");

      if (opening && !loaded && window.AI_BOOKMARKS) {
        loaded = true;
        status.textContent = "Loading…";
        const note = await window.AI_BOOKMARKS.getNote(entryEl.id);
        if (note && note.content) {
          textarea.value = note.content;
          status.textContent = "Last saved " + new Date(note.updated_at).toLocaleString();
        } else {
          status.textContent = "";
        }
      }
    });

    saveBtn.addEventListener("click", async function () {
      if (!window.AI_BOOKMARKS) return;
      saveBtn.disabled = true;
      status.textContent = "Saving…";
      const saved = await window.AI_BOOKMARKS.saveNote(entryEl.id, textarea.value);
      saveBtn.disabled = false;
      if (saved) {
        status.textContent = "Saved " + new Date(saved.updated_at).toLocaleString();
      } else {
        status.textContent = "Save failed.";
      }
    });

    deleteBtn.addEventListener("click", async function () {
      if (!window.AI_BOOKMARKS) return;
      if (!confirm("Delete this note?")) return;
      deleteBtn.disabled = true;
      await window.AI_BOOKMARKS.deleteNote(entryEl.id);
      textarea.value = "";
      status.textContent = "Deleted.";
      deleteBtn.disabled = false;
    });
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
        e.querySelectorAll(".entry-save-btn, .entry-note-toggle, .entry-note-panel")
          .forEach((el) => el.remove());
      });
      return;
    }

    if (!window.AI_BOOKMARKS) return;

    const set = await window.AI_BOOKMARKS.loadSet(true);
    entries.forEach((entryEl) => {
      if (!entryEl.id) return;
      renderSaveButton(entryEl, set.has(entryEl.id));
      renderNoteToggle(entryEl);
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

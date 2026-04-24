/* =============================================================
   Analyzing Islam — Community lightbox
   -------------------------------------------------------------
   Clicking any image or video embedded inside a post body, an
   attached build, a comment, or a feed snippet opens it in a
   full-screen overlay. Close with the X button, the backdrop,
   or the ESC key.
   ============================================================= */
(function () {
  "use strict";

  // Only lift images/videos that are inside actual post content — not
  // site chrome (avatars, icons, nav). Covers:
  //   - full post body           .cf-post-full-content
  //   - feed snippet preview      .cf-post-snippet
  //   - attached build preview    .cf-attached-build-body
  //   - comment body              .cf-comment-body
  const SELECTOR = [
    ".cf-post-full-content img",
    ".cf-post-full-content video",
    ".cf-post-snippet img",
    ".cf-post-snippet video",
    ".cf-attached-build-body img",
    ".cf-attached-build-body video",
    ".cf-comment-body img",
    ".cf-comment-body video",
  ].join(",");

  let overlay = null;
  let lastFocus = null;

  function ensureOverlay() {
    if (overlay) return overlay;
    overlay = document.createElement("div");
    overlay.className = "cf-lightbox";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Media viewer");
    overlay.innerHTML =
      '<button type="button" class="cf-lightbox-close" aria-label="Close">✕</button>' +
      '<div class="cf-lightbox-stage"></div>';
    overlay.addEventListener("click", function (e) {
      // Close when clicking the backdrop (overlay itself) or the X button.
      // Clicks landing on the media element or inside the stage fall through.
      if (e.target === overlay) return close();
      if (e.target.closest(".cf-lightbox-close")) return close();
    });
    document.body.appendChild(overlay);
    return overlay;
  }

  function open(el) {
    ensureOverlay();
    const stage = overlay.querySelector(".cf-lightbox-stage");
    stage.innerHTML = "";

    let node = null;
    if (el.tagName === "IMG") {
      node = document.createElement("img");
      node.src = el.currentSrc || el.src;
      if (el.alt) node.alt = el.alt;
    } else if (el.tagName === "VIDEO") {
      node = document.createElement("video");
      node.src = el.currentSrc || el.src;
      node.controls = true;
      node.autoplay = true;
      node.playsInline = true;
      // Don't have two copies playing at once.
      try { el.pause(); } catch (_) {}
    }
    if (!node) return;

    stage.appendChild(node);
    overlay.classList.add("is-open");
    document.body.classList.add("cf-lightbox-open");
    lastFocus = document.activeElement;
    const closeBtn = overlay.querySelector(".cf-lightbox-close");
    if (closeBtn && closeBtn.focus) closeBtn.focus();
  }

  function close() {
    if (!overlay || !overlay.classList.contains("is-open")) return;
    overlay.classList.remove("is-open");
    document.body.classList.remove("cf-lightbox-open");

    const stage = overlay.querySelector(".cf-lightbox-stage");
    const v = stage && stage.querySelector("video");
    if (v) { try { v.pause(); } catch (_) {} }
    if (stage) stage.innerHTML = "";

    if (lastFocus && typeof lastFocus.focus === "function") {
      try { lastFocus.focus(); } catch (_) {}
    }
    lastFocus = null;
  }

  // Event delegation so new posts / comments loaded after page start
  // pick up the behavior automatically.
  document.addEventListener("click", function (e) {
    // Let the user use the standard "open in new tab" modifier clicks.
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (e.button !== undefined && e.button !== 0) return;

    const target = e.target.closest(SELECTOR);
    if (!target) return;

    // If the image/video is already wrapped in its own <a href> link,
    // respect that — don't hijack it.
    const link = target.closest("a[href]");
    if (link) return;

    e.preventDefault();
    open(target);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlay && overlay.classList.contains("is-open")) {
      close();
    }
  });
})();

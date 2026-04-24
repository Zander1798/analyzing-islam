/* =============================================================
   Analyzing Islam
   Universal hash-anchor scroll snapper
   -------------------------------------------------------------
   Problem: style.css sets `html { scroll-behavior: smooth }`,
   and the native hash-scroll fires before late-loading fonts
   and images settle. A link like `read/quran.html#s5v43` can
   therefore land SHORT of the target verse, leaving it off
   screen or far below the fold.

   Fix: on load + hashchange, force-snap to the target with
   `behavior: "instant"` (bypasses the CSS smooth rule) and
   re-snap a few times so late layout shifts get corrected.
   The target's heading sits just below the sticky site nav.
   ============================================================= */

(function () {
  "use strict";

  function getNavHeight() {
    const nav = document.querySelector(".site-nav");
    return nav ? nav.getBoundingClientRect().height : 70;
  }

  function snap() {
    const hash = window.location.hash;
    if (!hash || hash.length < 2) return;
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { id = hash.slice(1); }
    const target = document.getElementById(id);
    if (!target) return;
    const offset = getNavHeight() + 16;
    const rect = target.getBoundingClientRect();
    const top = rect.top + window.pageYOffset - offset;
    window.scrollTo({ top: top, left: 0, behavior: "instant" });
  }

  // Exposed so other scripts (e.g. catalog's app.js, which first has to
  // clear filters that hide the target) can trigger a re-snap.
  window.__snapToHash = snap;

  function schedule() {
    snap();
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(snap);
    }
    setTimeout(snap, 150);
    setTimeout(snap, 400);
  }

  if (document.readyState === "complete") {
    schedule();
  } else {
    window.addEventListener("load", schedule);
  }
  window.addEventListener("hashchange", schedule);
})();

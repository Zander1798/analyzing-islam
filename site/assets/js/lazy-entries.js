/* ============================================================
   lazy-entries.js
   Progressive batch reveal for pages that list entries but
   have no filter bar (category pages, argument index pages,
   etc.).  Works independently — does not require app.js.

   Entries beyond the first BATCH are hidden (display:none) so
   the browser skips their layout on initial paint. They are
   revealed in batches of BATCH as the user scrolls, or all
   at once if a hash anchor points to a pending entry.
   ============================================================ */
(function () {
  "use strict";

  var BATCH = 50;

  var container = document.getElementById("entries-container");
  if (!container) return;

  var entries = Array.from(container.querySelectorAll(".entry"));
  if (entries.length <= BATCH) return;

  // If the page was loaded with a hash anchor, reveal everything immediately
  // so the browser can snap to the target without extra JS.
  if (window.location.hash) return;

  // ── Hide pending entries ─────────────────────────────────────────────────
  var pendingSet = new Set();

  for (var i = BATCH; i < entries.length; i++) {
    entries[i].style.display = "none";
    pendingSet.add(entries[i]);
  }

  // ── Sentinel ─────────────────────────────────────────────────────────────
  // A zero-height div placed after the last visible entry. When it scrolls
  // into view (with a generous rootMargin), the next batch is revealed and
  // the sentinel advances to the new batch boundary.

  var sentinel = document.createElement("div");
  sentinel.setAttribute("aria-hidden", "true");
  sentinel.style.cssText = "height:1px;margin:0;padding:0;pointer-events:none;";
  entries[BATCH - 1].insertAdjacentElement("afterend", sentinel);

  // ── Batch reveal ─────────────────────────────────────────────────────────
  function loadNextBatch() {
    var lastRevealed = null;
    var count = 0;

    for (var entry of pendingSet) {
      entry.style.display = "";
      pendingSet.delete(entry);
      lastRevealed = entry;
      if (++count >= BATCH) break;
    }

    if (pendingSet.size === 0) {
      obs.disconnect();
      sentinel.remove();
    } else if (lastRevealed) {
      // Advance sentinel to after the new batch boundary
      lastRevealed.insertAdjacentElement("afterend", sentinel);
    }
  }

  // ── IntersectionObserver ─────────────────────────────────────────────────
  var obs = new IntersectionObserver(
    function (entries) { if (entries[0].isIntersecting) loadNextBatch(); },
    { rootMargin: "600px" } // start loading 600px before sentinel reaches viewport
  );
  obs.observe(sentinel);

  // ── Hash anchor navigation within the page ───────────────────────────────
  // If the user clicks a permalink (#entry-id) that points to a pending entry,
  // reveal everything and let snap-to-hash.js handle the scroll.
  function revealForHash() {
    if (!pendingSet.size) return;
    var hash = window.location.hash;
    if (!hash || hash.length < 2) return;
    var id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { id = hash.slice(1); }
    var target = document.getElementById(id);
    if (!target || !pendingSet.has(target)) return;

    // Reveal all pending entries
    pendingSet.forEach(function (e) { e.style.display = ""; });
    pendingSet.clear();
    obs.disconnect();
    sentinel.remove();

    // Re-snap after layout settles
    if (typeof window.__snapToHash === "function") {
      requestAnimationFrame(window.__snapToHash);
      setTimeout(window.__snapToHash, 150);
    }
  }

  window.addEventListener("hashchange", revealForHash);
})();

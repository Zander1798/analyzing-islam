/* ============================================
   Analyzing Islam
   Catalog filters + search + URL query params
   + Progressive lazy reveal (IntersectionObserver)
   ============================================ */

(function () {
  "use strict";

  // Only run on pages that have the entries container
  const entriesContainer = document.getElementById("entries-container");
  if (!entriesContainer) return;

  // ── Constants ─────────────────────────────────────────────────────────────
  const LAZY_BATCH = 50; // entries per scroll batch

  // ── State ─────────────────────────────────────────────────────────────────
  const state = {
    category: "all",
    strength: "all",
    search: "",
  };

  // ── DOM references ────────────────────────────────────────────────────────
  const entries = Array.from(document.querySelectorAll(".entry"));
  const totalCountEl  = document.getElementById("total-count");
  const visibleCountEl = document.getElementById("visible-count");
  const emptyState    = document.getElementById("empty-state");
  const searchInput   = document.getElementById("search");

  if (totalCountEl) totalCountEl.textContent = entries.length;

  // ── Lazy loading ──────────────────────────────────────────────────────────
  // On initial page load (no filter/search/hash in URL), entries beyond the
  // first LAZY_BATCH are hidden (display:none) so the browser skips their
  // layout. They are revealed progressively as the user scrolls, or all at
  // once if the user applies any filter or search.

  const pendingSet = new Set(); // entries not yet rendered
  let lazyObserver = null;
  let lazySentinel = null;

  function initLazyLoad() {
    if (entries.length <= LAZY_BATCH) return; // not worth it

    // If URL has filter/search params or a hash anchor, skip lazy loading —
    // the user expects to see a specific subset or jump to a specific entry.
    const params = new URLSearchParams(window.location.search);
    if (params.has("category") || params.has("strength") || params.has("q")) return;
    if (window.location.hash) return;

    // Mark entries beyond the first batch as pending (display:none)
    for (var i = LAZY_BATCH; i < entries.length; i++) {
      entries[i].style.display = "none";
      pendingSet.add(entries[i]);
    }

    // Sentinel: a zero-height div placed after the last visible entry.
    // When it scrolls into view, the next batch is revealed.
    lazySentinel = document.createElement("div");
    lazySentinel.setAttribute("aria-hidden", "true");
    lazySentinel.style.cssText = "height:1px;margin:0;padding:0;pointer-events:none;";
    entries[LAZY_BATCH - 1].insertAdjacentElement("afterend", lazySentinel);

    lazyObserver = new IntersectionObserver(
      function (obs) { if (obs[0].isIntersecting) loadNextBatch(); },
      { rootMargin: "600px" } // start loading 600px before sentinel hits viewport
    );
    lazyObserver.observe(lazySentinel);
  }

  function loadNextBatch() {
    var lastRevealed = null;
    var count = 0;

    for (var entry of pendingSet) {
      // Only show the entry if it is not currently filtered out
      if (!entry.classList.contains("hidden")) {
        entry.style.display = "";
      }
      pendingSet.delete(entry);
      lastRevealed = entry;
      if (++count >= LAZY_BATCH) break;
    }

    if (pendingSet.size === 0) {
      // All entries loaded — remove observer and sentinel
      if (lazyObserver) { lazyObserver.disconnect(); lazyObserver = null; }
      if (lazySentinel) { lazySentinel.remove(); lazySentinel = null; }
    } else if (lastRevealed) {
      // Advance sentinel to after the last revealed entry
      lastRevealed.insertAdjacentElement("afterend", lazySentinel);
    }
  }

  function revealAllPending() {
    if (pendingSet.size === 0) return;
    pendingSet.forEach(function (entry) {
      // Reveal now; applyFilters() will re-hide non-matching ones right after
      entry.style.display = "";
    });
    pendingSet.clear();
    if (lazyObserver) { lazyObserver.disconnect(); lazyObserver = null; }
    if (lazySentinel) { lazySentinel.remove(); lazySentinel = null; }
  }

  // ── Text cache ────────────────────────────────────────────────────────────
  // Built on first search; reused on subsequent keystrokes.
  const textCache = new WeakMap();
  function getEntryText(entry) {
    if (!textCache.has(entry)) {
      textCache.set(entry, entry.textContent.toLowerCase());
    }
    return textCache.get(entry);
  }

  // ── Filter application ────────────────────────────────────────────────────
  function applyFilters() {
    const query = state.search.toLowerCase().trim();
    const hasFilter =
      state.category !== "all" || state.strength !== "all" || query;

    // If any filter or search is active, all entries must be in the DOM so
    // the full matching set is visible. Pending (display:none) entries are
    // revealed here; applyFilters will hide the non-matching ones immediately.
    if (hasFilter) revealAllPending();

    let visible = 0;

    entries.forEach(function (entry) {
      const cats      = (entry.dataset.category || "").split(" ");
      const strengths = (entry.dataset.strength  || "").split(" ");

      const catOk      = state.category === "all" || cats.includes(state.category);
      const strengthOk = state.strength === "all" || strengths.includes(state.strength);
      const searchOk   = !query || getEntryText(entry).includes(query);

      if (catOk && strengthOk && searchOk) {
        entry.classList.remove("hidden");
        // Only clear display:none if the entry is not pending (pending entries
        // will be revealed by scroll; filtering doesn't force their reveal
        // unless hasFilter is true, which already called revealAllPending()).
        if (!pendingSet.has(entry)) {
          entry.style.display = "";
        }
        visible++;
      } else {
        entry.classList.add("hidden");
        entry.style.display = ""; // ensure hidden-by-filter entries aren't also display:none
      }
    });

    if (visibleCountEl) visibleCountEl.textContent = visible;
    if (emptyState) emptyState.style.display = visible === 0 ? "block" : "none";
  }

  // ── Chip interaction ──────────────────────────────────────────────────────
  function setFilter(type, value) {
    state[type] = value;
    document
      .querySelectorAll('.chip[data-filter-type="' + type + '"]')
      .forEach(function (c) { c.classList.remove("active"); });
    const target = document.querySelector(
      '.chip[data-filter-type="' + type + '"][data-filter-value="' + value + '"]'
    );
    if (target) target.classList.add("active");
    applyFilters();
    updateURL();
  }

  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      setFilter(chip.dataset.filterType, chip.dataset.filterValue);
    });
  });

  // ── Search input ──────────────────────────────────────────────────────────
  if (searchInput) {
    let searchTimer = null;
    searchInput.addEventListener("input", function (e) {
      state.search = e.target.value;
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function () { applyFilters(); updateURL(); }, 100);
    });
  }

  // ── URL query params ──────────────────────────────────────────────────────
  function readURL() {
    const params = new URLSearchParams(window.location.search);
    const cat = params.get("category");
    const str = params.get("strength");
    const q   = params.get("q");

    if (cat) state.category = cat;
    if (str) state.strength = str;
    if (q)   {
      state.search = q;
      if (searchInput) searchInput.value = q;
    }

    // Sync active chip highlights to URL state
    ["category", "strength"].forEach(function (type) {
      document
        .querySelectorAll('.chip[data-filter-type="' + type + '"]')
        .forEach(function (c) { c.classList.remove("active"); });
      const chip = document.querySelector(
        '.chip[data-filter-type="' + type + '"][data-filter-value="' + state[type] + '"]'
      );
      if (chip) chip.classList.add("active");
    });
  }

  function updateURL() {
    const params = new URLSearchParams();
    if (state.category !== "all") params.set("category", state.category);
    if (state.strength !== "all") params.set("strength", state.strength);
    if (state.search)             params.set("q", state.search);

    const newURL =
      window.location.pathname +
      (params.toString() ? "?" + params.toString() : "") +
      window.location.hash;

    window.history.replaceState(null, "", newURL);
  }

  // ── Entry deep-link anchors ───────────────────────────────────────────────
  entries.forEach(function (entry) {
    if (!entry.id) return;
    const header = entry.querySelector(".entry-header");
    if (!header) return;
    const link = document.createElement("a");
    link.href       = "#" + entry.id;
    link.className  = "entry-link";
    link.title      = "Permalink to this entry";
    link.setAttribute("aria-label", "Copy link to this entry");
    link.textContent = "#";
    link.addEventListener("click", function () {
      setTimeout(function () {
        if (navigator.clipboard) {
          navigator.clipboard.writeText(window.location.href).catch(function () {});
        }
      }, 0);
    });
    header.appendChild(link);
  });

  // ── Hash anchor: clear filters (and pending) if target is hidden ──────────
  // snap-to-hash.js handles the actual scroll. We handle two catalog-specific
  // cases here:
  //   1. Target is filtered out (.hidden class) — clear filters
  //   2. Target is lazy-pending (display:none but not .hidden) — reveal all
  function revealHashEntry() {
    const hash = window.location.hash;
    if (!hash || hash.length < 2) return;
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { id = hash.slice(1); }
    const target = document.getElementById(id);
    if (!target || !target.classList.contains("entry")) return;

    // Case 1: entry is lazy-pending — reveal all pending, re-snap
    if (pendingSet.has(target)) {
      revealAllPending();
      applyFilters();
      if (typeof window.__snapToHash === "function") {
        requestAnimationFrame(window.__snapToHash);
        setTimeout(window.__snapToHash, 150);
      }
      return;
    }

    // Case 2: entry is filtered out — clear filters, re-snap
    if (!target.classList.contains("hidden")) return;

    state.category = "all";
    state.strength = "all";
    state.search   = "";
    if (searchInput) searchInput.value = "";
    ["category", "strength"].forEach(function (type) {
      document
        .querySelectorAll('.chip[data-filter-type="' + type + '"]')
        .forEach(function (c) { c.classList.remove("active"); });
      const chip = document.querySelector(
        '.chip[data-filter-type="' + type + '"][data-filter-value="all"]'
      );
      if (chip) chip.classList.add("active");
    });
    applyFilters();
    updateURL();
    if (typeof window.__snapToHash === "function") {
      requestAnimationFrame(window.__snapToHash);
      setTimeout(window.__snapToHash, 150);
    }
  }

  if (document.readyState === "complete") {
    revealHashEntry();
  } else {
    window.addEventListener("load", revealHashEntry);
  }
  window.addEventListener("hashchange", revealHashEntry);

  // ── Initialize ────────────────────────────────────────────────────────────
  initLazyLoad(); // must run BEFORE applyFilters so pending entries are known
  readURL();
  applyFilters();

})();

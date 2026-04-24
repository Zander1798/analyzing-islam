/* ============================================
   Analyzing Islam
   Catalog filters + search + URL query params
   ============================================ */

(function () {
  "use strict";

  // Only run on the catalog page (if these elements don't exist, bail out)
  const entriesContainer = document.getElementById("entries-container");
  if (!entriesContainer) return;

  const state = {
    category: "all",
    strength: "all",
    search: "",
  };

  const entries = document.querySelectorAll(".entry");
  const totalCountEl = document.getElementById("total-count");
  const visibleCountEl = document.getElementById("visible-count");
  const emptyState = document.getElementById("empty-state");
  const searchInput = document.getElementById("search");

  if (totalCountEl) totalCountEl.textContent = entries.length;

  // --- Filter application ---
  function applyFilters() {
    const query = state.search.toLowerCase().trim();
    let visible = 0;

    entries.forEach((entry) => {
      const cats = (entry.dataset.category || "").split(" ");
      const strengths = (entry.dataset.strength || "").split(" ");
      const text = entry.textContent.toLowerCase();

      const catOk = state.category === "all" || cats.includes(state.category);
      const strengthOk =
        state.strength === "all" || strengths.includes(state.strength);
      const searchOk = !query || text.includes(query);

      if (catOk && strengthOk && searchOk) {
        entry.classList.remove("hidden");
        visible++;
      } else {
        entry.classList.add("hidden");
      }
    });

    if (visibleCountEl) visibleCountEl.textContent = visible;
    if (emptyState) emptyState.style.display = visible === 0 ? "block" : "none";
  }

  // --- Chip interaction ---
  function setFilter(type, value) {
    state[type] = value;
    document
      .querySelectorAll('.chip[data-filter-type="' + type + '"]')
      .forEach((c) => c.classList.remove("active"));
    const target = document.querySelector(
      '.chip[data-filter-type="' + type + '"][data-filter-value="' + value + '"]'
    );
    if (target) target.classList.add("active");
    applyFilters();
    updateURL();
  }

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      setFilter(chip.dataset.filterType, chip.dataset.filterValue);
    });
  });

  // --- Search input ---
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      state.search = e.target.value;
      applyFilters();
      updateURL();
    });
  }

  // --- URL query params: read on load, update on change ---
  function readURL() {
    const params = new URLSearchParams(window.location.search);
    const cat = params.get("category");
    const str = params.get("strength");
    const q = params.get("q");

    if (cat) state.category = cat;
    if (str) state.strength = str;
    if (q) {
      state.search = q;
      if (searchInput) searchInput.value = q;
    }

    // Update active chips to reflect state
    ["category", "strength"].forEach((type) => {
      document
        .querySelectorAll('.chip[data-filter-type="' + type + '"]')
        .forEach((c) => c.classList.remove("active"));
      const target = document.querySelector(
        '.chip[data-filter-type="' + type + '"][data-filter-value="' + state[type] + '"]'
      );
      if (target) target.classList.add("active");
    });
  }

  function updateURL() {
    const params = new URLSearchParams();
    if (state.category !== "all") params.set("category", state.category);
    if (state.strength !== "all") params.set("strength", state.strength);
    if (state.search) params.set("q", state.search);

    const newURL =
      window.location.pathname +
      (params.toString() ? "?" + params.toString() : "") +
      window.location.hash;

    // replaceState keeps the back button clean (no history pollution from typing)
    window.history.replaceState(null, "", newURL);
  }

  // --- Entry deep-link anchors: add copy-link buttons ---
  entries.forEach((entry) => {
    if (!entry.id) return;
    const header = entry.querySelector(".entry-header");
    if (!header) return;
    const link = document.createElement("a");
    link.href = "#" + entry.id;
    link.className = "entry-link";
    link.title = "Permalink to this entry";
    link.setAttribute("aria-label", "Copy link to this entry");
    link.textContent = "#";
    link.addEventListener("click", (e) => {
      // Let the hash change naturally, then copy to clipboard
      setTimeout(() => {
        if (navigator.clipboard) {
          navigator.clipboard
            .writeText(window.location.href)
            .catch(() => {});
        }
      }, 0);
    });
    header.appendChild(link);
  });

  // --- Hash anchor: land precisely on the entry's heading at the top ---
  // html{scroll-behavior:smooth} is set globally, so behavior:"auto" inherits
  // it and still animates — losing the race with late-loading fonts/images
  // that shift the target. We force behavior:"instant" to bypass the CSS,
  // and re-run across several frames so any post-load layout shift (fonts
  // settling, image reflow, filter-chip wrap) gets snapped out.
  function scrollToHashEntry() {
    const hash = window.location.hash;
    if (!hash || hash.length < 2) return;
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { id = hash.slice(1); }
    const target = document.getElementById(id);
    if (!target || !target.classList.contains("entry")) return;

    // If a filter hides the target, clear filters so the user can see it.
    if (target.classList.contains("hidden")) {
      state.category = "all";
      state.strength = "all";
      state.search = "";
      if (searchInput) searchInput.value = "";
      ["category", "strength"].forEach((type) => {
        document
          .querySelectorAll('.chip[data-filter-type="' + type + '"]')
          .forEach((c) => c.classList.remove("active"));
        const chip = document.querySelector(
          '.chip[data-filter-type="' + type + '"][data-filter-value="all"]'
        );
        if (chip) chip.classList.add("active");
      });
      applyFilters();
      updateURL();
    }

    const nav = document.querySelector(".site-nav");
    const navHeight = nav ? nav.getBoundingClientRect().height : 70;
    const offset = navHeight + 16;
    const rect = target.getBoundingClientRect();
    const top = rect.top + window.pageYOffset - offset;
    window.scrollTo({ top, left: 0, behavior: "instant" });
  }

  function snapToHashEntry() {
    scrollToHashEntry();
    requestAnimationFrame(scrollToHashEntry);
    setTimeout(scrollToHashEntry, 150);
    setTimeout(scrollToHashEntry, 400);
  }

  if (document.readyState === "complete") {
    snapToHashEntry();
  } else {
    window.addEventListener("load", snapToHashEntry);
  }
  window.addEventListener("hashchange", snapToHashEntry);

  // --- Initialize ---
  readURL();
  applyFilters();
})();

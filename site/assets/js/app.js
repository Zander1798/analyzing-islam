/* ============================================
   Islam Analyzed
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

  // --- Initialize ---
  readURL();
  applyFilters();
})();

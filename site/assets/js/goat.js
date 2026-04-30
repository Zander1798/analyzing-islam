// Nav goat button: injects the goat into the site nav. Click navigates to goat.html.
// Animations and skins will be GIF-based — old CSS animation system removed.
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

  function buildNavGoatSvg() {
    if (window.GoatSkins && typeof window.GoatSkins.buildSvg === "function") {
      const id = window.GoatSkins.getSelectedId();
      return window.GoatSkins.buildSvg(id, { withGrass: true });
    }
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("class", "goat-svg");
    svg.setAttribute("viewBox", "0 0 24 20");
    return svg;
  }

  function repaintNavGoat(btn) {
    const old = btn.querySelector(".goat-svg");
    const next = buildNavGoatSvg();
    if (old) old.replaceWith(next);
    else btn.insertBefore(next, btn.firstChild);
  }

  function init() {
    const navInner = document.querySelector(".site-nav-inner");
    if (!navInner) return;
    if (navInner.querySelector(".goat-scream")) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "goat-scream";
    btn.setAttribute("aria-label", "Goat page");
    btn.title = "Click me for the Goat page";
    btn.appendChild(buildNavGoatSvg());
    navInner.appendChild(btn);

    btn.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      window.location.href = (assetPrefix() || "") + "goat.html";
    });

    window.addEventListener("aig:skin-changed", function () { repaintNavGoat(btn); });
    window.addEventListener("storage", function (e) {
      if (e.key === "aig:goat-skin") repaintNavGoat(btn);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // --- Hide nav on scroll-down, reveal on scroll-up ---------------------
  function initNavAutoHide() {
    const nav = document.querySelector(".site-nav");
    if (!nav) return;

    const DELTA = 8;
    const REVEAL_NEAR_TOP = 80;
    let lastY = window.scrollY || 0;
    let ticking = false;

    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        const y = window.scrollY || 0;
        const delta = y - lastY;
        // On mobile always keep the nav visible — only auto-hide on desktop.
        if (window.innerWidth <= 768) {
          nav.classList.remove("is-hidden");
        } else if (y < REVEAL_NEAR_TOP) {
          nav.classList.remove("is-hidden");
        } else if (delta > DELTA) {
          nav.classList.add("is-hidden");
        } else if (delta < -DELTA) {
          nav.classList.remove("is-hidden");
        }
        if (Math.abs(delta) > DELTA || y < REVEAL_NEAR_TOP) lastY = y;
        ticking = false;
      });
    }

    window.addEventListener("scroll", onScroll, { passive: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNavAutoHide);
  } else {
    initNavAutoHide();
  }

  // --- Embed mode (for iframes on the Compare page) ---------------------
  function applyEmbedMode() {
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.get("embed") === "1") {
        document.documentElement.classList.add("embed-mode");
        document.body && document.body.classList.add("embed-mode");
      }
    } catch (_) {}
  }
  applyEmbedMode();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyEmbedMode);
  }
})();

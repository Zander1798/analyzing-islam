// Resizable splitter between two adjacent panes.
//
// Declarative: drop a <div class="splitter" data-splitter-var="..." ...> between
// two siblings inside a CSS grid/flex layout, and this script makes that div
// draggable. Dragging updates the named CSS variable on :root, which the
// layout's grid-template-columns reads as the left pane's width.
//
// Data attributes (on the splitter element):
//   data-splitter-var   — CSS variable to update (e.g. "--reader-toc-w").   REQUIRED
//   data-splitter-key   — localStorage key (defaults to the var name).
//   data-splitter-min   — min px for the left pane (default 140).
//   data-splitter-max   — max px for the left pane (default 600).
//   data-splitter-ref   — CSS selector for the "left pane" used to measure
//                          the drag delta. Defaults to previousElementSibling.
//
// Behaviour:
//   - Works with Pointer events (mouse + touch unified). Falls back to mouse + touch.
//   - Double-click resets the width (removes the inline var + purges localStorage).
//   - If the splitter is hidden by CSS (display:none on mobile), dragging is disabled.
//   - Saved width is restored on page load.
(function () {
  "use strict";

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  function initOne(el) {
    if (el.__splitterInited) return;
    el.__splitterInited = true;
    const cssVar = el.getAttribute("data-splitter-var");
    if (!cssVar) return;
    const key = "splitter:" + (el.getAttribute("data-splitter-key") || cssVar);
    const min = parseInt(el.getAttribute("data-splitter-min") || "140", 10);
    const max = parseInt(el.getAttribute("data-splitter-max") || "600", 10);
    const refSel = el.getAttribute("data-splitter-ref");
    const refEl = refSel ? document.querySelector(refSel) : el.previousElementSibling;
    if (!refEl) return;

    el.setAttribute("role", "separator");
    el.setAttribute("aria-orientation", "vertical");
    el.setAttribute("tabindex", "0");

    // Restore persisted width.
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        const px = clamp(parseInt(saved, 10) || 0, min, max);
        if (px) document.documentElement.style.setProperty(cssVar, px + "px");
      }
    } catch (_) {}

    let dragging = false;

    function isHidden() {
      return getComputedStyle(el).display === "none";
    }

    function currentX(e) {
      if (e.clientX !== undefined) return e.clientX;
      if (e.touches && e.touches[0]) return e.touches[0].clientX;
      return null;
    }

    function applyX(x) {
      const rect = refEl.getBoundingClientRect();
      const w = clamp(Math.round(x - rect.left), min, max);
      document.documentElement.style.setProperty(cssVar, w + "px");
    }

    function onDown(e) {
      if (isHidden()) return;
      dragging = true;
      el.classList.add("is-dragging");
      document.body.classList.add("splitter-dragging");
      if (e.pointerId !== undefined && el.setPointerCapture) {
        try { el.setPointerCapture(e.pointerId); } catch (_) {}
      }
      e.preventDefault();
    }

    function onMove(e) {
      if (!dragging) return;
      const x = currentX(e);
      if (x == null) return;
      applyX(x);
      e.preventDefault();
    }

    function onUp() {
      if (!dragging) return;
      dragging = false;
      el.classList.remove("is-dragging");
      document.body.classList.remove("splitter-dragging");
      // Persist whatever's currently set on :root.
      const val = document.documentElement.style.getPropertyValue(cssVar).trim();
      const px = parseInt(val, 10);
      if (px) {
        try { localStorage.setItem(key, px + ""); } catch (_) {}
      }
    }

    function onKey(e) {
      if (isHidden()) return;
      // Arrow keys nudge 16 px per press; Home/End jump to min/max.
      const step = e.shiftKey ? 40 : 16;
      let current = parseInt(
        document.documentElement.style.getPropertyValue(cssVar) ||
        getComputedStyle(refEl).width, 10
      ) || refEl.getBoundingClientRect().width;
      let next = current;
      if (e.key === "ArrowLeft") next = current - step;
      else if (e.key === "ArrowRight") next = current + step;
      else if (e.key === "Home") next = min;
      else if (e.key === "End") next = max;
      else return;
      next = clamp(next, min, max);
      document.documentElement.style.setProperty(cssVar, next + "px");
      try { localStorage.setItem(key, next + ""); } catch (_) {}
      e.preventDefault();
    }

    el.addEventListener("dblclick", function () {
      document.documentElement.style.removeProperty(cssVar);
      try { localStorage.removeItem(key); } catch (_) {}
    });

    el.addEventListener("keydown", onKey);

    if (window.PointerEvent) {
      el.addEventListener("pointerdown", onDown);
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    } else {
      el.addEventListener("mousedown", onDown);
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
      el.addEventListener("touchstart", onDown, { passive: false });
      window.addEventListener("touchmove", onMove, { passive: false });
      window.addEventListener("touchend", onUp);
    }
  }

  function initAll(root) {
    const scope = root || document;
    const nodes = scope.querySelectorAll(".splitter[data-splitter-var]");
    for (let i = 0; i < nodes.length; i++) initOne(nodes[i]);
  }

  // Public API so dynamically-built layouts (e.g. the Build editor) can
  // re-scan after they insert splitter markup.
  window.AI_SPLITTER = { init: initAll };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { initAll(); });
  } else {
    initAll();
  }
})();

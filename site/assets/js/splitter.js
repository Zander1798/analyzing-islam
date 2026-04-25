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
//   data-splitter-collapsible — "true" enables drag-to-zero with snap-back arrow.
//   data-splitter-default     — default width used when expanding from a
//                                collapsed state (defaults to min).
//   data-splitter-collapse-threshold — drag below this many px to snap to 0.
//
// Reader TOC splitters (data-splitter-key="reader-toc") get collapsibility
// automatically so you don't need to redeploy page markup.
//
// Behaviour:
//   - Pointer events (mouse + touch unified) with a mouse + touch fallback.
//   - Double-click resets the width.
//   - Hidden (display:none) splitters ignore drags.
//   - Saved width + collapsed state restored on load.
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
    // data-splitter-side="right" → splitter sits to the LEFT of the
    // resizable pane (rather than to its right). Used for the highlights
    // sidebar which lives at the far right of reader layouts. In that
    // mode `refEl` is the resizable pane itself (nextElementSibling), and
    // the drag formula inverts so that dragging LEFT grows the pane.
    const side = (el.getAttribute("data-splitter-side") || "left").toLowerCase();
    const isRight = side === "right";
    const refEl = refSel
      ? document.querySelector(refSel)
      : (isRight ? el.nextElementSibling : el.previousElementSibling);
    if (!refEl) return;

    // Reader TOCs default to collapsible — users want a "hide the chapter
    // list" button for immersive reading.
    const collapsible =
      el.getAttribute("data-splitter-collapsible") === "true" ||
      (el.getAttribute("data-splitter-key") || "") === "reader-toc";
    const collapseThreshold = parseInt(
      el.getAttribute("data-splitter-collapse-threshold") || "90", 10
    );
    const defaultPx = parseInt(
      el.getAttribute("data-splitter-default") || String(min), 10
    );

    el.setAttribute("role", "separator");
    el.setAttribute("aria-orientation", "vertical");
    el.setAttribute("tabindex", "0");

    // --- Expand button (only rendered on collapsible splitters) -----------
    let expandBtn = null;
    if (collapsible) {
      expandBtn = document.createElement("button");
      expandBtn.type = "button";
      expandBtn.className = "splitter-expand";
      expandBtn.setAttribute("aria-label", "Expand");
      expandBtn.innerHTML =
        '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">' +
          '<path d="M6 3 L11 8 L6 13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
        '</svg>';
      expandBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        expand();
      });
      // Prevent expand-button mousedown from starting a drag.
      expandBtn.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
      expandBtn.addEventListener("mousedown", function (e) { e.stopPropagation(); });
      expandBtn.addEventListener("touchstart", function (e) { e.stopPropagation(); }, { passive: true });
      el.appendChild(expandBtn);
    }

    function setCollapsed(on) {
      if (on) {
        document.documentElement.style.setProperty(cssVar, "0px");
        el.classList.add("is-collapsed");
        el.setAttribute("aria-expanded", "false");
      } else {
        el.classList.remove("is-collapsed");
        el.setAttribute("aria-expanded", "true");
      }
    }

    function expand() {
      const px = clamp(defaultPx, min, max);
      document.documentElement.style.setProperty(cssVar, px + "px");
      setCollapsed(false);
      try { localStorage.setItem(key, px + ""); } catch (_) {}
    }

    // Restore persisted state.
    try {
      const saved = localStorage.getItem(key);
      if (saved !== null) {
        const px = parseInt(saved, 10);
        if (!isNaN(px)) {
          if (px === 0 && collapsible) {
            document.documentElement.style.setProperty(cssVar, "0px");
            setCollapsed(true);
          } else if (px > 0) {
            const w = clamp(px, min, max);
            document.documentElement.style.setProperty(cssVar, w + "px");
            setCollapsed(false);
          }
        }
      }
    } catch (_) {}

    let dragging = false;
    // Cached at drag start so we don't call getBoundingClientRect() per move.
    // For left splitters: refLeft = left edge of left pane (used: w = x - refLeft).
    // For right splitters: refLeft = right edge of right pane (used: w = refLeft - x).
    let refLeft = 0;
    // Drag intent (where the left pane's right edge will land on release).
    // Updated via translateX on the ghost element — compositor-only, no reflow.
    let pendingX = null;
    let rafId = 0;

    // Ghost line: a fixed-position 2-pixel accent line that tracks the cursor
    // while dragging. We only update `transform: translateX()` on the ghost,
    // which the browser handles on the compositor without any text reflow.
    // The actual grid column resize (which DOES reflow every visible verse)
    // happens exactly once, on pointerup.
    let ghostEl = null;
    function ensureGhost() {
      if (ghostEl) return ghostEl;
      ghostEl = document.createElement("div");
      ghostEl.className = "splitter-ghost";
      document.body.appendChild(ghostEl);
      return ghostEl;
    }

    function isHidden() {
      return getComputedStyle(el).display === "none";
    }

    function currentX(e) {
      if (e.clientX !== undefined) return e.clientX;
      if (e.touches && e.touches[0]) return e.touches[0].clientX;
      return null;
    }

    // Given a raw pointer X, return the clamped final (refLeft + width) X
    // where the divider will actually land — so the ghost lines up exactly
    // with the post-release position.
    function resolveX(x) {
      let w = isRight ? Math.round(refLeft - x) : Math.round(x - refLeft);
      if (collapsible && w < collapseThreshold) {
        return refLeft; // ghost snaps back to the pane's anchored edge
      }
      const cw = clamp(w, min, max);
      return isRight ? (refLeft - cw) : (refLeft + cw);
    }

    function positionGhost() {
      rafId = 0;
      if (pendingX == null || !ghostEl) return;
      const x = resolveX(pendingX);
      ghostEl.style.transform = "translateX(" + x + "px)";
    }

    function schedule() {
      if (rafId) return;
      rafId = requestAnimationFrame(positionGhost);
    }

    function commitFinal() {
      if (pendingX == null) return;
      let w = isRight ? Math.round(refLeft - pendingX) : Math.round(pendingX - refLeft);
      if (collapsible && w < collapseThreshold) {
        document.documentElement.style.setProperty(cssVar, "0px");
        setCollapsed(true);
        return;
      }
      if (collapsible) setCollapsed(false);
      w = clamp(w, min, max);
      document.documentElement.style.setProperty(cssVar, w + "px");
    }

    function onDown(e) {
      if (isHidden()) return;
      if (e.target !== el) return;
      dragging = true;
      const rect = refEl.getBoundingClientRect();
      refLeft = isRight ? rect.right : rect.left;
      pendingX = currentX(e);
      el.classList.add("is-dragging");
      document.body.classList.add("splitter-dragging");
      // Spawn the ghost at the current splitter position so there's no jump.
      const ghost = ensureGhost();
      ghost.classList.add("is-visible");
      positionGhost();
      if (e.pointerId !== undefined && el.setPointerCapture) {
        try { el.setPointerCapture(e.pointerId); } catch (_) {}
      }
      e.preventDefault();
    }

    function onMove(e) {
      if (!dragging) return;
      const x = currentX(e);
      if (x == null) return;
      pendingX = x;
      schedule();
    }

    function onUp() {
      if (!dragging) return;
      dragging = false;
      if (rafId) { cancelAnimationFrame(rafId); rafId = 0; }
      el.classList.remove("is-dragging");
      document.body.classList.remove("splitter-dragging");
      // Remove the ghost, then commit the real resize in a single reflow.
      if (ghostEl) ghostEl.classList.remove("is-visible");
      commitFinal();
      pendingX = null;
      // Persist.
      if (collapsible && el.classList.contains("is-collapsed")) {
        try { localStorage.setItem(key, "0"); } catch (_) {}
        return;
      }
      const val = document.documentElement.style.getPropertyValue(cssVar).trim();
      const px = parseInt(val, 10);
      if (px) {
        try { localStorage.setItem(key, px + ""); } catch (_) {}
      }
    }

    function onKey(e) {
      if (isHidden()) return;
      const step = e.shiftKey ? 40 : 16;
      let current = parseInt(
        document.documentElement.style.getPropertyValue(cssVar) ||
        getComputedStyle(refEl).width, 10
      ) || refEl.getBoundingClientRect().width;
      let next = current;
      // For right-side splitters, arrow direction inverts (left grows the pane).
      if (e.key === "ArrowLeft")  next = current + (isRight ? step : -step);
      else if (e.key === "ArrowRight") next = current + (isRight ? -step : step);
      else if (e.key === "Home") next = collapsible ? 0 : min;
      else if (e.key === "End") next = max;
      else if (e.key === "Enter" || e.key === " ") {
        // Enter/Space on a collapsed splitter expands it.
        if (collapsible && el.classList.contains("is-collapsed")) {
          expand();
          e.preventDefault();
        }
        return;
      } else return;
      if (collapsible && next < collapseThreshold) {
        document.documentElement.style.setProperty(cssVar, "0px");
        setCollapsed(true);
        try { localStorage.setItem(key, "0"); } catch (_) {}
      } else {
        if (collapsible) setCollapsed(false);
        next = clamp(next, min, max);
        document.documentElement.style.setProperty(cssVar, next + "px");
        try { localStorage.setItem(key, next + ""); } catch (_) {}
      }
      e.preventDefault();
    }

    el.addEventListener("dblclick", function (e) {
      if (e.target !== el) return;
      document.documentElement.style.removeProperty(cssVar);
      setCollapsed(false);
      try { localStorage.removeItem(key); } catch (_) {}
    });

    el.addEventListener("keydown", onKey);

    if (window.PointerEvent) {
      el.addEventListener("pointerdown", onDown);
      el.addEventListener("pointermove", onMove);
      el.addEventListener("pointerup", onUp);
      el.addEventListener("pointercancel", onUp);
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

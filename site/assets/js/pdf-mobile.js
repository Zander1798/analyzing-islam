// On small viewports the iframe'd PDF is effectively unusable (mobile browsers
// render it in a tiny non-scrollable box). Swap it for a big "Open PDF" button
// that opens the file in its own tab, where the mobile browser's native PDF
// viewer can do its job properly.
(function () {
  "use strict";

  function apply() {
    // Treat narrow viewports AND touch-only devices as "mobile" — iPads in
    // portrait and many Android tablets live in this band too.
    var narrow = window.matchMedia("(max-width: 900px)").matches;
    var touchOnly = window.matchMedia("(hover: none) and (pointer: coarse)").matches;
    if (!narrow && !touchOnly) return;

    var frame = document.getElementById("pdf-frame");
    if (!frame) return;
    var src = frame.getAttribute("src");
    if (!src) return;

    // Build a big tap-target that opens the PDF in a new tab.
    var link = document.createElement("a");
    link.href = src;
    link.target = "_blank";
    link.rel = "noopener";
    link.className = "pdf-reader-mobile-open";
    link.innerHTML =
      '<span class="pdf-reader-mobile-open-icon"> 📄 </span>' +
      '<span class="pdf-reader-mobile-open-label">Open PDF in a new tab</span>' +
      '<span class="pdf-reader-mobile-open-hint">The in-page reader is too small on mobile. Tap here to open the full PDF in your browser’s PDF viewer.</span>';
    frame.parentNode.replaceChild(link, frame);

    // The Fullscreen button is pointless now — the iframe is gone.
    var fsBtn = document.getElementById("fullscreen-btn");
    if (fsBtn && fsBtn.parentNode) fsBtn.parentNode.removeChild(fsBtn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  } else {
    apply();
  }
})();

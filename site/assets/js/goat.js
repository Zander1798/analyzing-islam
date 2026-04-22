// Pixel-art goat button: injects itself into the site nav on every page,
// loads the goat-scream MP3, and plays it + runs an animation on click.
(function () {
  "use strict";

  // Determine the path prefix to /assets/ from the current page so this works
  // equally on site/index.html and site/catalog/quran.html.
  function assetPrefix() {
    // Find <link> or <script> already pointing at assets/ to mirror its prefix.
    const el = document.querySelector('link[href*="assets/"], script[src*="assets/"]');
    if (el) {
      const attr = el.getAttribute("href") || el.getAttribute("src");
      const idx = attr.indexOf("assets/");
      return attr.slice(0, idx);
    }
    // Fallback: count directory depth below /site/.
    const parts = location.pathname.split("/").filter(Boolean);
    // Assume last part is the HTML file. Every extra directory = one "../".
    const depth = Math.max(0, parts.length - 1);
    return depth > 0 ? "../".repeat(depth) : "";
  }

  // Pixel-art goat SVG. ViewBox 24x20; each unit = 1 pixel of a sprite.
  // Shape-rendering: crispEdges preserves hard pixel edges at any scale.
  //
  // There are two mouth states inside the SVG; CSS toggles them based on
  // the .is-screaming class on the button.
  const GOAT_SVG = `
<svg class="goat-svg" viewBox="0 0 24 20" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" aria-hidden="true">
  <!-- Horns -->
  <rect x="9"  y="0" width="1" height="3" fill="#8a8a8a"/>
  <rect x="10" y="2" width="1" height="1" fill="#8a8a8a"/>
  <rect x="13" y="0" width="1" height="3" fill="#8a8a8a"/>
  <rect x="14" y="2" width="1" height="1" fill="#8a8a8a"/>

  <!-- Head outline (dark grey) -->
  <rect x="7"  y="3"  width="10" height="1" fill="#6a6a6a"/>
  <rect x="6"  y="4"  width="1"  height="5" fill="#6a6a6a"/>
  <rect x="17" y="4"  width="1"  height="5" fill="#6a6a6a"/>
  <rect x="7"  y="9"  width="10" height="1" fill="#6a6a6a"/>

  <!-- Head fill (white) -->
  <rect x="7"  y="4"  width="10" height="5" fill="#f2f2f2"/>

  <!-- Ear (small notch at top-right of head) -->
  <rect x="15" y="3"  width="2"  height="1" fill="#6a6a6a"/>
  <rect x="16" y="4"  width="1"  height="1" fill="#bfbfbf"/>

  <!-- Eye -->
  <rect x="14" y="5"  width="1"  height="1" fill="#1a1a1a"/>

  <!-- Beard (small white fluff under chin) -->
  <rect x="7"  y="9"  width="1"  height="2" fill="#f2f2f2"/>
  <rect x="7"  y="9"  width="1"  height="2" fill="#f2f2f2"/>

  <!-- Mouth: closed state (visible by default) -->
  <g class="goat-mouth-closed">
    <rect x="8"  y="7"  width="2"  height="1" fill="#6a6a6a"/>
  </g>

  <!-- Mouth: open / screaming state (hidden by default) -->
  <g class="goat-mouth-open">
    <rect x="7"  y="6"  width="4"  height="3" fill="#2a0a0a"/>
    <rect x="8"  y="7"  width="2"  height="1" fill="#c04040"/>
    <rect x="6"  y="7"  width="1"  height="1" fill="#6a6a6a"/>
  </g>

  <!-- Body outline -->
  <rect x="15" y="6"  width="1"  height="1" fill="#6a6a6a"/>
  <rect x="16" y="7"  width="6"  height="1" fill="#6a6a6a"/>
  <rect x="22" y="8"  width="1"  height="5" fill="#6a6a6a"/>
  <rect x="17" y="13" width="5"  height="1" fill="#6a6a6a"/>

  <!-- Body fill -->
  <rect x="16" y="8"  width="6"  height="5" fill="#f2f2f2"/>
  <rect x="15" y="8"  width="1"  height="4" fill="#f2f2f2"/>

  <!-- Body shading -->
  <rect x="17" y="12" width="5"  height="1" fill="#d8d8d8"/>
  <rect x="16" y="11" width="1"  height="1" fill="#d8d8d8"/>

  <!-- Legs (four) with hooves -->
  <rect x="15" y="13" width="1"  height="5" fill="#6a6a6a"/>
  <rect x="16" y="13" width="1"  height="5" fill="#f2f2f2"/>
  <rect x="15" y="17" width="2"  height="1" fill="#1a1a1a"/>

  <rect x="17" y="14" width="1"  height="4" fill="#f2f2f2"/>
  <rect x="18" y="14" width="1"  height="4" fill="#6a6a6a"/>
  <rect x="17" y="17" width="2"  height="1" fill="#1a1a1a"/>

  <rect x="19" y="14" width="1"  height="4" fill="#f2f2f2"/>
  <rect x="20" y="14" width="1"  height="4" fill="#6a6a6a"/>
  <rect x="19" y="17" width="2"  height="1" fill="#1a1a1a"/>

  <rect x="21" y="13" width="1"  height="5" fill="#f2f2f2"/>
  <rect x="22" y="13" width="1"  height="5" fill="#6a6a6a"/>
  <rect x="21" y="17" width="2"  height="1" fill="#1a1a1a"/>

  <!-- Tail -->
  <rect x="22" y="7"  width="1"  height="1" fill="#6a6a6a"/>
</svg>
`.trim();

  function init() {
    const navInner = document.querySelector(".site-nav-inner");
    if (!navInner) return;
    if (navInner.querySelector(".goat-scream")) return; // idempotent

    const prefix = assetPrefix();
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "goat-scream";
    btn.setAttribute("aria-label", "Scream");
    btn.title = "Click me";
    btn.innerHTML = GOAT_SVG;

    const audio = document.createElement("audio");
    audio.preload = "auto";
    audio.src = prefix + "assets/sounds/goat-scream.mp3";
    btn.appendChild(audio);

    navInner.appendChild(btn);

    let animTimer = null;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      // Restart playback each click.
      try {
        audio.pause();
        audio.currentTime = 0;
        const p = audio.play();
        if (p && typeof p.catch === "function") p.catch(function () { /* autoplay blocked; ignored */ });
      } catch (_) { /* ignore */ }

      btn.classList.add("is-screaming");
      if (animTimer) clearTimeout(animTimer);
      animTimer = setTimeout(function () {
        btn.classList.remove("is-screaming");
      }, 1600);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

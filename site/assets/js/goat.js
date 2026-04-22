// Pixel-art goat button: injects itself into the site nav on every page,
// loads the goat-scream MP3, and plays it + runs an animation on click.
//
// Zero-latency playback:
//   1. Decode the MP3 into an AudioBuffer up-front via Web Audio API.
//   2. Listen on `pointerdown` (fires on the initial touch, not after touchend).
//   3. Play via AudioBufferSourceNode — starts immediately, no decoding delay.
//
// A fallback path using the <audio> element is used only if Web Audio isn't
// available.
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

  const GOAT_SVG = `
<svg class="goat-svg" viewBox="0 0 24 20" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" aria-hidden="true">

  <!-- Grass tufts — static, never animated, never removed. -->
  <g class="goat-grass">
    <rect x="1"  y="17" width="1" height="1" fill="#7ebf7e"/>
    <rect x="3"  y="17" width="1" height="1" fill="#7ebf7e"/>
    <rect x="4"  y="16" width="1" height="2" fill="#4a8a4a"/>
    <rect x="5"  y="17" width="1" height="1" fill="#7ebf7e"/>
  </g>

  <!-- Goat body — all animations target this group. -->
  <g class="goat-body">
    <rect x="9"  y="0" width="1" height="3" fill="#8a8a8a"/>
    <rect x="10" y="2" width="1" height="1" fill="#8a8a8a"/>
    <rect x="13" y="0" width="1" height="3" fill="#8a8a8a"/>
    <rect x="14" y="2" width="1" height="1" fill="#8a8a8a"/>

    <rect x="7"  y="3"  width="10" height="1" fill="#6a6a6a"/>
    <rect x="6"  y="4"  width="1"  height="5" fill="#6a6a6a"/>
    <rect x="17" y="4"  width="1"  height="5" fill="#6a6a6a"/>
    <rect x="7"  y="9"  width="10" height="1" fill="#6a6a6a"/>

    <rect x="7"  y="4"  width="10" height="5" fill="#f2f2f2"/>

    <rect x="15" y="3"  width="2"  height="1" fill="#6a6a6a"/>
    <rect x="16" y="4"  width="1"  height="1" fill="#bfbfbf"/>

    <rect x="14" y="5"  width="1"  height="1" fill="#1a1a1a"/>

    <rect x="7"  y="9"  width="1"  height="2" fill="#f2f2f2"/>
    <rect x="7"  y="9"  width="1"  height="2" fill="#f2f2f2"/>

    <g class="goat-mouth-closed">
      <rect x="8"  y="7"  width="2"  height="1" fill="#6a6a6a"/>
    </g>

    <g class="goat-mouth-open">
      <rect x="7"  y="6"  width="4"  height="3" fill="#2a0a0a"/>
      <rect x="8"  y="7"  width="2"  height="1" fill="#c04040"/>
      <rect x="6"  y="7"  width="1"  height="1" fill="#6a6a6a"/>
    </g>

    <rect x="15" y="6"  width="1"  height="1" fill="#6a6a6a"/>
    <rect x="16" y="7"  width="6"  height="1" fill="#6a6a6a"/>
    <rect x="22" y="8"  width="1"  height="5" fill="#6a6a6a"/>
    <rect x="17" y="13" width="5"  height="1" fill="#6a6a6a"/>

    <rect x="16" y="8"  width="6"  height="5" fill="#f2f2f2"/>
    <rect x="15" y="8"  width="1"  height="4" fill="#f2f2f2"/>

    <rect x="17" y="12" width="5"  height="1" fill="#d8d8d8"/>
    <rect x="16" y="11" width="1"  height="1" fill="#d8d8d8"/>

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

    <rect x="22" y="7"  width="1"  height="1" fill="#6a6a6a"/>
  </g>
</svg>
`.trim();

  function init() {
    const navInner = document.querySelector(".site-nav-inner");
    if (!navInner) return;
    if (navInner.querySelector(".goat-scream")) return;

    const prefix = assetPrefix();
    const audioUrl = prefix + "assets/sounds/goat-scream.mp3";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "goat-scream";
    btn.setAttribute("aria-label", "Scream");
    btn.title = "Click me";
    btn.innerHTML = GOAT_SVG;
    navInner.appendChild(btn);

    // --- Speech bubble ---------------------------------------------------
    const PHRASES = [
      "Feed Me!",
      "hmmm Yummy Quran",
      "Such powerful Dawha",
      "Screems in Hadith",
      "Much Knowledge",
      "Why are You Running!",
    ];

    function pickPhrase(exclude) {
      if (PHRASES.length < 2) return PHRASES[0];
      let next;
      do {
        next = PHRASES[Math.floor(Math.random() * PHRASES.length)];
      } while (next === exclude);
      return next;
    }

    const bubble = document.createElement("span");
    bubble.className = "goat-bubble";
    bubble.setAttribute("aria-live", "polite");
    bubble.innerHTML =
      '<span class="goat-bubble-spinner" aria-hidden="true"></span>' +
      '<span class="goat-bubble-text"></span>';
    const bubbleText = bubble.querySelector(".goat-bubble-text");
    bubbleText.textContent = pickPhrase();
    navInner.insertBefore(bubble, btn);

    function replayPop() {
      bubble.classList.remove("is-pop");
      // Force reflow so the animation restarts.
      void bubble.offsetWidth;
      bubble.classList.add("is-pop");
    }
    replayPop();

    let currentPhrase = bubbleText.textContent;
    setInterval(function () {
      currentPhrase = pickPhrase(currentPhrase);
      bubbleText.textContent = currentPhrase;
      replayPop();
    }, 15 * 60 * 1000); // rotate every 15 minutes

    // --- Idle animation loop ---------------------------------------------
    // Every 5 seconds the goat plays a little "chew" animation (bending
    // down toward the grass). Every 6th idle tick (~30 seconds) the chew
    // is replaced with a bigger "stretch" animation. If the goat is
    // currently screaming (clicked), idle ticks are skipped — the scream
    // plays cleanly and the idle resumes on the next tick.
    const IDLE_INTERVAL_MS = 5000;
    const STRETCH_EVERY_N = 6; // 6 × 5s = 30s
    const CHEW_DURATION_MS = 1500;
    const STRETCH_DURATION_MS = 2000;

    let idleCount = 0;
    function playIdle() {
      if (btn.classList.contains("is-screaming")) return; // yield to scream
      if (btn.classList.contains("is-chewing")) return;   // don't stack
      if (btn.classList.contains("is-stretching")) return;
      idleCount++;
      const doStretch = idleCount % STRETCH_EVERY_N === 0;
      if (doStretch) {
        btn.classList.add("is-stretching");
        setTimeout(function () { btn.classList.remove("is-stretching"); }, STRETCH_DURATION_MS);
      } else {
        btn.classList.add("is-chewing");
        setTimeout(function () { btn.classList.remove("is-chewing"); }, CHEW_DURATION_MS);
      }
    }

    // Start the loop 2 seconds after page load so the goat isn't chewing
    // the moment the page paints.
    setTimeout(playIdle, 2000);
    setInterval(playIdle, IDLE_INTERVAL_MS);

    // --- Web Audio path: decode once, play instantly on each click. ---
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    let audioCtx = null;
    let audioBuffer = null;
    let currentSource = null;
    let fallbackAudio = null;

    // Fallback <audio> element (used if Web Audio isn't available, or while
    // the Web Audio decode is still in flight on the very first click).
    function getFallback() {
      if (!fallbackAudio) {
        fallbackAudio = new Audio(audioUrl);
        fallbackAudio.preload = "auto";
        // Nudge the browser to actually start loading now.
        try { fallbackAudio.load(); } catch (_) {}
      }
      return fallbackAudio;
    }

    // Fetch and decode the MP3 into an AudioBuffer. Kicked off on the first
    // user gesture so that iOS/Android are happy with the AudioContext.
    let decodePromise = null;
    function ensureDecoded() {
      if (!AudioCtxClass) return Promise.reject();
      if (!audioCtx) audioCtx = new AudioCtxClass();
      if (audioCtx.state === "suspended") audioCtx.resume();
      if (audioBuffer) return Promise.resolve(audioBuffer);
      if (decodePromise) return decodePromise;
      decodePromise = fetch(audioUrl)
        .then(function (r) { return r.arrayBuffer(); })
        .then(function (buf) {
          return new Promise(function (resolve, reject) {
            // Old Safari uses the callback signature for decodeAudioData.
            audioCtx.decodeAudioData(buf, resolve, reject);
          });
        })
        .then(function (decoded) {
          audioBuffer = decoded;
          return decoded;
        });
      return decodePromise;
    }

    // Warm the decode in the background after page load — best-effort.
    // Always prime the <audio> fallback so the *first* click has something
    // ready-to-play even before the Web Audio decode finishes.
    getFallback();
    if (AudioCtxClass && window.fetch) {
      // Don't auto-create the AudioContext on load (needs user gesture on mobile).
      // Just fetch & arrayBuffer the MP3 so it's in the HTTP cache.
      fetch(audioUrl, { cache: "force-cache" }).catch(function () {});
    }

    // Kick off the AudioContext + decode on the first user gesture that
    // *precedes* a click (hover, focus, touchstart). By the time the user
    // actually presses, audioBuffer is usually ready and playback is instant.
    let decodeArmed = false;
    function armDecode() {
      if (decodeArmed) return;
      decodeArmed = true;
      ensureDecoded().catch(function () {});
    }
    btn.addEventListener("pointerenter", armDecode);
    btn.addEventListener("focus", armDecode);
    btn.addEventListener("touchstart", armDecode, { passive: true });

    function playWebAudio() {
      if (!audioBuffer) return false;
      try {
        if (currentSource) {
          try { currentSource.stop(); } catch (_) {}
        }
        const src = audioCtx.createBufferSource();
        src.buffer = audioBuffer;
        src.connect(audioCtx.destination);
        src.start(0);
        currentSource = src;
        return true;
      } catch (_) {
        return false;
      }
    }

    function playFallback() {
      const a = getFallback();
      try {
        a.pause();
        a.currentTime = 0;
        const p = a.play();
        if (p && typeof p.catch === "function") p.catch(function () {});
      } catch (_) {}
    }

    let animTimer = null;
    function trigger() {
      btn.classList.add("is-screaming");
      if (animTimer) clearTimeout(animTimer);
      animTimer = setTimeout(function () {
        btn.classList.remove("is-screaming");
      }, 1600);

      // Try Web Audio first (instant if already decoded).
      if (AudioCtxClass) {
        if (audioBuffer) {
          if (playWebAudio()) return;
        } else {
          // First click: decode + play as soon as ready. Meanwhile, start the
          // fallback element playing so the user still hears it immediately.
          playFallback();
          ensureDecoded().then(function () {
            // If the fallback is already playing we keep it (avoids double-play).
          }).catch(function () {});
          return;
        }
      }
      playFallback();
    }

    // pointerdown fires at the start of a tap/click — no 300ms tap delay.
    btn.addEventListener("pointerdown", function (e) {
      e.preventDefault();
      trigger();
    });
    // Keyboard activation (Enter / Space) still uses click.
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      if (e.detail === 0) trigger(); // keyboard-invoked click only
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

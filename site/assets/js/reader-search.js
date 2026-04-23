// Reader-page verse search.
// -------------------------------------------------------------------
// Injects a small search input at the top of every reader page's TOC
// (or at the top of the main reading column if no TOC is present),
// then lets the user jump to any verse / hadith / chapter using the
// same casual reference syntax supported by the Compare and Build
// search bars — "John 3:16", "John 3 16", "John 3.16", "Bukhari 2749",
// "Sanhedrin 4:5", "2:23", etc.
//
// Depends on window.VERSE_PARSER (loaded from verse-parser.js).
// Skips itself when the page is loaded in embed mode (?embed=1), so
// the floating search doesn't double-up inside Compare/Build iframes.
(function init() {
  "use strict";

  if (!window.VERSE_PARSER) {
    // verse-parser.js may still be loading (defer); retry shortly.
    setTimeout(init, 50);
    return;
  }

  // Don't render the search UI inside an iframe-embedded reader — the
  // parent page (Compare / Build) has its own search, and ours would
  // just clutter the pane.
  try {
    const params = new URLSearchParams(location.search);
    if (params.get("embed") === "1") return;
    if (document.documentElement.classList.contains("embed-mode")) return;
    if (document.body && document.body.classList.contains("embed-mode")) return;
  } catch (_) {}

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function findAnchor(ids) {
    for (let i = 0; i < ids.length; i++) {
      const el = document.getElementById(ids[i]);
      if (el) return { el: el, id: ids[i] };
    }
    return null;
  }

  function flash(el) {
    if (!el) return;
    try {
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      const prev = el.style.animation;
      el.style.animation = "compare-jump-flash 1.5s ease-out 1";
      setTimeout(function () { el.style.animation = prev || ""; }, 1700);
    } catch (_) {}
  }

  function mount() {
    const slug = window.VERSE_PARSER.detectReaderSlug(location);
    if (!slug) return; // not a recognised reader page

    // Choose a parent to drop the search into. Prefer the TOC so the
    // search sits alongside chapter navigation; fall back to the start
    // of the reading column if there's no TOC.
    const toc = document.querySelector(".reader-toc");
    const target = toc || document.querySelector(".reader-layout > *:not(.splitter)") || document.body;
    if (!target) return;

    const wrap = document.createElement("div");
    wrap.className = "reader-search-wrap";
    wrap.innerHTML =
      '<input type="search" class="reader-search-input" ' +
      'placeholder="Jump to verse (e.g. ' + escapeHtml(placeholderFor(slug)) + ')" ' +
      'autocomplete="off" spellcheck="false" />' +
      '<div class="reader-search-hint" hidden></div>';

    // Insert at the top of the chosen container.
    if (target.firstChild) target.insertBefore(wrap, target.firstChild);
    else target.appendChild(wrap);

    const input = wrap.querySelector(".reader-search-input");
    const hint  = wrap.querySelector(".reader-search-hint");

    function showHint(text, kind) {
      hint.textContent = text;
      hint.className = "reader-search-hint" + (kind ? " reader-search-hint--" + kind : "");
      hint.hidden = false;
    }
    function clearHint() {
      hint.hidden = true;
      hint.textContent = "";
    }

    let typingTimer = null;
    function tryJump() {
      const q = (input.value || "").trim();
      if (!q) { clearHint(); return; }

      // 1) Parser-derived IDs (casual verse refs).
      const ids = window.VERSE_PARSER.candidateIds(q, slug);
      let hit = findAnchor(ids);

      // 2) Raw anchor ID (user typed exactly "s2v23" or "genesis-1-1").
      if (!hit) {
        const asId = q.replace(/^#/, "").toLowerCase();
        if (/^[a-z0-9][a-z0-9\-]*$/.test(asId) && asId.length <= 40) {
          const el = document.getElementById(asId);
          if (el) hit = { el: el, id: asId };
        }
      }

      if (hit) {
        flash(hit.el);
        showHint("Jumped to #" + hit.id, "ok");
        setTimeout(clearHint, 1600);
      } else {
        showHint("No match for “" + q + "”", "miss");
      }
    }

    input.addEventListener("input", function () {
      clearTimeout(typingTimer);
      typingTimer = setTimeout(tryJump, 220);
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        clearTimeout(typingTimer);
        tryJump();
      }
      if (e.key === "Escape") {
        input.value = "";
        clearHint();
      }
    });
  }

  function placeholderFor(slug) {
    if (slug === "quran") return "2:23 or Surah 2 23";
    if (slug === "ibn-kathir") return "a23 or ayah 23";
    if (slug === "mishnah") return "Sanhedrin 4:5";
    if (slug === "tanakh" || slug === "new-testament" ||
        slug === "bible-interlinear" || slug === "apocryphal-gospels" ||
        slug === "book-of-enoch" || slug === "talmud" || slug === "josephus") {
      return "John 3:16";
    }
    // hadith collections
    return "2749 or Bukhari 2749";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();

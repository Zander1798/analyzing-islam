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

  // Multi-page sources (index landing page + dozens/hundreds of sub-pages).
  // When the user is on one of these index pages, there are no verse /
  // section anchors on the current document — the real content lives on
  // sub-pages. We fetch the pre-built compare-index JSON, match the
  // query against every entry's ref + text, and navigate to the correct
  // sub-page (preserving any anchor). Keyed by the VERSE_PARSER slug.
  //
  // URLs here are resolved against the site root (BASE_URL, computed
  // below), so the paths keep working whether the reader is loaded at
  // the root (`/bible.html`) or under a sub-directory on GitHub Pages.
  const INDEXED_SOURCES = {
    "bible-interlinear": {
      indexPath: "assets/compare-index/bible.json",
      contentBase: "read-external/bible/",
    },
    "ibn-kathir": {
      indexPath: "assets/compare-index/ibn-kathir.json",
      contentBase: "read-external/",
    },
  };

  // Compute the site's root prefix from the current reader page's
  // location. Reader pages live under /read/ or /read-external/
  // (possibly under a repo-name prefix on github.io), so we strip that
  // segment to get back to the site root.
  function siteRoot() {
    const path = location.pathname || "/";
    const m = path.match(/^(.*?)\/(read|read-external)(\/|$)/);
    return m ? m[1] + "/" : "/";
  }
  // Per-slug cache of the loaded index (or a pending Promise).
  const INDEX_CACHE = Object.create(null);

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

  // True when the user is on an index landing page (no per-verse
   // anchors in the DOM) for a multi-page source — tells the search to
   // route through the JSON index rather than giving up.
  function isIndexLandingPage(slug) {
    if (!INDEXED_SOURCES[slug]) return false;
    const path = location.pathname || "";
    // /read-external/bible.html and /read-external/ibn-kathir.html.
    if (slug === "bible-interlinear") return /\/bible\.html$/.test(path);
    if (slug === "ibn-kathir")        return /\/ibn-kathir\.html$/.test(path);
    return false;
  }

  function loadIndex(slug) {
    const cfg = INDEXED_SOURCES[slug];
    if (!cfg) return Promise.resolve(null);
    if (INDEX_CACHE[slug] !== undefined) return Promise.resolve(INDEX_CACHE[slug]);
    const url = siteRoot() + cfg.indexPath;
    const p = fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .catch(function (err) {
        delete INDEX_CACHE[slug];
        throw err;
      });
    INDEX_CACHE[slug] = p;
    return p;
  }

  function searchIndexEntries(entries, query, limit) {
    const qLower = query.toLowerCase();
    const refMatches = [];       // ref-match (verse ref / section name)
    const refExact   = [];       // ref that ends exactly with the query
    const textMatches = [];      // text-match (keyword)
    const seen = Object.create(null);

    // When the query ends with a verse-like number pair ("John 3:16",
    // "Ayah 9:5") we want entries whose ref ENDS with those numbers —
    // otherwise "9:5" also matches "9:50", "9:55", etc. via substring.
    const tailMatch = qLower.match(/(?:^|\s|·)\d+:\d+$|\d+:\d+$/);
    const tailExact = tailMatch ? tailMatch[0].trim() : null;

    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      const ref = (e.ref || "").toLowerCase();
      const txt = (e.text || "").toLowerCase();
      const hit = ref.indexOf(qLower) >= 0;
      if (hit) {
        if (!seen[e.href]) {
          // A "clean tail" match is one where the digits in the query
          // land at the end of the ref with nothing after them — so
          // "9:5" doesn't match "9:50" or "9:55".
          const cleanTail = tailExact
            ? new RegExp("(?:^|\\s|·\\s*)" + tailExact.replace(/[:]/g, "\\$&") + "$").test(ref)
            : false;
          if (cleanTail) refExact.push(e);
          else refMatches.push(e);
          seen[e.href] = true;
        }
      } else if (txt.indexOf(qLower) >= 0) {
        if (!seen[e.href]) { textMatches.push(e); seen[e.href] = true; }
      }
      if (refExact.length + refMatches.length + textMatches.length >= limit) break;
    }
    return {
      refExact: refExact,
      refMatches: refMatches,
      textMatches: textMatches,
    };
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

    const onIndexPage = isIndexLandingPage(slug);
    const placeholder = onIndexPage
      ? placeholderFor(slug) + " — or any keyword"
      : placeholderFor(slug);

    const wrap = document.createElement("div");
    wrap.className = "reader-search-wrap";
    wrap.innerHTML =
      '<input type="search" class="reader-search-input" ' +
      'placeholder="Jump to verse (e.g. ' + escapeHtml(placeholder) + ')" ' +
      'autocomplete="off" spellcheck="false" />' +
      '<div class="reader-search-hint" hidden></div>' +
      '<div class="reader-search-results" hidden></div>';

    // Insert at the top of the chosen container.
    if (target.firstChild) target.insertBefore(wrap, target.firstChild);
    else target.appendChild(wrap);

    const input   = wrap.querySelector(".reader-search-input");
    const hint    = wrap.querySelector(".reader-search-hint");
    const results = wrap.querySelector(".reader-search-results");

    function showHint(text, kind) {
      hint.textContent = text;
      hint.className = "reader-search-hint" + (kind ? " reader-search-hint--" + kind : "");
      hint.hidden = false;
    }
    function clearHint() {
      hint.hidden = true;
      hint.textContent = "";
    }
    function clearResults() {
      results.hidden = true;
      results.innerHTML = "";
    }

    // Kick off the JSON fetch early on index landing pages so the first
    // query doesn't wait on a multi-MB download.
    if (onIndexPage) loadIndex(slug).catch(function () {});

    function navigateToEntry(entry) {
      const cfg = INDEXED_SOURCES[slug];
      if (!cfg) return;
      // entry.href is "sub-page.html#anchor" relative to the source's
      // content dir; resolve against the site root so the jump works
      // regardless of what reader page we're currently on.
      location.href = siteRoot() + cfg.contentBase + entry.href;
    }

    function buildSnippet(text, query) {
      const flat = (text || "").replace(/\s+/g, " ").trim();
      const lower = flat.toLowerCase();
      const idx = lower.indexOf(query.toLowerCase());
      if (idx < 0) return escapeHtml(flat.slice(0, 140));
      const start = Math.max(0, idx - 40);
      const end = Math.min(flat.length, idx + query.length + 80);
      const pre = start > 0 ? "…" : "";
      const suf = end < flat.length ? "…" : "";
      return pre +
        escapeHtml(flat.slice(start, idx)) +
        "<mark>" + escapeHtml(flat.slice(idx, idx + query.length)) + "</mark>" +
        escapeHtml(flat.slice(idx + query.length, end)) +
        suf;
    }

    function renderResultList(matches, query) {
      results.innerHTML = "";
      if (!matches.length) { clearResults(); return; }
      const header = document.createElement("div");
      header.className = "reader-search-results-header";
      header.textContent = matches.length === 1
        ? "1 match — press Enter to jump"
        : matches.length + " matches — click one to open";
      results.appendChild(header);
      matches.slice(0, 20).forEach(function (e) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "reader-search-result";
        btn.innerHTML =
          '<span class="reader-search-result-ref">' + escapeHtml(e.ref || "") + "</span>" +
          '<span class="reader-search-result-snippet">' + buildSnippet(e.text || "", query) + "</span>";
        btn.addEventListener("click", function () { navigateToEntry(e); });
        results.appendChild(btn);
      });
      results.hidden = false;
    }

    let typingTimer = null;
    function tryJump() {
      const q = (input.value || "").trim();
      if (!q) { clearHint(); clearResults(); return; }

      // 1) Parser-derived IDs (casual verse refs) — only meaningful when
      //    verse anchors actually live on this page. On multi-page
      //    index landings we skip straight to the JSON index search.
      if (!onIndexPage) {
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
          clearResults();
          return;
        }
      }

      // 3) Multi-page source with a pre-built search index — look up the
      //    query there and either auto-jump (single confident match) or
      //    show a clickable result list.
      if (INDEXED_SOURCES[slug]) {
        showHint("Searching every page…", "");
        loadIndex(slug).then(function (idx) {
          if ((input.value || "").trim() !== q) return; // user moved on
          const entries = (idx && idx.entries) || [];
          const res = searchIndexEntries(entries, q, 50);
          const total = res.refExact.length + res.refMatches.length + res.textMatches.length;
          if (!total) {
            clearResults();
            showHint("No match for “" + q + "”", "miss");
            return;
          }
          // Single exact ref-tail match → auto-navigate (e.g. "John
          // 3:16" uniquely identifies one entry).
          if (res.refExact.length === 1) {
            navigateToEntry(res.refExact[0]);
            return;
          }
          // Single fuzzy match across all buckets → auto-navigate too.
          if (total === 1) {
            navigateToEntry(res.refExact[0] || res.refMatches[0] || res.textMatches[0]);
            return;
          }
          clearHint();
          renderResultList(
            res.refExact.concat(res.refMatches).concat(res.textMatches), q
          );
        }).catch(function (err) {
          clearResults();
          showHint("Couldn't load index: " + (err.message || err), "miss");
        });
        return;
      }

      // 4) Nothing matched and there's no index to fall back to.
      clearResults();
      showHint("No match for “" + q + "”", "miss");
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

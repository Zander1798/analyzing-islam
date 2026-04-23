// Compare page controller.
// - Two panes: left + right. Each has a <select> source picker, a search
//   input, and an <iframe> pointing at the chosen reader (with ?embed=1
//   so the nav/footer inside is hidden).
// - Selections are mirrored to the URL query string so the view is
//   shareable: compare.html?left=quran&right=tanakh&lh=s9v5&rh=sanhedrin-4-5
// - Search uses same-origin iframe DOM access to find matching verse /
//   chapter / hadith elements and scroll/flash them.
(function () {
  "use strict";

  // -- Catalogue of readable sources --------------------------------------
  // slug:  URL-safe key used in the query string.
  // title: what appears in the dropdown.
  // path:  URL to load in the iframe.
  // group: optgroup label in the dropdown.
  const SOURCES = [
    // --- Qur'an ---
    { slug: "quran",       title: "The Qurʾān (Saheeh International)", path: "read/quran.html",       group: "Qurʾān" },

    // --- Six canonical Sunni hadith collections ---
    { slug: "bukhari",   title: "Ṣaḥīḥ al-Bukhārī",   path: "read/bukhari.html",   group: "Hadith · the Six" },
    { slug: "muslim",    title: "Ṣaḥīḥ Muslim",       path: "read/muslim.html",    group: "Hadith · the Six" },
    { slug: "abu-dawud", title: "Sunan Abī Dāwūd",    path: "read/abu-dawud.html", group: "Hadith · the Six" },
    { slug: "tirmidhi",  title: "Jāmiʿ at-Tirmidhī",  path: "read/tirmidhi.html",  group: "Hadith · the Six" },
    { slug: "nasai",     title: "Sunan an-Nasāʾī",    path: "read/nasai.html",     group: "Hadith · the Six" },
    { slug: "ibn-majah", title: "Sunan Ibn Mājah",    path: "read/ibn-majah.html", group: "Hadith · the Six" },

    // --- Comparative scripture ---
    { slug: "tanakh",             title: "The Tanakh (JPS 1917)",         path: "read-external/tanakh.html",             group: "Comparative scripture" },
    { slug: "new-testament",      title: "The New Testament (WEB)",       path: "read-external/new-testament.html",      group: "Comparative scripture" },
    // Interlinear Bible is a multi-page library (66 books). Real verse
    // text lives in read-external/bible/<abbr>.html, so iframe-only DOM
    // search would only see the index. The ``indexUrl`` entry lets the
    // compare page fetch a pre-built JSON of every verse and search it
    // in one go; clicking a result loads that specific book page.
    { slug: "bible-interlinear",  title: "Interlinear Bible (Hebrew · Greek · Strong's)", path: "read-external/bible.html",   group: "Comparative scripture",
      indexUrl: "assets/compare-index/bible.json", indexBase: "read-external/bible/" },
    { slug: "apocryphal-gospels", title: "Apocryphal Infancy Gospels",    path: "read-external/apocryphal-gospels.html", group: "Comparative scripture" },
    { slug: "book-of-enoch",      title: "The Book of Enoch (1 Enoch)",   path: "read-external/book-of-enoch.html",      group: "Comparative scripture" },
    { slug: "mishnah",            title: "The Mishnah (Kulp)",            path: "read-external/mishnah.html",            group: "Comparative scripture" },
    { slug: "josephus",           title: "Flavius Josephus",              path: "read-external/josephus.html",           group: "Comparative scripture" },

    // --- Classical Islamic scholarship ---
    // Ibn Kathir is also split across 114 surah pages; same indexing
    // trick as the Interlinear Bible above.
    { slug: "ibn-kathir",  title: "Tafsīr Ibn Kathīr",               path: "read-external/ibn-kathir.html",  group: "Classical Islamic scholarship",
      indexUrl: "assets/compare-index/ibn-kathir.json", indexBase: "read-external/" },
    { slug: "talmud",      title: "The Talmud",                      path: "read-external/talmud.html",      group: "Comparative scripture" },
  ];

  const DEFAULT_LEFT = "quran";
  const DEFAULT_RIGHT = "tanakh";

  const SOURCE_BY_SLUG = Object.create(null);
  SOURCES.forEach(function (s) { SOURCE_BY_SLUG[s.slug] = s; });

  // -- DOM ---------------------------------------------------------------
  const panes = {
    left:  document.querySelector('.compare-pane[data-side="left"]'),
    right: document.querySelector('.compare-pane[data-side="right"]'),
  };

  if (!panes.left || !panes.right) return;

  function populateSelect(sel) {
    // Build <optgroup>s so the long list stays browsable.
    const groups = {};
    SOURCES.forEach(function (s) {
      if (!groups[s.group]) groups[s.group] = [];
      groups[s.group].push(s);
    });
    sel.innerHTML = "";
    Object.keys(groups).forEach(function (groupName) {
      const og = document.createElement("optgroup");
      og.label = groupName;
      groups[groupName].forEach(function (s) {
        const opt = document.createElement("option");
        opt.value = s.slug;
        opt.textContent = s.title;
        og.appendChild(opt);
      });
      sel.appendChild(og);
    });
  }

  function getPaneEls(side) {
    const pane = panes[side];
    return {
      pane: pane,
      select: pane.querySelector(".compare-source"),
      search: pane.querySelector(".compare-search"),
      results: pane.querySelector(".compare-search-results"),
      frame: pane.querySelector(".compare-frame"),
    };
  }

  // -- URL state ---------------------------------------------------------
  function readParams() {
    const p = new URLSearchParams(location.search);
    return {
      left:  p.get("left")  || DEFAULT_LEFT,
      right: p.get("right") || DEFAULT_RIGHT,
      lh:    p.get("lh")    || "",
      rh:    p.get("rh")    || "",
    };
  }

  function writeParams(state) {
    const p = new URLSearchParams();
    p.set("left",  state.left);
    p.set("right", state.right);
    if (state.lh) p.set("lh", state.lh);
    if (state.rh) p.set("rh", state.rh);
    const url = location.pathname + "?" + p.toString();
    history.replaceState(null, "", url);
  }

  function prefetchIndex(source) {
    // Kick off the JSON fetch early so search feels instant. Swallow
    // errors; performIndexedSearch will surface them when it tries to
    // use the index.
    if (source && source.indexUrl) {
      try { Promise.resolve(loadIndex(source)).catch(function () {}); }
      catch (_) {}
    }
  }

  // -- Pane behaviour ----------------------------------------------------
  function setSource(side, slug, hash) {
    const els = getPaneEls(side);
    const source = SOURCE_BY_SLUG[slug] || SOURCE_BY_SLUG[DEFAULT_LEFT];
    if (!source) return;

    // For indexed sources the URL-state ``hash`` can be either a bare
    // anchor ("gen-1-1"), which means the index landing page, or a
    // composite ``<subpage>.html#<anchor>`` which means a specific
    // sub-page. Detect the composite form by the literal "#" we wrote
    // out in jumpIndexed.
    let src;
    if (source.indexUrl && hash && hash.indexOf("#") >= 0) {
      const base = source.indexBase || "";
      const hashAt = hash.indexOf("#");
      const pagePart = hash.slice(0, hashAt);
      const anchor   = hash.slice(hashAt + 1);
      const joiner = (base + pagePart).indexOf("?") >= 0 ? "&" : "?";
      src = base + pagePart + joiner + "embed=1" + (anchor ? "#" + anchor : "");
    } else {
      src = source.path + (source.path.indexOf("?") >= 0 ? "&" : "?") + "embed=1";
      if (hash) src += "#" + hash.replace(/^#/, "");
    }

    if (els.frame.src !== location.origin + "/" + src && els.frame.getAttribute("src") !== src) {
      els.frame.src = src;
    }
    els.select.value = slug;
    // Reset the search UI on source change.
    els.search.value = "";
    els.results.hidden = true;
    els.results.innerHTML = "";

    // Warm the cache for multi-page indexed sources so the first search
    // doesn't wait on a multi-MB download.
    prefetchIndex(source);
  }

  function onSelectChange(side) {
    return function () {
      const els = getPaneEls(side);
      const state = readParams();
      state[side] = els.select.value;
      // Clear the hash on source change to avoid a stale hash pointing
      // at a different source's anchor scheme.
      if (side === "left")  state.lh = "";
      if (side === "right") state.rh = "";
      writeParams(state);
      setSource(side, state[side], "");
    };
  }

  // -- Search inside the iframe ------------------------------------------
  // Iframes load same-origin reader pages, so we can read their DOM and
  // find matches. We look at the most common content containers used by
  // the readers: verse items, hadiths, and chapter sections.
  const CONTENT_SELECTOR = [
    ".verses li",
    ".hadith",
    ".chapter",
    ".surah > p",
    "article.surah section",
  ].join(",");

  function iframeDoc(frame) {
    try { return frame.contentDocument || (frame.contentWindow && frame.contentWindow.document); }
    catch (_) { return null; }
  }

  function buildSnippet(text, query) {
    const flat = text.replace(/\s+/g, " ").trim();
    const lower = flat.toLowerCase();
    const q = query.toLowerCase();
    const idx = lower.indexOf(q);
    if (idx < 0) return flat.slice(0, 140);
    const start = Math.max(0, idx - 40);
    const end = Math.min(flat.length, idx + q.length + 80);
    const pre = start > 0 ? "…" : "";
    const suf = end < flat.length ? "…" : "";
    const before = flat.slice(start, idx);
    const hit    = flat.slice(idx, idx + q.length);
    const after  = flat.slice(idx + q.length, end);
    const esc = function (s) {
      return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    };
    return pre + esc(before) + "<mark>" + esc(hit) + "</mark>" + esc(after) + suf;
  }

  function scrollFrameTo(frame, el) {
    const doc = iframeDoc(frame);
    if (!doc || !el) return;
    try {
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      const prev = el.style.animation;
      el.style.animation = "compare-jump-flash 1.5s ease-out 1";
      setTimeout(function () { el.style.animation = prev || ""; }, 1700);
    } catch (_) {}
  }

  function renderResults(els, matches, query, onClick, totalHint) {
    // ``onClick(match)`` performs the jump — the caller decides whether
    // that's an in-frame scroll (iframe search) or a full iframe.src
    // replacement (pre-built index search).
    // ``totalHint`` lets the caller override the match count shown in
    // the header (index searches cap scanning so the "real" total isn't
    // always matches.length).
    els.results.innerHTML = "";
    if (!matches.length) {
      const empty = document.createElement("div");
      empty.className = "compare-search-status";
      empty.textContent = 'No matches for "' + query + '".';
      els.results.appendChild(empty);
      els.results.hidden = false;
      return;
    }
    const shown = Math.min(matches.length, 50);
    const total = typeof totalHint === "number" ? totalHint : matches.length;
    const hdr = document.createElement("div");
    hdr.className = "compare-search-status";
    hdr.textContent =
      total + " match" + (total === 1 ? "" : "es") +
      (shown < total ? " (showing first " + shown + ")" : "");
    els.results.appendChild(hdr);
    matches.slice(0, shown).forEach(function (m) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "compare-search-result";
      btn.innerHTML =
        '<span class="ref">' + (m.ref || "").replace(/[<>&]/g, "") + "</span>" +
        '<span class="snippet">' + m.snippet + "</span>";
      btn.addEventListener("click", function () {
        onClick(m);
        els.results.hidden = true;
      });
      els.results.appendChild(btn);
    });
    els.results.hidden = false;
  }

  // -- Pre-built search indexes (multi-page sources) ---------------------
  // Sources like the Interlinear Bible and Ibn Kathīr are split across
  // dozens of sub-pages, so a DOM scan of the iframe only sees the index
  // landing page. For those, we fetch a JSON list of every verse /
  // section once, then search it in-memory and replace the iframe's src
  // when a result is clicked.
  const INDEX_CACHE = Object.create(null);

  function loadIndex(source) {
    if (!source || !source.indexUrl) return null;
    if (INDEX_CACHE[source.slug] !== undefined) return INDEX_CACHE[source.slug];
    const p = fetch(source.indexUrl)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status + " fetching " + source.indexUrl);
        return r.json();
      })
      .catch(function (err) {
        // Drop the cached promise so a later search can retry.
        delete INDEX_CACHE[source.slug];
        throw err;
      });
    INDEX_CACHE[source.slug] = p;
    return p;
  }

  function searchIndexEntries(entries, query, limit) {
    const qLower = query.toLowerCase();
    const matches = [];
    let total = 0;
    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      const t = e.text || "";
      if (t.toLowerCase().indexOf(qLower) >= 0 ||
          (e.ref && e.ref.toLowerCase().indexOf(qLower) >= 0)) {
        total++;
        if (matches.length < limit) matches.push(e);
      }
    }
    return { matches: matches, total: total };
  }

  function jumpIndexed(side, source, href) {
    // href is "<sub-page>.html#<anchor>" relative to source.indexBase.
    // Rewrite the iframe src so it navigates to that sub-page.
    const els = getPaneEls(side);
    const base = source.indexBase || "";
    const hashAt = href.indexOf("#");
    const pagePart = hashAt >= 0 ? href.slice(0, hashAt) : href;
    const anchor   = hashAt >= 0 ? href.slice(hashAt + 1) : "";
    const joiner = (base + pagePart).indexOf("?") >= 0 ? "&" : "?";
    const newSrc = base + pagePart + joiner + "embed=1" + (anchor ? "#" + anchor : "");
    els.frame.src = newSrc;

    // Mirror the full sub-page+anchor to the URL so reload and sharing
    // land back on the exact verse / section. setSource recognises the
    // composite form (contains "#") and routes to the sub-page.
    const state = readParams();
    if (side === "left")  state.lh = href;
    if (side === "right") state.rh = href;
    writeParams(state);
  }

  // Turn a user-friendly reference ("2:23", "Quran 2:23", "Bukhari 3731",
  // "Genesis 1:1", "hadith 2953", …) into candidate anchor IDs for the
  // given source. Returns a (possibly empty) list — we'll try each in
  // order before falling back to a text scan.
  function candidateIds(query, sourceSlug) {
    const q = query.trim();
    if (!q) return [];
    const ids = [];

    // "2:23", "2.23", "2-23"  (two-part numeric ref)
    const two = q.match(/^(\d{1,3})\s*[:.\- ]\s*(\d{1,3})$/);
    // plain number (hadith number / ayah ordinal)
    const onlyNum = q.match(/^\d{1,5}$/);
    // "<book or prefix> <chapter>[:verse][:sub]"  OR  "<prefix> <hadith-number>"
    // Allows a leading ordinal ("1 Samuel", "2 Kings") before the book name.
    // First number is up to 5 digits so hadith numbers ("Bukhari 3731") fit.
    const prefixed = q.match(/^((?:[123]\s+)?[a-zA-Z][a-zA-Z'’. -]*?)\s+(\d{1,5})(?:\s*[:.\- ]\s*(\d{1,3}))?(?:\s*[:.\- ]\s*(\d{1,3}))?$/);

    function addQuranId(s, v) {
      if (s && v) ids.push("s" + s + "v" + v);
    }
    function addHadithId(n) {
      if (n) ids.push("h" + String(n).replace(/^0+/, ""));
    }
    function addBibleId(book, c, v) {
      let slug = String(book || "")
        .toLowerCase()
        .replace(/[.'’]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      if (!slug) return;
      // Numbered books collapse the digit prefix into the book name:
      // "1 Samuel" → "1samuel", "2 Kings" → "2kings", "1 Corinthians" → "1corinthians".
      slug = slug.replace(/^([123])-([a-z])/, "$1$2");
      if (v) ids.push(slug + "-" + c + "-" + v);
      else if (c) ids.push(slug + "-" + c);
      else ids.push(slug);
    }
    function addTractateId(book, c, v) {
      // Mishnah: `{tractate}-{chapter}-{mishnah}`
      addBibleId(book, c, v);
    }

    const isHadithSource = (
      sourceSlug === "bukhari" || sourceSlug === "muslim" ||
      sourceSlug === "abu-dawud" || sourceSlug === "tirmidhi" ||
      sourceSlug === "nasai" || sourceSlug === "ibn-majah"
    );
    const isBibleSource = (
      sourceSlug === "tanakh" || sourceSlug === "new-testament" ||
      sourceSlug === "bible-interlinear" || sourceSlug === "apocryphal-gospels" ||
      sourceSlug === "book-of-enoch"
    );

    if (sourceSlug === "quran") {
      if (two) addQuranId(two[1], two[2]);
      if (prefixed && /^(quran|qur'?an|surah?)$/i.test(prefixed[1])) {
        addQuranId(prefixed[2], prefixed[3] || "1");
      }
    } else if (isHadithSource) {
      if (onlyNum) addHadithId(q);
      if (prefixed && /^(hadith|h|bukhari|muslim|dawud|abu\s*dawud|tirmidhi|nasa|nasai|ibn\s*majah)$/i.test(prefixed[1])) {
        addHadithId(prefixed[2]);
      }
    } else if (isBibleSource) {
      if (prefixed) addBibleId(prefixed[1], prefixed[2], prefixed[3]);
    } else if (sourceSlug === "mishnah") {
      if (prefixed) addTractateId(prefixed[1], prefixed[2], prefixed[3]);
      // Chapter-only and mishnah-only within a currently-open tractate are
      // handled by text scan, since we don't know the tractate from the query.
    } else if (sourceSlug === "ibn-kathir") {
      // Per-surah page; "a1" is the first ayah commentary on the open page.
      if (onlyNum) ids.push("a" + q);
      if (two) ids.push("a" + two[2]);
    }

    return ids;
  }

  function performSearch(side) {
    const els = getPaneEls(side);
    const query = els.search.value.trim();
    if (!query) {
      els.results.hidden = true;
      els.results.innerHTML = "";
      return;
    }

    const slug = els.select.value;
    const source = SOURCE_BY_SLUG[slug];

    // Multi-page sources: search the pre-built JSON index.
    if (source && source.indexUrl) {
      performIndexedSearch(side, source, query);
      return;
    }

    // Single-page sources: scan the iframe DOM.
    performIframeSearch(side, slug, query);
  }

  function performIframeSearch(side, slug, query) {
    const els = getPaneEls(side);
    const doc = iframeDoc(els.frame);
    if (!doc) {
      els.results.innerHTML = '<div class="compare-search-status">Iframe still loading — try again in a moment.</div>';
      els.results.hidden = false;
      return;
    }

    // Try candidate IDs derived from a friendly verse reference first.
    const derivedIds = candidateIds(query, slug);
    for (let j = 0; j < derivedIds.length; j++) {
      const el = doc.getElementById(derivedIds[j]);
      if (el) {
        scrollFrameTo(els.frame, el);
        els.results.innerHTML = '<div class="compare-search-status">Jumped to #' + derivedIds[j] + '.</div>';
        els.results.hidden = false;
        setTimeout(function () { els.results.hidden = true; }, 1800);
        return;
      }
    }

    // Raw anchor id (user typed it exactly — e.g. "s2v23", "genesis-1-1").
    // All IDs in the readers are lowercase, so try the lowercased form too.
    const looksLikeId = /^[a-z0-9][a-z0-9\-]*$/i.test(query) && query.length <= 40 && query.indexOf(" ") < 0;
    if (looksLikeId) {
      const byId = doc.getElementById(query) || doc.getElementById(query.toLowerCase());
      if (byId) {
        scrollFrameTo(els.frame, byId);
        els.results.innerHTML = '<div class="compare-search-status">Jumped to #' + byId.id + '.</div>';
        els.results.hidden = false;
        setTimeout(function () { els.results.hidden = true; }, 1800);
        return;
      }
    }

    const items = doc.querySelectorAll(CONTENT_SELECTOR);
    const qLower = query.toLowerCase();
    const matches = [];
    for (let i = 0; i < items.length && matches.length < 100; i++) {
      const el = items[i];
      const txt = el.textContent || "";
      if (txt.toLowerCase().indexOf(qLower) >= 0) {
        matches.push({
          el: el,
          ref: el.id || "",
          snippet: buildSnippet(txt, query),
        });
      }
    }
    renderResults(els, matches, query, function (m) {
      scrollFrameTo(els.frame, m.el);
    });
  }

  function performIndexedSearch(side, source, query) {
    const els = getPaneEls(side);

    // Show a loading state while the JSON fetches — multi-MB indexes
    // take a noticeable moment the first time the user searches.
    els.results.innerHTML =
      '<div class="compare-search-status">Searching all of ' +
      source.title.replace(/[<>&]/g, "") + "…</div>";
    els.results.hidden = false;

    // Remember what the user typed at fetch time so we don't render
    // results for a stale query if the user kept typing.
    const atSubmit = query;

    Promise.resolve(loadIndex(source)).then(function (idx) {
      // Bail if the input changed or the pane switched sources while we
      // were waiting for the fetch.
      if (els.search.value.trim() !== atSubmit) return;
      if (els.select.value !== source.slug) return;

      const res = searchIndexEntries(idx.entries || [], atSubmit, 50);
      const rendered = res.matches.map(function (e) {
        return {
          ref:     e.ref || e.href || "",
          snippet: buildSnippet(e.text || "", atSubmit),
          href:    e.href,
        };
      });
      renderResults(els, rendered, atSubmit, function (m) {
        jumpIndexed(side, source, m.href);
      }, res.total);
    }).catch(function (err) {
      els.results.innerHTML =
        '<div class="compare-search-status">Could not load the search index: ' +
        String(err.message || err).replace(/[<>&]/g, "") + "</div>";
      els.results.hidden = false;
    });
  }

  // -- Init --------------------------------------------------------------
  function debounce(fn, ms) {
    let t = null;
    return function () {
      const args = arguments;
      const ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  function init() {
    const left = getPaneEls("left");
    const right = getPaneEls("right");

    populateSelect(left.select);
    populateSelect(right.select);

    left.select.addEventListener("change", onSelectChange("left"));
    right.select.addEventListener("change", onSelectChange("right"));

    const onLeftSearch  = debounce(function () { performSearch("left");  }, 220);
    const onRightSearch = debounce(function () { performSearch("right"); }, 220);
    left.search.addEventListener("input", onLeftSearch);
    right.search.addEventListener("input", onRightSearch);

    // Hide the results dropdown on click outside the pane.
    document.addEventListener("click", function (e) {
      ["left", "right"].forEach(function (side) {
        const els = getPaneEls(side);
        if (!els.pane.contains(e.target)) els.results.hidden = true;
      });
    });

    // ESC closes the open results list.
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        left.results.hidden = true;
        right.results.hidden = true;
      }
    });

    // When user scrolls/clicks inside an iframe to a new anchor, reflect
    // that back into the URL so reloads preserve it.
    function watchFrameHash(side) {
      const frame = getPaneEls(side).frame;
      frame.addEventListener("load", function () {
        try {
          const win = frame.contentWindow;
          if (!win) return;
          win.addEventListener("hashchange", function () {
            const h = (win.location.hash || "").replace(/^#/, "");
            // For indexed sources, the iframe may be on a sub-page; we
            // also need to remember which sub-page so reload lands on
            // the right one. We encode it as "<subpage>.html#<anchor>".
            const state = readParams();
            const slug = state[side];
            const source = SOURCE_BY_SLUG[slug];
            let value = h;
            if (source && source.indexUrl && h) {
              const pathname = win.location.pathname || "";
              const filename = pathname.slice(pathname.lastIndexOf("/") + 1);
              // Only prepend the sub-page when it's different from the
              // source's index landing page.
              const landing = source.path.slice(source.path.lastIndexOf("/") + 1);
              if (filename && filename !== landing) {
                value = filename + "#" + h;
              }
            }
            if (side === "left")  state.lh = value;
            if (side === "right") state.rh = value;
            writeParams(state);
          });
        } catch (_) {}
      });
    }
    watchFrameHash("left");
    watchFrameHash("right");

    // Initial load from URL params.
    const state = readParams();
    setSource("left",  state.left,  state.lh);
    setSource("right", state.right, state.rh);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

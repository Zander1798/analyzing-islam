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
    { slug: "apocryphal-gospels", title: "Apocryphal Infancy Gospels",    path: "read-external/apocryphal-gospels.html", group: "Comparative scripture" },
    { slug: "book-of-enoch",      title: "The Book of Enoch (1 Enoch)",   path: "read-external/book-of-enoch.html",      group: "Comparative scripture" },
    { slug: "mishnah",            title: "The Mishnah (Kulp)",            path: "read-external/mishnah.html",            group: "Comparative scripture" },
    { slug: "josephus",           title: "Flavius Josephus",              path: "read-external/josephus.html",           group: "Comparative scripture" },

    // --- Classical Islamic scholarship ---
    { slug: "ibn-kathir",  title: "Tafsīr Ibn Kathīr",               path: "read-external/ibn-kathir.html",  group: "Classical Islamic scholarship" },
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

  // -- Pane behaviour ----------------------------------------------------
  function setSource(side, slug, hash) {
    const els = getPaneEls(side);
    const source = SOURCE_BY_SLUG[slug] || SOURCE_BY_SLUG[DEFAULT_LEFT];
    if (!source) return;

    let src = source.path + (source.path.indexOf("?") >= 0 ? "&" : "?") + "embed=1";
    if (hash) src += "#" + hash.replace(/^#/, "");
    if (els.frame.src !== location.origin + "/" + src && els.frame.getAttribute("src") !== src) {
      els.frame.src = src;
    }
    els.select.value = slug;
    // Reset the search UI on source change.
    els.search.value = "";
    els.results.hidden = true;
    els.results.innerHTML = "";
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

  function renderResults(els, matches, query, frame) {
    els.results.innerHTML = "";
    if (!matches.length) {
      const empty = document.createElement("div");
      empty.className = "compare-search-status";
      empty.textContent = 'No matches for "' + query + '".';
      els.results.appendChild(empty);
      els.results.hidden = false;
      return;
    }
    const hdr = document.createElement("div");
    hdr.className = "compare-search-status";
    hdr.textContent = matches.length + " match" + (matches.length === 1 ? "" : "es") + (matches.length >= 50 ? " (showing first 50)" : "");
    els.results.appendChild(hdr);
    matches.slice(0, 50).forEach(function (m) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "compare-search-result";
      btn.innerHTML =
        '<span class="ref">' + (m.ref || "").replace(/[<>&]/g, "") + "</span>" +
        '<span class="snippet">' + m.snippet + "</span>";
      btn.addEventListener("click", function () {
        scrollFrameTo(frame, m.el);
        els.results.hidden = true;
      });
      els.results.appendChild(btn);
    });
    els.results.hidden = false;
  }

  function performSearch(side) {
    const els = getPaneEls(side);
    const query = els.search.value.trim();
    if (!query) {
      els.results.hidden = true;
      els.results.innerHTML = "";
      return;
    }
    const doc = iframeDoc(els.frame);
    if (!doc) {
      els.results.innerHTML = '<div class="compare-search-status">Iframe still loading — try again in a moment.</div>';
      els.results.hidden = false;
      return;
    }

    // Optimisation: if the query looks like an anchor id the source uses,
    // jump straight to it instead of doing a text scan.
    const looksLikeId = /^[a-z0-9][a-z0-9\-]*$/i.test(query) && query.length <= 40 && query.indexOf(" ") < 0;
    if (looksLikeId) {
      const byId = doc.getElementById(query);
      if (byId) {
        scrollFrameTo(els.frame, byId);
        els.results.innerHTML = '<div class="compare-search-status">Jumped to #' + query + '.</div>';
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
    renderResults(els, matches, query, els.frame);
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
            const state = readParams();
            if (side === "left")  state.lh = h;
            if (side === "right") state.rh = h;
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

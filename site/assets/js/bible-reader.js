// Bible interlinear reader. Click any <span class="w" data-s="…">
// to slide a panel open with the Strong's entry, parsed morphology,
// and a concordance list of every verse where this Strong's appears.
//
// Data sources (all under ../bible/data/):
//   strongs-hebrew.json    Loaded once, at page ready.
//   strongs-greek.json     Loaded once, at page ready.
//   concordance.json       Loaded once, at first panel open.
//   books/<slug>.json      Loaded only when a concordance row is clicked
//                          AND it links to a different book than the one
//                          currently rendered (for the "jump to verse"
//                          preview). Current book's text is already in
//                          the DOM.
(function () {
  "use strict";

  const DATA = (document.body && document.body.dataset) || {};
  const CURRENT_BOOK = DATA.bookSlug || "";
  const DATA_BASE = DATA.dataBase || "data/";
  const BOOKS_BASE = DATA.booksBase || "../bible/";

  // --- Book display names (populated from the page itself via data attr) ---
  const BOOK_NAMES = (function () {
    try { return JSON.parse(DATA.bookNames || "{}"); }
    catch (e) { return {}; }
  })();

  // Canonical book order so the aggregated concordance lists hits in
  // OT-then-NT canonical sequence rather than alphabetical book code.
  const BOOK_ORDER = {
    gen:1, exo:2, lev:3, num:4, deu:5, jos:6, jdg:7, rut:8, "1sa":9, "2sa":10,
    "1ki":11, "2ki":12, "1ch":13, "2ch":14, ezr:15, neh:16, est:17, job:18,
    psa:19, pro:20, ecc:21, sng:22, isa:23, jer:24, lam:25, ezk:26, dan:27,
    hos:28, jol:29, amo:30, oba:31, jon:32, mic:33, nam:34, hab:35, zep:36,
    hag:37, zec:38, mal:39,
    mat:40, mrk:41, luk:42, jhn:43, act:44, rom:45, "1co":46, "2co":47,
    gal:48, eph:49, php:50, col:51, "1th":52, "2th":53, "1ti":54, "2ti":55,
    tit:56, phm:57, heb:58, jas:59, "1pe":60, "2pe":61, "1jn":62, "2jn":63,
    "3jn":64, jud:65, rev:66,
  };

  // --- Lazy caches ---
  let strongsHeb = null;
  let strongsGrk = null;
  let concordance = null;
  const fetchCache = new Map();

  function fetchJson(url) {
    if (fetchCache.has(url)) return fetchCache.get(url);
    const p = fetch(url).then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
    fetchCache.set(url, p);
    return p;
  }

  // --- Side panel DOM ---
  const panel = document.createElement("aside");
  panel.className = "bible-panel";
  panel.innerHTML =
    '<div class="bible-panel-header">' +
    '  <div>' +
    '    <h3 id="panel-lemma">—</h3>' +
    '    <div class="panel-meta" id="panel-meta"></div>' +
    '  </div>' +
    '  <button type="button" class="bible-panel-close" aria-label="Close">×</button>' +
    '</div>' +
    '<div class="bible-panel-body" id="panel-body">' +
    '  <div class="bible-loading">Loading…</div>' +
    '</div>';
  document.body.appendChild(panel);
  const panelLemma = panel.querySelector("#panel-lemma");
  const panelMeta = panel.querySelector("#panel-meta");
  const panelBody = panel.querySelector("#panel-body");
  panel.querySelector(".bible-panel-close").addEventListener("click", closePanel);

  // Close on Esc
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closePanel();
  });

  function openPanel() {
    panel.classList.add("is-open");
  }
  function closePanel() {
    panel.classList.remove("is-open");
    document.querySelectorAll(".w.is-active").forEach((el) => el.classList.remove("is-active"));
  }

  // --- Load dictionaries on demand ---
  async function ensureStrongs(lang) {
    if (lang === "heb" && !strongsHeb) {
      strongsHeb = await fetchJson(DATA_BASE + "strongs-hebrew.json");
    }
    if (lang === "grk" && !strongsGrk) {
      strongsGrk = await fetchJson(DATA_BASE + "strongs-greek.json");
    }
    return lang === "heb" ? strongsHeb : strongsGrk;
  }
  async function ensureConcordance() {
    if (!concordance) {
      concordance = await fetchJson(DATA_BASE + "concordance.json");
    }
    return concordance;
  }

  // STEPBible's TAHOT/TAGNT data tags words with a disambiguation
  // suffix (e.g. H0776G, H7225G, H2148v, G2316T) that the OpenScriptures
  // Strong's dictionaries don't carry — those use the bare number
  // (H0776, G2316). Strip the trailing letter(s) to fall back to the
  // base entry. Case-insensitive so H2148v / H2148w also strip.
  function baseSid(sid) {
    return String(sid || "").replace(/[A-Z]+$/i, "");
  }
  // Some words carry a compound tag like "H0001G,H5703" meaning the
  // word fuses two lemmas. Take the first as the primary lookup.
  function primarySid(sid) {
    const s = String(sid || "");
    const comma = s.indexOf(",");
    return comma >= 0 ? s.slice(0, comma) : s;
  }
  // Resolve a Strong's tag against a dictionary using all fallbacks.
  function resolveEntry(dict, sid) {
    if (!dict || !sid) return null;
    return dict[sid] ||
           dict[baseSid(sid)] ||
           dict[primarySid(sid)] ||
           dict[baseSid(primarySid(sid))] ||
           null;
  }

  // --- Format the panel body ---
  function renderPanel(meta) {
    // meta: {strongs, morph, morph_en, orig, trans, gloss, verseRef, lang}
    const sid = meta.strongs;
    const dict = meta.lang === "heb" ? strongsHeb : strongsGrk;
    // Lexicon lookup: exact key first (H0776A); fall back through the
    // disambiguation-stripped base number (H0776), then the first half
    // of any compound tag (H0001G,H5703 → H0001G → H0001).
    const entry = resolveEntry(dict, sid);

    panelLemma.textContent = entry ? (entry.lemma || meta.orig) : meta.orig;
    panelMeta.textContent = [
      sid || "(no Strong's)",
      entry && entry.translit ? entry.translit : meta.trans,
      entry && entry.pron ? "/" + entry.pron + "/" : "",
    ].filter(Boolean).join(" · ");

    let html = "";

    // Gloss at this position
    html += '<div class="panel-section">' +
      '<div class="panel-section-label">In this verse</div>' +
      '<div class="panel-section-content">' +
      '<em>' + escapeHtml(meta.verseRef) + '</em> — ' +
      '“' + escapeHtml(meta.gloss || "(no gloss)") + '”' +
      '</div></div>';

    // Morphology
    if (meta.morph || (meta.morph_en && meta.morph_en.length)) {
      html += '<div class="panel-section">' +
        '<div class="panel-section-label">Morphology</div>' +
        '<div class="panel-section-content">' +
        (meta.morph_en && meta.morph_en.length ? escapeHtml(meta.morph_en.join(" · ")) : "") +
        (meta.morph ? '<div class="concordance-count" style="margin-top:4px;">raw: ' + escapeHtml(meta.morph) + '</div>' : '') +
        '</div></div>';
    }

    // Lexicon
    if (entry) {
      html += '<div class="panel-section">' +
        '<div class="panel-section-label">Strong\'s ' + escapeHtml(sid) + '</div>' +
        '<dl class="panel-grid">' +
        (entry.lemma ? '<dt>Lemma</dt><dd>' + escapeHtml(entry.lemma) + '</dd>' : '') +
        (entry.translit ? '<dt>Translit.</dt><dd>' + escapeHtml(entry.translit) + '</dd>' : '') +
        (entry.pron ? '<dt>Pronunciation</dt><dd>' + escapeHtml(entry.pron) + '</dd>' : '') +
        (entry.derivation ? '<dt>Derivation</dt><dd>' + escapeHtml(entry.derivation) + '</dd>' : '') +
        (entry.strongs_def ? '<dt>Definition</dt><dd>' + escapeHtml(entry.strongs_def) + '</dd>' : '') +
        (entry.kjv_def ? '<dt>KJV uses</dt><dd>' + escapeHtml(entry.kjv_def) + '</dd>' : '') +
        '</dl>' +
        '</div>';
    } else if (sid) {
      // Reaching this branch now means BOTH the suffixed sid AND the
      // base number missed. That genuinely indicates a grammatical-
      // morpheme tag (H9xxx range used by STEPBible for affixes,
      // particles, joiners etc.) that has no Strong's entry.
      const isMorpheme = /^[HG]9\d{3}/i.test(sid);
      html += '<div class="panel-section"><div class="panel-section-label">Strong\'s ' +
        escapeHtml(sid) + '</div>' +
        '<div class="panel-section-content">' +
        (isMorpheme
          ? 'STEPBible grammatical morpheme (H9xxx range) — no Strong\'s entry exists. These tags mark prefixes, suffixes, conjunctions, and other grammatical particles, not lexical roots.'
          : 'No lexicon entry available for this Strong\'s tag.') +
        '</div></div>';
    }

    // Concordance
    html += '<div class="panel-section">' +
      '<div class="panel-section-label">Other occurrences</div>' +
      '<div id="panel-concordance"><div class="bible-loading">Loading concordance…</div></div>' +
      '</div>';

    panelBody.innerHTML = html;

    // Load concordance async
    if (sid) loadConcordance(sid, meta);
  }

  async function loadConcordance(sid, meta) {
    try {
      const conc = await ensureConcordance();
      // Concordance was built per raw `data-s` value, so H0776, H0776A,
      // H0776G are split into separate keys. Aggregate every variant of
      // the base number so the user sees the full base-word concordance,
      // not the fragment for one inflected form. De-dupe by location.
      // Aggregate across every key that shares the same base number, so
      // H0776, H0776A, H0776B, H0776G all contribute to the lookup of
      // any one of them. Also handles compound tags by using the
      // primary (first) half. Letter suffixes are matched case-insensitively.
      const base = baseSid(primarySid(sid));
      const seen = new Set();
      let hits = [];
      const isVariant = function (k) {
        if (k === base) return true;
        if (k.indexOf(base) !== 0) return false;
        return /^[A-Za-z]+$/.test(k.slice(base.length));
      };
      const variantKeys = Object.keys(conc).filter(isVariant);
      // Always include the exact sid first if present, even if its base
      // didn't match the filter above (defensive).
      if (variantKeys.indexOf(sid) < 0 && conc[sid]) variantKeys.push(sid);
      for (const k of variantKeys) {
        const list = conc[k];
        if (!Array.isArray(list)) continue;
        for (const row of list) {
          const key = row.join(":");
          if (seen.has(key)) continue;
          seen.add(key);
          hits.push(row);
        }
      }
      // Sort for deterministic ordering: by book index, chapter, verse, word.
      hits.sort(function (a, b) {
        const ai = BOOK_ORDER[a[0]] || 999, bi = BOOK_ORDER[b[0]] || 999;
        return ai - bi || a[1] - b[1] || a[2] - b[2] || a[3] - b[3];
      });
      const target = document.getElementById("panel-concordance");
      if (!target) return;
      if (!hits.length) {
        target.innerHTML = '<div class="panel-section-content">No other occurrences indexed.</div>';
        return;
      }
      let html = '<div class="concordance-count">' + hits.length + ' occurrence' +
                 (hits.length === 1 ? '' : 's') + ' across the Bible</div>';
      html += '<ol class="concordance-list">';
      for (const [bk, ch, vs, wi] of hits.slice(0, 200)) {
        const name = BOOK_NAMES[bk] || bk;
        const isCurrent = bk === CURRENT_BOOK;
        const href = isCurrent
          ? "#" + bk + "-" + ch + "-" + vs
          : BOOKS_BASE + bk + ".html#" + bk + "-" + ch + "-" + vs;
        html += '<li><a href="' + href + '" ' +
                'data-target="' + bk + '-' + ch + '-' + vs + '" ' +
                'data-strongs="' + sid + '">' +
                '<span>' + escapeHtml(name) + ' ' + ch + ':' + vs + '</span>' +
                '<span class="concordance-ref">' + sid + '</span>' +
                '</a></li>';
      }
      if (hits.length > 200) {
        html += '<li><span class="concordance-ref" style="padding: 4px 0; display:block;">' +
                '(+' + (hits.length - 200) + ' more not shown)</span></li>';
      }
      html += '</ol>';
      target.innerHTML = html;

      // Wire up click → highlight target verse on same-page jumps
      target.querySelectorAll("a").forEach((a) => {
        a.addEventListener("click", function (e) {
          const tgt = a.getAttribute("data-target");
          const same = a.getAttribute("href").startsWith("#");
          if (same) {
            // Let the browser do its default scroll, then highlight.
            setTimeout(() => {
              document.querySelectorAll(".w.is-highlight").forEach(el => el.classList.remove("is-highlight"));
              const vs = document.getElementById(tgt);
              if (!vs) return;
              const strongs = a.getAttribute("data-strongs");
              vs.querySelectorAll('.w[data-s="' + strongs + '"]').forEach((w) => w.classList.add("is-highlight"));
            }, 50);
          }
          // cross-book links carry a hash; the target book's reader will
          // naturally scroll on hash change.
        });
      });
    } catch (e) {
      const target = document.getElementById("panel-concordance");
      if (target) target.innerHTML = '<div class="panel-section-content">Failed to load concordance: ' + e.message + '</div>';
    }
  }

  // --- Word click handler ---
  document.addEventListener("click", async function (e) {
    const w = e.target.closest(".w");
    if (!w) return;
    const sid = w.getAttribute("data-s") || "";
    const morph = w.getAttribute("data-m") || "";
    const morphEn = (w.getAttribute("data-me") || "").split("|").filter(Boolean);
    const verseEl = w.closest(".bible-verse");
    const chapterEl = w.closest(".bible-chapter");
    const verseN = verseEl ? verseEl.dataset.v : "?";
    const chapterN = chapterEl ? chapterEl.dataset.c : "?";
    const lang = document.body.classList.contains("bible-lang-heb") ? "heb" : "grk";
    const origEl = w.querySelector(".w-orig");
    const transEl = w.querySelector(".w-trans");
    const glossEl = w.querySelector(".w-gloss");
    const bookName = BOOK_NAMES[CURRENT_BOOK] || CURRENT_BOOK;

    document.querySelectorAll(".w.is-active").forEach((el) => el.classList.remove("is-active"));
    w.classList.add("is-active");

    openPanel();
    panelLemma.textContent = "Loading…";
    panelBody.innerHTML = '<div class="bible-loading">Loading…</div>';

    try {
      await ensureStrongs(lang);
    } catch (e) {
      panelBody.innerHTML = '<div class="bible-loading">Failed to load dictionary.</div>';
      return;
    }

    renderPanel({
      strongs: sid,
      morph: morph,
      morph_en: morphEn,
      orig: origEl ? origEl.textContent : "",
      trans: transEl ? transEl.textContent : "",
      gloss: glossEl ? glossEl.textContent : "",
      verseRef: bookName + " " + chapterN + ":" + verseN,
      lang: lang,
    });
  });

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
})();

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

  // --- Format the panel body ---
  function renderPanel(meta) {
    // meta: {strongs, morph, morph_en, orig, trans, gloss, verseRef, lang}
    const sid = meta.strongs;
    const dict = meta.lang === "heb" ? strongsHeb : strongsGrk;
    const entry = dict && dict[sid];

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
      html += '<div class="panel-section"><div class="panel-section-label">Strong\'s ' +
        escapeHtml(sid) + '</div>' +
        '<div class="panel-section-content">No lexicon entry loaded — this may be a ' +
        'grammatical-morpheme tag (e.g. H9xxx) not present in the Strong\'s dictionary.</div>' +
        '</div>';
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
      const hits = conc[sid] || [];
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

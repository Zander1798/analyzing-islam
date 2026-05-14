// Quran interlinear reader. Click any <span class="w" data-root="…">
// to slide a panel open with the root/lemma entry, parsed morphology,
// and a concordance list of every verse in the Quran where this root appears.
//
// Data sources (all under data/ relative to each surah page):
//   concordance.json   Loaded once, at first panel open.
//   lexicon.json       Loaded once, at first panel open.
(function () {
  "use strict";

  const DATA = (document.body && document.body.dataset) || {};
  const DATA_BASE = DATA.dataBase || "data/";

  // Map of surah number → {name, en, ar, slug} (populated from body data attr)
  const SURAH_NAMES = (function () {
    try { return JSON.parse(DATA.surahNames || "{}"); }
    catch (e) { return {}; }
  })();

  // Detect current surah number from the first .bible-chapter element
  function getCurrentSurah() {
    const ch = document.querySelector(".bible-chapter");
    return ch ? parseInt(ch.dataset.c || "1", 10) : 1;
  }
  const CURRENT_SURAH = getCurrentSurah();

  // --- Lazy caches ---
  let concordance = null;
  let lexicon = null;
  let definitions = null;
  const fetchCache = new Map();
  let activeWord = null;

  function fetchJson(url) {
    if (fetchCache.has(url)) return fetchCache.get(url);
    const p = fetch(url).then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
    fetchCache.set(url, p);
    return p;
  }

  // Prefetch data files during idle time so the first click is fast
  if (typeof requestIdleCallback === "function") {
    requestIdleCallback(function () {
      fetchJson(DATA_BASE + "concordance.json");
      fetchJson(DATA_BASE + "lexicon.json");
      fetchJson(DATA_BASE + "definitions.json");
    });
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
  const panelMeta  = panel.querySelector("#panel-meta");
  const panelBody  = panel.querySelector("#panel-body");
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
    if (activeWord) { activeWord.classList.remove("is-active"); activeWord = null; }
  }

  // --- Ensure data loaded ---
  async function ensureData() {
    if (!concordance) {
      concordance = await fetchJson(DATA_BASE + "concordance.json");
    }
    if (!lexicon) {
      lexicon = await fetchJson(DATA_BASE + "lexicon.json");
    }
    if (!definitions) {
      definitions = await fetchJson(DATA_BASE + "definitions.json").catch(() => ({}));
    }
  }

  // Expand POS abbreviation
  function expandPos(pos) {
    const posMap = {
      N: "Noun", V: "Verb", ADJ: "Adjective", ADV: "Adverb",
      PRON: "Pronoun", PREP: "Preposition", CONJ: "Conjunction",
      PART: "Particle", PN: "Proper noun", INTJ: "Interjection",
      REL: "Relative pronoun", DEM: "Demonstrative pronoun",
      DET: "Definite article",
    };
    if (!pos) return "";
    return posMap[pos] || pos;
  }

  // --- Render panel ---
  function renderPanel(meta) {
    // meta: {root, lem, pos, feats, orig, trans, gloss, verseRef, surahNum}
    const root  = meta.root || "";
    const lem   = meta.lem  || "";
    const entry = root ? (lexicon && lexicon[root]) : null;

    // Header: lemma (Arabic lemma or root if no lemma)
    const displayLemma = lem || root;
    panelLemma.innerHTML = displayLemma
      ? '<span class="quran-panel-root">' + escapeHtml(displayLemma) + '</span>'
      : '—';
    const metaParts = [];
    if (root && root !== displayLemma) metaParts.push("root: " + root);
    if (meta.pos) metaParts.push(expandPos(meta.pos));
    panelMeta.textContent = metaParts.filter(Boolean).join(" · ");

    let html = "";

    // Gloss at this position
    html += '<div class="panel-section">' +
      '<div class="panel-section-label">In this verse</div>' +
      '<div class="panel-section-content">' +
      '<em>' + escapeHtml(meta.verseRef) + '</em> — ' +
      '"' + escapeHtml(meta.gloss || "(no gloss)") + '"' +
      '</div></div>';

    // Morphology
    if (meta.feats) {
      const featList = meta.feats.split("|").filter(Boolean);
      if (featList.length) {
        html += '<div class="panel-section">' +
          '<div class="panel-section-label">Morphology</div>' +
          '<div class="panel-section-content">' +
          escapeHtml(featList.join(" · ")) +
          '</div></div>';
      }
    }

    // Lexicon entry
    const defn = root && definitions ? (definitions[root] || null) : null;
    if (entry) {
      html += '<div class="panel-section">' +
        '<div class="panel-section-label">Root: ' + escapeHtml(root) + '</div>' +
        '<dl class="panel-grid">' +
        (entry.lem ? '<dt>Lemma</dt><dd><span dir="rtl" style="font-family:\'Scheherazade New\',serif;">' + escapeHtml(entry.lem) + '</span></dd>' : '') +
        (entry.pos ? '<dt>Part of speech</dt><dd>' + escapeHtml(expandPos(entry.pos) || entry.pos) + '</dd>' : '') +
        (entry.gloss ? '<dt>Gloss</dt><dd>' + escapeHtml(entry.gloss) + '</dd>' : '') +
        (defn ? '<dt>Definition</dt><dd class="panel-definition">' + escapeHtml(defn) + '</dd>' : '') +
        (entry.count ? '<dt>Occurrences</dt><dd>' + entry.count + ' in Quran</dd>' : '') +
        '</dl>' +
        (defn ? '<div class="panel-attrib">Lane\'s Arabic-English Lexicon, 1863</div>' : '') +
        '</div>';
    } else if (!root) {
      html += '<div class="panel-section"><div class="panel-section-content">Grammatical particle — no root entry.</div></div>';
    } else {
      html += '<div class="panel-section"><div class="panel-section-label">Root: ' + escapeHtml(root) + '</div>' +
        '<div class="panel-section-content">No lexicon entry available.</div></div>';
    }

    // Concordance
    html += '<div class="panel-section">' +
      '<div class="panel-section-label">Other occurrences</div>' +
      '<div id="panel-concordance">' +
      (root ? '<div class="bible-loading">Loading concordance…</div>' : '<div class="panel-section-content">No root — no concordance.</div>') +
      '</div>' +
      '</div>';

    panelBody.innerHTML = html;

    if (root) loadConcordance(root, meta);
  }

  async function loadConcordance(root, meta) {
    try {
      const target = document.getElementById("panel-concordance");
      if (!target) return;

      const hits = (concordance && concordance[root]) ? concordance[root] : [];

      if (!hits.length) {
        target.innerHTML = '<div class="panel-section-content">No other occurrences indexed.</div>';
        return;
      }

      // Sort by surah, verse, word position
      const sorted = hits.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);

      let html = '<div class="concordance-count">' + sorted.length + ' occurrence' +
                 (sorted.length === 1 ? '' : 's') + ' in the Quran</div>';
      html += '<ol class="concordance-list">';
      for (const [s, v, w] of sorted.slice(0, 200)) {
        const si = SURAH_NAMES[String(s)];
        const surahLabel = si ? si.name : ("Surah " + s);
        const isCurrent = s === CURRENT_SURAH;
        const surahFile = "surah-" + String(s).padStart(3, "0") + ".html";
        const anchor    = "#s" + s + "v" + v;
        const href = isCurrent ? anchor : (surahFile + anchor);
        html += '<li><a href="' + href + '" ' +
                'data-target="s' + s + 'v' + v + '" ' +
                'data-root="' + escapeHtml(root) + '">' +
                '<span>' + escapeHtml(surahLabel) + ' ' + s + ':' + v + '</span>' +
                '<span class="concordance-ref">' + s + ':' + v + '</span>' +
                '</a></li>';
      }
      if (sorted.length > 200) {
        html += '<li><span class="concordance-ref" style="padding: 4px 0; display:block;">' +
                '(+' + (sorted.length - 200) + ' more not shown)</span></li>';
      }
      html += '</ol>';
      target.innerHTML = html;

      // Wire up click → highlight target verse on same-page jumps
      target.querySelectorAll("a").forEach((a) => {
        a.addEventListener("click", function () {
          const tgt = a.getAttribute("data-target");
          const same = a.getAttribute("href").startsWith("#");
          if (same) {
            setTimeout(() => {
              document.querySelectorAll(".w.is-highlight").forEach((el) => el.classList.remove("is-highlight"));
              const vs = document.getElementById(tgt);
              if (!vs) return;
              const r = a.getAttribute("data-root");
              vs.querySelectorAll('.w[data-root="' + r + '"]').forEach((w) => w.classList.add("is-highlight"));
            }, 50);
          }
        });
      });
    } catch (e) {
      const target = document.getElementById("panel-concordance");
      if (target) target.innerHTML = '<div class="panel-section-content">Failed to load concordance: ' + escapeHtml(e.message) + '</div>';
    }
  }

  // --- Word click handler ---
  document.addEventListener("click", async function (e) {
    const w = e.target.closest(".w");
    if (!w) return;

    const root  = w.getAttribute("data-root") || "";
    const lem   = w.getAttribute("data-lem")  || "";
    const pos   = w.getAttribute("data-pos")  || "";
    const feats = w.getAttribute("data-m")    || "";

    const verseEl   = w.closest(".bible-verse");
    const chapterEl = w.closest(".bible-chapter");
    const vNum      = verseEl ? verseEl.dataset.v : "?";
    const sNum      = chapterEl ? chapterEl.dataset.c : "?";

    const si = SURAH_NAMES[String(sNum)];
    const surahLabel = si ? si.name : ("Surah " + sNum);

    const origEl  = w.querySelector(".w-orig");
    const transEl = w.querySelector(".w-trans");
    const glossEl = w.querySelector(".w-gloss");

    if (activeWord) activeWord.classList.remove("is-active");
    activeWord = w;
    w.classList.add("is-active");

    openPanel();
    panelLemma.innerHTML = '<span class="quran-panel-root">…</span>';
    panelBody.innerHTML = '<div class="bible-loading">Loading…</div>';

    try {
      await ensureData();
    } catch (err) {
      panelBody.innerHTML = '<div class="bible-loading">Failed to load data: ' + escapeHtml(err.message) + '</div>';
      return;
    }

    renderPanel({
      root:     root,
      lem:      lem,
      pos:      pos,
      feats:    feats,
      orig:     origEl  ? origEl.textContent  : "",
      trans:    transEl ? transEl.textContent : "",
      gloss:    glossEl ? glossEl.textContent : "",
      verseRef: surahLabel + " " + sNum + ":" + vNum,
      surahNum: parseInt(sNum, 10) || 1,
    });
  });

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
})();

#!/usr/bin/env node
// build-quran-interlinear.js
// Generates the full Arabic-English interlinear Quran reader.
// Node v22+, no npm dependencies.
"use strict";

const https = require("https");
const fs = require("fs");
const path = require("path");

const SITE = path.join(__dirname, "site");
const OUT_DIR = path.join(SITE, "read-external", "quran");
const DATA_DIR = path.join(OUT_DIR, "data");

fs.mkdirSync(DATA_DIR, { recursive: true });

// ── Fetch helpers ────────────────────────────────────────────────────────────

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return get(res.headers.location).then(resolve, reject);
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        } else {
          resolve(Buffer.concat(chunks).toString("utf8"));
        }
      });
    }).on("error", reject);
  });
}

async function fetchJson(url, label) {
  let text;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      process.stdout.write(`  Fetching ${label || url}…`);
      text = await get(url);
      process.stdout.write(" ok\n");
      return JSON.parse(text);
    } catch (e) {
      process.stdout.write(` attempt ${attempt} failed: ${e.message}\n`);
      if (attempt < 3) await delay(500);
      else throw e;
    }
  }
}

async function fetchText(url, label) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      process.stdout.write(`  Fetching ${label || url}…`);
      const t = await get(url);
      process.stdout.write(" ok\n");
      return t;
    } catch (e) {
      process.stdout.write(` attempt ${attempt} failed: ${e.message}\n`);
      if (attempt < 3) await delay(500);
      else throw e;
    }
  }
}

function delay(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ── HTML escaping ─────────────────────────────────────────────────────────────

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// ── Slug generation ───────────────────────────────────────────────────────────

function slugify(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/['']/g, "")
    .replace(/\s*(?:ibn|al|el|at|as|an|ar|az)-\s*/gi, (m) => {
      // Keep "al-" prefix attached with hyphen
      return "-" + m.trim().replace(/\s+/g, "-") + "-";
    })
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Simpler slug: just lowercase-hyphenate the English name
function makeSlug(englishName) {
  return String(englishName || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// ── Morphology parser ─────────────────────────────────────────────────────────
// Line format: surah:verse:word:morpheme\tARABIC_FORM\tPOS\tFEATURES
// We want, per (surah, verse, word): root, lem, pos, features string

function parseMorphology(text) {
  // Map: "s:v:w" → {root, lem, pos, features[]}
  const map = new Map();

  const lines = text.split(/\n/);
  for (const line of lines) {
    if (!line.trim()) continue;
    const tab = line.indexOf("\t");
    if (tab < 0) continue;
    const key = line.slice(0, tab);
    const rest = line.slice(tab + 1);
    const parts = key.split(":");
    if (parts.length < 4) continue;
    const [s, v, w] = parts; // surah, verse, word (morpheme index ignored)
    const mapKey = `${s}:${v}:${w}`;

    const cols = rest.split("\t");
    // cols[0] = Arabic form, cols[1] = POS, cols[2] = FEATURES (optional)
    const pos = cols[1] || "";
    const feats = cols[2] || "";

    // Parse ROOT and LEM from FEATURES
    let root = "";
    let lem = "";
    const rootM = feats.match(/ROOT:([^|]+)/);
    const lemM  = feats.match(/LEM:([^|]+)/);
    if (rootM) root = rootM[1];
    if (lemM)  lem  = lemM[1];

    // A morpheme is a grammatical prefix/suffix if PREF or SUFF appears
    // in its feature string (e.g. "P|PREF|LEM:ب" is a preposition prefix).
    const isPrefSuf = /\bPREF\b/.test(feats) || /\bSUFF\b/.test(feats) || pos === "";

    if (!map.has(mapKey)) {
      // Initialise entry: prefer non-prefix/non-suffix morpheme data
      map.set(mapKey, {
        root: isPrefSuf ? "" : root,
        lem:  isPrefSuf ? "" : lem,
        pos:  isPrefSuf ? "" : pos,
        feats: [], // collect all feature strings
      });
    }

    const entry = map.get(mapKey);
    // Upgrade if this morpheme carries root/lem and current entry doesn't
    if (!isPrefSuf) {
      if (!entry.root && root) entry.root = root;
      if (!entry.lem  && lem)  entry.lem  = lem;
      if (!entry.pos  && pos)  entry.pos  = pos;
    }
    // Collect features for morphology display (skip prefix/suffix markers and LEM/ROOT)
    if (!isPrefSuf) {
      const featParts = feats.split("|").filter((f) => f && !f.startsWith("ROOT:") && !f.startsWith("LEM:") && f !== "PREF" && f !== "SUFF");
      for (const f of featParts) {
        if (!entry.feats.includes(f)) entry.feats.push(f);
      }
    }
  }
  return map;
}

// ── Surah name data ───────────────────────────────────────────────────────────

const SURAH_NAMES_OVERRIDE = {
  1: { name: "Al-Fatiha", en: "The Opening" },
  9: { name: "At-Tawba", en: "The Repentance" }, // no bismillah
};

function buildSurahNamesMap(infoChapters) {
  // Returns array indexed by surah number (1-based), elements: {slug, name, en, ar}
  const result = {};
  for (const ch of infoChapters) {
    const n = ch.chapter;
    const name = ch.name || ch.englishname || `Surah ${n}`;
    const en   = ch.englishname || name;
    const ar   = ch.arabicname || "";
    const slug = makeSlug(name);
    result[n] = { slug, name, en, ar };
  }
  return result;
}

// ── HTML template ─────────────────────────────────────────────────────────────

function padNum(n) {
  return String(n).padStart(3, "0");
}

function buildSurahHtml(opts) {
  const {
    surahNum, surahInfo, surahNames, wordData, morphMap,
    wordCount, surahNamesJson,
  } = opts;

  const { slug, name, en, ar } = surahInfo;
  const revelation  = surahNames[surahNum] ? (surahNames[surahNum].revelation || "") : "";
  const verseCount  = Object.keys(wordData).length;
  // Build the verse list
  const verseNums   = Object.keys(wordData).map(Number).sort((a, b) => a - b);

  // TOC <li> items
  const tocItems = verseNums.map((v) => `<li><a href="#s${surahNum}v${v}">${v}</a></li>`).join("");

  // --- Verse content ---
  let verseHtml = "";
  for (const vNum of verseNums) {
    const vData = wordData[String(vNum)];
    const words = vData.w || [];
    let wordsHtml = "";
    for (let wi = 0; wi < words.length; wi++) {
      const wordIdx = wi + 1; // 1-based
      const mKey = `${surahNum}:${vNum}:${wordIdx}`;
      const morph = morphMap.get(mKey) || { root: "", lem: "", pos: "", feats: [] };

      const arabic   = words[wi].c || "";
      const trans    = words[wi].d || "";
      const gloss    = words[wi].e || "";
      const root     = morph.root || "";
      const lem      = morph.lem  || "";
      const pos      = morph.pos  || "";
      const feats    = morph.feats.join("|");

      wordsHtml +=
        `<span class="w" id="s${surahNum}v${vNum}w${wordIdx}" data-root="${esc(root)}" data-lem="${esc(lem)}" data-pos="${esc(pos)}" data-m="${esc(feats)}">` +
        `<span class="w-orig">${esc(arabic)}</span>` +
        `<span class="w-trans">${esc(trans)}</span>` +
        `<span class="w-gloss">${esc(gloss)}</span>` +
        `</span>`;
    }
    verseHtml +=
      `<li class="bible-verse" id="s${surahNum}v${vNum}" data-v="${vNum}">` +
      `<span class="verse-num">${vNum}</span>` +
      `<span class="ilt-words">${wordsHtml}</span>` +
      `</li>`;
  }

  // Bismillah: add for all surahs except 1 (it's part of the text) and 9
  const bismillah = (surahNum !== 1 && surahNum !== 9)
    ? `<div class="quran-bismillah">بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ</div>\n`
    : "";

  // Revelation info
  const revelStr = revelation ? esc(revelation) + " · " : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="${esc(name)} (${esc(en)}) — Arabic interlinear with root, morphology, and English glosses word-by-word. Click any word for its root entry and concordance.">
<!-- Favicon + app-icon set (browser tab, iOS home-screen, Android manifest) -->
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png">
<link rel="icon" href="/assets/icons/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/assets/icons/site.webmanifest">
<meta name="theme-color" content="#0a0a0a">
<title>${esc(name)} — Quran Interlinear — Analyzing Islam</title>
<link rel="stylesheet" href="../../assets/css/style.css">
<link rel="stylesheet" href="../../assets/css/bible-reader.css">
<link rel="stylesheet" href="../../assets/css/quran-reader.css">
</head>
<body class="quran-lang-ar" data-surah-slug="${esc(slug)}" data-data-base="data/" data-surah-names='${surahNamesJson}'>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../../index.html">Home</a>
      <a href="../../catalog.html">Catalog</a>
      <a href="../../arguments.html">Dossiers</a>
      <a href="../../read.html" class="active">Read</a>
      <a href="../../compare.html">Compare</a>
      <a href="../../build.html">Build</a>
      <a href="../../stats.html">Stats</a>
      <a href="../../about.html">About</a>
      <a href="../../faq.html">FAQ</a>
    </div>
  </div>
</nav>

<div class="bible-layout has-hl-card">

  <aside class="bible-toc">
    <div class="bible-toc-header">Verses</div>
    <ol>
${tocItems}
    </ol>
  </aside>

  <main class="bible-main">
    <header class="bible-hero">
      <div class="bible-meta">Arabic · Interlinear · Root + Morphology</div>
      <h1>${esc(name)} · ${esc(ar)}</h1>
      <p>${esc(en)} — ${revelStr}${verseCount} verses · ${wordCount} words</p>
      <div class="bible-hero-actions"><a href="../quran.html" class="btn">← Quran Interlinear</a></div>
    </header>

${bismillah}<article class="bible-chapter" id="s${surahNum}" data-c="${surahNum}">
<h2>Surah ${surahNum} — ${esc(name)}</h2>
<ol class="bible-verses">
${verseHtml}
</ol>
</article>
  </main>

</div>

<footer class="site-footer">
  Quran interlinear reader. Arabic word-by-word with root, lemma, morphology, and English glosses. Data from qazasaz/quranwbw (CC-BY) and mustafa0x/quran-morphology (CC-BY).
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/auth.js" defer></script>
<script src="../../assets/js/auth-ui.js" defer></script>
<script src="../../assets/js/verse-parser.js" defer></script>
<script src="../../assets/js/quran-reader.js" defer></script>
<script src="../../assets/js/reader-search.js" defer></script>
<script src="../../assets/js/snap-to-hash.js" defer></script>
<script src="../../assets/js/goat-skins.js"></script>
<script src="../../assets/js/goat.js" defer></script>
</body>
</html>`;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  console.log("=== Quran Interlinear Builder ===\n");

  // 1. Fetch surah info
  console.log("Step 1: Fetching surah info…");
  const info = await fetchJson(
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/info.min.json",
    "info.min.json"
  );
  const chapters = info.chapters || [];
  console.log(`  Got ${chapters.length} chapters.\n`);

  // Build a quick map: surahNum → chapter info
  const chapterMap = {};
  for (const ch of chapters) {
    chapterMap[ch.chapter] = ch;
  }

  // Build surah names map
  const surahNamesObj = buildSurahNamesMap(chapters);
  // Add revelation from info
  for (const ch of chapters) {
    if (surahNamesObj[ch.chapter]) {
      surahNamesObj[ch.chapter].revelation = ch.revelation || "";
    }
  }

  // Serialise the names map for embedding in HTML (surah number → {name, en, ar, slug})
  // We embed as a number-keyed map
  const surahNamesForHtml = {};
  for (const [num, info2] of Object.entries(surahNamesObj)) {
    surahNamesForHtml[num] = { name: info2.name, en: info2.en, ar: info2.ar, slug: info2.slug };
  }
  const surahNamesJson = JSON.stringify(surahNamesForHtml).replace(/'/g, "&#39;");

  // 2. Fetch morphology
  console.log("Step 2: Fetching morphology…");
  const morphText = await fetchText(
    "https://raw.githubusercontent.com/mustafa0x/quran-morphology/master/quran-morphology.txt",
    "quran-morphology.txt"
  );
  console.log("  Parsing morphology…");
  const morphMap = parseMorphology(morphText);
  console.log(`  Parsed ${morphMap.size} word entries.\n`);

  // 3. Fetch all 114 surah word JSONs + build concordance + lexicon
  console.log("Step 3: Fetching 114 surah word-by-word JSONs…");
  const concordance = {}; // root → [[surah, verse, word], ...]
  const rootGlosses = {}; // root → {gloss: count}
  const rootLemPos  = {}; // root → {lem, pos}

  let totalWords = 0;
  let totalVerses = 0;
  const surahWordData = {}; // surahNum → wordData JSON

  for (let n = 1; n <= 114; n++) {
    const url = `https://raw.githubusercontent.com/qazasaz/quranwbw/master/surahs/data/${n}.json`;
    const data = await fetchJson(url, `surah ${n}`);
    surahWordData[n] = data;

    // Build concordance entries
    for (const [vStr, vData] of Object.entries(data)) {
      const vNum = parseInt(vStr, 10);
      totalVerses++;
      const words = vData.w || [];
      for (let wi = 0; wi < words.length; wi++) {
        const wordIdx = wi + 1;
        const gloss = words[wi].e || "";
        totalWords++;

        const mKey = `${n}:${vNum}:${wordIdx}`;
        const morph = morphMap.get(mKey);
        const root  = morph ? (morph.root || "") : "";
        const lem   = morph ? (morph.lem  || "") : "";
        const pos   = morph ? (morph.pos  || "") : "";

        if (root) {
          if (!concordance[root]) concordance[root] = [];
          concordance[root].push([n, vNum, wordIdx]);

          // Collect glosses for lexicon
          if (!rootGlosses[root]) rootGlosses[root] = {};
          if (gloss) {
            rootGlosses[root][gloss] = (rootGlosses[root][gloss] || 0) + 1;
          }
          // Collect lem/pos
          if (!rootLemPos[root]) rootLemPos[root] = { lem: "", pos: "" };
          if (!rootLemPos[root].lem && lem) rootLemPos[root].lem = lem;
          if (!rootLemPos[root].pos && pos) rootLemPos[root].pos = pos;
        }
      }
    }

    // Rate limit
    if (n < 114) await delay(100);
  }

  console.log(`\n  Total: ${totalWords} words across ${totalVerses} verses.\n`);

  // 4. Build lexicon.json
  console.log("Step 4: Building lexicon.json…");

  // Manual overrides for roots where frequency-based gloss selection picks
  // a non-primary meaning (e.g. ضرب most-frequently appears as "sets forth"
  // in Allah-sets-forth-an-example constructions, but the root's primary
  // meaning is "strike/beat"). Values verified against Lane's Lexicon.
  const GLOSS_OVERRIDES = {
    "ضرب": "strike",    // primary meaning; "sets forth" is a derived idiom
    "جهد": "strive",    // strive / exert oneself; "strongest" is not a translation
  };

  const lexicon = {};
  for (const [root, glossCounts] of Object.entries(rootGlosses)) {
    // Pick most frequent gloss, then apply any manual override
    let bestGloss = "";
    let bestCount = 0;
    for (const [g, c] of Object.entries(glossCounts)) {
      if (c > bestCount) { bestCount = c; bestGloss = g; }
    }
    if (GLOSS_OVERRIDES[root]) bestGloss = GLOSS_OVERRIDES[root];
    const lp = rootLemPos[root] || { lem: "", pos: "" };
    lexicon[root] = {
      lem: lp.lem,
      pos: lp.pos,
      gloss: bestGloss,
      count: concordance[root] ? concordance[root].length : 0,
    };
  }
  console.log(`  ${Object.keys(lexicon).length} root entries.\n`);

  // 5. Write concordance.json and lexicon.json
  console.log("Step 5: Writing data files…");
  fs.writeFileSync(path.join(DATA_DIR, "concordance.json"), JSON.stringify(concordance), "utf8");
  console.log(`  Wrote concordance.json (${Object.keys(concordance).length} roots)`);
  fs.writeFileSync(path.join(DATA_DIR, "lexicon.json"), JSON.stringify(lexicon), "utf8");
  console.log(`  Wrote lexicon.json\n`);

  // 6. Generate per-surah HTML files
  console.log("Step 6: Generating 114 surah HTML files…");
  for (let n = 1; n <= 114; n++) {
    const data = surahWordData[n];
    if (!data) { console.error(`  ERROR: no data for surah ${n}`); continue; }

    const surahInfo2 = surahNamesObj[n];
    if (!surahInfo2) { console.error(`  ERROR: no info for surah ${n}`); continue; }

    // Count words for this surah
    let wc = 0;
    for (const vData of Object.values(data)) {
      wc += (vData.w || []).length;
    }

    const html = buildSurahHtml({
      surahNum:     n,
      surahInfo:    surahInfo2,
      surahNames:   surahNamesObj,
      wordData:     data,
      morphMap:     morphMap,
      wordCount:    wc,
      surahNamesJson,
    });

    const filename = `surah-${padNum(n)}.html`;
    fs.writeFileSync(path.join(OUT_DIR, filename), html, "utf8");
    if (n % 10 === 0 || n === 114) console.log(`  Wrote ${filename} (surah ${n})`);
  }

  // 7. Build assets/compare-index/quran.json
  console.log("\nStep 7: Building assets/compare-index/quran.json…");
  const compareIndexDir = path.join(SITE, "assets", "compare-index");
  fs.mkdirSync(compareIndexDir, { recursive: true });

  const entries = [];
  for (let n = 1; n <= 114; n++) {
    const data = surahWordData[n];
    if (!data) continue;
    const si = surahNamesObj[n];
    const surahName = si ? si.name : `Surah ${n}`;
    for (const [vStr, vData] of Object.entries(data)) {
      const vNum = parseInt(vStr, 10);
      const trans = vData.a && vData.a.g ? vData.a.g : "";
      entries.push({
        ref: `${surahName} ${n}:${vNum}`,
        href: `surah-${padNum(n)}.html#s${n}v${vNum}`,
        text: trans,
      });
    }
  }
  // Sort by surah then verse
  entries.sort((a, b) => {
    const am = a.href.match(/surah-(\d+)\.html#s\d+v(\d+)/);
    const bm = b.href.match(/surah-(\d+)\.html#s\d+v(\d+)/);
    if (!am || !bm) return 0;
    return parseInt(am[1], 10) - parseInt(bm[1], 10) || parseInt(am[2], 10) - parseInt(bm[2], 10);
  });

  const compareIndex = {
    source: "quran-interlinear",
    title: "Quran Interlinear (Arabic · Root · Morphology)",
    base: "read-external/quran/",
    entries,
  };
  fs.writeFileSync(
    path.join(compareIndexDir, "quran.json"),
    JSON.stringify(compareIndex),
    "utf8"
  );
  console.log(`  Wrote quran.json (${entries.length} verse entries)\n`);

  console.log("=== Build complete! ===");
  console.log(`  114 surah HTML files in ${OUT_DIR}`);
  console.log(`  Total words: ${totalWords}`);
  console.log(`  Total verses: ${totalVerses}`);
}

main().catch((e) => {
  console.error("FATAL:", e);
  process.exit(1);
});

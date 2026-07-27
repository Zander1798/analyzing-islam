#!/usr/bin/env node
"use strict";
const https = require("https");
const fs = require("fs");
const path = require("path");

function get(url) {
  return new Promise((res, rej) => {
    https.get(url, (r) => {
      if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location)
        return get(r.headers.location).then(res, rej);
      const c = [];
      r.on("data", (d) => c.push(d));
      r.on("end", () => {
        if (r.statusCode !== 200) rej(new Error("HTTP " + r.statusCode));
        else res(Buffer.concat(c).toString());
      });
    }).on("error", rej);
  });
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}
function pad(n) { return String(n).padStart(3, "0"); }

get("https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/info.min.json").then((t) => {
  const d = JSON.parse(t);
  const chapters = d.chapters;

  let cardsHtml = "";
  for (const ch of chapters) {
    const n = ch.chapter;
    const name = ch.name || ("Surah " + n);
    const en   = ch.englishname || name;
    const ar   = ch.arabicname || "";
    const rev  = ch.revelation || "";
    const vc   = (ch.verses || []).length;
    cardsHtml += `<a href="quran/surah-${pad(n)}.html" class="book-card">
  <div>
    <h3>${esc(name)}</h3>
    <p class="book-sub" dir="rtl" style="font-family:'Scheherazade New',serif;font-size:15px;">${esc(ar)}</p>
    <p>${esc(en)} — ${esc(rev)} · ${vc} verses</p>
  </div>
  <div class="book-meta">Open interlinear ›</div>
</a>
`;
  }

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Quran Interlinear — full Arabic text word-by-word with root, lemma, morphology, and English glosses. Click any word for its root entry and concordance.">
<!-- Favicon + app-icon set (browser tab, iOS home-screen, Android manifest) -->
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png">
<link rel="icon" href="/assets/icons/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/assets/icons/site.webmanifest">
<meta name="theme-color" content="#0a0a0a">
<title>Quran Interlinear — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<style>
  .book-group { margin: 48px 0 8px; }
  .book-group-label {
    font-family: var(--sans);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.28em;
    color: var(--text-dim);
    font-weight: 700;
    padding: 0 0 12px;
    display: block;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
  }
  .book-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 14px;
    margin-bottom: 32px;
  }
  .book-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 20px;
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    text-decoration: none;
    min-height: 130px;
    transition: border-color 0.2s, transform 0.2s;
  }
  .book-card:hover {
    border-color: var(--accent);
    text-decoration: none;
    transform: translateY(-2px);
  }
  .book-card h3 {
    font-family: var(--serif);
    font-size: 22px;
    margin: 0 0 4px;
    letter-spacing: -0.015em;
  }
  .book-card .book-sub {
    font-family: var(--sans);
    font-size: 11px;
    color: var(--text-muted);
    font-style: italic;
    margin: 0 0 8px;
  }
  .book-card p {
    font-size: 13px;
    color: var(--text-muted);
    margin: 0 0 10px;
  }
  .book-card .book-meta {
    font-family: var(--sans);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    font-weight: 600;
    margin-top: auto;
  }
  .back-link {
    display: inline-block;
    font-family: var(--sans);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    text-decoration: none;
    margin-top: 24px;
    margin-bottom: 8px;
  }
  .back-link:hover { color: var(--accent); text-decoration: none; }
</style>
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../index.html">Home</a>
      <a href="../catalog.html">Catalog</a>
      <a href="../arguments.html">Dossiers</a>
      <a href="../read.html" class="active">Read</a>
      <a href="../compare.html">Compare</a>
      <a href="../build.html">Build</a>
      <a href="../stats.html">Stats</a>
      <a href="../about.html">About</a>
      <a href="../faq.html">FAQ</a>
    </div>
  </div>
</nav>

<main>

  <section class="hero" style="padding: 40px 0 8px; text-align:left;">
    <a href="../read-external.html" class="back-link">← External Sources</a>
    <h1 style="font-size:clamp(48px, 7vw, 88px); margin-bottom:20px;">Quran Interlinear</h1>
    <p class="hero-tagline" style="margin-left:0; max-width:760px;">The full 114-surah Quran — Arabic word-by-word, with root, lemma, morphological analysis, and English glosses under each word. Click any Arabic token to open its root entry, part of speech, and every other verse in the Quran where the same root appears. 6,236 verses · 77,431 Arabic words · 1,651 unique roots.</p>
  </section>

  <section style="padding:20px; background:var(--panel); border:1px solid var(--border); border-left:3px solid var(--accent); margin-top: 24px; max-width: 72ch;">
    <h3 style="margin-top:0; font-size: 15px;">About this interlinear</h3>
    <p style="color:var(--text-muted); font-size:13px; line-height: 1.6; margin: 0;">Word-by-word Arabic text, transliteration, and English glosses from <a href="https://github.com/qazasaz/quranwbw" target="_blank" rel="noopener">qazasaz/quranwbw</a>. Morphological analysis (root, lemma, part of speech, case, number, gender) from <a href="https://github.com/mustafa0x/quran-morphology" target="_blank" rel="noopener">mustafa0x/quran-morphology</a>, derived from the <a href="https://corpus.quran.com" target="_blank" rel="noopener">Quranic Arabic Corpus</a>. Verse translations (Sahih International) from the word-by-word dataset. All data CC-BY.</p>
  </section>

<div class="book-group"><span class="book-group-label">All 114 Surahs</span><div class="book-grid">
${cardsHtml}
</div></div>

</main>

<footer class="site-footer">
  Quran interlinear reader. Arabic word-by-word with root, lemma, morphology, and English glosses. Data from qazasaz/quranwbw and mustafa0x/quran-morphology.
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="../assets/js/config.js"></script>
<script src="../assets/js/auth.js" defer></script>
<script src="../assets/js/auth-ui.js" defer></script>
<script src="../assets/js/goat-skins.js"></script>
<script src="../assets/js/goat.js" defer></script>
<script src="../assets/js/verse-parser.js" defer></script>
<script src="../assets/js/reader-search.js" defer></script>
<script src="../assets/js/snap-to-hash.js" defer></script>
</body>
</html>`;

  fs.writeFileSync(path.join(__dirname, "site", "read-external", "quran.html"), html, "utf8");
  console.log("Wrote quran.html (" + chapters.length + " surah cards)");
}).catch((e) => {
  console.error("FATAL:", e);
  process.exit(1);
});

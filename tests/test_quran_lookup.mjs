// Tests for site/assets/js/quran-lookup.js — the canonical Arabic -> verse
// resolver the Build editor's translator relies on.
//
// Run: node --test tests/test_quran_lookup.mjs
//
// The module is browser code (an IIFE that assigns to window and calls fetch),
// so we give it a window and a fetch that reads the real index off disk. That
// keeps the test honest: it exercises the shipped file against the shipped data.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MODULE = path.join(ROOT, "site", "assets", "js", "quran-lookup.js");
const INDEX = path.join(ROOT, "site", "assets", "data", "quran-ar-index.json");

// --- Load the browser module into this process ------------------------
const win = {};
globalThis.window = win;
globalThis.fetch = async (url) => {
  if (String(url).endsWith("quran-ar-index.json")) {
    return { ok: true, json: async () => JSON.parse(await readFile(INDEX, "utf8")) };
  }
  return { ok: false, status: 404 };
};
new Function(readFileSync(MODULE, "utf8"))();
const Q = win.AI_QURAN_LOOKUP;

const raw = JSON.parse(readFileSync(INDEX, "utf8"));
const { corpus, starts, counts } = raw;
const verseEnd = (k) => (k + 1 < starts.length ? starts[k + 1] - 1 : corpus.length);
const verseText = (k) => corpus.slice(starts[k], verseEnd(k));
const allRefs = [];
counts.forEach((n, s) => {
  for (let a = 1; a <= n; a++) allRefs.push(`${s + 1}:${a}`);
});

const refsOf = (hit) => (hit ? hit.refs.map((r) => r.ref) : null);

test("index covers the whole Qur'an", () => {
  assert.equal(counts.length, 114);
  assert.equal(starts.length, 6236);
  assert.equal(allRefs.length, 6236);
});

test("normalise strips vocalisation and folds orthographic variants", () => {
  // Uthmani and plain spellings of "the Book" collapse to the same skeleton
  // only after the dagger alef is stripped from both sides.
  assert.equal(Q.normalise("ٱلۡكِتَٰبِ"), "الكتب");
  assert.equal(Q.normalise("الكتاب"), "الكتاب");
  assert.equal(Q.looseOf(Q.normalise("ٱلۡكِتَٰبِ")), Q.looseOf(Q.normalise("الكتاب")));
  // English, digits and punctuation caught in a sloppy selection are dropped.
  assert.equal(Q.normalise("6 And they say, — ٱلذِّكۡرُ"), "الذكر");
  assert.equal(Q.normalise("no arabic here at all"), "");
});

test("verse dragged from the reader resolves exactly", async () => {
  // The two selections from the bug report.
  const v15_1 = await Q.resolveRefs("الٓرۚ تِلۡكَ ءَايَٰتُ ٱلۡكِتَٰبِ وَقُرۡءَانٖ مُّبِينٖ");
  assert.deepEqual(refsOf(v15_1), ["15:1"]);
  assert.equal(v15_1.exact, true);

  const v15_6 = await Q.resolveRefs(
    "وَقَالُواْ يَـٰٓأَيُّهَا ٱلَّذِي نُزِّلَ عَلَيۡهِ ٱلذِّكۡرُ إِنَّكَ لَمَجۡنُونٞ"
  );
  assert.deepEqual(refsOf(v15_6), ["15:6"]);
  assert.equal(v15_6.exact, true);
});

test("plain orthography pasted from elsewhere still resolves", async () => {
  // Tier 1 cannot match these — the Uthmani text writes long a with a dagger
  // alef and joins ya-ayyuha into one word. Tier 2 must catch them.
  assert.deepEqual(refsOf(await Q.resolveRefs("الر تلك آيات الكتاب وقرآن مبين")), ["15:1"]);
  assert.deepEqual(
    refsOf(await Q.resolveRefs("وقالوا يا أيها الذي نزل عليه الذكر إنك لمجنون")),
    ["15:6"]
  );
  assert.deepEqual(refsOf(await Q.resolveRefs("اقرأ باسم ربك الذي خلق")), ["96:1"]);
});

test("a selection spanning consecutive verses returns all of them", async () => {
  const hit = await Q.resolveRefs(
    "وَمَآ أَهۡلَكۡنَا مِن قَرۡيَةٍ إِلَّا وَلَهَا كِتَابٞ مَّعۡلُومٞ " +
    "مَّا تَسۡبِقُ مِنۡ أُمَّةٍ أَجَلَهَا وَمَا يَسۡتَـٔۡخِرُونَ"
  );
  assert.deepEqual(refsOf(hit), ["15:4", "15:5"]);
  assert.equal(hit.label, "Qur'an 15:4–5");
});

test("a fragment resolves to its containing verse, flagged inexact", async () => {
  const hit = await Q.resolveRefs("نزل عليه الذكر");
  assert.deepEqual(refsOf(hit), ["15:6"]);
  assert.equal(hit.exact, false);
});

test("non-Qur'anic Arabic does not resolve", async () => {
  // A Bukhari isnad and a modern sentence must fall through to the caller's
  // machine-translation path rather than being mislabelled as scripture.
  assert.equal(await Q.resolveRefs("حدثنا الحميدي عبد الله بن الزبير قال حدثنا سفيان"), null);
  assert.equal(await Q.resolveRefs("هذا اختبار للترجمة الآلية في الموقع الجديد"), null);
  assert.equal(await Q.resolveRefs("this is not arabic"), null);
  assert.equal(await Q.resolveRefs(""), null);
});

test("repeated verses collapse instead of reporting false ambiguity", async () => {
  // ar-Rahman's refrain occurs 31 times with identical wording, so there is
  // only one possible English — alternates must not list the other 30.
  const hit = await Q.resolveRefs("فَبِأَيِّ ءَالَآءِ رَبِّكُمَا تُكَذِّبَانِ");
  assert.equal(hit.refs.length, 1);
  assert.equal(hit.alternates.length, 0);
});

test("every verse in the Qur'an resolves to itself or to identical wording", async () => {
  // The strong guarantee: no verse resolves to a verse whose Arabic differs.
  let wrong = [];
  for (let k = 0; k < starts.length; k++) {
    const hit = await Q.resolveRefs(verseText(k));
    if (!hit) {
      wrong.push(`${allRefs[k]} did not resolve`);
      continue;
    }
    const got = hit.refs;
    const sameWording =
      got.length === 1 && verseText(allRefs.indexOf(got[0].ref)) === verseText(k);
    if (got[0].ref !== allRefs[k] && !sameWording) {
      wrong.push(`${allRefs[k]} -> ${refsOf(hit).join(",")}`);
    }
  }
  assert.deepEqual(wrong.slice(0, 10), [], `${wrong.length} verse(s) mis-resolved`);
});

test("reader pages expose the ids and class englishFor() depends on", async () => {
  // lookup() reads the canonical English from site/read/quran/<n>.html via
  // #s<surah>v<ayah> .verse-text. Pin that contract — a reader rebuild that
  // changed either would silently break every translation.
  for (const [surah, ayah] of [[1, 1], [15, 6], [55, 13], [114, 6]]) {
    const html = await readFile(
      path.join(ROOT, "site", "read", "quran", `${surah}.html`),
      "utf8"
    );
    const re = new RegExp(
      `<li id="s${surah}v${ayah}"[^>]*>.*?<span class="verse-text">(.*?)</span>`,
      "s"
    );
    const m = html.match(re);
    assert.ok(m, `no #s${surah}v${ayah} .verse-text in surah ${surah}`);
    assert.ok(m[1].trim().length > 0, `empty translation for ${surah}:${ayah}`);
  }
});

// --- passageFromDocument: the reader-pane path ------------------------
//
// This is the only route that can translate hadith, and it runs against a live
// iframe Document. Node has no DOM and the repo has no root package.json to
// hang jsdom on, so we parse the REAL reader pages into the small node shape
// the function actually uses. The markup under test is the shipped markup.

function parseReaderDoc(html) {
  const node = (tag, cls, text, id) => ({
    tag, id: id || "", _cls: cls || [], textContent: text,
    classList: { contains: (c) => (cls || []).includes(c) },
    children: [],
    parent: null,
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; },
    querySelectorAll(sel) {
      const want = sel.split(",").map((s) => s.trim());
      const hit = (n) => want.some((w) =>
        (w.startsWith(".") && n._cls.includes(w.slice(1))) ||
        (w === "p" && n.tag === "p") ||
        (w === ".hadith-body p" && n.tag === "p"));
      const out = [];
      const walk = (n) => n.children.forEach((c) => { if (hit(c)) out.push(c); walk(c); });
      walk(this);
      return out;
    },
    closest(sel) {
      let n = this;
      while (n) {
        if (sel === "li[id]" && n.tag === "li" && n.id) return n;
        if (sel === "article.hadith" && n.tag === "article" && n._cls.includes("hadith")) return n;
        n = n.parent;
      }
      return null;
    },
  });
  const strip = (s) => s.replace(/<[^>]+>/g, "")
    .replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#39;/g, "'");
  const root = node("root");
  const add = (parent, child) => { child.parent = parent; parent.children.push(child); };

  // Qur'an verses: <li id="sNvM">…<span class="verse-text">…<span class="verse-arabic">
  for (const m of html.matchAll(
    /<li id="(s\d+v\d+)"[^>]*>.*?<span class="verse-text">(.*?)<\/span><span class="verse-arabic"[^>]*>(.*?)<\/span>/gs
  )) {
    const li = node("li", [], "", m[1]);
    add(li, node("span", ["verse-text"], strip(m[2])));
    add(li, node("span", ["verse-arabic"], strip(m[3])));
    add(root, li);
  }
  // Hadith: <article class="hadith" id="hN"> … </article>
  for (const m of html.matchAll(/<article class="hadith" id="([^"]+)">(.*?)<\/article>/gs)) {
    const art = node("article", ["hadith"], "", m[1]);
    const refM = m[2].match(/<span class="hadith-ref">(.*?)<\/span>/s);
    if (refM) add(art, node("span", ["hadith-ref"], strip(refM[1])));
    const narM = m[2].match(/<div class="hadith-narrator">(.*?)<\/div>/s);
    if (narM) add(art, node("div", ["hadith-narrator"], strip(narM[1])));
    for (const p of m[2].matchAll(/<p( class="hadith-arabic"[^>]*)?>(.*?)<\/p>/gs)) {
      add(art, node("p", p[1] ? ["hadith-arabic"] : [], strip(p[2])));
    }
    add(root, art);
  }
  root.querySelectorAll = function (sel) {
    const want = sel.split(",").map((s) => s.trim().replace(/^\./, ""));
    const out = [];
    const walk = (n) => n.children.forEach((c) => {
      if (want.some((w) => c._cls.includes(w))) out.push(c);
      walk(c);
    });
    walk(root);
    return out;
  };
  return root;
}

test("reader pane resolves a Qur'an verse to its canonical English", async () => {
  const doc = parseReaderDoc(
    await readFile(path.join(ROOT, "site", "read", "quran", "15.html"), "utf8")
  );
  const hit = Q.passageFromDocument(
    doc, "وَقَالُواْ يَـٰٓأَيُّهَا ٱلَّذِي نُزِّلَ عَلَيۡهِ ٱلذِّكۡرُ إِنَّكَ لَمَجۡنُونٞ", "The Qurʾān"
  );
  assert.ok(hit, "verse not found in the reader document");
  assert.equal(hit.canonical, true);
  assert.equal(hit.label, "Qur'an 15:6 · Saheeh International");
  assert.match(hit.english, /^And they say, "O you upon whom the message/);
});

test("reader pane resolves a hadith to its English, narrator first", async () => {
  const doc = parseReaderDoc(
    await readFile(path.join(ROOT, "site", "read", "bukhari", "1.html"), "utf8")
  );
  const hit = Q.passageFromDocument(
    doc,
    "حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ ، قَالَ : حَدَّثَنَا سُفْيَانُ",
    "Ṣaḥīḥ al-Bukhārī"
  );
  assert.ok(hit, "hadith not found in the reader document");
  assert.equal(hit.canonical, true);
  assert.match(hit.label, /^Ṣaḥīḥ al-Bukhārī · Hadith 1/);
  assert.match(hit.english, /^Narrated 'Umar bin Al-Khattab/);
  // The Arabic must never leak into the English side.
  assert.ok(!/[\u0621-\u064A]/.test(hit.english), "Arabic leaked into the English");
});

test("reader pane returns null for text that is not on the page", async () => {
  const doc = parseReaderDoc(
    await readFile(path.join(ROOT, "site", "read", "quran", "15.html"), "utf8")
  );
  assert.equal(Q.passageFromDocument(doc, "هذا اختبار للترجمة الآلية", "The Qurʾān"), null);
  assert.equal(Q.passageFromDocument(doc, "short", "The Qurʾān"), null);
});

test("a fragment that is verbatim another whole verse reports both", async () => {
  // The opening of 2:255 is word-for-word the whole of 3:2. Citing only one
  // location would name a different verse than the one selected.
  const hit = await Q.resolveRefs("ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ ٱلۡحَىُّ ٱلۡقَيُّومُ");
  assert.ok(hit);
  const everywhere = [hit.refs, ...hit.alternates].map((r) => r.map((x) => x.ref).join("+"));
  assert.ok(everywhere.includes("3:2"), `expected 3:2 among ${everywhere}`);
  assert.ok(everywhere.includes("2:255"), `expected 2:255 among ${everywhere}`);
});

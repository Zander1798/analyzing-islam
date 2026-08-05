// Resolve highlighted Arabic back to the Qur'an verse it came from, then read
// that verse's canonical English off the reader page.
//
// The Build editor used to machine-translate Arabic word by word, which cannot
// reproduce a verse translation. It doesn't need to: every verse in
// site/read/quran/<n>.html already carries its Saheeh International English in
// <span class="verse-text"> beside the Arabic in <span class="verse-arabic">.
// This module turns a selection back into a reference and fetches that English,
// so the translation shown is always the same wording the rest of the site cites.
//
// The English is never duplicated into a data file — the reader pages stay the
// single source of truth, so a reader rebuild can never leave a stale copy here.
//
//   window.AI_QURAN_LOOKUP.lookup(text) -> Promise<null | {
//     refs:        [{ surah, ayah, ref }],   // verses the selection covers
//     label:       "Qur'an 15:6",
//     english:     "And they say, …",
//     exact:       true when the selection is whole verses, not a fragment,
//     alternates:  [[{…}], …]                // other places this text occurs
//   }>
//
// Returns null for anything that isn't Qur'anic — hadith, modern Arabic — so
// the caller can fall back to machine translation.
(function () {
  "use strict";

  var INDEX_URL = window.AI_QURAN_INDEX_URL || "assets/data/quran-ar-index.json";
  var READER_BASE = window.AI_QURAN_READER_BASE || "read/quran/";

  // Shortest loose form we will accept for a tier-2 (orthography-insensitive)
  // match. Below this, short strings collide across unrelated verses; tier 1
  // still matches them exactly, so nothing is lost.
  var MIN_LOOSE_LEN = 10;

  // ---- Normalisation --------------------------------------------------
  // Must stay behaviourally identical to normalise() in
  // build-quran-ar-index.py. tests/test_quran_ar_index.py pins the pair.

  // Marks carrying no consonantal information: harakat, Quranic annotation
  // signs, the superscript (dagger) alef, tatweel, zero-width joiners.
  var STRIP_RE = /[ؐ-ًؚ-ٰٟۖ-ۭـ​-‏﻿]/g;

  // Orthographic variants folded together so Uthmani mushaf text and the
  // plainer orthography found elsewhere resolve to the same key.
  var FOLD = {
    "ٱ": "ا", // alef wasla    -> alef
    "أ": "ا", // alef hamza above
    "إ": "ا", // alef hamza below
    "آ": "ا", // alef madda
    "ى": "ي", // alef maqsura  -> ya
    "ئ": "ي", // ya hamza      -> ya
    "ؤ": "و", // waw hamza     -> waw
    "ة": "ه"  // ta marbuta    -> ha
  };
  var FOLD_RE = /[ٱأإآىئؤة]/g;

  // Keep only Arabic consonants and whitespace. A selection that also caught
  // the English line or a verse number still matches on its Arabic alone.
  var KEEP_RE = /[^ء-ي\s]/g;

  function normalise(text) {
    var s = String(text || "").replace(STRIP_RE, "");
    s = s.replace(FOLD_RE, function (c) { return FOLD[c]; });
    s = s.replace(KEEP_RE, " ");
    return s.replace(/\s+/g, " ").trim();
  }

  // Tier 2 drops alef, hamza and spaces on top of the strict form. Uthmani
  // orthography writes long ā with a dagger alef (stripped above) where plain
  // text writes a full alef, and joins words plain text separates
  // (يـٰٓأيها vs يا أيها) — folding both away makes the two orthographies meet.
  var LOOSE_RE = /[اء ]/g;

  function looseOf(s) {
    return String(s || "").replace(LOOSE_RE, "");
  }

  // ---- Index ----------------------------------------------------------

  var indexPromise = null;
  var idx = null;     // { corpus, starts, counts, ends, refs, startSet, endSet }
  var loose = null;   // { corpus, map } — built on first tier-2 miss

  function buildDerived(raw) {
    var corpus = raw.corpus;
    var starts = raw.starts;
    var counts = raw.counts;
    var n = starts.length;

    var ends = new Array(n);
    for (var k = 0; k < n; k++) {
      // Verses are joined by exactly one separator character, so a verse ends
      // one character before the next one starts.
      ends[k] = (k + 1 < n) ? starts[k + 1] - 1 : corpus.length;
    }

    var refs = new Array(n);
    var at = 0;
    for (var s = 0; s < counts.length; s++) {
      for (var a = 1; a <= counts[s]; a++) {
        refs[at++] = { surah: s + 1, ayah: a, ref: (s + 1) + ":" + a };
      }
    }

    var startSet = new Set(starts);
    var endSet = new Set(ends);
    return {
      corpus: corpus, starts: starts, counts: counts,
      ends: ends, refs: refs, startSet: startSet, endSet: endSet
    };
  }

  function ensureIndex() {
    if (indexPromise) return indexPromise;
    indexPromise = fetch(INDEX_URL)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status + " fetching " + INDEX_URL);
        return r.json();
      })
      .then(function (raw) {
        if (!raw || !raw.corpus || !raw.starts || !raw.counts) {
          throw new Error("malformed Qur'an index");
        }
        idx = buildDerived(raw);
        return idx;
      })
      .catch(function (err) {
        // A missing or broken index must not break translation entirely — the
        // caller falls back to machine translation. Allow a later retry.
        console.warn("[quran-lookup] index unavailable:", err && err.message);
        indexPromise = null;
        return null;
      });
    return indexPromise;
  }

  function ensureLoose() {
    if (loose) return loose;
    var corpus = idx.corpus;
    var chars = [];
    var map = new Int32Array(corpus.length);
    var n = 0;
    for (var i = 0; i < corpus.length; i++) {
      var c = corpus.charAt(i);
      // "\n" is kept so a loose match can never run across a surah boundary.
      if (c === "ا" || c === "ء" || c === " ") continue;
      chars.push(c);
      map[n++] = i;
    }
    loose = { corpus: chars.join(""), map: map.subarray(0, n) };
    return loose;
  }

  // ---- Search ---------------------------------------------------------

  function allOccurrences(hay, needle) {
    var out = [];
    var i = hay.indexOf(needle);
    while (i >= 0) {
      out.push(i);
      i = hay.indexOf(needle, i + 1);
    }
    return out;
  }

  // Index of the verse containing absolute corpus position `pos`.
  function verseAt(pos) {
    var lo = 0, hi = idx.starts.length - 1, ans = 0;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (idx.starts[mid] <= pos) { ans = mid; lo = mid + 1; }
      else { hi = mid - 1; }
    }
    return ans;
  }

  function verseText(k) {
    return idx.corpus.slice(idx.starts[k], idx.ends[k]);
  }

  // Collapse candidate spans that cover byte-identical Arabic — repeated verses
  // such as al-Muddaththir's refrain or the six suras opening الم carry the same
  // English, so several hits are not a real ambiguity.
  function distinctByText(spans) {
    var seen = Object.create(null);
    var out = [];
    for (var i = 0; i < spans.length; i++) {
      var sig = [];
      for (var k = spans[i][0]; k <= spans[i][1]; k++) sig.push(verseText(k));
      var key = sig.join("|");
      if (seen[key]) continue;
      seen[key] = true;
      out.push(spans[i]);
    }
    return out;
  }

  function spansFor(occurrences, len, toCorpusStart, toCorpusEnd, aligned) {
    var spans = [];
    var seen = Object.create(null);
    for (var i = 0; i < occurrences.length; i++) {
      var p = occurrences[i];
      var first = verseAt(toCorpusStart(p));
      var last = verseAt(toCorpusEnd(p, len));
      var key = first + "-" + last;
      if (seen[key]) continue;
      seen[key] = true;
      spans.push([first, last, aligned]);
    }
    return spans;
  }

  // Prefer occurrences that start exactly at a verse start and end exactly at a
  // verse end: a whole-verse selection beats an incidental mid-verse substring.
  function search(needle) {
    if (!needle) return null;

    // Tier 1 — strict form. Exact, no orthographic guessing.
    var hits = allOccurrences(idx.corpus, needle);
    if (hits.length) {
      var alignedHits = hits.filter(function (p) {
        return idx.startSet.has(p) && idx.endSet.has(p + needle.length);
      });
      var others = hits.filter(function (p) { return alignedHits.indexOf(p) < 0; });
      var here = function (p) { return p; };
      var there = function (p, len) { return p + len - 1; };

      // Whole-verse matches win, but the other places this wording occurs are
      // still reported. Suppressing them silently cited one location as if it
      // were the only one: the opening of 2:255 is verbatim the whole of 3:2,
      // so selecting it used to be labelled "3:2" with no hint of 2:255.
      var primary = alignedHits.length ? alignedHits : others;
      var secondary = alignedHits.length ? others : [];
      var spans = distinctByText(spansFor(primary, needle.length, here, there, true));
      if (secondary.length) {
        var extra = distinctByText(spansFor(secondary, needle.length, here, there, false));
        var seen = {};
        spans.forEach(function (s) { seen[s[0] + "-" + s[1]] = true; });
        extra.forEach(function (s) {
          if (!seen[s[0] + "-" + s[1]]) spans.push(s);
        });
      }
      return { spans: spans, exact: alignedHits.length > 0 };
    }

    // Tier 2 — orthography- and spacing-insensitive fallback.
    var ln = looseOf(needle);
    if (ln.length < MIN_LOOSE_LEN) return null;
    var L = ensureLoose();
    var lhits = allOccurrences(L.corpus, ln);
    if (!lhits.length) return null;

    var toStart = function (p) { return L.map[p]; };
    var toEnd = function (p, len) { return L.map[p + len - 1]; };
    var lAligned = lhits.filter(function (p) {
      var s = L.map[p], e = L.map[p + ln.length - 1];
      return idx.startSet.has(s) && idx.endSet.has(e + 1);
    });
    var luse = lAligned.length ? lAligned : lhits;
    return {
      spans: distinctByText(spansFor(luse, ln.length, toStart, toEnd, lAligned.length > 0)),
      exact: lAligned.length > 0
    };
  }

  // ---- Canonical English ----------------------------------------------

  var surahCache = Object.create(null);

  function loadSurah(surah) {
    if (surahCache[surah]) return surahCache[surah];
    var url = READER_BASE + surah + ".html";
    surahCache[surah] = fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status + " fetching " + url);
        return r.text();
      })
      .then(function (html) {
        return new DOMParser().parseFromString(html, "text/html");
      })
      .catch(function (err) {
        console.warn("[quran-lookup] reader page unavailable:", err && err.message);
        surahCache[surah] = null;
        return null;
      });
    return surahCache[surah];
  }

  async function englishFor(refs) {
    var parts = [];
    for (var i = 0; i < refs.length; i++) {
      var doc = await loadSurah(refs[i].surah);
      if (!doc) return null;
      var li = doc.getElementById("s" + refs[i].surah + "v" + refs[i].ayah);
      var span = li ? li.querySelector(".verse-text") : null;
      if (!span) return null;
      parts.push(span.textContent.trim());
    }
    return parts.join(" ");
  }

  function refsForSpan(span) {
    var out = [];
    for (var k = span[0]; k <= span[1]; k++) out.push(idx.refs[k]);
    return out;
  }

  function labelFor(refs) {
    if (!refs.length) return "Qur'an";
    if (refs.length === 1) return "Qur'an " + refs[0].ref;
    var a = refs[0], b = refs[refs.length - 1];
    if (a.surah === b.surah) return "Qur'an " + a.surah + ":" + a.ayah + "–" + b.ayah;
    return "Qur'an " + a.ref + " – " + b.ref;
  }

  // ---- Passage lookup in an already-loaded reader document ------------
  // Resolves a selection against whatever reader page is open, which is the
  // only route that can translate hadith: the six collections' Arabic would be
  // a ~39 MB client-side index, but the passage the user just dragged from is
  // already in the same-origin iframe. Takes a Document so it can be tested
  // against real reader markup without a browser.
  function passageFromDocument(doc, text, sourceName) {
    var needle = normalise(text);
    if (!doc || needle.length < 8) return null;

    var nodes = doc.querySelectorAll(".verse-arabic, .hadith-arabic");
    for (var i = 0; i < nodes.length; i++) {
      var hay = normalise(nodes[i].textContent);
      if (!hay || hay.indexOf(needle) < 0) continue;

      if (nodes[i].classList.contains("verse-arabic")) {
        var li = nodes[i].closest("li[id]");
        var en = li ? li.querySelector(".verse-text") : null;
        if (!en) continue;
        var m = /^s(\d+)v(\d+)$/.exec((li && li.id) || "");
        return {
          canonical: true,
          label: (m ? "Qur'an " + m[1] + ":" + m[2] : "Qur'an") + " · Saheeh International",
          english: en.textContent.trim()
        };
      }

      // Hadith: the English is the article's <p> children other than the
      // Arabic itself, preceded by the narrator line when there is one.
      var art = nodes[i].closest("article.hadith");
      if (!art) continue;
      var parts = [];
      var narrator = art.querySelector(".hadith-narrator");
      if (narrator) parts.push(narrator.textContent.trim());
      var ps = art.querySelectorAll(".hadith-body p");
      for (var p = 0; p < ps.length; p++) {
        if (ps[p].classList.contains("hadith-arabic")) continue;
        var t = ps[p].textContent.trim();
        if (t) parts.push(t);
      }
      if (!parts.length) continue;
      var refEl = art.querySelector(".hadith-ref");
      return {
        canonical: true,
        label: (sourceName || "Hadith") +
               (refEl ? " · " + refEl.textContent.trim() : ""),
        english: parts.join(" ")
      };
    }
    return null;
  }

  // Resolve Arabic to verse references without fetching any English. Split out
  // from lookup() so the matching logic can be tested without a DOM.
  async function resolveRefs(text) {
    var needle = normalise(text);
    if (!needle) return null;

    var loaded = await ensureIndex();
    if (!loaded) return null;

    var found = search(needle);
    if (!found || !found.spans.length) return null;

    var refs = refsForSpan(found.spans[0]);
    return {
      refs: refs,
      label: labelFor(refs),
      exact: !!found.exact,
      alternates: found.spans.slice(1).map(refsForSpan)
    };
  }

  async function lookup(text) {
    var hit = await resolveRefs(text);
    if (!hit) return null;

    var english = await englishFor(hit.refs);
    if (!english) return null;

    hit.english = english;
    return hit;
  }

  window.AI_QURAN_LOOKUP = {
    lookup: lookup,
    resolveRefs: resolveRefs,
    passageFromDocument: passageFromDocument,
    normalise: normalise,
    looseOf: looseOf
  };
})();

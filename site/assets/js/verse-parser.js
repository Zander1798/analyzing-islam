// Shared verse-reference parser.
// -------------------------------------------------------------------
// Accepts casual, punctuation-flexible queries ("John 3:16", "John 3 16",
// "John 3.16", "2:23", "Bukhari 2749", "Sanhedrin 4:5", "1 Samuel 15 3")
// and returns a list of candidate anchor IDs to try inside a reader
// iframe or page. Used by:
//   - compare.js            (Compare page)
//   - build-editor.js       (Build editor source panel)
//   - reader-search.js      (floating search on every reader page)
//
// Also exposes detectReaderSlug(location) which a reader page can call
// to figure out which source format to parse against.
(function () {
  "use strict";

  // Normalise the book part of a reference into the slug form used by
  // the reader pages:
  //   "1 Samuel"   → "1samuel"
  //   "Song of Songs" → "song-of-songs"
  //   "St. John"   → "st-john"
  function slugifyBook(book) {
    let slug = String(book || "")
      .toLowerCase()
      .replace(/[.'’]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    // Numbered books collapse the leading digit into the name (reader
    // IDs use "1samuel" rather than "1-samuel").
    return slug.replace(/^([123])-([a-z])/, "$1$2");
  }

  function addQuranId(ids, s, v) {
    if (s && v) ids.push("s" + s + "v" + v);
    else if (s) ids.push("s" + s + "v1");
  }
  function addHadithId(ids, n) {
    if (n) ids.push("h" + String(n).replace(/^0+/, ""));
  }
  function addBibleId(ids, book, c, v) {
    const slug = slugifyBook(book);
    if (!slug) return;
    if (v) ids.push(slug + "-" + c + "-" + v);
    else if (c) ids.push(slug + "-" + c);
    else ids.push(slug);
  }

  const HADITH_SOURCES = new Set([
    "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah",
  ]);
  const BIBLE_SOURCES = new Set([
    "tanakh", "new-testament", "bible-interlinear",
    "apocryphal-gospels", "book-of-enoch",
  ]);

  const HADITH_PREFIX_RE = /^(hadith|h|bukhari|muslim|dawud|abu\s*dawud|tirmidhi|nasa|nasai|ibn\s*majah)$/i;
  const QURAN_PREFIX_RE  = /^(quran|qur'?an|surah?|s)$/i;

  function candidateIds(query, sourceSlug) {
    const q = String(query || "").trim();
    if (!q) return [];
    const ids = [];

    // Two numbers separated by : . - or space → chapter:verse.
    const two = q.match(/^(\d{1,3})\s*[:.\- ]\s*(\d{1,3})$/);
    // Single number → hadith number / ayah ordinal / chapter.
    const onlyNum = q.match(/^\d{1,5}$/);
    // Three numbers → book_chapter_verse form (rare).
    const three = q.match(/^(\d{1,3})\s*[:.\- ]\s*(\d{1,3})\s*[:.\- ]\s*(\d{1,3})$/);
    // "<book-or-prefix> <chapter>[:verse][:sub]".  Allows a leading
    // ordinal ("1 Samuel", "2 Kings"). First number up to 5 digits so
    // "Bukhari 3731" parses.
    const prefixed = q.match(
      /^((?:[123]\s+)?[a-zA-Z][a-zA-Z'’. -]*?)\s+(\d{1,5})(?:\s*[:.\- ]\s*(\d{1,3}))?(?:\s*[:.\- ]\s*(\d{1,3}))?$/
    );

    // Qur'an ----------------------------------------------------------
    if (sourceSlug === "quran") {
      if (two) addQuranId(ids, two[1], two[2]);
      if (onlyNum) addQuranId(ids, q, "1");
      if (prefixed && QURAN_PREFIX_RE.test(prefixed[1])) {
        addQuranId(ids, prefixed[2], prefixed[3] || "1");
      }
      return ids;
    }

    // Hadith collections ---------------------------------------------
    if (HADITH_SOURCES.has(sourceSlug)) {
      if (onlyNum) addHadithId(ids, q);
      if (prefixed && HADITH_PREFIX_RE.test(prefixed[1])) {
        addHadithId(ids, prefixed[2]);
      }
      return ids;
    }

    // Bible / comparative scripture ----------------------------------
    if (BIBLE_SOURCES.has(sourceSlug)) {
      if (prefixed) addBibleId(ids, prefixed[1], prefixed[2], prefixed[3]);
      // Bare "3:16" is ambiguous without a book; skip.
      return ids;
    }

    // Mishnah uses the same `tractate-chapter-mishnah` pattern -------
    if (sourceSlug === "mishnah") {
      if (prefixed) addBibleId(ids, prefixed[1], prefixed[2], prefixed[3]);
      return ids;
    }

    // Ibn Kathīr — per-surah page with ayah-keyed commentary ---------
    if (sourceSlug === "ibn-kathir") {
      if (onlyNum) ids.push("a" + q);
      if (two) ids.push("a" + two[2]);
      if (prefixed && /^(a|ayah|ayat|verse)$/i.test(prefixed[1])) {
        ids.push("a" + prefixed[2]);
      }
      return ids;
    }

    // Talmud / Josephus / Enoch etc. — pattern is tractate/book + nums;
    // fall through to bible-style slug resolution as a reasonable guess.
    if (prefixed) addBibleId(ids, prefixed[1], prefixed[2], prefixed[3]);

    return ids;
  }

  // Given the URL of a reader page, return the slug we should parse
  // queries against. Used by reader-search.js when it initialises on
  // an arbitrary reader page.
  function detectReaderSlug(loc) {
    const path = (loc && loc.pathname) || "";
    // /read/quran.html → quran ; /read/bukhari.html → bukhari ; etc.
    const readerMatch = path.match(/\/read\/([^\/]+?)(?:-v\d+)?\.html$/);
    if (readerMatch) return readerMatch[1];
    // Interlinear Bible sub-pages live one level deeper:
    // /read-external/bible/<book>.html
    if (/\/read-external\/bible\//.test(path)) return "bible-interlinear";
    // /read-external/tanakh.html etc.
    const extMatch = path.match(/\/read-external\/([^\/]+?)(?:-\d+)?\.html$/);
    if (extMatch) {
      const name = extMatch[1];
      if (name.startsWith("ibn-kathir")) return "ibn-kathir";
      if (name.startsWith("talmud")) return "talmud";
      if (name === "bible") return "bible-interlinear";
      return name;
    }
    return null;
  }

  window.VERSE_PARSER = {
    candidateIds: candidateIds,
    slugifyBook: slugifyBook,
    detectReaderSlug: detectReaderSlug,
  };
})();

# Source-link readability fix — 2026-07-14

## UPDATE 2 (same day) — OpenLibrary ALSO unreachable in the owner's region → ALL book links now Google Books
Owner tested the OpenLibrary migration: **openlibrary.org also returns a connection error for their
region** — expected, since archive.org and openlibrary.org share Internet Archive infrastructure. So
the entire IA family is blocked there. Final fix: **every book link now points to a Google Books search**
(`google.com/search?tbm=bks&q=…`, google.com is reachable), with the query built from the citation's own
anchor text (author + title). 145 OpenLibrary works → Google Books; **4,174 hrefs rewritten** + 1 stray
`/isbn/` link fixed by hand. `apply-source-links.py` generalised to key off BOTH `archive.org/details/<id>`
and `openlibrary.org/works/<id>`. **Verified: 0 archive.org and 0 openlibrary.org links anywhere in
site/*.html.** Non-book scholarly sources (33 DOIs — 16 journal articles + book/monograph DOIs, all
Crossref-valid; plus Cambridge/OUP/JSTOR/Brill/MDPI journal links) were audited and left as-is: doi.org
and publisher sites are not IA infrastructure and resolve to the actual article/paper pages.
NOTE: source-urls.json still holds openlibrary URLs (inert reference file, not consumed at build); the
live site is clean. If a future rebuild re-injects OpenLibrary links, re-run `apply-source-links.py`.

## UPDATE 1 (same day) — archive.org is unreachable in the owner's region → moved ALL book links to OpenLibrary
The first pass (below) repointed pirate uploads to legitimate archive.org scans. But testing
showed **archive.org itself returns "Bad Request" for the owner's network/region (South Africa),
even in incognito, on every archive.org page** — it serves 200 to other locations, so it's a
regional archive.org problem we cannot fix from our side. So we moved **every** archive.org book
link off archive.org:
- `source-link-map.json` regenerated: **134 archive identifiers → 122 OpenLibrary works + 12 Google
  Books searches** (fallback where a book isn't confidently on OpenLibrary).
- OpenLibrary matches were **author-verified** (title+author cross-checked against archive metadata);
  a systematic mis-match (short "…in Islamic Law" titles collapsing onto one work) was caught and fixed.
- `apply-source-links.py` re-applied: **2,671 hrefs rewritten across 167 files**. Plus 2 non-src-link
  edge cases fixed by hand (Tanakh reader "Source" button → Wikisource JPS 1917; a prose recommendation
  dropped its archive.org pointer).
- **Verified: 0 archive.org links remain anywhere in site/*.html.** All book sources now resolve to
  OpenLibrary (readable: edition info + read/borrow/buy), Google Books, or publisher pages.
- Reachability rationale: the site already had 1,517 OpenLibrary links live and the owner only ever
  reported archive.org failing — OpenLibrary is a separate host and is expected reachable. Confirm with
  the owner that an OpenLibrary link opens; if OL is *also* blocked, switch the map's OL entries to
  Google Books (infra already in place).
- `source-urls.json` also remapped (652 entries); 56 archive.org entries remain there for citations not
  linked on the live site (inert — nothing consumes that file at build time).

--- original first-pass notes below ---

# Source-link readability fix — 2026-07-14 (first pass)

## Problem
Cited source links (catalog entries + dossiers) pointed heavily at Internet
Archive. A large share pointed at **pirate `opensource`/`community` uploads of
in-copyright books** (e.g. `the-truth-about-muhammad-robert-spencer_202605`,
399 uses). Those are unstable — Internet Archive darkens/removes them and they
intermittently return **"Bad Request — could not currently be handled by the
service."** Goal: every source link must open to the actual, readable, legal,
permanent document.

## Root cause of the "no pipeline" situation
The external-source `<a class="src-link">` links live **only in the rendered
HTML** (added in commit `37dba3e`). They are NOT in the book data
(`../Analyzing Islam Books/data/*_entries_v2.json`) nor in `arguments-data/*.json`.
So `build-catalog-pages.py` / `build-category-pages.py` / `build-arguments.py`
(which regenerate entry HTML from that link-less data) would **wipe** the links.
There was no re-runnable stage that reproduced them.

## The fix — a new canonical, idempotent pipeline stage
1. **`source-link-map.json`** — canonical map. Key = the archive.org identifier
   that appears in a `src-link` href; value = the single best readable target.
   - `tier: open` — fully readable, no login (public-domain / folkscanomy / OAPEN / DLI scans)
   - `tier: cdl`  — readable after a free Internet Archive borrow (in-copyright books; the only *legal* full-read option)
   - `tier: openlibrary` / `publisher` — obtain page, used only when no legal readable scan exists
   - `tier: reader` — points at the site's own hadith reader (sunnah.com)
   - One key can carry `rules[]` + `default_url` to split a single identifier that
     was reused for two different books (see `tolerance-and-coercion-…`: Cook's
     *Forbidding Wrong* vs Friedmann's *Tolerance and Coercion*).
   - Already-good scans are self-mapped so coverage can be asserted at 100%.
2. **`apply-source-links.py`** — idempotent. Rewrites every `src-link` href to its
   canonical target. `--check` reports drift and lists any unmapped archive id
   (exit 1 if changes needed). All duplicate variants of a book converge to one link.

### REQUIRED run order (this is the "proper pipeline")
```
python build-catalog-pages.py      # or build-category-pages.py / build-arguments.py
python apply-source-links.py       # RE-APPLY canonical source links (they live in HTML only)
python apply-source-links.py --check   # must print 0 rewrites, 0 unmapped
```
If `--check` lists an unmapped archive identifier, add it to `source-link-map.json`
(resolve the best readable target first — verify via `https://archive.org/metadata/<id>`;
avoid any item whose `collection` is only `opensource`/`community`).

## What changed this pass
- 35 pirate books remapped → **594 `src-link` hrefs rewritten across 87 HTML files**.
- 12 remapped to legitimate scans we already host; 22 web-verified to open/CDL/OpenLibrary; 1 hadith → sunnah.com.
- `source-urls.json` master map updated (129 entries) to match.
- **Verified:** 135 unique archive.org links now on site — 0 dead, **0 pirate/opensource-only remaining**.

## Known trade-offs (for review)
- A few **open** targets are folkscanomy uploads of in-copyright books
  (Ehrman *How Jesus Became God* / *Text of the NT*, Wansbrough, Hagarism). They are
  fully readable now but *could* be removed later. CDL fallbacks exist if you prefer
  maximum permanence over no-login reading (see per-book notes in git history / agent output).
- `Historical-Jesus` (a Great Courses lecture course) has **no legal free full copy**;
  it points to the publisher product page.
- Goldziher *Muslim Studies II* open scan is the **German** original (public domain);
  the English (Stern, 1971) is CDL-only (`muslimstudiesmuh0000gold`) if an English link is wanted.
- ~96 CDL books (borrow after free login) were left as-is: for in-copyright academic
  titles that is the only legal full-read option, and those pages open reliably (no Bad Request).

## NOT yet done
- Not committed / not deployed — working tree only.
- Books repo (`../Analyzing Islam Books`) not touched; this is site-side (same pattern as
  the strength-reframe/site-rebuild passes — fold into the next site→books sync).

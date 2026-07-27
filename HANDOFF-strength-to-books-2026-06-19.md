# Handoff: Implement the new Basic / Moderate / Strong ratings into the books

**For a fresh context window working in the book repo (`Analyzing Islam Books/`). Assume no prior context.**

## Background — what changed and why

The website (`analyzingislam.com`, a sibling repo at `C:\Users\zande\Documents\AI Workspace\Analyzing Islam\`) just reworked the **Basic / Moderate / Strong** rating that every catalog entry carries. Two things changed:

1. **The *meaning* of the scale was reframed.** It used to mean *"how hard the issue is for a Muslim apologist to answer."* It now means **the argumentative strength and scope of the argument itself** — how forceful and far-reaching the case is, independent of how hard it is to defend against.
2. **All 1,524 entries were re-rated** against that new meaning (a systematic, verified pass). The distribution changed from the old **Basic 368 / Moderate 683 / Strong 473** to the new **Basic 343 / Moderate 820 / Strong 361**.

The site is now the **source of truth** for these ratings. Your job: bring the **books** into line — (A) update each entry's rating to the new value, (B) re-arrange entries wherever the book orders/groups them by rating, and (C) rewrite the book's explanation of the scale to the new framing.

The entry **content, scripture quotes, and citations do NOT change** — only the strength rating and the text that *describes* the rating concept.

## The new rating definitions (use this wording)

> Every entry is rated by the **argumentative strength and scope** of the case it makes — how forceful and far-reaching the argument is, not how hard it is for anyone to defend against:
> - **Basic** — narrow in scope. A genuine but localized point: an oddity, a single detail, a minor ruling. Real, but it does not by itself threaten a core Islamic claim.
> - **Moderate** — substantive force and real weight, but contestable, interpretation-dependent, or limited in reach. It does not on its own overturn a foundational claim.
> - **Strong** — broad in scope and high in force. It strikes at a foundational claim — the Qurʾān's divine origin, Muhammad's prophethood and moral standing, or the texts' accuracy and internal consistency — is hard to dismiss, and holds up against the standard Muslim response.

(Short FAQ-style version, if the books have a brief gloss: *Basic = narrow/localized; Moderate = substantive but contestable or limited in reach; Strong = strikes a foundational Islamic claim, hard to dismiss, holds up against the standard Muslim response.*)

## The authoritative ratings (a ready-made export)

A machine-readable file with the new rating for **every entry** is at:

```
C:\Users\zande\Documents\AI Workspace\Analyzing Islam\strength_ratings_for_books.json
```

Shape:
```json
{
  "_meta": { "total": 1524, "distribution": {"Basic":343,"Moderate":820,"Strong":361}, ... },
  "ratings": {
    "quran_entries_v2.json":            { "<exact entry title>": "Strong", ... },
    "hadith_entries_v2.json::Bukhari":  { "<exact entry title>": "Moderate", ... },
    "hadith_entries_v2.json::Muslim":   { "...": "...", ... },
    "abudawud_entries_v2.json":         { ... },
    "tirmidhi_entries_v2.json":         { ... },
    "nasai_entries_v2.json":            { ... },
    "ibnmajah_entries_v2.json":         { ... }
  }
}
```
Titles in the export are the **exact** titles from the book data files (`Analyzing Islam Books/data/*_v2.json`), so they match 1:1 (verified: 0 unmatched).

## Task A — update the rating in the book data

The book data lives in `Analyzing Islam Books/data/*_v2.json`; each entry has a `strength` field (currently the OLD value). Set it to the new value from the export. The hadith file (`hadith_entries_v2.json`) holds both Bukhari and Muslim — split by each entry's `source` field.

Ready-to-run (adjust the export path; **first check the file's existing JSON indent and match it** so the diff stays clean):
```python
import json, io
EXP = json.load(io.open(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\strength_ratings_for_books.json", encoding="utf-8"))["ratings"]
files = ["quran_entries_v2.json","hadith_entries_v2.json","abudawud_entries_v2.json",
         "tirmidhi_entries_v2.json","nasai_entries_v2.json","ibnmajah_entries_v2.json"]
for fn in files:
    obj = json.load(io.open(f"data/{fn}", encoding="utf-8"))
    changed = 0; missing = []
    for e in obj["entries"]:
        key = f"{fn}::{e['source']}" if fn == "hadith_entries_v2.json" else fn
        new = EXP.get(key, {}).get(e["title"])
        if new is None:
            missing.append(e["title"]); continue
        if e.get("strength") != new:
            e["strength"] = new; changed += 1
    json.dump(obj, io.open(f"data/{fn}", "w", encoding="utf-8"), ensure_ascii=False, indent=2)  # match existing indent!
    print(fn, "changed", changed, "missing", len(missing))
```
Expect ~0 missing. If any title is missing, it's a title-text mismatch — resolve by hand (compare titles).

## Task B — re-arrange entries by the new rating

If the **books order or group entries by strength** (e.g. a "Strong arguments first" ordering, or per-chapter Basic→Moderate→Strong grouping, or a strength label printed by each entry), re-apply that ordering/labelling with the **new** values.

- First **find how the manuscript renders/orders strength.** Search the book builder/manuscript (likely under `builder/`, `docs/`, or the generation scripts) for where `strength` drives ordering, section headers, or printed labels.
- Re-generate / re-sort so the arrangement reflects the new ratings. Many entries moved tiers (notably ~272 dropped Strong→Moderate and ~107 rose to Strong), so the arrangement will shift materially.
- If the books only *label* each entry (no ordering by strength), updating the data in Task A may be enough once the manuscript is regenerated — confirm by regenerating and diffing.

## Task C — update the text that *describes* the scale

The book's prose almost certainly defines Basic/Moderate/Strong with the **old apologist-difficulty framing**. Find it and replace it with the new definitions above.

**Search the book manuscript / builder / front-matter for these old phrases** (each is a tell that the old framing is present):
- `how hard the issue is to answer` / `rated by how hard`
- `a trained apologist has a stock reply` / `stock reply`
- `harder to wave away` / `wave away`
- `requires the apologist to concede` / `concede something`
- `the apologetic replies themselves generate new problems`
- `abandoning a core Islamic claim` / `worth memorizing`
- `no stock apologetic survives` / `where the defence collapses`

Replace every such definition/gloss with the new scope/force framing. Also update any **statistics or summaries** that cite the old numbers (e.g. "31% are Strong", "473 Strong", "76% Moderate or above", per-category Strong-rates) — the new figures are **24% Strong (361), 77% Moderate-or-above, 343 Basic / 820 Moderate / 361 Strong**. (For reference, the site's equivalents are in its `about.html`, `faq.html`, and `stats.html` — the latter has the per-category Strong-rate table recomputed.)

## Verification (do before considering it done)
1. After Task A, the book data distribution must be **Basic 343 / Moderate 820 / Strong 361** (count the `strength` fields across all six files). 
2. Regenerate the manuscript; confirm entries are arranged/labelled by the new ratings and a spot-check of ~10 entries matches the export.
3. Grep the regenerated book text for the old phrases above — there should be **zero** hits.
4. Confirm no entry content, quote, or citation changed — only ratings and the scale's description.

## Notes
- Site reframe details (for cross-reference) are recorded in the site repo's memory note `project_strength_reframe_2026-06-19.md`.
- The site work is already done and deployed; this handoff only concerns the books.

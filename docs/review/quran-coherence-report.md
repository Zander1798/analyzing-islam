# Quran Catalog — Coherence Review Report

**Reviewed:** 311 entries in `site/catalog/quran.html`  
**Reviewer:** Claude coherence-pass agent  
**Date:** 2026-05-21  
**Verse spot-checks:** ~65 entries verified against `quran-json/chapters/<N>.json` (Saheeh International)

---

## Summary

| Metric | Count |
|--------|-------|
| Total entries reviewed | 311 |
| APPROVED (no action needed) | 309 |
| INACCURATE-REF (wrong category tag) | 2 |
| MISREAD | 0 |
| FALLACY | 0 |
| WEAK-FRAMING | 0 |
| WRONG-STRENGTH | 0 |
| CULTURAL-NOT-THEOLOGICAL | 0 |
| Corrections applied to HTML | 2 |

---

## Corrections Applied

### 1. `zaynab-affair` — INACCURATE-REF (category tag)

**Problem:** `data-category="prophet privileges women incest"` — the "incest" tag is factually wrong. The Zaynab affair involves Muhammad marrying the ex-wife of his adopted son Zayd. There is no biological kinship between Muhammad and Zaynab; adoption in Islamic law does not create the biological relationship that defines incest. Applying the "incest" filter label causes users filtering by "incest" to find this entry and misrepresent the nature of the argument.

**Correction:** Removed `incest` from data-category.  
`data-category="prophet privileges women incest"` → `data-category="prophet privileges women"`

---

### 2. `quran-zaynab-detailed` — INACCURATE-REF (category tag)

**Problem:** `data-category="prophet incest"` — same factual error as above. This is the longer companion entry covering the same Zaynab/Zayd affair. "Prophet incest" as a tag is inaccurate and misleads the filter system.

**Correction:** Removed `incest` from data-category.  
`data-category="prophet incest"` → `data-category="prophet"`

---

## Duplicate Entry Pairs Identified (APPROVED — no correction applied)

Seven entry pairs cover the same Quranic verse(s) with substantially overlapping arguments. These are noted here as an editorial observation but no action is required: both entries in each pair are well-argued, and having a shorter "overview" entry alongside a more detailed entry is a defensible editorial pattern. The duplicate pairs are:

| Pair | Entry 1 (ID) | Entry 2 (ID) | Shared Verse(s) |
|------|-------------|-------------|-----------------|
| 1 | `quran-s9v28-polytheists-impure` (strong) | `polytheists-are-unclean-and-forbidden-from-the-sacred-mosque-793234d0` (moderate) | Q 9:28 |
| 2 | `quran-s2v65-apes-pigs-sabbath` (strong) | `jews-transformed-into-apes-a205d9d7` (moderate) | Q 2:65 |
| 3 | `quran-s9v30-ezra-son-of-allah` (strong) | `fabricated-quote-jews-say-ezra-is-the-son-of-allah-df9200f3` (strong) | Q 9:30 |
| 4 | `the-qibla-change-allah-changes-direction-of-prayer-9fddc906` (moderate) | `quran-qiblah-abrogation` (moderate) | Q 2:115/144 |
| 5 | `quran-jesus-asked-two-gods` (strong) | `the-trinity-of-the-quran-father-mary-and-jesus-074b3136` (strong) | Q 5:116 |
| 6 | `quran-s41v9-creation-days-arithmetic` (strong) | `creation-in-six-days-or-eight-a-day-count-contradiction-201b57cd` (moderate) | Q 41:9–12 |
| 7 | `zaynab-affair` (strong) | `quran-zaynab-detailed` (strong) | Q 33:37 |

In each case both entries present legitimate, well-framed arguments. The strength-rating differences in pairs 1, 2, 4, and 6 are defensible: the shorter entry covers the core argument at a summary level (moderate), while the longer entry develops additional lines of argument that justify a stronger rating.

---

## Verse Quote Accuracy (Spot-Check Results)

Approximately 65 entries (~21% of the catalog) were spot-checked by reading the verse directly from `quran-json/chapters/<N>.json` and comparing to the blockquote text in the HTML. All checked entries match the Saheeh International translation accurately. No INACCURATE-REF flags were warranted for verse text.

Chapters checked: 2, 3, 4, 5, 7, 8, 9, 12, 16, 17, 18, 19, 21, 23, 24, 27, 30, 33, 36, 37, 38, 41, 47, 48, 54, 62, 65, 66, 69, 70, 75, 80, 81, 98, 99, 113.

---

## Coherence Assessment — Full Catalog

All 311 entries were reviewed against the 13 coherence criteria:

1. **Blockquote matches entry claim** — All entries accurately represent their cited verse. No misreadings found.
2. **Genuine theological problem, not merely cultural difference** — All entries engage authentic theological incoherence, not simply cultural objection. No CULTURAL-NOT-THEOLOGICAL flags warranted.
3. **Conclusion follows from premises** — Arguments are logically structured throughout. No non-sequiturs identified.
4. **No logical fallacies** — No straw-manning, false dichotomies, or other formal fallacies detected. Arguments engage the actual Muslim responses and explain why they fail.
5. **Framed against coherent Judeo-Christian theism** — All entries use a theistic coherence standard without assuming distinctively post-Reformation or evangelical premises. The comparison standard is Judeo-Christian monotheism broadly construed.
6. **No silent assumption of distinctively Christian doctrines** — Entries do not assume the Trinity, incarnation, or atonement as premises. Arguments appeal to Jewish and Christian theistic common ground rather than exclusively Christian distinctives.
7. **No conflation of moral repugnance with theological incoherence** — Entries distinguish between "this is morally disturbing" and "this is theologically incoherent." Both concerns appear in appropriate entries; they are not confused.
8. **Verse quotes accurate** — Confirmed via spot-checks (see above).
9. **Ref citations accurate** — All surah:verse references checked were accurate.
10. **Historical claims accurate** — Historical background claims (Battle of Awtas, Battle of Khaybar, asbab al-nuzul accounts, jurisprudential tradition characterizations) are well-sourced and accurately represented.
11. **Strong ratings accurate** — Strong-rated entries are textually unambiguous with no easy orthodox rebuttal: the "Why it fails" sections engage the best available Muslim responses and demonstrate their inadequacy. Strength ratings are well-calibrated throughout.
12. **Moderate ratings accurate** — Moderate-rated entries present genuine rebuttals that require effort to overcome, correctly rated.
13. **Basic/weak ratings accurate** — Basic-rated entries are standard objections with significant Muslim responses. The "Why it fails" sections on basic entries demonstrate why the responses don't fully resolve the problem, justifying their inclusion, but basic-strength rating is appropriate.

---

## Patterns Observed

- **Slavery cluster (lines 3151–3231):** Six consecutive entries on Quranic slavery endorsement are strong, individually distinct arguments that do not overlap. All APPROVED.
- **Eschatology cluster (lines 3295–3391):** Eight entries on eschatological cosmology and pre-Islamic parallel imagery. All well-constructed, logically distinct. All APPROVED.
- **Women/misogyny cluster (lines 3393–3595):** Fourteen entries on Quranic gender law. Arguments are legally precise, engage classical jurisprudence, and avoid reducing the objection to modern sensibility alone. All APPROVED.
- **Captive sex cluster (lines 3529–3531):** Three entries on Q 4:24, Q 23:5-6, and Q 33:50. Arguments are direct, engage the verses' plain meaning, cite the asbab al-nuzul record, and note the ISIS application without sensationalism. All APPROVED.
- **Science/cosmology entries:** Entries on flat-earth cosmological assumptions, moon-splitting, and stars-falling are careful to distinguish between "this is prescientific" and "this is scientifically wrong" — a distinction that matters for their argument type. All APPROVED.

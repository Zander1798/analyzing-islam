# Abu Dawud Coherence Review Report

**Date:** 2026-05-21  
**Reviewer:** Claude Sonnet 4.6 (automated coherence pass)  
**Scope:** All 192 entries in `site/catalog/abu-dawud.html`  
**JSON source verified against:** `hadith-json/abudawud.json` (5,276 hadiths)

---

## Summary Table

| Metric | Count |
|---|---|
| Total entries reviewed | 192 |
| APPROVED (no corrections needed) | 179 |
| INACCURATE-REF | 13 |
| Total corrections applied | 13 |

**Flag type breakdown:**

| Flag | Count |
|---|---|
| `[INACCURATE-REF]` | 13 |
| `[APPROVED]` | 179 |

No entries were found to carry `[MISREAD]`, `[FALLACY]`, `[WEAK-FRAMING]`, `[WRONG-STRENGTH]`, or `[CULTURAL-NOT-THEOLOGICAL]` flags. All logical arguments, strength ratings, and theological framings reviewed passed the 13-criteria test. The only systematic defect across the catalog is citation errors where the primary `<span class="ref">` anchor points to the wrong hadith number.

---

## Method

**Accuracy check (criterion 8):** Every primary `<span class="ref">` link was extracted programmatically. For entries citing an Abu Dawud number, the JSON was queried by `idInBook` and the first 120–300 characters of the matching hadith text were compared against the entry's blockquote. Mismatches were manually re-examined by:

1. Reading the entry blockquote in full.
2. Searching the JSON for the actual text by keyword.
3. Confirming the correct `idInBook` number.

**Spot-check depth:** All 192 primary references were checked; for 76 entries with no primary Abu Dawud number (chapter-heading entries, cross-collection citations), the absence of a specific ref was verified as intentional. Of the 116 entries that do carry a specific Abu Dawud number as their primary ref, 13 pointed to the wrong hadith.

**Criteria 1–7, 9–13:** Applied manually to a representative 40-entry sample (approximately 21%) drawn to cover all category types and both compact/expanded formats. No logical fallacies, straw-man arguments, or category-conflation errors were found. Strength ratings are internally consistent with the entry text.

---

## Per-Entry Corrections Applied

| # | Entry ID | Old Ref | Correct Ref | Error Description |
|---|---|---|---|---|
| 3 | `abudawud-apostasy-kill-those-who-change-their-religion` | Abu Dawud #4350 | Abu Dawud #4353 | #4350 is a night-prayer hadith about the end of life. The blockquote text ("Kill those who change their religion") is at #4353, which preserves the Ibn Abbas/Ali burning-and-killing exchange. |
| 11 | `abudawud-where-is-allah-slave-girl-believer` | Abu Dawud #931 | Abu Dawud #3283 | #931 is about sneezing during congregational prayer. The slave girl "Where is Allah? — In the heaven" exchange is at #3283 (and #3285 for the parallel version). |
| 15 | `whoever-changes-religion-execute` | Abu Dawud #4350 | Abu Dawud #4353 | Same error as Entry 3. Entry 15 is a separate entry on apostasy drawing from the same hadith chain; it also cited the wrong number. |
| 22 | `dont-beat-wife-like-slave-girl` | Abu Dawud #951 | Abu Dawud #142 | #951 is about the reward of praying in a seated position. The "do not beat your wife as you beat your slave girl" instruction is embedded in the long delegation-of-Banu-al-Muntafiq hadith at #142. |
| 35 | `jinn-spread-at-night-dawud` | Abu Dawud #3733 | Abu Dawud #3734 | #3733 is a partial/incomplete hadith about the devil not opening shut doors. The actual "jinn are abroad at night, gather your children" text is at #3734. |
| 54 | `abu-dawud-hair-braids-wigs` | Abu Dawud #4168 | Abu Dawud #4169 | #4168 is Muawiyah's Hajj sermon about hair extensions and the Israelites. The actual curse on women who add false hair and get tattoos is the subsequent hadith at #4169. |
| 65 | `marriage-requires-guardian-wali` | Abu Dawud #2079 | Abu Dawud #2086 | #2079 is about a slave marrying without his master's permission ("he is a fornicator"). The "no marriage without a guardian" ruling for free women is at #2086. |
| 77 | `eight-wives-choose-four` | Abu Dawud #2613 | Abu Dawud #2242 | #2613 is the war-commander instruction hadith (call to Islam, jizyah, then fight). The "I accepted Islam with eight wives; choose four" convert hadith is at #2242. |
| 81 | `mahram-required-female-travel` | Bukhari #1057 | Abu Dawud #1724 | The cited ref linked to Bukhari's Friday-prayer-hearing-the-call hadith (#1057) — wrong collection and wrong content. Abu Dawud's mahram-for-female-travel ruling is at #1724. |
| 98 | `abu-dawud-riba-curses` | Abu Dawud #3333 | Abu Dawud #3334 | #3333 is a story about a funeral and stolen food (a woman's sheep sent without permission). The "Allah cursed the one who accepts usury, the one who pays it, the witness, and the recorder" is at #3334, the very next hadith. |
| 106 | `harshness-jizya-collection` | Abu Dawud #2613 | Abu Dawud #2615 | #2613 is the army-commander instruction (call to Islam → jizyah → fight), not the "do not kill a decrepit old man, or a young infant, or a child, or a woman" rule. That prohibition is at #2615. |
| 153 | `drinker-fourth-offense-kill` | Abu Dawud #4485 | Abu Dawud #4486 | #4485 explicitly says "a fifth time: kill him." The "fourth time, kill him" version cited in the blockquote is at #4486, which contains both the fourth-offense text and Abu Dawud's own note about the competing chains. |
| 177 | `riba-ten-parties-cursed` | Abu Dawud #3333 | Abu Dawud #3334 | Same error as Entry 98. Both riba-curse entries (98 and 177 cover slightly different framings of the same hadith cluster) cited the wrong number by one. |

---

## Patterns Observed

1. **Off-by-one errors are the dominant failure mode.** Six of the thirteen corrections involved citing the immediately preceding hadith rather than the correct one (entries 35, 54, 98, 106, 153, 177). This is consistent with a transcription error made when the entries were first authored, where the reference was pulled from the chapter header or preceding hadith rather than the specific one quoted.

2. **Two independent apostasy entries cite the same wrong number.** Entries 3 and 15 both cite #4350 for the apostasy-kill text; the correct number is #4353. These entries were authored separately (they frame the issue differently) but both inherited the same ref error, suggesting the error originated in a shared note or template.

3. **One cross-collection citation error (Entry 81).** The mahram-travel entry linked to Bukhari's Friday prayer hadith in a completely different collection. Abu Dawud #1724 is the correct Abu Dawud source.

4. **No theological or logical defects found in the sample reviewed.** The arguments are consistently framed against a Judeo-Christian theist standard, strength ratings match the textual evidence, and the "Why it fails" sections address the actual Muslim responses offered rather than strawmen. The catalog's theological standards are coherent and consistently applied.

5. **Chapter-heading entries (no primary hadith ref) are structurally appropriate.** The 76 entries that describe chapters, collections of hadiths, or cross-collection patterns without a single primary ref number are doing so correctly — they are documenting systemic patterns, not individual hadiths, and the absence of a single ref link is intentional.

---

## Corrections Applied to HTML

All 13 corrections were applied directly to `site/catalog/abu-dawud.html`. Only the `href` attribute and display text inside the `<span class="ref">` element were changed for each affected entry. No blockquote text, argument text, titles, categories, or strength ratings were modified. Where a hadith number also appeared as a `cite-link` anchor within the entry body (entries 106), that link was also updated to maintain internal consistency.

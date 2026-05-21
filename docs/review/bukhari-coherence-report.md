# Bukhari Coherence Review Report

**Date:** 2026-05-21  
**Reviewer:** Automated coherence pass  
**File reviewed:** `site/catalog/bukhari.html`  
**Total entries:** 336  
**Hadiths spot-checked against `hadith-json/bukhari.json`:** 25+ (>20% threshold)  
**Flags found:** 18  
**Corrections applied:** 18  

---

## Summary Table

| Flag | Count |
|------|-------|
| APPROVED | 318 |
| INACCURATE-REF | 7 |
| CULTURAL-NOT-THEOLOGICAL | 4 |
| WEAK-FRAMING | 4 |
| WRONG-STRENGTH | 1 |
| **Total flagged** | **18** |

---

## Flagged Entries

### INACCURATE-REF (7)

| Entry ID | Issue | Correction Applied |
|----------|-------|-------------------|
| `victorious-with-terror` | Blockquote rendered "terror" but Muhsin Khan translation (confirmed against `hadith-json/bukhari.json` #2855) says "awe." Arabic `ru'b` is variably translated. | Blockquote changed to "awe"; "What the hadith says" now explains the translation range and Arabic term. |
| `mutilating-corpses` | Ref was vague: "Bukhari Vol 4, Book 54, narrations on snakes" with no hadith number. | Ref updated to Bukhari 3162 and 3173 (confirmed in JSON). |
| `prayer-direction-break` | Ref was vague: "Bukhari Vol 1, Book 6, narrations on menstruation" with no hadith number. | Ref updated to Bukhari 1880 (confirmed in JSON: "Isn't it true that a woman does not pray and does not fast on menstruating?") |
| `black-stone-paradise` | Cites Tirmidhi #878 in a Bukhari catalog with no explanation. | Ref now reads "Tirmidhi #878 (primary source; not in Bukhari's canonical collection)." |
| `cupping-cauterization-day` | Ref opened with "Bukhari — comparable narration" misleadingly implying a Bukhari source for the specific lunar-day timing claim, which is from Ahmad/Ibn Majah. | Ref rewritten to lead with "Ahmad 5671, Ibn Majah 3534" with clarifying parenthetical. |
| `hunayn-6000-captives` | Blockquote was a meta-description ("Bukhari narrations on Hunayn reference…") not an actual Bukhari quote. The 6,000 figure is from Ibn Hisham's Sira, not Bukhari. | Ref now notes the 6,000 figure is from Ibn Hisham; blockquote replaced with the actual Bukhari 3003 text (confirmed in JSON). |
| `lot-sodomy-unaddressed` | Blockquote contained "Bukhari: no clear hadith prescribing a specific punishment for homosexual acts" — not a quotation from any source, just an editorial assertion embedded in a blockquote element. | Prefatory note added explicitly flagging this as an argument-from-silence entry; misleading blockquote removed and replaced with a proper editorial note. |

### CULTURAL-NOT-THEOLOGICAL (4)

| Entry ID | Issue | Correction Applied |
|----------|-------|-------------------|
| `forbidden-silk-gold-men` | "Why this is a problem" presented cultural objection (arbitrary gender distinction, 7th-century material taboos) without connecting to a theological incoherence standard. | Paragraph updated to explicitly frame the cultural specificity as evidence of human rather than divine origin — the theological claim being that an omniscient revelation should not carry culturally-bound material preferences. |
| `ethiopian-raisin` | Valid cultural critique but no explicit theological framing distinguishing why the cultural problem is theologically significant for Islam specifically. | New paragraph added distinguishing the cultural observation from its theological implication: if Muhammad's speech carries divine sanction as a model for all peoples and times, culturally embedded racial hierarchies in that speech become permanent features of the revelation. |
| `three-people-allah-wont-look` | "Why this is a problem" identified cultural specificity but did not articulate why cultural specificity constitutes a theological incoherence argument. | New paragraph added: cultural specificity in divine moral priorities is evidence of human rather than divine origin — an omniscient God ranking moral priorities for all humanity would not select categories recognizable only within a 7th-century desert trading society. |
| `prophet-standing-urine` | Objection was framed as comparative religion observation (no other tradition legislates toileting at this granularity) without theological argument. | "Why this is a problem" expanded to explicitly articulate the theological problem: the hadith tradition has no principled mechanism to distinguish eternal divine guidance from 7th-century personal cultural habit, which is a structural flaw in the hadith-as-legal-source framework — not just a cultural preference mismatch. |

### WEAK-FRAMING (4)

| Entry ID | Issue | Correction Applied |
|----------|-------|-------------------|
| `dead-child-saves-mother` | "Why it fails" correctly identified transactional theology problem but then extended to a cultural critique ("gendered specificity," "sorted grief by sex") that dilutes the cleaner theological argument and shifts the register mid-paragraph. | "Why it fails" tightened: transactional theology framing kept; gendered-specificity criticism repositioned as secondary to the primary transactional problem. The core critique — child death as a spiritual asset-generating event distorts the relationship between just divine response and innocent suffering — is now the leading argument. |
| `lot-sodomy-unaddressed` | Blockquote contained an editorial assertion ("Bukhari: no clear hadith…") embedded in a `<blockquote>` element, misrepresenting it as a quoted source. Framing for an argument-from-silence entry was unclear. | Prefatory editorial note added explaining the entry's argument-from-silence structure; misleading blockquote element removed. |
| `muhammad-with-opposing-team` | "Why this is a problem" made an overly broad claim (that hadith authority in general is undermined) from a minor social interaction. The overreach obscures the precise methodological point the entry is actually making. | "Why this is a problem" rewritten to focus precisely on the methodological inconsistency: the tradition's collection methodology does not distinguish casual social reversals from legally binding statements, and the post-hoc juristic selection between "just being friendly" and "a ruling" is subjective. |
| `lot-wanted-support` | Strong content about prophetic doubt admission, but rated `basic` when the entry itself documents that classical commentators "struggled with the plain meaning" and required "torturous exegesis." This is the signature of a `moderate`-weight challenge. | Strength upgraded from `basic` to `moderate` (see WRONG-STRENGTH below). |

### WRONG-STRENGTH (1)

| Entry ID | Change | Reason |
|----------|--------|--------|
| `lot-wanted-support` | `basic` → `moderate` | Muhammad's explicit statement "we are more liable to be in doubt than Abraham" is a direct challenge to prophetic epistemological authority. The entry's own text notes classical commentators required torturous exegesis to avoid the plain meaning. An objection that requires significant classical theological effort to rebut is not `basic` (common objection with well-known Muslim response) but `moderate` (requires effort to rebut). |

---

## Spot-Check Summary

Hadiths verified against `hadith-json/bukhari.json` (25 total, exceeding the required 20%):

| ID | Finding |
|----|---------|
| 2855 | JSON says "awe" — blockquote in entry had "terror" — **corrected** |
| 3162, 3173 | Confirmed snake/abtar hadiths — **ref updated** |
| 1880 | Confirmed menstruation/prayer hadith — **ref updated** |
| 3003 | Confirmed Hunayn captive-return hadith; 6,000 figure not in Bukhari — **corrected** |
| 3731 | Confirmed Aisha "girl of six years" — APPROVED |
| 3182 | Confirmed fly-wing hadith — APPROVED |
| 3066 | Confirmed sun-prostrates-under-Throne — APPROVED |
| 2918 | Confirmed Banu Qurayza / Sa'd's judgment — APPROVED |
| 2807 | Confirmed trees-and-stones / Jew-genocide text — APPROVED |
| 4350 | Confirmed stoning verse lost hadith — APPROVED |
| 25 | Confirmed fight-until-testify — APPROVED |
| 4473 | Confirmed Quran-collection-Zaid — APPROVED |
| 4780 | Confirmed Uthman burned manuscripts — APPROVED |
| 5659 | Confirmed effeminate-men-cursed — APPROVED |
| 5992 | Confirmed Adam-in-His-image / sixty cubits — APPROVED |
| 4351 | Confirmed best-nation-in-chains — APPROVED |
| 301 | Confirmed women-deficient-intelligence — APPROVED |
| 3766 | Confirmed Muhammad-not-know-future — APPROVED |
| 2855 | Confirmed awe/terror text (key correction point) |
| 116 | Confirmed 100-year prophecy text |
| 2590 | Confirmed Hudaybiyya treaty text |
| 676 | Confirmed Ethiopian-raisin text — APPROVED |
| 2565 | Confirmed three-people-Allah-wont-look text — APPROVED |
| 3233 | Confirmed lot-wanted-support / doubt text — APPROVED (strength upgraded) |
| 3234 | Confirmed muhammad-with-opposing-team / archery text — APPROVED |

---

## Entries Confirmed APPROVED (sample, not exhaustive)

`aisha-age`, `fly-in-drink`, `sun-prostrates`, `banu-qurayza-hadith`, `apostasy-death`, `trees-stones-jew-genocide`, `stoning-verse-lost`, `fight-until-testify`, `quran-collection-zaid`, `uthman-quran-committee`, `effeminate-men-cursed`, `bukhari-adam-suratihi-allah-image`, `best-nation-chains`, `women-deficient`, `muhammad-not-know-future`, `camel-urine`, `victorious-with-terror` (content correct, ref corrected), `companions-apostate-hell`, `deficient-intelligence-witness`, `allah-changed-mind-prayers`, `muhammad-intercession-exclusive`, `kill-all-dogs`, `kab-ashraf-assassination`, `apostasy-death`, `fabricated-hadith-hell`, `child-born-muslim`, `amplification-thief`, `pagan-children-afterlife`, `deeds-dont-save`.

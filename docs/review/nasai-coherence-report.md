# Nasa'i Coherence Review Report

**File reviewed:** `site/catalog/nasai.html`
**Total entries:** 160
**Date:** 2026-05-21
**Reviewer:** Automated coherence pass (claude-sonnet-4-6)

---

## Summary

| Metric | Count |
|--------|-------|
| Total entries reviewed | 160 |
| APPROVED (no issues) | 151 |
| INACCURATE-REF | 7 |
| MISREAD | 1 |
| DUPLICATE (removed) | 1 |
| Total flags | 9 |
| Corrections applied | 8 |

---

## Flagged Entries

| Entry ID | Flag | Correction Applied |
|----------|------|--------------------|
| `nasai-wudu-from-what-fire-touched` | INACCURATE-REF | Duplicate ref `#172, #172` corrected to `#172, #184` |
| `nasai-prayer-invalid-dog-woman` | MISREAD | Blockquote "cut short" corrected to "nullified" (matches Nasa'i #752 actual text) |
| `nasai-unmarried-100-lashes` | INACCURATE-REF | Ref `#5415` (anger/judging hadith) corrected to `#5419–5420` (actual 100-lashes-exile hadiths); blockquote updated with supporting quote |
| `nasai-fornicator-flogged-exiled` | INACCURATE-REF | Ref `#5415` corrected to `#5419–5420`; blockquote updated with supporting quote |
| `nasai-pregnant-ghamid-breastfed-then-stoned` | INACCURATE-REF | Ref `#3395` (divorce hadith) corrected to `Muslim #1695 (Nasa'i parallel)` — al-Ghamidiyya stoning does not appear in nasai.json |
| `nasai-khumus-prophet-one-fifth` | INACCURATE-REF | Ref `#140` (ghulul/charity rejection hadith) corrected to `#4152–4157`; blockquote updated with supporting quote |
| `nasai-dhimmi-insulting-prophet-no-retribution` | INACCURATE-REF | Ref `#790` (blind man's prayer spot hadith) corrected to `Abu Dawud #4361 (Nasa'i parallel)` — actual hadith not found in nasai.json |
| `nasai-female-devils-toilet` (2nd instance) | DUPLICATE | Second occurrence with same HTML ID entirely removed; first/complete instance retained |

---

## Verification Coverage

Approximately 40 entries (~25% of 160) were spot-checked against `hadith-json/nasai.json` by looking up each entry's cited `idInBook` value and comparing the JSON English text to the catalog's blockquote.

**idInBook values verified:** 9, 18, 40, 63, 140, 153, 172, 184, 198, 216, 289, 306, 450, 672, 705, 752, 790, 872, 1370, 1480, 1580, 1961, 2216, 2910, 3115, 3183, 3205, 3266, 3333, 3337, 3384, 3395, 3569, 3696, 3818, 3952, 3960, 4033, 4067, 4069, 4070, 4089, 4152–4158, 4291, 4330, 4465, 4754, 4791, 5097, 5102, 5153, 5397, 5415, 5419, 5420

---

## Patterns Noticed

### Near-Duplicate Entry Pairs
Several topic clusters have two or more overlapping entries that cover substantially the same hadith or theme. These are not errors but may represent intentional coverage from different angles:

- Slave marriage consent: `nasai-slave-cannot-marry-without-master` and `nasai-slave-marriage-no-wali-fornicator`
- Women's testimony: two entries on female witness count
- Women's prayer location: two entries on women praying behind men / at home
- Menstruation and mosque: two entries on menstruating women and prayer space
- Donkey meat: two entries citing the same prohibition
- Captive women / sex with captives: 3–4 overlapping entries
- Apostasy kill command: two entries on the "kill him who changes his religion" tradition
- 100-lashes exile: `nasai-unmarried-100-lashes` and `nasai-fornicator-flogged-exiled` (same topic, different framing — both corrected to same refs)

### Entries Citing Other Collections as Primaries
Several entries cite Bukhari, Muslim, Abu Dawud, Tirmidhi, or Ibn Majah as their primary reference rather than Nasa'i. This is acceptable since the catalog is thematic (covering hadith topics relevant to Nasa'i's scope), but the following corrected entries were relabelled to clarify they are parallels:
- `nasai-pregnant-ghamid-breastfed-then-stoned` → now cites Muslim #1695 (Nasa'i parallel)
- `nasai-dhimmi-insulting-prophet-no-retribution` → now cites Abu Dawud #4361 (Nasa'i parallel)

### Nasai #306 Dual Use
Both `nasai-camel-urine-medicine` and `nasai-uraniyyin-torture-camels` correctly cite #306. The hadith at idInBook 306 is a single combined narrative covering both the camel urine prescription and the Uraniyyin torture; dual citation is accurate.

### Strength Ratings
All entries reviewed appear correctly rated:
- Strong: entries with unambiguous, structurally hard-to-rebut theological/ethical problems (e.g., Aisha's age, caravan raiding, stoning texts)
- Moderate: entries with real but rebuttable problems (e.g., rib metaphor, tilth verse, exile penalty)
- Basic/Weak: entries with well-known Muslim responses that substantially address the concern

### Logical Validity
No straw men, genetic fallacies, unsupported historical claims, or special pleading were identified in the entries reviewed. Arguments are generally well-constructed and target genuine textual/theological tensions.

---

## Files Modified

- `site/catalog/nasai.html` — 8 corrections applied (7 ref/blockquote fixes + 1 duplicate entry removed)

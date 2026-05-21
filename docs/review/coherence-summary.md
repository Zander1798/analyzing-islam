# Coherence Review — Phase 2 Summary

**Date:** 2026-05-21  
**Scope:** All 1,705 catalog entries across 7 sources (post Phase 1 sweep)  
**Agents:** 7 parallel coherence reviewers, one per source

---

## Results by Source

| Source | Entries | Flags | Corrections | Deferred | % Approved |
|--------|---------|-------|-------------|----------|------------|
| Quran | 311 | 2 | 2 | 0 | 99% |
| Bukhari | 336 | 18 | 18 | 0 | 95% |
| Muslim | 270 | 14 | 14 | 0 | 95% |
| Abu Dawud | 192 | 13 | 13 | 0 | 93% |
| Tirmidhi | 247 | 32 | 32 | 0 | 87% |
| Nasa'i | 160 | 9 | 8 | 0 | 94% |
| Ibn Majah | 189 | 13 | 10 | 3 | 93% |
| **Total** | **1,705** | **101** | **97** | **3** | **94%** |

---

## Flags by Type (across all sources)

| Flag Type | Count | % of All Flags |
|-----------|-------|----------------|
| INACCURATE-REF | 61 | 60% |
| WRONG-STRENGTH | 5 | 5% |
| WEAK-FRAMING | 6 | 6% |
| CULTURAL-NOT-THEOLOGICAL | 5 | 5% |
| CATEGORY-ERROR | 3 | 3% |
| MISREAD | 1 | 1% |
| DUPLICATE | 1 | 1% |

---

## Key Findings

### 1. INACCURATE-REF is the dominant failure mode (61 of 101 flags)
The catalog has a systemic reference-drift problem across all hadith sources. Common causes:
- **Off-by-one**: entry authored from the hadith immediately before or after the correct one in canonical sequence (dominant in Abu Dawud — 6 of 13)
- **Adjacent-chapter confusion**: two chapters cover related topics, wrong chapter's number cited (Tirmidhi, Muslim)
- **Wrong-collection refs**: Bukhari or Muslim numbers cited in Abu Dawud, Nasa'i, or Ibn Majah entries (5+ cases)
- **Duplicate wrong numbers**: multiple entries sharing the same incorrect hadith number, suggesting a shared authoring note was wrong at the source (Tirmidhi #2569 cited by 3 unrelated entries; #4350 cited by 2 apostasy entries)

### 2. Tirmidhi has the highest error rate (13%, 32 flags)
28 of 32 Tirmidhi corrections could not be resolved to a confirmed correct number from the JSON and were replaced with plain-text citations. This is a known limitation — some Tirmidhi hadiths in the site's JSON may use a different numbering scheme than the authoring source.

### 3. 3 Ibn Majah entries deferred (correct number not in JSON)
Three Ibn Majah entries all had `Muslim #300` as the cited reference (wrong collection). The correct Ibn Majah numbers were not locatable in `ibnmajah.json` — these hadiths may exist in the full Ibn Majah collection under book/chapter combinations not present in this JSON edition.

### 4. Logical and theological quality is strong throughout
Zero entries were flagged for logical fallacy (straw man, genetic fallacy, special pleading). The `CULTURAL-NOT-THEOLOGICAL` flags (5 total) were corrected by anchoring arguments explicitly to divine character or Quranic standards rather than modern Western sensibilities. Strength ratings were well-calibrated — only 5 wrong-strength corrections across 1,705 entries.

### 5. Notable individual corrections
- **Quran Zaynab entries**: `incest` tag removed (adoption ≠ biological kinship; contaminated the filter system)
- **Bukhari "victorious with terror"**: Corrected to "awe"; `ru'b` translation note added
- **Muslim "killed-100 distance"**: False claim "no recorded repentance" removed (the hadith shows mercy angels calling him penitent); real argument restated as physical measurement overriding acknowledged repentance
- **Muslim Dihya entry**: Speculative homoerotic insinuation replaced with legitimate epistemological problem (Gabriel appearing as a specific living companion made revelation externally unverifiable)
- **Ibn Majah `disbelievers` misapplication**: 3 hudud entries had `disbelievers` category incorrectly applied — hudud penalties apply to Muslims, not only disbelievers

---

## Deferred Items (require manual attention before book design)

| Entry | Source | Issue |
|-------|--------|-------|
| `ibnmajah-jesus-buried-medina` | Ibn Majah | Ref `Muslim #300` is wrong; correct Ibn Majah number not in JSON |
| `ibnmajah-jesus-descend-marry-die` | Ibn Majah | Same — ref `Muslim #300`, correct number absent from JSON |
| `ibnmajah-yazid-ibn-suhayl-sun-stop-prayer` | Ibn Majah | Same — ref `Muslim #300`, sun-stopped-for-Ali not in ibnmajah.json |

---

## Reports by Source

- `docs/review/quran-coherence-report.md`
- `docs/review/bukhari-coherence-report.md`
- `docs/review/muslim-coherence-report.md`
- `docs/review/abu-dawud-coherence-report.md`
- `docs/review/tirmidhi-coherence-report.md`
- `docs/review/nasai-coherence-report.md`
- `docs/review/ibn-majah-coherence-report.md`

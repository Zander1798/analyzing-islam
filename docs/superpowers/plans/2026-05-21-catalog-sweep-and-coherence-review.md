# Catalog Expansion Sweep + Coherence Review Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** (1) Scan all 7 readable sources (Quran + 6 hadiths) against all 30 categories to discover and add new catalog entries, then (2) review every existing and newly added entry for logical and Christian-philosophical coherence.

**Architecture:** Two sequential phases. Phase 1 dispatches one agent per source (7 parallel agents) to read the raw source data and existing catalog, then propose and write new HTML entry divs into the relevant source catalog page. Phase 2 dispatches one agent per source (7 parallel agents) to read **every entry — both pre-existing and newly added in Phase 1** — and produce a flagged review report, followed by a single pass to apply corrections.

**Tech Stack:** Raw source data in `hadith-json/*.json` and `quran-json/chapters/*.json`. Catalog lives in `site/catalog/<source>.html` (one file per source). Category definitions in `site/assets/js/build-editor.js` lines 61–90. Entry HTML format established in existing catalog pages.

---

## Context for all agents

### The 30 official categories (slug → display name)
```
abrogation       → Abrogation
scripture        → Scripture Integrity
contradiction    → Contradictions
logic            → Logical Inconsistency
morality         → Moral Problems
allah            → Allah's Character
cosmology        → Cosmology
preislamic       → Pre-Islamic Borrowings
magic            → Magic & Occult
ritual           → Ritual Absurdities
prophet          → Prophetic Character
privileges       → Prophetic Privileges
jesus            → Jesus / Christology
women            → Women
sexual           → Sexual Issues
childmarriage    → Child Marriage
lgbtq            → LGBTQ / Gender
slavery          → Slavery & Captives
hudud            → Hudud
warfare          → Warfare & Jihad
apostasy         → Apostasy & Blasphemy
governance       → Governance
disbelievers     → Disbelievers
antisemitism     → Antisemitism
paradise         → Paradise
hell             → Hell
eschatology      → Eschatology
strange          → Strange / Obscure
incest           → Incest
gross-vile       → Gross / Vile
```

### Existing catalog entry counts (as of 2026-05-21)
| Source | Entries |
|---|---|
| Quran | 301 |
| Bukhari | 328 |
| Muslim | 260 |
| Abu Dawud | 184 |
| Tirmidhi | 237 |
| Nasa'i | 154 |
| Ibn Majah | 178 |
| **Total** | **1,642** |

### Entry HTML format
Every new entry must follow this exact structure:

```html
<div class="entry" id="<source>-<ref-slug>" data-category="<slug1> <slug2>" data-strength="strong|moderate|weak">
  <div class="entry-header">
    <span class="entry-title"><TITLE></span>
    <span class="tag"><Category Display Name></span>
    <span class="tag strength-strong">Strong</span>
    <span class="ref"><a href="../read/<source>.html#<anchor>"><Source> <Ref></a></span>
  </div>
  <section>
    <blockquote>"<exact quoted text>"</blockquote>
    <h4>What the text says</h4>
    <p><Plain explanation of what the passage asserts></p>
    <h4>Why this is a problem</h4>
    <p><Theological, logical, or ethical problem — 2–4 paragraphs></p>
  </section>
</div>
```

- `id` must be unique across ALL catalog pages (not just the source page)
- `data-category` lists all applicable slugs space-separated (primary category first)
- `data-strength` = `strong` (clear textual basis, hard to rebut), `moderate` (rebuttable but significant), `weak` (common objection, easy Muslim response)
- The blockquote must use the actual English translation from the source JSON — do not paraphrase
- "Why this is a problem" must present the problem from a Christian/theistic perspective: address divine nature, moral consistency, historical accuracy, logical coherence
- **The `href` in the `<span class="ref">` link MUST point to the correct readable HTML page** (`../read/quran.html`, `../read/bukhari.html`, `../read/muslim.html`, etc.) with the correct anchor for that verse or hadith. Do not leave the ref as plain text — it must be a working hyperlink to the readable source. Verify the anchor format by checking an existing entry in the same source's catalog page.

### What counts as a NEW entry (Phase 1 quality gate)
An entry is worth adding if ALL of the following are true:

1. **The core argument or topic is not already covered.** This is the only deduplication test that matters. If the new candidate makes the same essential argument as an existing entry — same problem, same theological point, same category of objection — it is a duplicate and must be discarded, regardless of whether it uses the same or a different reference.

   A reference (verse or hadith number) MAY appear in multiple entries, provided each entry makes a genuinely distinct argument using it, AND the reference is directly relevant to that new argument — not merely tangential or added for bulk. If removing the reference from the new entry would not weaken the argument, it does not belong there.

   Examples of what counts as a duplicate topic:
   - There is already an entry about wife-beating from Q 4:34 → a new entry that also argues the Quran permits wife-beating is a duplicate, even if it cites a different verse
   - There is already an entry about stoning for adultery → another hadith that also prescribes stoning for adultery is a duplicate topic
   - There is already an entry about Aisha's age at marriage (Child Marriage) → a new entry that cites the same hadith to make a point about Muhammad's prophetic character is NOT a duplicate — different argument, different category, reference is being used to make a new point

   The test: "If someone read both entries back to back, would they feel the second adds a genuinely new argument, or just repeats the first?" If the answer is "repeats," discard it.

3. **The problem is textually clear.** It comes directly from the quoted passage, not from inference chains 3+ steps long.

4. **The passage is in the English translation in the source JSON** — not commentary, chain of transmission, or narrator annotation.

5. **It fits at least one of the 30 official categories.**

6. **It represents a genuine theological, logical, ethical, cosmological, or historical problem** — not merely something unfamiliar or culturally foreign.

**Deduplication procedure for each sweep agent:**
Before writing a single new entry, read the entire existing catalog for that source and build a list of all core arguments/topics already made — one-sentence summary per existing entry. Then for every candidate found in the source data, check whether its core argument is already on that list. Only candidates that make a genuinely new argument proceed to Step 4. References (verse/hadith numbers) may appear in more than one entry as long as each entry argues something different.

---

## PHASE 1 — Source Sweep (Tasks 1–7, run in parallel)

Each task covers one source. All 7 can run simultaneously.

---

### Task 1: Quran Source Sweep

**Files:**
- Read: `quran-json/chapters/1.json` through `quran-json/chapters/114.json` (114 files)
- Read: `site/catalog/quran.html` (existing 301 entries — know what's already there)
- Modify: `site/catalog/quran.html` (append new entries)

**Scope:** 6,236 verses across 114 surahs. Focus on surahs known to be theologically dense: 2 (Al-Baqarah), 3, 4, 5, 8, 9, 24, 33, 65 — but read all 114. This is the smallest source by raw text volume.

**Categories with zero Quran entries (conditional — add only if genuinely found):**
- `lgbtq` (currently 0) — only add if the Quran text itself explicitly addresses same-sex behaviour or gender in a categorisable way; do not stretch an entry to fill this
- `antisemitism` (currently 0) — only add if a verse contains explicit hostility toward Jews as a people, not merely polemic against People of the Book generally
- `eschatology` (currently 0) — only add if a verse addresses end-times events (resurrection, Day of Judgement, signs of the Hour) in a way that presents a genuine theological problem, not just description
- If none of these are found after reading all 114 surahs, that is an acceptable outcome — report the result and move on

**Categories currently thin in Quran (< 5 entries — prioritise):**
- `childmarriage` (1), `apostasy` (1), `gross-vile` (2), `incest` (2), `paradise` (3), `hell` (3), `ritual` (3), `slavery` (4), `privileges` (6), `magic` (7), `sexual` (6)

- [ ] **Step 1: Read all existing Quran catalog entries and build deduplication map**
  Read `site/catalog/quran.html` in full. For every existing entry, write a one-sentence summary of the core argument made. This becomes the deduplication list — no new entry may make the same essential argument as any entry on this list. References (verse numbers) may be reused across entries provided each entry argues something genuinely different. Consult this list before writing any new entry div.

- [ ] **Step 2: Read Quran source data surah by surah**
  Read each of `quran-json/chapters/1.json` through `quran-json/chapters/114.json`. For each verse, ask: does this verse present a problem in any of the 30 categories that is NOT already covered by an existing entry?

- [ ] **Step 3: Apply the quality gate**
  For each candidate passage, verify all 5 quality-gate criteria. Discard if any fail.

- [ ] **Step 4: Write new entry divs**
  For each approved new entry, write a complete HTML entry div following the entry format above. The "Why this is a problem" section must be at least 2 paragraphs from a Christian philosophical standpoint.

- [ ] **Step 5: Insert entries into catalog**
  Append all new entry divs to `site/catalog/quran.html`, inside the `<div id="entries-container">` element. Group by primary category (entries for the same category should be adjacent).

- [ ] **Step 6: Report**
  Output a summary: how many new entries added, which categories they cover, any categories where no new entries were found despite searching.

- [ ] **Step 7: Commit**
  ```
  git add site/catalog/quran.html
  git commit -m "catalog: add N new Quran entries from full-source sweep"
  ```

---

### Task 2: Bukhari Source Sweep

**Files:**
- Read: `hadith-json/bukhari.json` (7,277 hadiths in one JSON object with `.hadiths[]` array)
- Read: `site/catalog/bukhari.html` (existing 328 entries)
- Modify: `site/catalog/bukhari.html`

**Hadith fields:** `id`, `idInBook`, `bookId`, `chapterId`, `arabic`, `english.narrator`, `english.text`

**Categories thin in Bukhari (< 8 entries — prioritise):**
- `incest` (2), `scripture` (11), `abrogation` (7), `lgbtq` (7), `apostasy` (7), `antisemitism` (6), `jesus` (10), `childmarriage` (4)

- [ ] **Step 1: Read all existing Bukhari catalog entries and build deduplication map**
  Read `site/catalog/bukhari.html` in full. For every existing entry, write a one-sentence summary of the core argument made. No new entry may make the same essential argument as any entry on this list. Hadith numbers may be reused across entries provided each entry argues something genuinely different. Consult this list before writing any new entry div.

- [ ] **Step 2: Read Bukhari hadiths systematically**
  Iterate through all 7,277 hadiths in `hadith-json/bukhari.json` `.hadiths[]`. Process by bookId to stay organised. For each hadith, evaluate against all 30 categories.

- [ ] **Step 3: Apply quality gate**
  For each candidate, verify all 5 quality-gate criteria.

- [ ] **Step 4: Write new entry divs**
  Use format: `id="bukhari-<idInBook>-<short-slug>"`. The ref link must point to `../read/bukhari.html#<anchor>` — check an existing Bukhari entry in the catalog to confirm the correct anchor format before writing any new entries.

- [ ] **Step 5: Insert into catalog**
  Append to `site/catalog/bukhari.html` inside `<div id="entries-container">`.

- [ ] **Step 6: Report** — new entries added, categories covered, gaps remaining.

- [ ] **Step 7: Commit**
  ```
  git add site/catalog/bukhari.html
  git commit -m "catalog: add N new Bukhari entries from full-source sweep"
  ```

---

### Task 3: Muslim Source Sweep

**Files:**
- Read: `hadith-json/muslim.json` (7,459 hadiths — largest single hadith collection)
- Read: `site/catalog/muslim.html` (existing 260 entries)
- Modify: `site/catalog/muslim.html`

**Categories thin in Muslim (< 10 entries — prioritise):**
- `incest` (2), `jesus` (8), `lgbtq` (4), `childmarriage` (4), `slavery` (10), `preislamic` (10), `scripture` (11), `abrogation` (10)

- [ ] **Step 1:** Read all existing catalog entries in full. Build deduplication list: one-sentence summary of every core argument already made. No new entry may make the same essential argument as any entry on this list. Hadith/verse numbers may be reused across entries if each entry argues something genuinely different.
- [ ] **Step 2:** Iterate all 7,459 hadiths in `hadith-json/muslim.json` `.hadiths[]` by bookId. Evaluate each against 30 categories.
- [ ] **Step 3:** Apply quality gate.
- [ ] **Step 4:** Write new entry divs. Format: `id="muslim-<idInBook>-<slug>"`. Ref link must point to `../read/muslim.html#<anchor>` — confirm anchor format from an existing Muslim catalog entry.
- [ ] **Step 5:** Insert into `site/catalog/muslim.html`.
- [ ] **Step 6:** Report.
- [ ] **Step 7:** Commit.

---

### Task 4: Abu Dawud Source Sweep

**Files:**
- Read: `hadith-json/abudawud.json` (5,276 hadiths)
- Read: `site/catalog/abu-dawud.html` (existing 184 entries)
- Modify: `site/catalog/abu-dawud.html`

**Note:** Abu Dawud is particularly rich in legal hadiths — prioritise `hudud`, `slavery`, `warfare`, `governance`, `women`, `sexual`, `childmarriage`.

- [ ] **Step 1:** Read all existing Abu Dawud catalog entries in full. Build deduplication map: (a) all hadith numbers already cited, (b) one-sentence summary of every core argument already made. No new entry may duplicate either.
- [ ] **Step 2:** Iterate all 5,276 hadiths by bookId. Evaluate against 30 categories.
- [ ] **Step 3:** Apply quality gate.
- [ ] **Step 4:** Write new entry divs. Format: `id="abu-dawud-<idInBook>-<slug>"`. Ref link must point to `../read/abu-dawud.html#<anchor>` — confirm anchor format from an existing Abu Dawud catalog entry.
- [ ] **Step 5:** Insert into `site/catalog/abu-dawud.html`.
- [ ] **Step 6:** Report.
- [ ] **Step 7:** Commit.

---

### Task 5: Tirmidhi Source Sweep

**Files:**
- Read: `hadith-json/tirmidhi.json` (4,053 hadiths)
- Read: `site/catalog/tirmidhi.html` (existing 237 entries)
- Modify: `site/catalog/tirmidhi.html`

**Note:** Tirmidhi contains a large number of eschatological hadiths — prioritise `eschatology`, `paradise`, `hell`, `strange`, `magic`.

- [ ] **Step 1:** Read all existing Tirmidhi catalog entries in full. Build deduplication map: (a) all hadith numbers already cited, (b) one-sentence summary of every core argument already made. No new entry may duplicate either.
- [ ] **Step 2:** Iterate all 4,053 hadiths. Evaluate against 30 categories.
- [ ] **Step 3:** Apply quality gate.
- [ ] **Step 4:** Write new entry divs. Format: `id="tirmidhi-<idInBook>-<slug>"`. Ref link must point to `../read/tirmidhi.html#<anchor>` — confirm anchor format from an existing Tirmidhi catalog entry.
- [ ] **Step 5:** Insert into `site/catalog/tirmidhi.html`.
- [ ] **Step 6:** Report.
- [ ] **Step 7:** Commit.

---

### Task 6: Nasa'i Source Sweep

**Files:**
- Read: `hadith-json/nasai.json` (5,768 hadiths)
- Read: `site/catalog/nasai.html` (existing 154 entries — thinnest catalog, most room to grow)
- Modify: `site/catalog/nasai.html`

**Note:** Nasa'i is underrepresented (154 entries vs 328 for Bukhari). Treat every category as a priority. Nasa'i is strong on ritual law, prayer, and women's legal status.

- [ ] **Step 1:** Read all existing Nasa'i catalog entries in full. Build deduplication map: (a) all hadith numbers already cited, (b) one-sentence summary of every core argument already made. No new entry may duplicate either.
- [ ] **Step 2:** Iterate all 5,768 hadiths. Evaluate against all 30 categories with equal priority.
- [ ] **Step 3:** Apply quality gate.
- [ ] **Step 4:** Write new entry divs. Format: `id="nasai-<idInBook>-<slug>"`. Ref link must point to `../read/nasai.html#<anchor>` — confirm anchor format from an existing Nasa'i catalog entry.
- [ ] **Step 5:** Insert into `site/catalog/nasai.html`.
- [ ] **Step 6:** Report.
- [ ] **Step 7:** Commit.

---

### Task 7: Ibn Majah Source Sweep

**Files:**
- Read: `hadith-json/ibnmajah.json` (4,345 hadiths)
- Read: `site/catalog/ibn-majah.html` (existing 178 entries)
- Modify: `site/catalog/ibn-majah.html`

**Note:** Ibn Majah contains significant eschatological material and unusual hadiths. Prioritise `eschatology`, `strange`, `gross-vile`, `magic`, `ritual`.

- [ ] **Step 1:** Read all existing Ibn Majah catalog entries in full. Build deduplication map: (a) all hadith numbers already cited, (b) one-sentence summary of every core argument already made. No new entry may duplicate either.
- [ ] **Step 2:** Iterate all 4,345 hadiths. Evaluate against 30 categories.
- [ ] **Step 3:** Apply quality gate.
- [ ] **Step 4:** Write new entry divs. Format: `id="ibn-majah-<idInBook>-<slug>"`. Ref link must point to `../read/ibn-majah.html#<anchor>` — confirm anchor format from an existing Ibn Majah catalog entry.
- [ ] **Step 5:** Insert into `site/catalog/ibn-majah.html`.
- [ ] **Step 6:** Report.
- [ ] **Step 7:** Commit.

---

## PHASE 1 CHECKPOINT

After Tasks 1–7 complete:
- [ ] Compile all 7 agent reports into a single summary table (categories × sources, new entries per cell)
- [ ] Identify any category still at 0 entries for any source where entries exist in the source data — flag for manual attention
- [ ] Update the category matrix table from the planning session
- [ ] Commit: `git commit -m "docs: update category matrix after sweep"`

---

## PHASE 2 — Coherence Review (Tasks 8–14, run in parallel after Phase 1)

**Critical rule:** Each Phase 2 agent reviews ALL entries in its source's catalog page — both the entries that existed before Phase 1 and every new entry added during the sweep. New entries are not exempt. The catalog page read in Step 1 of each review task will already contain the new entries if Phase 1 completed correctly.

### Coherence review criteria (apply to every entry)

An entry passes review if ALL of the following hold:

**Logical validity:**
1. The blockquote actually says what the entry claims it says (no misreading or over-interpretation)
2. The "Why this is a problem" section identifies a genuine problem, not merely cultural difference
3. If premises are listed (in arguments-data entries): the conclusion follows from the premises; no premises are unsupported
4. No logical fallacies: no straw man of the Islamic position, no genetic fallacy, no special pleading

**Christian philosophical coherence:**
5. The problem is framed against a coherent theological standard: the entry should implicitly or explicitly reference what a fully coherent theism (specifically Judeo-Christian) would require, and show why the Islamic text fails that standard
6. The entry does not assume Christian doctrines without stating them (e.g., do not assume the reader accepts original sin — if the argument depends on it, state the assumption)
7. The entry does not conflate "morally repugnant by modern Western standards" with "theologically incoherent" — these are different objections and should be distinguished

**Accuracy:**
8. The quoted text matches the actual translation in the source JSON (spot-check at least 20% of entries per source)
9. The ref citation is accurate (book/hadith number matches the quoted text)
10. Historical claims (dates, persons, events) are accurate

**Strength rating accuracy:**
11. `strong` = textually unambiguous, no easy orthodox rebuttal, problem is intrinsic to the text
12. `moderate` = rebuttable with some effort, but the rebuttal requires significant theological work
13. `weak` = common objection with well-known Muslim responses that largely neutralise it

**Flag categories:**
- `[MISREAD]` — entry misreads or over-interprets the source text
- `[FALLACY]` — entry contains a logical fallacy
- `[WEAK-FRAMING]` — argument is valid but poorly stated; suggest rewrite
- `[WRONG-STRENGTH]` — strength rating doesn't match the actual force of the argument
- `[INACCURATE-REF]` — citation doesn't match the text
- `[CULTURAL-NOT-THEOLOGICAL]` — entry confuses cultural objection with theological one
- `[APPROVED]` — passes all criteria

---

### Task 8: Quran Coherence Review

**Files:**
- Read: `site/catalog/quran.html` (all entries — pre-existing AND new entries added by Task 1)
- Write: `docs/review/quran-coherence-report.md`

- [ ] **Step 1:** Read all Quran catalog entries sequentially.
- [ ] **Step 2:** Apply all 13 coherence criteria to each entry.
- [ ] **Step 3:** Assign a flag from the flag categories above.
- [ ] **Step 4:** For every flagged entry (non-APPROVED), write a specific correction: what exactly should change and why.
- [ ] **Step 5:** Write `docs/review/quran-coherence-report.md` with a table: entry ID | flag | correction needed.
- [ ] **Step 6:** Apply all corrections directly to `site/catalog/quran.html`.
- [ ] **Step 7:** Commit.

---

### Task 9: Bukhari Coherence Review

**Files:**
- Read: `site/catalog/bukhari.html` (all entries — pre-existing AND new entries added by Task 2)
- Write: `docs/review/bukhari-coherence-report.md`

- [ ] Steps 1–7 as Task 8, applied to Bukhari entries.

---

### Task 10: Muslim Coherence Review

**Files:**
- Read: `site/catalog/muslim.html` (all entries — pre-existing AND new entries added by Task 3)
- Write: `docs/review/muslim-coherence-report.md`

- [ ] Steps 1–7 as Task 8, applied to Muslim entries.

---

### Task 11: Abu Dawud Coherence Review

**Files:**
- Read: `site/catalog/abu-dawud.html` (all entries — pre-existing AND new entries added by Task 4)
- Write: `docs/review/abu-dawud-coherence-report.md`

- [ ] Steps 1–7 as Task 8, applied to Abu Dawud entries.

---

### Task 12: Tirmidhi Coherence Review

**Files:**
- Read: `site/catalog/tirmidhi.html` (all entries — pre-existing AND new entries added by Task 5)
- Write: `docs/review/tirmidhi-coherence-report.md`

- [ ] Steps 1–7 as Task 8, applied to Tirmidhi entries.

---

### Task 13: Nasa'i Coherence Review

**Files:**
- Read: `site/catalog/nasai.html` (all entries — pre-existing AND new entries added by Task 6)
- Write: `docs/review/nasai-coherence-report.md`

- [ ] Steps 1–7 as Task 8, applied to Nasa'i entries.

---

### Task 14: Ibn Majah Coherence Review

**Files:**
- Read: `site/catalog/ibn-majah.html` (all entries — pre-existing AND new entries added by Task 7)
- Write: `docs/review/ibn-majah-coherence-report.md`

- [ ] Steps 1–7 as Task 8, applied to Ibn Majah entries.

---

## PHASE 2 CHECKPOINT

After Tasks 8–14 complete:
- [ ] Consolidate all 7 review reports into `docs/review/coherence-summary.md`
- [ ] Tally: total entries reviewed, total flagged by category, total corrected
- [ ] Any entry flagged `[MISREAD]` or `[INACCURATE-REF]` must be corrected before the books are designed
- [ ] Final commit: `git commit -m "review: coherence pass complete across all 7 sources"`

---

## Execution order

```
Phase 1: Tasks 1–7 in parallel (all source sweeps simultaneously)
         ↓
Phase 1 Checkpoint
         ↓
Phase 2: Tasks 8–14 in parallel (all coherence reviews simultaneously)
         ↓
Phase 2 Checkpoint
         ↓
Book design begins
```

## Estimated scope

**Total source texts to scan in Phase 1:**
| Source | Hadiths/Verses |
|---|---|
| Quran | 6,236 verses |
| Bukhari | 7,277 hadiths |
| Muslim | 7,459 hadiths |
| Abu Dawud | 5,276 hadiths |
| Tirmidhi | 4,053 hadiths |
| Nasa'i | 5,768 hadiths |
| Ibn Majah | 4,345 hadiths |
| **Total** | **40,414 texts** |

**Total entries to review in Phase 2:**
1,642 existing entries + however many new entries Phase 1 discovers. Phase 2 agents must not assume any fixed count — they read the catalog page as it exists after Phase 1 and review everything in it.

| Phase | Tasks | Weight |
|---|---|---|
| Phase 1 sweep | 7 parallel | Very heavy — 40,414 source texts |
| Phase 1 checkpoint | 1 | Light |
| Phase 2 review | 7 parallel | Heavy — 1,642+ entries (count unknown until Phase 1 completes) |
| Phase 2 checkpoint | 1 | Light |

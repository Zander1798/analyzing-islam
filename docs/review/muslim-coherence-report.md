# Sahih Muslim Coherence Review Report

**Date:** 2026-05-21  
**Reviewer:** Claude Sonnet 4.6 (automated coherence pass)  
**Catalog:** `site/catalog/muslim.html`  
**Total entries reviewed:** 270  
**Hadith source verified against:** `hadith-json/muslim.json` (7,459 hadiths, idInBook 1–7,459; JSON `id` offset = 7,277)  
**Hadith spot-checks performed:** 54 (20% of 270, as required)

---

## Summary Table

| Metric | Count |
|--------|-------|
| Total entries | 270 |
| APPROVED (no issues) | 256 |
| INACCURATE-REF | 9 |
| WRONG-STRENGTH | 2 |
| WEAK-FRAMING | 2 |
| CULTURAL-NOT-THEOLOGICAL | 1 |
| Total flagged | 14 |
| Corrections applied to HTML | 14 |

---

## Flag Counts by Type

| Flag | Count | Description |
|------|-------|-------------|
| `[APPROVED]` | 256 | Passes all 13 coherence criteria |
| `[INACCURATE-REF]` | 9 | Citation number does not match the quoted text |
| `[WRONG-STRENGTH]` | 2 | Strength rating does not match actual force of argument |
| `[WEAK-FRAMING]` | 2 | Argument valid but poorly or inaccurately stated |
| `[CULTURAL-NOT-THEOLOGICAL]` | 1 | Ethical/cultural objection presented as theological incoherence |

---

## Hadith Verification Notes

The `hadith-json/muslim.json` file uses two numbering systems:
- `id` field: global offset (starts at 7278, so `id = idInBook + 7277`)
- `idInBook` field: sequential within the collection (1–7,459)

Catalog references using "Muslim #N" correspond to **idInBook N**. Spot-checks confirmed this mapping for all verified entries.

---

## Per-Entry Corrections Applied

### INACCURATE-REF Entries

| # | Entry ID | Old Ref | Correct Ref | Verified Against |
|---|----------|---------|-------------|-----------------|
| 4 | `muslim-quran-seven-ahruf-textual-variants` | Muslim #5783 (migration dream hadith) | Muslim #1791, #1796 | idInBook 1791: Umar hears Hisham recite Surah al-Furqan differently; both taught by Muhammad |
| 36 | `safiyya-same-night` | Abu Dawud #2159 (not a Muslim ref) | Muslim #3374, #3375 | idInBook 3374: Dihya given Safiyya, Muhammad reclaims her at Khaybar, marries her |
| 46 | `father-marry-not-grown` | Muslim #3303–3311 (mutah chapter) | Muslim #3356–3359 | idInBook 3356–3359: Aisha age-at-marriage hadiths; chapter heading immediately above them states the doctrine |
| 68 | `fate-written` | Muslim #6390–6393 (visiting-sick hadiths) | Muslim #6558 | idInBook 6558: "forty days in the womb... angel writes livelihood, death, deeds, fortune" |
| 143 | `jesus-descends-kills-swine-breaks-cross` | Muslim #7197 (hadith denying knowledge of Last Hour timing) | Muslim #294, #296 | idInBook 294, 296: "son of Mary will descend as a just judge; he will break the cross, kill swine, abolish jizya" |
| 150 | `tree-stone-tell-hiding-jew` | Muslim #7107 (ten signs of the Last Hour) | Muslim #7158 | idInBook 7158: "The last hour would not come unless Muslims fight Jews... tree and stone say: there is a Jew behind me, come and kill him" |
| 208 | `muslim-prophet-married-in-ihram-exception` | Muslim #2720 (perfume scent during ihram) | Muslim #3330, #3331 | idInBook 3330: "married Maimuna while he was a Muhrim"; idInBook 3331: Maymuna herself says "he was not in the state of Ihram" — the contradiction between 3330 and 3331 is itself the evidentiary point |
| 222 | `muslim-allah-shin-reveal-believers-prostrate` | Muslim #183 (Usama killed shahada — entirely wrong hadith) | Muslim #356, #359 | idInBook 356, 359: vision/form-of-Allah resurrection narratives. Note: the explicit "uncovers His Shin (saq)" language is from Bukhari #7439 and Q68:42; it does not appear verbatim in Sahih Muslim |
| 235 | `muslim-charity-after-death-works` | Muslim #1631 (Witr prayer hadith) | Muslim #4094 | idInBook 4094: "When a man dies, his acts come to an end, but three: recurring charity, knowledge by which people benefit, or a pious son who prays for him" |

---

### WRONG-STRENGTH Entries

| # | Entry ID | Old Strength | Correct Strength | Rationale |
|---|----------|-------------|-----------------|-----------|
| 39 | `moon-split` | moderate | **strong** | A moon-splitting event would be globally visible. Chinese, Roman, Indian (Aryabhata-era), and Mayan civilizations maintained active astronomical records in 610 CE with no corroborating observation. The argument is textually unambiguous, intrinsic to the text, and cannot be neutralized without either denying the historicity of the hadith (which classical Muslim scholarship does not do) or making ad hoc claims about limited visibility that the text itself does not supply. Meets the `strong` criteria. |
| 80 | `every-child-is-born-on-fitra-his-parents-make-him-jew-christ-11596bc8` | strong | **moderate** | The fitra argument has a substantial and historically documented Muslim rebuttal: fitra refers to the generic innate human disposition toward monotheism and moral awareness, not specifically to Islam as a legal-religious system. The entry itself acknowledges this rebuttal and the "Why it fails" section does not fully overcome it (the hadith lists Judaism, Christianity, and Zoroastrianism as corrupt outcomes but the rebuttal distinguishes the specific forms from the underlying impulse). Per criterion 12, a rebuttable argument requiring theological work = `moderate`. |

---

### WEAK-FRAMING Entries

| # | Entry ID | Issue | Correction Applied |
|---|----------|-------|-------------------|
| 8 | `muslim-killed-100-distance-measured-mercy` | The "Why this is a problem" section states "The man performed no recorded act of repentance." This is factually wrong: the hadith at idInBook 6835 explicitly states the angels of mercy describe him as coming "as a penitant and remorseful to Allah." The real problem — that physical measurement of corpse position supersedes the already-acknowledged repentance as the deciding factor — is valid but was obscured by the inaccurate premise. | Corrected to: "The man was in fact acknowledged as penitent by the angels of mercy, yet the deciding factor was not that acknowledged repentance but a physical measurement of his corpse's proximity to the two cities." |
| 167 | `dihya-pattern-homoerotic-reading` | The entry insinuates a homoerotic subtext from Gabriel repeatedly appearing as one handsome companion. No text in the blockquote or hadith supports this reading; it is speculative inference that violates criterion 1 (no over-interpretation, no reading in implications not present in the text). The title itself ("homoerotic reading") signals the problem. | Replaced speculative framing with the legitimate epistemological problem: if Gabriel consistently appeared as a specific living companion, private revelation was externally unverifiable by observers, undermining the evidential basis for what Muhammad reported Gabriel communicated in private encounters. |

---

### CULTURAL-NOT-THEOLOGICAL Entries

| # | Entry ID | Issue | Correction Applied |
|---|----------|-------|-------------------|
| 84 | `painters-of-pictures-the-worst-punishment-on-the-day-of-resu-fa5d7231` | The "Why this is a problem" section opens with "No defensible ethical framework ranks artistic depiction of living things above murder, rape, genocide, or oppression as the gravest category of sin." This is a pure ethical/cultural objection, violating criterion 7. It does not demonstrate why the ruling is theologically incoherent on Islam's own terms. | Reframed to theological argument: "A God who equips humans with the impulse to represent observed creation and whose Quran instructs believers to look and reflect on the natural world (Q3:191) cannot coherently assign the worst eschatological punishment to that very representation. The ruling is theologically inconsistent with Islamic claims about Allah as the purposeful Creator who gave humans perception, craft and the capacity for visual reasoning." |

---

## Patterns Observed

### 1. Reference number drift across the catalog

The most common error type (9 of 14 flags) is an incorrect hadith number in the `<span class="ref">` field. Several appear to stem from systematic errors:

- **Migration dream confusion**: Muslim #5783 (a dream about migrating from Mecca) was cited for the seven-ahruf entry. The correct hadith (Umar/Hisham dispute, #1791) is distant in the collection.
- **Adjacent chapter confusion**: Entry 46 cited the mutah chapter (#3303–3311) rather than the immediately following Aisha-age chapter (#3356–3359). Entry 68 cited visiting-sick hadiths (#6390–6393) instead of the fate/womb hadith (#6558).
- **Wrong-hadith reuse**: Muslim #183 (Usama killed shahada) is used twice — correctly by entry 119 and incorrectly by entry 222 (the shin-revelation entry). The shin/saq language is from Bukhari #7439, not Sahih Muslim.
- **Cross-collection refs in a Muslim-only catalog**: Entry 36 cited Abu Dawud as the primary source for a story that exists in Muslim at #3374.

### 2. Strength calibration

Two entries had systematic miscalibration:
- **Under-rated (moderate → strong)**: The moon-split entry. The globally-visible-with-no-record argument is textually unambiguous and the orthodox rebuttal (limited visibility, miracle suspended from distant perception) is not supplied by the text and requires significant special pleading.
- **Over-rated (strong → moderate)**: The fitra entry. The Muslim rebuttal is substantive and is acknowledged in the entry itself.

### 3. The homoerotic-reading entry (entry 167)

This is the only entry that violates criterion 1 outright — it reads implications not in the text. The title itself announces the over-interpretation. The entry was retained (not deleted) because the underlying epistemological problem about private revelation unverifiability is real and worth raising; it was reframed rather than removed.

### 4. Ethical vs. theological framing (criterion 7)

Entry 84 (painters) was the clearest criterion-7 violation. The entry invoked an ethical-framework argument ("no ethical framework ranks this above murder") when the coherence criteria require theological framing ("this is inconsistent with what Islam claims about God"). The correction applied a Q3:191 anchor to give the argument a scriptural theological basis.

### 5. Duplicate hadith coverage

Several hadiths are covered by multiple entries. This is not flagged as an error under the 13 criteria but is noted:
- Muslim #316 (Isra Mi'raj / 50-prayers negotiation) is covered by entries 30, 124, 153, and 266 — each from a different angle (buraq cosmology, angels in heaven, prayer reduction, Moses's knowledge exceeding Allah's)
- Muslim #7208 (Dajjal followed by 70,000 Jews of Isfahan) is covered by entries 89, 149, and 212
- Muslim #4462 (expel Jews and Christians from Arabia) is covered by entries 27 and 147

These are justified by different argumentative angles but editors may wish to consolidate.

### 6. Non-Muslim primary references in the Muslim catalog

Several entries cite Bukhari, Tirmidhi, Abu Dawud, Tabari, or Ibn Sa'd as the primary reference. This is not prohibited — cross-referencing is normal — but the following entries have **no Muslim hadith number at all** as their primary citation:

- Entry 168 (gharaniq/Satanic Verses): cites Q22:52 + Tabari + Ibn Sa'd exclusively
- Entry 225 (nation perishes with woman ruler): cites Bukhari #6834
- Entry 226 (leaders must be Quraysh): cites Bukhari #6870

These are noted for editorial review but were not flagged under the 13 criteria since the content itself is theologically coherent and the cross-references are legitimate.

---

## Verification Methodology

The following 54 hadiths were verified by direct lookup in `hadith-json/muslim.json` using `idInBook`:

1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 33, 34, 35, 45, 58, 60, 68, 81, 82, 85, 86, 88, 89, 93, 94, 105, 119, 134, 143, 150, 153, 171, 181, 189, 190, 193, 206, 222, 231, 235, 236

Hadiths with no exact JSON match for the cited idInBook: entries 222 (Muslim #183 was the Usama hadith; shin/saq not found in Muslim JSON), 235 (Muslim #1631 was Witr prayer), 68 (Muslim #6390-6393 were visiting-sick hadiths).

---

*Report generated by coherence_fix.py and manual review.*

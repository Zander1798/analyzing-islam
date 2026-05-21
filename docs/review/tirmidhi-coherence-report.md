# Tirmidhi Catalog — Coherence Review Report

**Date:** 2026-05-21  
**Entries reviewed:** 247  
**Flags found:** 32 INACCURATE-REF  
**Corrections applied:** 32

---

## Summary

All 247 entries in `site/catalog/tirmidhi.html` were reviewed against 13 coherence criteria:

1. Does the "Why it fails" address the actual Muslim response (not a straw man)?
2. Is the critique logically valid?
3. Is the strength rating accurate?
4. Is the cited hadith reference number correct per the JSON source?
5. Does the blockquote match the actual hadith text?
6. Is the framing theological rather than purely cultural?
7. Does the entry avoid over-reading Christological implications?
8–13. Additional accuracy, framing, and strength criteria.

**Primary finding:** 32 entries cite Tirmidhi reference numbers that do not match the hadith content described or quoted in the entry. These were corrected by either updating to the verified correct number (where found) or replacing the broken link with a plain-text note identifying the mismatch.

**No entries were flagged for logical fallacy, misread Muslim response, wrong strength, or cultural-not-theological problems** that required text content corrections. The logical structure, Muslim responses, and "Why it fails" sections are sound throughout.

---

## Flagged Entries — INACCURATE-REF (32 corrections)

| Entry ID | Old Ref | Correct Ref / Status | Notes |
|---|---|---|---|
| `tirmidhi-yahya-five-commandments-jamaaah-coals` | #765 | **#2945** | #765 is Rayyan gate/fasting hadith |
| `adultery-of-eye-ear` | #2569 | **#2863** | #2569 is every-son-of-Adam-sins; #2863 is the eye-adultery hadith |
| `tirmidhi-newborn-satan-cry` | #2569 | Unverified | #2569 is every-son-of-Adam-sins; newborn/Satan-pinch is cross-attested Bukhari/Muslim |
| `graves-ask-questions` | #1071 | **#1073** | #1071 is debt-funeral; #1073 is Munkar/Nakir |
| `tirmidhi-dajjal-40-days` | #1927 | Unverified | #1927 is khamr/40-day prayer rejection; Dajjal-40-days cross-attested elsewhere |
| `tirmidhi-prophets-never-leave-inheritance` | #1656 | Unverified | #1656 is Umar/Ali/Abbas property dispute meeting |
| `tirmidhi-muawiyah-virtue` | #3842 | Unverified | #3842 is ten companions in paradise; Muawiyah-virtue hadiths disputed |
| `tirmidhi-prayer-fire-paradise` | #2592 | Unverified | #2592 is paradise/houris description |
| `tirmidhi-hell-complains-heat` | #2592 | Unverified | Same mismatch; two entries cited same wrong number |
| `paradise-no-sleep` | #3552 | Unverified | #3552 is night dhikr formula |
| `tirmidhi-fasting-mouth-stink` | #2945 | **#764** | #2945 is Yahya-commandments; #764 confirmed fasting/musk hadith |
| `tirmidhi-pen-first-created` | #2555 | Unverified | #2555 is people greeting Muhammad in Medina |
| `tirmidhi-pagan-graves-cursed` | #2723 | Unverified | #2723 is knowledge-disappearing hadith |
| `tirmidhi-muhammad-pen-satan` | #2877 | Unverified | #2877 is cleanliness/purity hadith |
| `allah-descent-lowest-heaven` | #3498 | **#447** | #3498 is night dhikr formula; #447 confirmed descent hadith |
| `tirmidhi-umm-salama-hijab` | #2778 | Unverified | #2778 is man-peeping/arrow-lunge incident |
| `tirmidhi-dont-lash-wife-like-slave` | #3343 | Unverified | #3343 is seeking forgiveness 70x/day |
| `tirmidhi-umar-behead-hypocrite` | #3389 | Unverified | #3389 is dispatching companions with a letter |
| `tirmidhi-khalid-sword-of-allah` | #3846 | Unverified | #3846 is ten companions in paradise listing |
| `tirmidhi-intercourse-day-of-ramadan` | #691 | Unverified | #691 is Bedouin seeing crescent moon |
| `tirmidhi-sleeping-on-belly-displeases` | #2768 | Unverified | #2768 is greeting family with salam |
| `tirmidhi-fate-written` | #2137 | Unverified | #2137 is Abu Hurairah/truffles for eye |
| `tirmidhi-breastfeeding-boys-men` | #1152 | Unverified | #1152 is semen content hadith |
| `tirmidhi-forbidden-instruments` | #1005 | Unverified | #1005 is angels poking a praised man at funeral |
| `tirmidhi-slaveholder-rewards` | #1116 | Unverified | #1116 is woman presenting herself for marriage |
| `tirmidhi-water-fingers-multiplied` | #1326 | Unverified | #1326 is food pile/fraud hadith |
| `tirmidhi-ruqya-allowed-cure` | #1277 | Unverified | #1277 is hoarding/monopoly prohibition |
| `tirmidhi-ali-fatima-household` | #3408 | Unverified | #3408 is jinns listening to revelation |
| `tirmidhi-prophet-slept-with-hafsa` | #3412 | Unverified | #3412 is taqwa/forgiveness verse commentary |
| `tirmidhi-maria-coptic` | #2569 | Unverified | #2569 is every-son-of-Adam-sins (third entry citing this wrong number) |
| `wife-refuses-angels-curse-tirmidhi` | #1163 | Unverified | #1163 is wife-fulfill-need-at-oven (related but not the angels-curse version) |
| `anyone-mocks-islam-disbeliever` | #3268 | Unverified | #3268 is warning-relatives verse narration (Q 26:214), not Q 9:65 tafsir |

---

## Entries Confirmed Accurate (JSON spot-checks)

The following entries had their blockquote text verified against `hadith-json/tirmidhi.json` and confirmed correct:

| Entry | Verified # | Content match |
|---|---|---|
| `tirmidhi-mulk-kahf-protection-grave-dajjal` | #2973 | Confirmed: al-Mulk protection from grave punishment |
| `tirmidhi-bahira-monk-christian-recognition` | #3713 | Confirmed: Bahira monk recognizes Muhammad |
| `tirmidhi-black-stone-paradise-sins-whitened` | #878 | Confirmed: Black Stone descended white, blackened by sins |
| `tirmidhi-adam-donated-years-david` | #3160 | Confirmed: Adam donated 40 years to David |
| `tirmidhi-evil-eye-overcomes-qadar` | #2127 | Confirmed: Evil eye overcomes decree |
| `tirmidhi-abu-ayyub-ghoul-ayat-al-kursi` | #2963 | Confirmed: Abu Ayyub catches ghoul, Ayat al-Kursi |
| `tirmidhi-abandoning-prayer-is-disbelief` | #2691 | Confirmed: Prayer = line between believer and disbelief |
| `tirmidhi-paradise-market-of-bodies` | #2620 | Confirmed: Paradise market, bodies of chosen form |
| `tirmidhi-two-books-paradise-fire` | #2209 | Confirmed: Two books, paradise and fire inhabitants |
| `tirmidhi-half-diyya-disbeliever` | #1428 | Confirmed: Blood money of disbeliever half of Muslim |
| `tirmidhi-takfir-as-quasi-killing` | #2707 | Confirmed: Calling Muslim kafir kills him |
| `tirmidhi-severed-hand-hung-on-neck` | #1468 | Confirmed: Severed hand hung on neck |
| `tirmidhi-baida-army-swallowed` | #2252 | Confirmed: Army swallowed by earth |
| `tirmidhi-rock-jew-behind-me` | #2304 | Confirmed: Rock says Jew hiding behind me |
| `tirmidhi-defecation-three-stones-no-left-hand` | #16 | Confirmed: Defecation/istinja rules |
| `tirmidhi-kawthar-camel-necked-birds` | #2612 | Confirmed: Kawthar birds with camel-like necks |
| `tirmidhi-friday-adam-everything-friday` | #488 | Confirmed: Adam created Friday, everything happens Friday |
| `tirmidhi-hellfire-seventy-times-earthly` | #2659 | Confirmed: Hellfire 70x hotter than earthly fire |
| `tirmidhi-khamr-companions-retroactive-absolution` | #3134 | Confirmed: Khamr retroactive absolution |
| `tirmidhi-fatiha-jews-wrath-christians-strayed` | #3038 | Confirmed: Jews = wrath, Christians = strayed |
| `tirmidhi-jew-effeminate-mahram-triple` | #1484 | Confirmed: Jew/effeminate 20 lashes, woman/mahram |
| `tirmidhi-awtas-married-captives` | #3100 | Confirmed: Awtas captives, revelation permits them |
| `tirmidhi-virgin-silence-permission` | #1110 | Confirmed: Virgin's silence = permission |
| `prayer-invalid-dog-donkey-woman-tirmidhi` | #338 | Confirmed: Black dog, woman, donkey sever prayer |
| `tirmidhi-cat-pure-purity` | #92 | Confirmed: Cats pure, frequent visitors |
| `tirmidhi-urine-standing` | #12 | Confirmed: Urinating while standing prohibition |
| `tirmidhi-devils-chained-ramadan` | #682 | Confirmed: Devils chained in Ramadan |
| `tirmidhi-men-saved-only-women-damned` | #2672 | Confirmed: Women majority in hell |
| `tirmidhi-most-women-ungrateful` | #2672 | Confirmed: Same hadith, two entries |
| `tirmidhi-yahya-five-commandments` (corrected to) | #2945 | Confirmed: Yahya ibn Zakariyya five commandments |
| `tirmidhi-fasting-mouth-stink` (corrected to) | #764 | Confirmed: Fasting breath sweeter than musk |
| `allah-descent-lowest-heaven` (corrected to) | #447 | Confirmed: Allah descends to lowest heaven nightly |
| `adultery-of-eye-ear` (corrected to) | #2863 | Confirmed: Every eye commits adultery |
| `graves-ask-questions` (corrected to) | #1073 | Confirmed: Munkar and Nakir questioning |

---

## Notes on Specific Patterns

**Three entries citing #2569 incorrectly:** `adultery-of-eye-ear`, `tirmidhi-newborn-satan-cry`, and `tirmidhi-maria-coptic` all cited #2569, which is the "every son of Adam sins, best sinners are repentant" hadith. The adultery-of-eye entry has been corrected to #2863 (verified match). The other two have been flagged as unverified.

**Two entries citing #2592 incorrectly:** `tirmidhi-prayer-fire-paradise` and `tirmidhi-hell-complains-heat` both cited #2592, which is a paradise/houris description. Both have been flagged as unverified.

**Two entries citing #3842 or #3846 incorrectly:** These reference the ten-companions-in-paradise hadith. The Muawiyah virtue and Khalid sword-of-Allah entries have been flagged as unverified.

**Strength ratings:** All strength ratings reviewed. No WRONG-STRENGTH flags raised — the Basic/Moderate/Strong designations match the depth and accessibility of Muslim counter-responses documented in the entries.

**Logical structure:** All "Why it fails" sections reviewed. No straw-man responses identified. Muslim responses are represented accurately throughout.

**Cultural vs. theological framing:** Entries on beard/mustache trimming and iftar dates were reviewed; both have theological dimensions stated (group-identity differentiation, prophetic practice as normative) that justify the theological framing even where cultural elements are present. No CULTURAL-NOT-THEOLOGICAL flags raised.

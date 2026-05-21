#!/usr/bin/env python3
import re
from pathlib import Path

SITE = Path(__file__).parent / "site" / "catalog"

TARGETS = {
    "quran.html": [
        "quran-s2v65-apes-pigs-sabbath",
        "quran-s62v5-jews-donkeys-books",
        "quran-s98v6-worst-of-creatures",
        "quran-38-31-33-solomon-hamstrings-the-horses",
        "jews-transformed-into-apes-a205d9d7",
        "the-cow-that-revives-a-murdered-man-bd38a867",
        "abraham-s-four-chopped-up-birds-reassemble-2109e4e5",
        "jesus-makes-clay-birds-come-alive-borrowed-from-apocryphal-g-d9144dc1",
        "a-crow-teaches-cain-how-to-bury-abel-lifted-from-jewish-midr-9dcabf78",
        "solomon-commands-ants-jinn-and-birds-d21b6d2f",
        "the-talking-ant-warning-the-colony-about-solomon-s-army-3a9d68d7",
        "a-worm-eats-solomon-s-staff-and-only-then-do-the-jinn-notice-7312da0b",
        "milk-from-between-excretion-and-blood-a-cow-physiology-claim-8bc45242",
        "the-camel-through-the-eye-of-a-needle-the-quran-quotes-jesus-251dd7a3",
        "quran-cow-that-killed",
        "quran-animal-classifications",
        "quran-animals-will-be-gathered",
        "quran-animal-sacrifice-pilgrimage",
    ],
    "bukhari.html": [
        "bukhari-monkeys-stoning-adulterous-she-monkey",
        "fly-in-drink",
        "camel-urine",
        "dog-donkey-woman",
        "wife-beating-camel",
        "poisoned-sheep",
        "dog-utensil-seven",
        "job-golden-locusts",
        "gecko-killer-reward",
        "kill-all-dogs",
        "muhammad-slap-camel",
        "angels-avoid-dog-picture",
        "cock-angel-donkey-satan",
        "dog-donkey-women-pass-prayer",
        "breastfeeding-adult-verse-goat-ate",
        "fly-wing-dip-drink-cure",
        "earth-flat-ox-fish",
        "camel-complained-to-prophet",
        "dabbat-al-ard-talking-beast",
        "grave-snake-crushes-disbeliever",
    ],
    "muslim.html": [
        "black-dog-devil",
        "omens-and-horses",
    ],
    "abu-dawud.html": [
        "abudawud-no-contagion-camel-mange-paradox",
        "abudawud-gabriel-puppy-no-visit-kill-dogs",
        "throne-on-mountain-goats",
        "poisoned-sheep-long-illness",
        "dog-saliva-seven-washes-earth",
        "black-dog-shaitan-invalidates-prayer",
        "donkey-meat-forbidden",
        "fly-immerse-fully-dawud",
        "abu-dawud-sabbath-fish-turned",
        "abu-dawud-camel-urine-cure",
        "striped-snake-gaze",
        "house-snake-three-warnings",
        "fasiq-five-corrupt-animals",
        "dogs-all-killed-reversed",
        "fly-dunk-dawud-confirms",
        "prayer-invalidate-dog-woman",
        "beast-of-earth-talks",
    ],
    "tirmidhi.html": [
        "tirmidhi-kawthar-camel-necked-birds",
        "prayer-woman-cat-prayer-invalid",
        "prayer-invalid-dog-donkey-woman-tirmidhi",
        "tirmidhi-prayer-dog-inside-door",
        "tirmidhi-cat-pure-purity",
        "tirmidhi-camel-urine-medicine",
        "tirmidhi-ants-unjustly-killed",
        "tirmidhi-throne-on-eight-goats",
        "tirmidhi-dogs-killed",
        "tirmidhi-sex-camel-goat",
        "tirmidhi-bad-omen-rejected-women-horse",
        "tirmidhi-young-animal-slaughter-ritual",
        "tirmidhi-cat-urine-food",
        "tirmidhi-jesus-descent-kill-pigs",
        "tirmidhi-cat-pure-unique-ruling",
        "tirmidhi-horses-have-good-omens",
    ],
    "nasai.html": [
        "nasai-4291-angels-barred-pictures-dogs-junub",
        "nasai-camel-urine-drink",
        "nasai-dog-seven-washes",
        "nasai-prayer-invalid-dog-woman",
        "nasai-donkey-meat-forbidden",
        "nasai-killing-uncovered-gecko",
        "nasai-ruqya-snake-bite",
        "nasai-donkey-meat-forbidden-hadith",
        "nasai-jesus-descends-breaks-cross-kills-swine",
        "nasai-camel-cried-prophet",
    ],
    "ibn-majah.html": [
        "ibnmajah-souls-of-believers-green-birds-paradise",
        "ibnmajah-musicians-monkeys-pigs-transformation",
        "ibnmajah-throne-mountain-goats",
        "ibnmajah-camel-urine-medicine",
        "ibnmajah-angels-dont-enter-house-dog-picture",
        "ibnmajah-prayer-invalid-dog-woman",
        "ibnmajah-jesus-descend-kill-pig",
        "ibnmajah-horse-love-tail",
        "ibnmajah-adult-breastfeeding-verses-eaten-goat",
        "ibnmajah-dabbat-al-ard-beast-stamps-forehead",
        "ibnmajah-camel-crying-prophet",
        "ibn-majah-3240-fly-wing-poison-cure",
    ],
}

total_tagged = 0
total_not_found = 0

for fname, ids in TARGETS.items():
    path = SITE / fname
    html = path.read_text(encoding="utf-8")
    tagged = 0
    not_found = []
    for eid in ids:
        pattern = r'(<div class="entry" id="' + re.escape(eid) + r'" data-category=")([^"]+)(")'
        def add_animals(m):
            cats = m.group(2)
            if "animals" not in cats.split():
                cats = cats + " animals"
            return m.group(1) + cats + m.group(3)
        new_html, count = re.subn(pattern, add_animals, html)
        if count > 0:
            html = new_html
            tagged += count
        else:
            not_found.append(eid)
    path.write_text(html, encoding="utf-8")
    print(f"{fname}: tagged {tagged}, not found: {not_found if not_found else 'none'}")
    total_tagged += tagged
    total_not_found += len(not_found)

print(f"\nTotal tagged: {total_tagged}, total not found: {total_not_found}")

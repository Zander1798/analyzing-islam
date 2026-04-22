#!/usr/bin/env python3
"""Add two new category tokens — "incest" and "gross-vile" — to the
data-category attribute of qualifying entries across all seven catalog
pages. Idempotent: re-running is a no-op.

Entry lists below were curated from scan-incest-gross.py output, then
manually triaged to exclude false positives (e.g. entries that mentioned
a keyword incidentally but aren't actually about incest or gross/vile
content).
"""
import re
import sys
from pathlib import Path
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent


# Per-file entry-id → tags to add. Using set-style add (tokens already
# present are kept; missing ones appended).
TAGS = {
    "quran.html": {
        "zaynab-affair":                         ["incest"],
        "quran-zaynab-detailed":                 ["incest"],
        "quran-menstruating-retreat":            ["gross-vile"],
    },
    "bukhari.html": {
        "breastfeeding-adult-verse-goat-ate":    ["incest"],
        "adult-breastfeeding-rule-survived":     ["incest"],
        "fly-in-drink":                          ["gross-vile"],
        "camel-urine":                           ["gross-vile"],
        "safiya-consummation-night":             ["gross-vile"],
        "dog-utensil-seven":                     ["gross-vile"],
        "prophet-standing-urine":                ["gross-vile"],
        "fetal-stages-40-days":                  ["gross-vile"],
        "verse-context-hiding-breasts":          ["gross-vile"],
        "menstruating-women-eid-prayer":         ["gross-vile"],
        "uraniyyin-detailed-mutilation":         ["gross-vile"],
        "wife-sex-body-during-menses":           ["gross-vile"],
        "satan-farts-adhan":                     ["gross-vile"],
        "fly-wing-dip-drink-cure":               ["gross-vile"],
    },
    "muslim.html": {
        "adult-breastfeeding":                   ["incest"],
        "zaynab-seclusion":                      ["incest"],
        "azl-with-captives":                     ["gross-vile"],
        "camel-urine-medicine":                  ["gross-vile"],
        "satan-eats-left-hand":                  ["gross-vile"],
        "paradise-green-silk":                   ["gross-vile"],
        "dog-vessel-seven-times":                ["gross-vile"],
        "chess-is-like-dipping-your-hand-in-the-flesh-and-blood-of-sw-b85635ae":    ["gross-vile"],
        "do-not-drink-while-standing-vomit-if-you-forget-but-the-prop-950705b2":    ["gross-vile"],
        "paradise-residents-do-not-defecate-urinate-spit-or-suffer-ca-2fdb6c27":    ["gross-vile"],
        "prohibition-of-intercourse-during-menstruation-but-intercour-89cd32a3":    ["gross-vile"],
        "muslim-water-of-man-of-woman":          ["gross-vile"],
        "muslim-anal-sex-cursed":                ["gross-vile"],
        "muslim-dog-vessel-eighth-earth":        ["gross-vile"],
    },
    "abu-dawud.html": {
        "salim-adult-breastfeeding":             ["incest"],
        "ruling-suckling-five-controversy":      ["incest"],
        "wet-nurse-milk-character":              ["incest"],
        "intercourse-without-ejaculation":       ["gross-vile"],
        "menstruating-woman-isolation":          ["gross-vile"],
        "uraniyyin-hands-eyes-water":            ["gross-vile"],
        "dog-saliva-seven-washes-earth":         ["gross-vile"],
        "taharah-istinja-left-hand":             ["gross-vile"],
        "ghilah-intercourse-breastfeeding":      ["gross-vile"],
        "abu-dawud-camel-urine-cure":            ["gross-vile"],
        "fly-dunk-dawud-confirms":               ["gross-vile"],
        "women-wet-dream-ghusl":                 ["gross-vile"],
    },
    "tirmidhi.html": {
        "tirmidhi-breastfeeding-boys-men":       ["incest"],
        "tirmidhi-camel-urine-medicine":         ["gross-vile"],
        "tirmidhi-intercourse-sexual-menses-prohibited": ["gross-vile"],
        "tirmidhi-drinking-blood":               ["gross-vile"],
        "tirmidhi-sex-camel-goat":               ["gross-vile"],
        "tirmidhi-masturbation-punishment":      ["gross-vile"],
        "tirmidhi-cat-pure-unique-ruling":       ["gross-vile"],
    },
    "nasai.html": {
        "nasai-zaynab-marriage-adopted-son":     ["incest"],
        "nasai-usury-seventy-sins-zina":         ["incest"],
        "nasai-uraniyyin-eyes-branded":          ["gross-vile"],
        "nasai-camel-urine-drink":               ["gross-vile"],
        "nasai-jews-menstruation-isolation":     ["gross-vile"],
        "nasai-dog-seven-washes":                ["gross-vile"],
        "nasai-semen-prostatic-fluid-distinction":          ["gross-vile"],
        "nasai-child-resembles-mother":          ["gross-vile"],
        "nasai-istihadah-continuous-bleeding":   ["gross-vile"],
        "nasai-wife-ghusl-cannot-refuse":        ["gross-vile"],
        "nasai-aisha-wet-feet":                  ["gross-vile"],
        "nasai-jinn-food-bone-dung":             ["gross-vile"],
        "nasai-istihadah-continuous-bleeding-complicated-rules": ["gross-vile"],
    },
    "ibn-majah.html": {
        "ibnmajah-usury-seventy-sins":           ["incest"],
        "ibnmajah-adult-breastfeeding-verses-eaten-goat":   ["incest"],
        "ibnmajah-camel-urine-medicine":         ["gross-vile"],
        "ibnmajah-intercourse-anus-cursed":      ["gross-vile"],
        "ibnmajah-prophet-anus-forbidden-woman": ["gross-vile"],
    },
}


def process_file(path: Path, id_to_tags: dict) -> tuple[int, int]:
    """Append new tokens to data-category for each listed entry.
    Returns (entries_touched, total_tokens_added)."""
    text = path.read_text(encoding="utf-8")
    touched = 0
    added = 0
    not_found = []

    for entry_id, new_tags in id_to_tags.items():
        # Find the entry opening <div ... id="..." ... data-category="...">.
        pat = re.compile(
            r'(<div class="entry"\s+id="' + re.escape(entry_id)
            + r'"[^>]*data-category=")([^"]*)(")'
        )
        m = pat.search(text)
        if not m:
            not_found.append(entry_id)
            continue
        existing = m.group(2).split()
        existing_set = set(existing)
        appended_here = []
        for tag in new_tags:
            if tag not in existing_set:
                existing.append(tag)
                existing_set.add(tag)
                appended_here.append(tag)
        if not appended_here:
            continue
        new_attr = " ".join(existing)
        replacement = m.group(1) + new_attr + m.group(3)
        text = text[:m.start()] + replacement + text[m.end():]
        touched += 1
        added += len(appended_here)

    if not_found:
        print(f"  WARN: {len(not_found)} entry IDs not found in {path.name}:")
        for nf in not_found[:10]:
            print(f"    - {nf}")

    path.write_text(text, encoding="utf-8")
    return touched, added


def main() -> None:
    grand_t = 0
    grand_a = 0
    tag_counts = defaultdict(int)
    for fname, entries in TAGS.items():
        p = ROOT / "site" / "catalog" / fname
        t, a = process_file(p, entries)
        for tags in entries.values():
            for tag in tags:
                tag_counts[tag] += 1
        print(f"  {fname}: touched {t} entries, added {a} tokens")
        grand_t += t
        grand_a += a
    print(f"\nTotal: {grand_t} entries touched, {grand_a} tokens added.")
    print(f"Per tag target counts (expected):")
    for tag, n in sorted(tag_counts.items()):
        print(f"  {tag}: {n}")


if __name__ == "__main__":
    main()

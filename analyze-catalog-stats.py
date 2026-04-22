#!/usr/bin/env python3
"""Extract per-category statistics from the catalog for the Stats page.

Outputs JSON with:
  - total entries (by source + overall)
  - per-category counts and strength distribution
  - keyword frequencies in the rendered body text
  - cross-category overlap (entries tagged in multiple categories)
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CATALOG_DIR = ROOT / "site" / "catalog"

# Canonical category slugs (from site/about.html list)
CATEGORIES = [
    ("abrogation", "Abrogation"),
    ("scripture", "Scripture Integrity"),
    ("contradiction", "Contradictions"),
    ("logic", "Logical Inconsistency"),
    ("morality", "Moral Problems"),
    ("allah", "Allah's Character"),
    ("cosmology", "Cosmology"),
    ("preislamic", "Pre-Islamic Borrowings"),
    ("magic", "Magic & Occult"),
    ("ritual", "Ritual Absurdities"),
    ("prophet", "Prophetic Character"),
    ("privileges", "Prophetic Privileges"),
    ("jesus", "Jesus / Christology"),
    ("women", "Women"),
    ("sexual", "Sexual Issues"),
    ("childmarriage", "Child Marriage"),
    ("lgbtq", "LGBTQ / Gender"),
    ("slavery", "Slavery & Captives"),
    ("hudud", "Hudud"),
    ("warfare", "Warfare & Jihad"),
    ("apostasy", "Apostasy & Blasphemy"),
    ("governance", "Governance"),
    ("disbelievers", "Disbelievers"),
    ("antisemitism", "Antisemitism"),
    ("paradise", "Paradise"),
    ("hell", "Hell"),
    ("eschatology", "Eschatology"),
    ("strange", "Strange / Obscure"),
]

NAME_TO_SLUG = {name: slug for slug, name in CATEGORIES}

# Build a tag-name -> canonical slug lookup (entries use slug-ish tags)
TAG_TO_SLUG = {}
for slug, name in CATEGORIES:
    TAG_TO_SLUG[slug] = slug
    TAG_TO_SLUG[name.lower()] = slug
# Common tag variants seen in the raw catalog
TAG_VARIANTS = {
    "treatment of disbelievers": "disbelievers",
    "prophetic character": "prophet",
    "prophetic privileges": "privileges",
    "jesus / christology": "jesus",
    "science claims": "cosmology",
    "violence": "warfare",
    "misogyny": "women",
    "sexual misconduct": "sexual",
    "medical / magical": "magic",
    "rape / captive sex": "sexual",
    "cross-dressing": "lgbtq",
    "hudud": "hudud",
    "warfare & jihad": "warfare",
    "magic & occult": "magic",
    "ritual absurdities": "ritual",
    "sexual issues": "sexual",
    "child marriage": "childmarriage",
    "lgbtq / gender": "lgbtq",
    "slavery & captives": "slavery",
    "slavery": "slavery",
    "apostasy & blasphemy": "apostasy",
    "strange / obscure": "strange",
    "strange": "strange",
    "contradiction": "contradiction",
    "contradictions": "contradiction",
    "moral problems": "morality",
    "allah's character": "allah",
    "cosmology": "cosmology",
    "pre-islamic borrowings": "preislamic",
    "logical inconsistency": "logic",
    "paradise": "paradise",
    "hell": "hell",
    "eschatology": "eschatology",
    "antisemitism": "antisemitism",
    "scripture integrity": "scripture",
    "abrogation": "abrogation",
    "governance": "governance",
    "disbelievers": "disbelievers",
    "prophet": "prophet",
    "privileges": "privileges",
    "women": "women",
    "jesus": "jesus",
    "magic": "magic",
    "ritual": "ritual",
    "sexual": "sexual",
    "warfare": "warfare",
    "apostasy": "apostasy",
    "morality": "morality",
    "preislamic": "preislamic",
    "logic": "logic",
    "allah": "allah",
    "scripture": "scripture",
    "childmarriage": "childmarriage",
    "lgbtq": "lgbtq",
}

ENTRY_RE = re.compile(
    r'<div class="entry"\s+id="(?P<id>[^"]+)"\s+'
    r'data-category="(?P<cats>[^"]*)"\s+'
    r'data-strength="(?P<strength>[^"]*)"[^>]*>'
    r'(?P<inner>.*?)(?=<div class="entry"\s+id=|</main>|</body>)',
    re.DOTALL,
)
TITLE_RE = re.compile(r'<span class="entry-title">([^<]+)</span>')


SOURCES = ("quran", "bukhari", "muslim", "abu-dawud", "tirmidhi", "nasai", "ibn-majah")


def analyze():
    stats = {
        "by_source": {},
        "total_entries": 0,
        "strength_total": Counter(),
        "categories": {},      # slug → {count, strong, moderate, basic, sources:{}, examples:[]}
        "overlaps": Counter(), # (slug_a, slug_b) → count
        "keywords": Counter(), # global keyword frequency in entry bodies
    }

    # Initialise categories
    for slug, name in CATEGORIES:
        stats["categories"][slug] = {
            "slug": slug, "name": name,
            "count": 0,
            "strength": Counter(),
            "sources": Counter(),
            "examples": [],      # list of (source, title)
        }

    for source in SOURCES:
        path = CATALOG_DIR / f"{source}.html"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        source_count = 0
        for em in ENTRY_RE.finditer(text):
            source_count += 1
            body = em.group("inner")
            cats_raw = em.group("cats")
            strength = em.group("strength").lower() or None

            title_m = TITLE_RE.search(body)
            title = title_m.group(1).strip() if title_m else "(untitled)"

            if strength:
                stats["strength_total"][strength] += 1

            # Category slugs straight from data-category attribute
            cat_slugs = set()
            for raw in cats_raw.split():
                raw = raw.strip().lower()
                if not raw:
                    continue
                slug = TAG_VARIANTS.get(raw) or TAG_TO_SLUG.get(raw)
                if slug:
                    cat_slugs.add(slug)

            # Record per-category
            for slug in cat_slugs:
                c = stats["categories"][slug]
                c["count"] += 1
                if strength:
                    c["strength"][strength] += 1
                c["sources"][source] += 1
                if len(c["examples"]) < 6 and strength == "strong":
                    c["examples"].append({"source": source, "title": title})

            # Overlaps
            for a in cat_slugs:
                for b in cat_slugs:
                    if a < b:
                        stats["overlaps"][(a, b)] += 1

            # Body keywords (strip tags, lowercase)
            body_text = re.sub(r"<[^>]+>", " ", body).lower()
            for kw in ["kill", "death", "execute", "slave", "beat ",
                       "stoning", "amputation", "polygam", "wives",
                       "jihad", "apostate", "women", "booty", "captive",
                       "beheading", "terror", "prescribed", "hellfire",
                       "houri", "deficient", "sword"]:
                stats["keywords"][kw.strip()] += body_text.count(kw)

        stats["by_source"][source] = source_count
        stats["total_entries"] += source_count

    # Convert Counter objects to dicts for JSON
    stats["strength_total"] = dict(stats["strength_total"])
    stats["keywords"] = dict(stats["keywords"])
    stats["overlaps"] = [
        {"a": a, "b": b, "n": n}
        for (a, b), n in stats["overlaps"].most_common(50)
    ]
    for c in stats["categories"].values():
        c["strength"] = dict(c["strength"])
        c["sources"] = dict(c["sources"])

    return stats


if __name__ == "__main__":
    data = analyze()
    out = ROOT / ".tmp" / "catalog-stats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Total entries: {data['total_entries']}")
    print(f"Strength distribution: {data['strength_total']}")
    print(f"Top categories:")
    rows = sorted(data["categories"].values(), key=lambda c: -c["count"])
    for c in rows[:12]:
        print(f"  {c['name']:<30s} {c['count']:>4d}  (strong {c['strength'].get('strong', 0)})")
    print(f"Top overlaps:")
    for o in data["overlaps"][:10]:
        print(f"  {o['a']} ∩ {o['b']}: {o['n']}")
    print(f"Keyword frequencies (across entry bodies):")
    for k in sorted(data["keywords"], key=data["keywords"].get, reverse=True)[:15]:
        print(f"  {k:<20s} {data['keywords'][k]}")

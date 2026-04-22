#!/usr/bin/env python3
"""Scan all catalog pages for entries matching "incest"-style or
"gross/vile"-style signals. Emit candidate lists so they can be
reviewed + tagged.

Output: JSON at .tmp/scan/candidates.json  with shape
  {
    "incest":   [{"file": "...", "id": "...", "title": "...", "hit": "..."}],
    "gross":    [...]
  }
and a human-readable summary to stdout.
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
CATALOGS = [
    "quran.html", "bukhari.html", "muslim.html",
    "abu-dawud.html", "tirmidhi.html", "nasai.html", "ibn-majah.html",
]

# Signals — tuned to minimize false positives. Everything is lowercase-matched.
# Each pattern is a regex string; any match in an entry body qualifies.
INCEST_PATTERNS = [
    r"\bincest(uous)?\b",
    r"\bmilk[\- ]?kinship\b",
    r"\bmilk[\- ]?(mother|brother|sister|father)\b",
    r"\bfoster[\- ]?(mother|brother|sister|father)\b",
    r"\bsuckl(ing|ed)\b",           # usually paired with adult-breastfeeding
    r"\bwet[\- ]?nurs(e|ing|ed)\b",
    r"\brida[ʿ'`]?a(h)?\b",         # riḍāʿa — milk-kinship term
    r"\badult[- ]breastfeeding\b",
    r"\bsalim\b.*hudhayfa|hudhayfa.*salim",  # the salim adult-breastfeeding case
    r"\badopted[- ]son'?s wife\b",
    r"\bzayd\b.*zaynab|zaynab\b.*zayd",  # the Zaynab bint Jahsh marriage
    r"\bzaynab bint jahsh\b",
    r"\bfather[- ]?in[- ]?law\b",
    r"\bson[- ]?in[- ]?law\b",
    r"\bstep[\- ]?(mother|father|daughter|son)\b",
    r"\bfather'?s wife\b",
    r"\bdaughter[- ]?in[- ]?law\b",
    r"\bmarry (his|her) (son|daughter|brother|sister|niece|nephew|uncle|aunt)\b",
    r"\bmarry (his|her) (adopted|foster)\b",
    r"\bnursing\b.*\bmarriage\b|\bmarriage\b.*\bnursing\b",
]

GROSS_PATTERNS = [
    r"\bcamel'?s? urine\b|\burine of (the )?camel\b",
    r"\burine\b.*\bdrink\b|\bdrink\b.*\burine\b",
    r"\bdip(ping)? (the )?fly\b|\bfly (into|in) (the )?(drink|cup)\b",
    r"\bhouse[- ]?fly\b",
    r"\bmenstrual blood\b",
    r"\bmenstruat(e|ing|ion)\b.*\b(sex|intercourse|lick|kiss|touch)\b",
    r"\bsemen\b",
    r"\bmadhy\b",                    # pre-seminal fluid; appears in purity hadiths
    r"\bwadī\b|\bwady\b",            # seminal fluid terms
    r"\bmasturbat(e|ion|ing)\b",
    r"\bthighing\b|\bmufakhadhah\b|\bmufakhkhaza\b|\btafkhidh\b",
    r"\bfeces\b|\bfaeces\b|\bexcrement\b|\bdefecat(e|ion|ing)\b|\bstool\b.*\btoilet\b",
    r"\bvomit\b.*\b(drink|eat|lick|swallow)\b|\blick .*\bvomit\b",
    r"\bpus\b(?!\w)",
    r"\bmaggots?\b",
    r"\bdog'?s? saliva\b|\bseven (times|washes)\b.*\bdog\b|\bdog\b.*\bseven (times|washes)\b",
    r"\banus\b|\banal\b",
    r"\bdung\b.*\b(medicine|heal|remedy|use|drink)\b",
    r"\bsweat\b.*\b(musk|perfume|eat|drink|swallow|pour|collect)\b",  # paradise-sweat-is-musk
    r"\btongue\b.*\bfeet\b|\bfeet\b.*\btongue\b",  # lick-feet hadiths
    r"\bbestial(ity|ly)?\b|\bzoophil\b",
    r"\bcorpse\b.*\b(violat|sex|touch|intercourse)\b",
    r"\bpig'?s? (milk|flesh|blood)\b",
    r"\bnecrophil\b",
    r"\bpedophil\b",  # already likely in childmarriage, but capture any remainder
    r"\bbreak[- ]?wind\b|\bpass(es|ed|ing) gas\b|\bfart\b",
    r"\bhe (ate|swallowed|licked|drank) .*\b(urine|blood|pus|semen|vomit|feces)\b",
]

ENTRY_RE = re.compile(
    r'<div class="entry"\s+id="([^"]+)"[^>]*>(.*?)</div>\s*(?=<div class="entry"|<!--|<footer|<script|\Z)',
    re.DOTALL
)
TITLE_RE = re.compile(r'<span class="entry-title">(.*?)</span>', re.DOTALL)


def extract_title(entry_html: str) -> str:
    m = TITLE_RE.search(entry_html)
    if not m:
        return "(no title)"
    title = re.sub(r"<[^>]+>", "", m.group(1))
    title = re.sub(r"\s+", " ", title).strip()
    return title


def scan_file(path: Path) -> list[dict]:
    """Return a list of {id, title, body_lower} for every entry in the file."""
    text = path.read_text(encoding="utf-8")
    out = []
    for m in ENTRY_RE.finditer(text):
        body = m.group(2)
        out.append({
            "id": m.group(1),
            "title": extract_title(body),
            "body_lower": re.sub(r"<[^>]+>", " ", body).lower(),
        })
    return out


def match_any(text: str, patterns: list[str]) -> str | None:
    """Return the first matching pattern (for debugging) or None."""
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def main() -> None:
    results = defaultdict(list)
    per_file = defaultdict(lambda: {"incest": 0, "gross": 0, "total": 0})

    for cat in CATALOGS:
        path = ROOT / "site" / "catalog" / cat
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            continue
        entries = scan_file(path)
        per_file[cat]["total"] = len(entries)
        for e in entries:
            hit_incest = match_any(e["body_lower"], INCEST_PATTERNS)
            hit_gross  = match_any(e["body_lower"], GROSS_PATTERNS)
            if hit_incest:
                results["incest"].append({
                    "file": cat, "id": e["id"], "title": e["title"], "hit": hit_incest,
                })
                per_file[cat]["incest"] += 1
            if hit_gross:
                results["gross"].append({
                    "file": cat, "id": e["id"], "title": e["title"], "hit": hit_gross,
                })
                per_file[cat]["gross"] += 1

    # Dedupe within each bucket by (file, id)
    for bucket in list(results.keys()):
        seen = set()
        dedup = []
        for r in results[bucket]:
            key = (r["file"], r["id"])
            if key in seen:
                continue
            seen.add(key)
            dedup.append(r)
        results[bucket] = dedup

    # Summary
    print("\n=== Summary ===")
    for f, d in per_file.items():
        print(f"  {f}: {d['total']} entries  →  incest: {d['incest']}  ·  gross: {d['gross']}")
    print(f"\n  TOTAL incest candidates: {len(results['incest'])}")
    print(f"  TOTAL gross  candidates: {len(results['gross'])}")

    out_path = ROOT / ".tmp" / "scan" / "candidates.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

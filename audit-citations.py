#!/usr/bin/env python3
"""Audit every <a class="cite-link"> in catalog + category pages.

Reports:
  1. Broken link (target file missing).
  2. Dangling anchor (file exists but #anchor doesn't).
  3. Nested anchors (<a ...><a ...>...</a></a>).
  4. Stats: link counts per target, per source file.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
TARGETS = list((SITE / "catalog").glob("*.html")) + \
          list((SITE / "category").glob("*.html"))

# Cache of anchors defined in each target file
anchor_cache: dict[Path, set[str]] = {}


def load_anchors(path: Path) -> set[str]:
    if path in anchor_cache:
        return anchor_cache[path]
    if not path.exists():
        anchor_cache[path] = set()
        return set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        anchor_cache[path] = set()
        return set()
    ids = set(re.findall(r'\bid="([^"]+)"', text))
    names = set(re.findall(r'\bname="([^"]+)"', text, flags=re.IGNORECASE))
    anchor_cache[path] = ids | names
    return anchor_cache[path]


def resolve(source_path: Path, href: str) -> tuple[Path, str]:
    """Resolve href (relative to source_path's folder) to (file, fragment)."""
    fragment = ""
    if "#" in href:
        url, fragment = href.split("#", 1)
    else:
        url = href
    # External URLs
    if url.startswith(("http://", "https://", "mailto:")):
        return Path(""), fragment
    # Resolve relative to file's folder
    target = (source_path.parent / url).resolve() if url else source_path.resolve()
    return target, fragment


LINK_RE = re.compile(
    r'<a\s+class="cite-link"\s+href="([^"]+)"[^>]*>(.*?)</a>',
    re.DOTALL | re.IGNORECASE,
)
NESTED_RE = re.compile(
    r'<a\s+[^>]*>[^<]*<a\s+[^>]*>',
    re.IGNORECASE,
)


def audit():
    broken_files: list[tuple[Path, str, str]] = []
    dangling_anchors: list[tuple[Path, str, str]] = []
    nested: list[tuple[Path, str]] = []

    target_counter: Counter[str] = Counter()
    by_source: Counter[Path] = Counter()
    external_links: Counter[str] = Counter()

    for src in TARGETS:
        text = src.read_text(encoding="utf-8", errors="replace")

        # Nested anchors (rough scan)
        for m in NESTED_RE.finditer(text):
            snippet = text[m.start():m.start() + 160]
            nested.append((src, snippet.replace("\n", " ")))

        # All cite-link anchors
        for m in LINK_RE.finditer(text):
            href = m.group(1)
            by_source[src] += 1

            if href.startswith(("http://", "https://")):
                external_links[href] += 1
                continue

            target_file, fragment = resolve(src, href)
            # Normalise for reporting
            if target_file and target_file.exists():
                target_key = str(target_file.relative_to(SITE.resolve()))
                target_counter[target_key] += 1

                if fragment:
                    anchors = load_anchors(target_file)
                    if fragment not in anchors:
                        dangling_anchors.append(
                            (src, href, m.group(2)[:60])
                        )
            else:
                broken_files.append((src, href, m.group(2)[:60]))

    # ---- report ----
    print("========== CITATION AUDIT ==========\n")

    total_cites = sum(by_source.values())
    print(f"Total cite-link anchors: {total_cites}")
    print(f"Source files scanned:    {len(TARGETS)}")
    print(f"External (http) links:   {sum(external_links.values())}")
    print()

    print("--- Top citation targets ---")
    for target, count in target_counter.most_common(25):
        print(f"  {count:5d}  {target}")
    print()

    print(f"--- BROKEN FILE TARGETS ({len(broken_files)}) ---")
    for src, href, label in broken_files[:40]:
        print(f"  {src.relative_to(ROOT)}: {href}  \"{label.strip()[:40]}\"")
    if len(broken_files) > 40:
        print(f"  ... and {len(broken_files) - 40} more")
    print()

    print(f"--- DANGLING ANCHORS ({len(dangling_anchors)}) ---")
    # Group by target file for readability
    by_target = defaultdict(list)
    for src, href, label in dangling_anchors:
        url = href.split("#")[0]
        by_target[url].append((src, href, label))
    for tgt in sorted(by_target, key=lambda k: -len(by_target[k])):
        rows = by_target[tgt]
        print(f"  {tgt}: {len(rows)} missing anchors")
        for src, href, label in rows[:6]:
            frag = href.split("#", 1)[1] if "#" in href else ""
            print(f"    {src.name} → #{frag}  \"{label.strip()[:40]}\"")
        if len(rows) > 6:
            print(f"    ... and {len(rows) - 6} more")
    print()

    print(f"--- NESTED ANCHORS ({len(nested)}) ---")
    # dedupe snippets
    seen = set()
    for src, snippet in nested:
        key = (src.name, snippet[:80])
        if key in seen:
            continue
        seen.add(key)
        print(f"  {src.name}: {snippet[:140]}")
    print()

    print("--- Source files with most citations ---")
    for src, count in by_source.most_common(15):
        print(f"  {count:5d}  {src.relative_to(ROOT)}")


if __name__ == "__main__":
    audit()

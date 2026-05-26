"""
_update_counts.py
Replaces the old total entry count (1,573) with the new count (1,549)
across all site HTML pages that display it.
Skips site/read/* and site/read-external/* (those have 1573 as hadith numbers).
"""
import re
from pathlib import Path

BASE = Path(r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site")

# Pages that display the catalog entry count (NOT the full-text reader pages)
TARGET_FILES = [
    BASE / "index.html",
    BASE / "about.html",
    BASE / "catalog.html",
    BASE / "build.html",
    BASE / "faq.html",
    BASE / "stats.html",
    BASE / "play.html",
    BASE / "compare.html",
    BASE / "read.html",
    BASE / "read-islamic.html",
    BASE / "shared.html",
    BASE / "saved.html",
    BASE / "goat.html",
]

OLD = "1,573"
NEW = "1,549"

total_replacements = 0
for path in TARGET_FILES:
    if not path.exists():
        print(f"  SKIP (not found): {path.name}")
        continue
    content = path.read_text(encoding="utf-8")
    count = content.count(OLD)
    if count == 0:
        continue
    new_content = content.replace(OLD, NEW)
    path.write_text(new_content, encoding="utf-8")
    print(f"  {path.name}: {count} replacement(s)")
    total_replacements += count

print(f"\nTotal replacements: {total_replacements}")
print(f"All occurrences of '{OLD}' replaced with '{NEW}'")

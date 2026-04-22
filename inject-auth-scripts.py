#!/usr/bin/env python3
"""Inject Supabase + auth-ui scripts into every HTML page that currently
loads goat.js. Uses the existing goat.js path to derive the correct
relative prefix (./assets/ vs ../assets/).

Idempotent: if the auth scripts are already present, skips the file.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = Path(__file__).parent / "site"

GOAT_RE = re.compile(
    r'(\s*)<script src="([^"]*assets/js/goat\.js)"[^>]*></script>'
)

def block_for_prefix(prefix):
    """Given the path to assets/js/ (without trailing goat.js), produce the
    script tag block to inject before the goat script tag."""
    # supabase-js is from a CDN, same on every page
    return (
        '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n'
        f'<script src="{prefix}config.js"></script>\n'
        f'<script src="{prefix}auth.js" defer></script>\n'
        f'<script src="{prefix}auth-ui.js" defer></script>\n'
    )


def process(path):
    text = path.read_text(encoding="utf-8")
    # Skip if we already injected
    if "js/auth.js" in text or "js/auth-ui.js" in text:
        return "skip (already injected)"

    m = GOAT_RE.search(text)
    if not m:
        return "skip (no goat.js found — probably auth page that loads manually)"

    goat_path = m.group(2)
    # derive prefix — everything up to "js/"
    idx = goat_path.rfind("js/")
    if idx < 0:
        return "skip (unexpected goat path)"
    prefix = goat_path[: idx + 3]  # includes "js/"

    block = block_for_prefix(prefix)

    indent = m.group(1) or "\n"
    # Insert block immediately before the goat script tag
    new = text[: m.start()] + indent + block.rstrip() + m.group(0) + text[m.end():]
    # Dedupe excess blank lines
    new = re.sub(r"\n{4,}", "\n\n\n", new)
    path.write_text(new, encoding="utf-8")
    return f"injected with prefix {prefix!r}"


def main():
    files = []
    files.extend(sorted(SITE.glob("*.html")))
    files.extend(sorted((SITE / "read").glob("*.html")))
    files.extend(sorted((SITE / "catalog").glob("*.html")))
    files.extend(sorted((SITE / "category").glob("*.html")))
    files.extend(sorted((SITE / "read-external").glob("*.html")) if (SITE / "read-external").exists() else [])

    stats = {"injected": 0, "skipped": 0}
    for f in files:
        result = process(f)
        if result.startswith("injected"):
            stats["injected"] += 1
        else:
            stats["skipped"] += 1
        # Print concise one-liner
        rel = f.relative_to(SITE).as_posix()
        print(f"  {rel}: {result}")

    print(f"\nSummary: {stats['injected']} injected, {stats['skipped']} skipped.")


if __name__ == "__main__":
    main()

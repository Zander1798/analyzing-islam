"""
Idempotent injector: adds the resizable-pane splitter to every page that uses
a recognised two-pane layout.

Layouts handled:
  1. reader-layout: injects a <div class="splitter"> between </aside> and
     <main class="reader-main">.  Target pages: site/read/*.html and the
     read-external pages that use .reader-layout.
  2. compare-panes: injects a splitter between the two .compare-pane
     sections on compare.html.
  3. build-panes: injects a splitter between the two .build-pane sections
     on build.html.

In every affected page the script also inserts
<script src=".../assets/js/splitter.js" defer></script> just before the
existing goat.js <script> tag (which is at the bottom of <body>).

Re-running the script is safe — all insertions are guarded by substring
checks.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

# ---- splitter markup for each layout -----------------------------------------
READER_SPLITTER = (
    '  <div class="splitter" data-splitter-var="--reader-toc-w" '
    'data-splitter-min="180" data-splitter-max="460" '
    'data-splitter-key="reader-toc" aria-label="Resize chapter list"></div>\n'
)

COMPARE_SPLITTER = (
    '    <div class="splitter" data-splitter-var="--compare-left-w" '
    'data-splitter-min="260" data-splitter-max="1400" '
    'data-splitter-key="compare-left" aria-label="Resize left pane"></div>\n'
)

BUILD_SPLITTER = (
    '      <div class="splitter" data-splitter-var="--build-left-w" '
    'data-splitter-min="280" data-splitter-max="1400" '
    'data-splitter-key="build-left" aria-label="Resize editor pane"></div>\n'
)


def inject_splitter_reader(text: str) -> str:
    """Insert reader splitter between </aside> (closing reader-toc) and
    <main class="reader-main">."""
    if 'data-splitter-key="reader-toc"' in text:
        return text  # already done
    pattern = re.compile(
        r'(</aside>\s*\n)(\s*<main\s+class="reader-main")',
        re.MULTILINE,
    )
    new_text, n = pattern.subn(r'\1' + READER_SPLITTER + r'\2', text, count=1)
    return new_text if n else text


def inject_splitter_compare(text: str) -> str:
    """Insert compare splitter between the two .compare-pane sections."""
    if 'data-splitter-key="compare-left"' in text:
        return text
    # Match the closing </section> of the first compare-pane, followed by
    # the opening <section class="compare-pane" data-side="right">.
    pattern = re.compile(
        r'(</section>\s*\n)(\s*<section\s+class="compare-pane"\s+data-side="right")',
        re.MULTILINE,
    )
    new_text, n = pattern.subn(r'\1' + COMPARE_SPLITTER + r'\2', text, count=1)
    return new_text if n else text


def inject_splitter_build(text: str) -> str:
    """Insert build splitter between the two .build-pane sections."""
    if 'data-splitter-key="build-left"' in text:
        return text
    pattern = re.compile(
        r'(</section>\s*\n)(\s*<section\s+class="build-pane\b[^"]*"\s+data-side="right")',
        re.MULTILINE,
    )
    new_text, n = pattern.subn(r'\1' + BUILD_SPLITTER + r'\2', text, count=1)
    return new_text if n else text


def inject_splitter_script(text: str, prefix: str) -> str:
    """Add <script src=".../splitter.js" defer> right before goat.js."""
    if "assets/js/splitter.js" in text:
        return text
    goat_tag = f'<script src="{prefix}assets/js/goat.js" defer></script>'
    if goat_tag not in text:
        return text  # page doesn't use goat.js; leave it alone
    splitter_tag = f'<script src="{prefix}assets/js/splitter.js" defer></script>\n'
    return text.replace(goat_tag, splitter_tag + goat_tag, 1)


def prefix_for(path: Path) -> str:
    """Number of ../ needed from the page back to site/."""
    rel = path.relative_to(SITE).parent
    depth = len(rel.parts)
    return "../" * depth if depth > 0 else ""


def process_file(path: Path, kind: str) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    if kind == "reader":
        text = inject_splitter_reader(text)
    elif kind == "compare":
        text = inject_splitter_compare(text)
    elif kind == "build":
        text = inject_splitter_build(text)

    text = inject_splitter_script(text, prefix_for(path))

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = []

    # --- Reader-layout pages (site/read + a few in site/read-external) --------
    reader_candidates = list((SITE / "read").glob("*.html"))
    reader_candidates += list((SITE / "read-external").glob("*.html"))
    for path in reader_candidates:
        text = path.read_text(encoding="utf-8")
        if 'class="reader-layout"' not in text:
            continue
        if process_file(path, "reader"):
            changed.append(path)

    # --- Compare page ----------------------------------------------------------
    compare = SITE / "compare.html"
    if compare.exists() and process_file(compare, "compare"):
        changed.append(compare)

    # --- Build page ------------------------------------------------------------
    build = SITE / "build.html"
    if build.exists() and process_file(build, "build"):
        changed.append(build)

    for p in changed:
        print("updated", p.relative_to(ROOT))
    print(f"\n{len(changed)} file(s) updated.")


if __name__ == "__main__":
    main()

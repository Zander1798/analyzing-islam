"""
Applies verified citation fixes to dossier HTML files.
Each fix targets an exact href + link-text pattern so no collateral
replacements occur on unrelated numbers.
"""

import re, os

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def apply(path, replacements):
    """
    replacements: list of (old_str, new_str) pairs.
    Applies each in order; asserts each old_str appears at least once.
    """
    content = read(path)
    original = content
    for old, new in replacements:
        if old not in content:
            print(f"  WARNING: pattern not found in {os.path.basename(path)}:")
            print(f"    {repr(old[:80])}")
            continue
        content = content.replace(old, new)
    if content != original:
        write(path, content)
        print(f"  Fixed: {os.path.relpath(path, SITE)}")
    else:
        print(f"  No changes: {os.path.relpath(path, SITE)}")


# ── 1. d01-awtas-captives-iddah.html  (2155 → 2156) ──────────────────────────
print("d01:")
apply(
    os.path.join(SITE, "arguments/abu-dawud/d01-awtas-captives-iddah.html"),
    [
        # href anchors
        ('read/abu-dawud.html#h2155">Abu Dawud 2155</a>',
         'read/abu-dawud.html#h2156">Abu Dawud 2156</a>'),
        # Bare "2155" in prose that refers to this hadith
        ('>Abu Dawud 2155</a> and 2150',
         '>Abu Dawud 2156</a> and 2150'),
    ]
)


# ── 2. d06-prepubescent-marriage-normalised.html  (2126→2122, 2095→2097) ──────
print("\nd06:")
apply(
    os.path.join(SITE, "arguments/abu-dawud/d06-prepubescent-marriage-normalised.html"),
    [
        # ── Aisha marriage-age hadith: 2126 → 2122 ──
        # href anchors
        ('read/abu-dawud.html#h2126">Abu Dawud 2126</a>',
         'read/abu-dawud.html#h2122">Abu Dawud 2122</a>'),
        # bare "2126" in prose (appears as " 2126 " or "2126)" etc.)
        ('Abu Dawud 2126', 'Abu Dawud 2122'),

        # ── Forced-marriage consent hadith: 2095 → 2097 ──
        ('read/abu-dawud.html#h2095">Abu Dawud 2095</a>',
         'read/abu-dawud.html#h2097">Abu Dawud 2097</a>'),
        ('Abu Dawud 2095', 'Abu Dawud 2097'),
    ]
)


# ── 3. b15-yawning-from-satan.html  (7320 → 5988) ────────────────────────────
print("\nb15:")
apply(
    os.path.join(SITE, "arguments/bukhari/b15-yawning-from-satan.html"),
    [
        ('read/bukhari.html#h7320">Bukhari 7320</a>',
         'read/bukhari.html#h5988">Bukhari 5988</a>'),
        ('Bukhari 7320', 'Bukhari 5988'),
    ]
)


# ── 4. m05-fight-until-shahada.html  (h17→h34, h21→h36) ──────────────────────
print("\nm05:")
apply(
    os.path.join(SITE, "arguments/muslim/m05-fight-until-shahada.html"),
    [
        # ── Primary citation: Muslim 17 → Muslim 34 ──
        ('read/muslim.html#h17">Muslim 17</a>',
         'read/muslim.html#h34">Muslim 34</a>'),
        # Header "/ 21" link: Muslim 21 → Muslim 36
        ('read/muslim.html#h21">21</a>',
         'read/muslim.html#h36">36</a>'),
        # Full-text link for parallel: ">Muslim 21<" pattern
        ('read/muslim.html#h21">Muslim 21</a>',
         'read/muslim.html#h36">Muslim 36</a>'),
        # Prose mentions after anchor updates (should now be done, but belt-and-suspenders)
        ('Muslim 17</a> / <a class="cite-link" href="../../read/muslim.html#h36">36</a>',
         'Muslim 34</a> / <a class="cite-link" href="../../read/muslim.html#h36">36</a>'),
    ]
)


# ── 5. m15-suns-prostration-throne.html  (h159→h304) ─────────────────────────
print("\nm15:")
apply(
    os.path.join(SITE, "arguments/muslim/m15-suns-prostration-throne.html"),
    [
        ('read/muslim.html#h159">Muslim 159</a>',
         'read/muslim.html#h304">Muslim 304</a>'),
        ('Muslim 159', 'Muslim 304'),
    ]
)

print("\nAll done.")

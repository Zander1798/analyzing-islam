"""
Second-pass catalog citation fixes:
- Chaining victims from fix 1 (h4108→h4107 slave, h3733→h3731 see-saw, h4288→h4284)
- Format mismatches (Nasai without apostrophe)
- Custom display text (abu-dawud h4413)
- New error revealed by fix 1 (bukhari h278→h263 for Children of Israel)
All replacements are entry-specific to avoid collateral changes.
"""

import os, re

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT  = os.path.join(SITE, "catalog")

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def fix_entry(content, entry_id, old_str, new_str):
    """Replace old_str with new_str only within the named entry div."""
    # Find the entry by its id attribute
    entry_start = content.find(f'id="{entry_id}"')
    if entry_start < 0:
        print(f"    WARN: entry '{entry_id}' not found")
        return content
    # Find the closing of this entry: next <div class="entry" (NOT entry-header etc.)
    rest = content[entry_start:]
    # Require class ends with "entry" then a non-word/non-dash char (space or >)
    next_entry = re.search(r'<div\s+class="entry[\s">]', rest[100:])
    entry_end = entry_start + 100 + (next_entry.start() if next_entry else len(rest))
    entry_block = content[entry_start:entry_end]
    if old_str not in entry_block:
        print(f"    WARN: '{old_str[:50]}' not found in entry '{entry_id}'")
        return content
    new_block = entry_block.replace(old_str, new_str)
    return content[:entry_start] + new_block + content[entry_end:]

def apply(path, fixes=None, entry_fixes=None):
    content = read(path)
    original = content
    # Global fixes (simple replace)
    for old, new in (fixes or []):
        if old not in content:
            print(f"    WARN (global): '{old[:60]}' not found")
        else:
            content = content.replace(old, new)
    # Entry-specific fixes
    for entry_id, old, new in (entry_fixes or []):
        content = fix_entry(content, entry_id, old, new)
    rel = os.path.relpath(path, SITE)
    if content != original:
        write(path, content)
        print(f"  Fixed: {rel}")
    else:
        print(f"  No changes: {rel}")

# ── catalog/abu-dawud.html ────────────────────────────────────────────────────
print("abu-dawud.html:")
apply(
    os.path.join(CAT, "abu-dawud.html"),
    fixes=[
        # h4413: only href changes (display text is custom "Book of Legal Punishments, Ch. 25")
        ('read/abu-dawud.html#h4413">', 'read/abu-dawud.html#h4423">'),
    ],
    entry_fixes=[
        # Chaining victim: slave/Fatimah entry got over-corrected to h4108
        ("fatima-young-slave-clothing",
         'read/abu-dawud.html#h4108">Abu Dawud 4108</a>',
         'read/abu-dawud.html#h4107">Abu Dawud 4107</a>'),
    ],
)

# ── catalog/bukhari.html ──────────────────────────────────────────────────────
print("bukhari.html:")
apply(
    os.path.join(CAT, "bukhari.html"),
    entry_fixes=[
        # Children of Israel bath: h278 → h263
        ("stone-ran-moses",
         'read/bukhari.html#h278">Bukhari 278</a>',
         'read/bukhari.html#h263">Bukhari 263</a>'),
        # Aisha-age entry: h3733 → h3731 (two occurrences — both in same entry block)
        ("aisha-age",
         'read/bukhari.html#h3733">Bukhari 3733</a>',
         'read/bukhari.html#h3731">Bukhari 3731</a>'),
        # Aisha bride-prep see-saw entry: h3733 → h3731
        ("aisha-bride-prep-mother-swing",
         'read/bukhari.html#h3733">Bukhari 3733</a>',
         'read/bukhari.html#h3731">Bukhari 3731</a>'),
    ],
)

# ── catalog/muslim.html ───────────────────────────────────────────────────────
print("muslim.html:")
apply(
    os.path.join(CAT, "muslim.html"),
    entry_fixes=[
        # hundred-lashes entry: h4288 → h4284 (stoning-adulterers entry keeps h4288)
        ("hundred-lashes-contradiction",
         'read/muslim.html#h4288">Muslim #4288</a>',
         'read/muslim.html#h4284">Muslim #4284</a>'),
    ],
)

# ── catalog/nasai.html ────────────────────────────────────────────────────────
print("nasai.html:")
apply(
    os.path.join(CAT, "nasai.html"),
    fixes=[
        # Format is "Nasai" (no apostrophe) — fix 1 used "Nasa'i" so these didn't match
        ('read/nasai.html#h671">Nasai #671</a>',  'read/nasai.html#h672">Nasai #672</a>'),
        ('read/nasai.html#h2525">Nasai #2525</a>', 'read/nasai.html#h2529">Nasai #2529</a>'),
    ],
)

print("\nAll done.")

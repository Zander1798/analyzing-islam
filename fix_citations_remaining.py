"""
Final cleanup: format mismatches not caught by lnk_pat.

Issues:
  1. catalog/nasai.html: entries display "Nasa'i #NNN" (apostrophe) — lnk_pat
     used "Nasai" and missed them
  2. catalog/muslim.html: some entries use bare "#NNN" format or range display
  3. catalog/ibn-majah.html: h3786 uses bare "#NNN" format
  4. catalog/bukhari.html: h1543→h1568 for safa-marwa-pagan-origin entry (chaining)
  5. arguments/tirmidhi/t13: h7122 range display not matched by lnk()
"""

import os, re

SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
CAT  = os.path.join(SITE, "catalog")
A    = os.path.join(SITE, "arguments")

def read(p):
    with open(p, encoding="utf-8") as f: return f.read()

def write(p, c):
    with open(p, "w", encoding="utf-8", newline="\n") as f: f.write(c)

def apply(path, fixes):
    content = read(path)
    orig = content
    for old, new in fixes:
        if old not in content:
            print(f"  WARN: not found in {os.path.relpath(path, SITE)}: {repr(old[:70])}")
        else:
            content = content.replace(old, new)
    rel = os.path.relpath(path, SITE)
    if content != orig:
        write(path, content)
        print(f"  Fixed: {rel}")
    else:
        print(f"  No changes: {rel}")

def fix_entry(content, entry_id, old, new):
    pos = content.find(f'id="{entry_id}"')
    if pos < 0:
        print(f"    WARN: entry '{entry_id}' not found")
        return content
    rest = content[pos:]
    ne = re.search(r'<div\s+class="entry[\s">]', rest[100:])
    end = pos + 100 + (ne.start() if ne else len(rest))
    block = content[pos:end]
    if old not in block:
        print(f"    WARN: old string not found in entry '{entry_id}'")
        return content
    return content[:pos] + block.replace(old, new) + content[end:]

# ── catalog/nasai.html ────────────────────────────────────────────────────────
# Entries using "Nasa'i #NNN" format (apostrophe) — lnk_pat missed these
print("nasai.html:")
apply(os.path.join(CAT, "nasai.html"), [
    # Full href+display replacements for "Nasa'i" format
    ('read/nasai.html#h99">Nasa\'i #99</a>',     'read/nasai.html#h68">Nasa\'i #68</a>'),
    ('read/nasai.html#h184">#184</a>',            'read/nasai.html#h172">#172</a>'),
    ('read/nasai.html#h202">Nasa\'i #202-#217</a>','read/nasai.html#h216">Nasa\'i #216</a>'),
    ('read/nasai.html#h295">Nasa\'i #295</a>',    'read/nasai.html#h285">Nasa\'i #285</a>'),
    ('read/nasai.html#h817">Nasa\'i #817</a>',    'read/nasai.html#h822">Nasa\'i #822</a>'),
    ('read/nasai.html#h1493">Nasa\'i #1493</a>',  'read/nasai.html#h1498">Nasa\'i #1498</a>'),
    ('read/nasai.html#h2215">Nasa\'i #2215</a>',  'read/nasai.html#h2216">Nasa\'i #2216</a>'),
    ('read/nasai.html#h3362">Nasa\'i #3362</a>',  'read/nasai.html#h3396">Nasa\'i #3396</a>'),
])

# ── catalog/muslim.html ───────────────────────────────────────────────────────
print("muslim.html:")
apply(os.path.join(CAT, "muslim.html"), [
    # Range display — change href only, keep range in display
    ('read/muslim.html#h576">Muslim 576-584</a>',  'read/muslim.html#h584">Muslim 576-584</a>'),
    # Bare "#NNN" format
    ('read/muslim.html#h1794">#1794</a>',          'read/muslim.html#h1791">#1791</a>'),
    ('read/muslim.html#h1798">#1798</a>',          'read/muslim.html#h1791">#1791</a>'),
    ('read/muslim.html#h5533">#5533</a>',          'read/muslim.html#h5531">#5531</a>'),
    ('read/muslim.html#h7205">#7205</a>',          'read/muslim.html#h7202">#7202</a>'),
])

# ── catalog/ibn-majah.html ────────────────────────────────────────────────────
print("ibn-majah.html:")
apply(os.path.join(CAT, "ibn-majah.html"), [
    ('read/ibn-majah.html#h3786">#3786</a>', 'read/ibn-majah.html#h3820">#3820</a>'),
])

# ── catalog/bukhari.html ──────────────────────────────────────────────────────
# h1543 appears correctly in 4 entries (Umar/Black Stone theme)
# but safa-marwa-pagan-origin should use h1568 (Ansar/idols revelation)
print("bukhari.html:")
content = read(os.path.join(CAT, "bukhari.html"))
content = fix_entry(content, "safa-marwa-pagan-origin",
    'read/bukhari.html#h1543">Bukhari 1543</a>',
    'read/bukhari.html#h1568">Bukhari 1568</a>')
orig_path = os.path.join(CAT, "bukhari.html")
orig_content = read(orig_path)
if content != orig_content:
    write(orig_path, content)
    print(f"  Fixed: catalog\\bukhari.html")
else:
    print(f"  No changes: catalog\\bukhari.html")

# ── arguments/tirmidhi/t13 ────────────────────────────────────────────────────
# h7122 uses range display "Bukhari 7122-7128" — lnk() matched "Bukhari 7122" only
print("t13:")
apply(os.path.join(A, "tirmidhi/t13-dajjal-eschatology.html"), [
    ('read/bukhari.html#h7122">Bukhari 7122-7128</a>',
     'read/bukhari.html#h7154">Bukhari 7154</a>'),
])

print("\nAll done.")

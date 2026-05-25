"""
Minimal patch from the original HTML:
  1. Fix overflow (height→min-height, overflow:hidden→visible)
  2. Front cover: replace [Author Name] and [Publisher] placeholders
  3. Back cover: fix entry count, chapter count, and placeholder bio
Colors and font sizes are left exactly as in the original.
"""
import os, re

SRC = r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran.html"
DST = r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran\Analyzing Islam Vol I — The Quran v3.html"

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. OVERFLOW FIX ──────────────────────────────────────────
html = html.replace(
    'width: 665px; height: 945px; background: #000; color: #f5f5f5; position: relative; overflow: hidden;',
    'width: 665px; min-height: 945px; background: #000; color: #f5f5f5; position: relative; overflow: visible;'
)
html = html.replace(
    'top: 76px; bottom: 76px; left: 68px; right: 53px; overflow: hidden;',
    'top: 76px; bottom: 76px; left: 68px; right: 53px; overflow: visible;'
)
html = html.replace(
    '.entry-page { height: 945px; overflow: hidden; }',
    '.entry-page { min-height: 945px; overflow: visible; }'
)

# ── 2. FRONT COVER ───────────────────────────────────────────
html = html.replace('[Author Name]', 'G.J. van Vuuren')
html = html.replace('[Publisher]', 'ANALYZINGISLAM.COM')

# ── 3. BACK COVER ────────────────────────────────────────────
# Fix entry count and chapter count in blurb
html = html.replace(
    'Each of the 311 entries presents a\n      specific verse exactly as it appears',
    'Each of the 282 entries presents a\n      specific verse exactly as it appears'
)
html = html.replace(
    '<div class="bc2-feat">311 entries organized across 23 thematic chapters</div>',
    '<div class="bc2-feat">282 entries organized across 20 chapters</div>'
)
html = html.replace(
    '<div class="bc2-feat">311 entries organized across 23 chapters</div>',
    '<div class="bc2-feat">282 entries organized across 20 chapters</div>'
)

# Replace placeholder "About the Author" section with actual ABOUT content
old_about = '''    <div class="bc2-author-label">About the Author</div>
    <div class="bc2-bio">
      [Author Name] has spent [X] years researching Islamic primary texts and the
      apologetic literature surrounding them. Drawing on classical Arabic sources,
      academic scholarship, and close textual analysis, [he/she/they] brings together
      the most significant challenges to Quranic truth claims in a single, accessible
      reference work.
    </div>'''

new_about = '''    <div class="bc2-author-label">About AnalyzingIslam.com</div>
    <div class="bc2-bio">
      AnalyzingIslam.com is an independent reference platform dedicated to the
      close examination of Islamic primary texts. Drawing on classical Arabic
      sources, academic scholarship, and direct textual analysis, it presents the
      most significant challenges to Islamic truth claims in a structured, accessible
      format.
    </div>'''

html = html.replace(old_about, new_about)

# Fix [Publisher Name] in bottom bar
html = html.replace('[Publisher Name]', 'ANALYZINGISLAM.COM')

# ── Write output ─────────────────────────────────────────────
with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Saved: {DST}')
os.startfile(DST)
print('Opened in default browser.')

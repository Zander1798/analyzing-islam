#!/usr/bin/env python3
"""Generate scaffolding for the 5 new secondary hadith collections.

Creates:
  - site/read/{slug}.html   — link-out reader page
  - site/catalog/{slug}.html — empty but structured catalog page

Also patches:
  - site/read-islamic.html — adds 'Secondary collections' group
  - site/catalog.html — adds 'Secondary collections' section
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent

COLLECTIONS = [
    {
        "slug": "ahmad",
        "title": "Musnad Ahmad ibn Ḥanbal",
        "title_plain": "Musnad Ahmad ibn Hanbal",
        "title_short": "Musnad Aḥmad",
        "description": (
            "Compiled by Imam Aḥmad ibn Ḥanbal (d. 855 CE), founder of the Ḥanbalī school. "
            "Organized by companion (<em>musnad</em>-style) rather than by topic. One of the "
            "largest hadith compilations — approximately 27,000–30,000 reports across "
            "roughly 900 companions."
        ),
        "description_plain": (
            "Compiled by Imam Ahmad ibn Hanbal (d. 855 CE), founder of the Hanbali school. "
            "Organized by companion rather than by topic. Approximately 27,000-30,000 reports."
        ),
        "source_url": "https://sunnah.com/ahmad",
        "source_label": "sunnah.com · English + Arabic",
        "n_hadiths": "~27,000 reports",
        "translation_note": (
            "English translation by Nasiruddin Al-Khattab, hosted on sunnah.com "
            "(a mainstream Muslim-community resource). Darussalam print edition is the "
            "primary reference."
        ),
    },
    {
        "slug": "darimi",
        "title": "Sunan al-Dārimī",
        "title_plain": "Sunan al-Darimi",
        "title_short": "Sunan al-Dārimī",
        "description": (
            "Compiled by 'Abd Allāh al-Dārimī (d. 869 CE). Arranged thematically like a "
            "<em>sunan</em>, covering jurisprudence, worship, commerce, and the virtues "
            "of the Qurʾan. Approximately 3,400 hadiths across 23 books."
        ),
        "description_plain": (
            "Compiled by Abd Allah al-Darimi (d. 869 CE). Arranged thematically like a sunan, "
            "covering jurisprudence, worship, commerce, and virtues of the Quran. "
            "Approximately 3,400 hadiths across 23 books."
        ),
        "source_url": "https://sunnah.com/darimi",
        "source_label": "sunnah.com · English + Arabic",
        "n_hadiths": "~3,400 hadiths",
        "translation_note": (
            "English translation hosted on sunnah.com (a mainstream Muslim-community "
            "resource). Several Arabic editions are also available on archive.org."
        ),
    },
    {
        "slug": "shafii",
        "title": "Musnad al-Shāfiʿī",
        "title_plain": "Musnad al-Shafi'i",
        "title_short": "Musnad al-Shāfiʿī",
        "description": (
            "Compiled from the narrations of Imam Muḥammad ibn Idrīs al-Shāfiʿī (d. 820 CE), "
            "founder of the Shāfiʿī school. Approximately 1,800 hadiths, primarily of "
            "legal-jurisprudential interest."
        ),
        "description_plain": (
            "Compiled from narrations of Imam Muhammad ibn Idris al-Shafi'i (d. 820 CE), "
            "founder of the Shafi'i school. Approximately 1,800 hadiths, primarily legal."
        ),
        "source_url": "https://archive.org/details/musnad-imam-shafi-published-by-idara-islamiat",
        "source_label": "archive.org · Arabic",
        "n_hadiths": "~1,800 hadiths",
        "translation_note": (
            "No complete English translation is available for free distribution. The Arabic "
            "text is readily available on archive.org; partial translations exist in "
            "academic works."
        ),
    },
    {
        "slug": "tayalisi",
        "title": "Musnad Abū Dāwūd al-Ṭayālisī",
        "title_plain": "Musnad Abu Dawud al-Tayalisi",
        "title_short": "Musnad al-Ṭayālisī",
        "description": (
            "Compiled by Sulaymān ibn Dāwūd al-Ṭayālisī (d. 819 CE). One of the oldest "
            "<em>musnad</em>-style hadith compilations, preceding the canonical six. "
            "Approximately 2,900 hadiths organised by companion."
        ),
        "description_plain": (
            "Compiled by Sulayman ibn Dawud al-Tayalisi (d. 819 CE). One of the oldest "
            "musnad-style compilations, predating the canonical six. Approximately 2,900 "
            "hadiths."
        ),
        "source_url": "https://archive.org/details/musnad-abu-dawud",
        "source_label": "archive.org · Arabic",
        "n_hadiths": "~2,900 hadiths",
        "translation_note": (
            "No complete English translation available. Arabic text on archive.org, with "
            "Urdu translation published by traditional Indian subcontinent publishers."
        ),
    },
    {
        "slug": "humaydi",
        "title": "Musnad al-Ḥumaydī",
        "title_plain": "Musnad al-Humaydi",
        "title_short": "Musnad al-Ḥumaydī",
        "description": (
            "Compiled by Abū Bakr al-Ḥumaydī (d. 834 CE), a senior student of al-Shāfiʿī "
            "and a teacher of al-Bukhārī. Approximately 1,500 hadiths organised by companion, "
            "beginning with the Ten Promised Paradise."
        ),
        "description_plain": (
            "Compiled by Abu Bakr al-Humaydi (d. 834 CE), a student of al-Shafi'i and "
            "teacher of al-Bukhari. Approximately 1,500 hadiths, beginning with the "
            "Ten Promised Paradise."
        ),
        "source_url": "https://archive.org/details/musnad-humaidi_202108",
        "source_label": "archive.org · Arabic",
        "n_hadiths": "~1,500 hadiths",
        "translation_note": (
            "No complete English translation available. Arabic text on archive.org."
        ),
    },
]


READER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Read {title_plain} — {n_hadiths}, with external link to the full source text.">
<title>Read {title_short} — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/reader.css">
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../index.html">Home</a>
      <a href="../catalog.html">Catalog</a>
      <a href="../read.html" class="active">Read</a>
      <a href="../about.html">About</a>
      <a href="../faq.html">FAQ</a>
    </div>
  </div>
</nav>

<div class="pdf-reader-layout">

  <div class="pdf-reader-header">
    <div>
      <div class="pdf-reader-meta">{title_plain} · Secondary hadith collection</div>
      <h1>{title_short}</h1>
      <p>{description}</p>
      <p style="font-size:13px;color:var(--text-dim);margin-top:14px;"><strong>Translation note:</strong> {translation_note}</p>
    </div>
    <div class="pdf-reader-actions">
      <a href="../read-islamic.html" class="btn">← Islamic sources</a>
      <a href="{source_url}" class="btn" target="_blank" rel="noopener">Open source ↗</a>
    </div>
  </div>

  <div style="background:var(--panel); border:1px solid var(--border); padding:40px; text-align:center; margin-bottom:32px;">
    <p style="font-size:15px; color:var(--text-muted); margin-bottom:24px;">The full text of {title_plain} is hosted externally at the source linked above.<br>We do not mirror the full corpus; the catalog entries on this site reference specific hadiths by number so you can verify them against the source.</p>
    <a href="{source_url}" class="btn btn-primary" target="_blank" rel="noopener">Read {title_short} on the source site ↗</a>
    <div style="margin-top:18px; font-size:11px; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.2em;">{source_label}</div>
  </div>

</div>

<footer class="site-footer">
  {title_plain} cited under fair use / fair dealing for the purposes of criticism, review, and commentary. Verify every entry against the primary source.
</footer>

<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


CATALOG_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Filterable catalog of critical-analysis entries on {title_plain}. Filter by category or strength, search any text, share pre-filtered views.">
<title>Catalog — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../index.html">Home</a>
      <a href="../catalog.html" class="active">Catalog</a>
      <a href="../read.html">Read</a>
      <a href="../about.html">About</a>
      <a href="../faq.html">FAQ</a>
    </div>
  </div>
</nav>

<main>

  <section class="hero" style="padding: 32px 0 16px;">
    <h1 style="font-size:32px;">{title_short}</h1>
    <p class="hero-tagline" style="font-size:16px;">{description}</p>
    <div class="hero-cta">
      <a href="../catalog.html" class="btn">← Back to all sources</a>
    </div>
  </section>

  <div class="catalog-header">
    <div class="controls-row">
      <input type="search" id="search" placeholder="Search text, hadith number, keyword..." autocomplete="off" />
      <div class="stats">
        <span id="visible-count">0</span> / <span id="total-count">0</span> entries
      </div>
    </div>
    <div class="controls-row">
      <span class="controls-label">Category</span>
      <div class="filter-group">
        <span class="chip active" data-filter-type="category" data-filter-value="all">All</span>
        <span class="chip" data-filter-type="category" data-filter-value="abrogation">Abrogation</span>
        <span class="chip" data-filter-type="category" data-filter-value="scripture">Scripture Integrity</span>
        <span class="chip" data-filter-type="category" data-filter-value="contradiction">Contradictions</span>
        <span class="chip" data-filter-type="category" data-filter-value="logic">Logical Inconsistency</span>
        <span class="chip" data-filter-type="category" data-filter-value="morality">Moral Problems</span>
        <span class="chip" data-filter-type="category" data-filter-value="allah">Allah's Character</span>
        <span class="chip" data-filter-type="category" data-filter-value="cosmology">Cosmology</span>
        <span class="chip" data-filter-type="category" data-filter-value="preislamic">Pre-Islamic Borrowings</span>
        <span class="chip" data-filter-type="category" data-filter-value="magic">Magic &amp; Occult</span>
        <span class="chip" data-filter-type="category" data-filter-value="ritual">Ritual Absurdities</span>
        <span class="chip" data-filter-type="category" data-filter-value="prophet">Prophetic Character</span>
        <span class="chip" data-filter-type="category" data-filter-value="privileges">Prophetic Privileges</span>
        <span class="chip" data-filter-type="category" data-filter-value="jesus">Jesus / Christology</span>
        <span class="chip" data-filter-type="category" data-filter-value="women">Women</span>
        <span class="chip" data-filter-type="category" data-filter-value="sexual">Sexual Issues</span>
        <span class="chip" data-filter-type="category" data-filter-value="childmarriage">Child Marriage</span>
        <span class="chip" data-filter-type="category" data-filter-value="lgbtq">LGBTQ / Gender</span>
        <span class="chip" data-filter-type="category" data-filter-value="slavery">Slavery &amp; Captives</span>
        <span class="chip" data-filter-type="category" data-filter-value="hudud">Hudud</span>
        <span class="chip" data-filter-type="category" data-filter-value="warfare">Warfare &amp; Jihad</span>
        <span class="chip" data-filter-type="category" data-filter-value="apostasy">Apostasy &amp; Blasphemy</span>
        <span class="chip" data-filter-type="category" data-filter-value="governance">Governance</span>
        <span class="chip" data-filter-type="category" data-filter-value="disbelievers">Disbelievers</span>
        <span class="chip" data-filter-type="category" data-filter-value="antisemitism">Antisemitism</span>
        <span class="chip" data-filter-type="category" data-filter-value="paradise">Paradise</span>
        <span class="chip" data-filter-type="category" data-filter-value="hell">Hell</span>
        <span class="chip" data-filter-type="category" data-filter-value="eschatology">Eschatology</span>
        <span class="chip" data-filter-type="category" data-filter-value="strange">Strange / Obscure</span>
      </div>
    </div>
    <div class="controls-row">
      <span class="controls-label">Strength</span>
      <div class="filter-group">
        <span class="chip active" data-filter-type="strength" data-filter-value="all">All</span>
        <span class="chip strength-basic" data-filter-type="strength" data-filter-value="basic">Basic</span>
        <span class="chip strength-moderate" data-filter-type="strength" data-filter-value="moderate">Moderate</span>
        <span class="chip strength-strong" data-filter-type="strength" data-filter-value="strong">Strong</span>
      </div>
    </div>
  </div>

  <div id="entries-container">

    <!-- Entries are being added progressively via the 7-fold category sweep.
         Each sweep pass covers 4 categories across the entire source text. -->

    <div class="empty-state" style="padding:80px 40px; text-align:center; color:var(--text-muted);">
      <p style="font-size:16px;">This catalog is being populated via a systematic 7-fold sweep of the source text.</p>
      <p style="font-size:14px; margin-top:16px;">Entries are published as they are verified. Check back, or read the source directly via the <a href="../read/{slug}.html">Read</a> page.</p>
    </div>

  </div>

</main>

<footer class="site-footer">
  {title_plain} cited under fair use / fair dealing for the purposes of criticism, review, and commentary.
</footer>

<script src="../assets/js/app.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def build_reader(c):
    path = ROOT / "site" / "read" / f"{c['slug']}.html"
    path.write_text(READER_TEMPLATE.format(**c), encoding="utf-8")
    print(f"  wrote reader: {path.name}")


def build_catalog(c):
    path = ROOT / "site" / "catalog" / f"{c['slug']}.html"
    path.write_text(CATALOG_TEMPLATE.format(**c), encoding="utf-8")
    print(f"  wrote catalog: {path.name}")


# Patch read-islamic.html to add the secondary collections group.
def patch_read_islamic():
    path = ROOT / "site" / "read-islamic.html"
    text = path.read_text(encoding="utf-8")

    # Marker: end of the Kutub al-Sittah list (before </div> that closes read-index).
    anchor = """    <a href="read/ibn-majah.html" class="source-row">
      <span class="source-num">07</span>
      <span>
        <span class="source-title">Sunan Ibn Mājah</span>
      </span>
      <span class="source-arrow" aria-hidden="true">→</span>
    </a>

  </div>"""
    if anchor not in text:
        print("  patch_read_islamic: anchor not found (already patched?)")
        return

    # Build the insertion block: a new group label + 5 rows (08-12).
    rows = []
    for i, c in enumerate(COLLECTIONS, start=8):
        rows.append(f"""    <a href="read/{c['slug']}.html" class="source-row">
      <span class="source-num">{i:02d}</span>
      <span>
        <span class="source-title">{c['title']}</span>
        <span class="source-partial">{c['n_hadiths']}</span>
      </span>
      <span class="source-arrow" aria-hidden="true">→</span>
    </a>""")
    rows_html = "\n\n".join(rows)

    replacement = anchor.replace(
        "  </div>",
        f"""    <span class="read-group-label">Secondary collections · beyond the Kutub al-Sittah</span>

{rows_html}

  </div>"""
    )
    text = text.replace(anchor, replacement)

    # Also update the hero tagline from "seven books" to acknowledge the expansion.
    text = text.replace(
        "grounded in one of these seven books",
        "grounded in one of the primary twelve collections",
    )

    path.write_text(text, encoding="utf-8")
    print("  patched: read-islamic.html")


# Patch catalog.html to add the secondary collections section.
def patch_catalog():
    path = ROOT / "site" / "catalog.html"
    text = path.read_text(encoding="utf-8")

    anchor = """      <a href="catalog/ibn-majah.html" class="card">
        <h3>Sunan Ibn Majah</h3>
        <p>Compiled by Ibn Majah (d. 887 CE). The last-added of the six canonical collections; contains some hadiths not found in the others. About 4,340 reports.</p>
        <span class="count">159 entries</span>
      </a>

    </div>
  </section>"""
    if anchor not in text:
        print("  patch_catalog: anchor not found (already patched?)")
        return

    cards = []
    for c in COLLECTIONS:
        cards.append(f"""      <a href="catalog/{c['slug']}.html" class="card">
        <h3>{c['title_plain']}</h3>
        <p>{c['description_plain']}</p>
        <span class="count">sweep in progress</span>
      </a>""")
    cards_html = "\n\n".join(cards)

    insertion = f"""

  <section>
    <div class="section-title">Secondary collections · beyond the Kutub al-Sittah</div>
    <p style="font-size:14px; color:var(--text-muted); margin-bottom:20px; max-width:720px;">Five additional early Sunnī hadith compilations — the large <em>Musnad</em> of Imam Aḥmad, the thematic <em>Sunan</em> of al-Dārimī, and three early <em>musnad</em>-style collections by al-Shāfiʿī, al-Ṭayālisī, and al-Ḥumaydī. These are not part of the Kutub al-Sittah but are widely cited in classical Sunnī scholarship. Their catalogs are being built via a systematic 7-fold category sweep.</p>
    <div class="card-grid">

{cards_html}

    </div>
  </section>"""

    text = text.replace(anchor, anchor + insertion)
    path.write_text(text, encoding="utf-8")
    print("  patched: catalog.html")


def main():
    print("Building reader pages...")
    for c in COLLECTIONS:
        build_reader(c)

    print("\nBuilding catalog pages...")
    for c in COLLECTIONS:
        build_catalog(c)

    print("\nPatching index pages...")
    patch_read_islamic()
    patch_catalog()

    print("\nDone.")


if __name__ == "__main__":
    main()

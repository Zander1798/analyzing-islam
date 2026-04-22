#!/usr/bin/env python3
"""Build 28 category pages under site/category/<slug>.html.

Each page pulls all <div class="entry" data-category="... {token} ..."> entries
from the four existing source catalogs (quran, bukhari, muslim, abu-dawud).
No filter UI — just the category name, its short description, a back button,
and the matching entries stacked top-to-bottom.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SITE = ROOT / "site"
CATALOG_DIR = SITE / "catalog"
OUT_DIR = SITE / "category"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (token, display_name, short_description)
CATEGORIES = [
    ("abrogation",    "Abrogation",
     "Verses that cancel or override earlier verses. The doctrine of <em>naskh</em> and its philosophical problems."),
    ("scripture",     "Scripture Integrity",
     '"Lost" verses, abrogated-in-text material, Uthman\'s variant-burning, preservation claims vs <em>tahrif</em>.'),
    ("contradiction", "Contradictions",
     "Verses and hadiths that directly contradict other verses and hadiths. The Quran's own self-test (4:82) fails."),
    ("logic",         "Logical Inconsistency",
     "Internal logical problems. The Islamic Dilemma. Claims of clarity that require extensive interpretation."),
    ("morality",      "Moral Problems",
     "Fatalism vs responsibility, collective punishment, eternal disproportion, the <em>fitra</em> paradox, pre-Islamic damnation."),
    ("allah",         "Allah's Character",
     'Anthropomorphism (foot, throne, descent), "best of deceivers," sealed hearts, mercy in 100 parts.'),
    ("cosmology",     "Cosmology",
     "Sun prostrating under the Throne, seven heavens, flat-earth imagery, 60-cubit Adam, the moon split."),
    ("preislamic",    "Pre-Islamic Borrowings",
     "Dajjal from Christian apocalyptic, Buraq, Sleepers of Ephesus, Abraham in fire, camel through the needle's eye."),
    ("magic",         "Magic &amp; Occult",
     "Evil eye, <em>ruqya</em>, jinn possession, Satan, cursed tattoos, the Prophet bewitched by a Jewish sorcerer."),
    ("ritual",        "Ritual Absurdities",
     "Dog-saliva seven washes, left/right-hand rules, yawn from Satan, Zamzam standing vs sitting, spit three times."),
    ("prophet",       "Prophetic Character",
     "Muhammad's conduct as depicted in Quran and hadith: marriages, warfare, personal dealings, unremorseful violence."),
    ("privileges",    "Prophetic Privileges",
     "More than four wives, <em>hiba</em> women, Zaynab authorization, honey affair, revelation-on-demand patterns."),
    ("jesus",         "Jesus / Christology",
     "The Quran's denial of the crucifixion, its portrait of Mary, misunderstanding of the Trinity, apocryphal borrowings."),
    ("women",         "Women",
     'Inheritance, testimony, veiling, beating, polygamy, <em>mahram</em>, "deficient in intellect and religion."'),
    ("sexual",        "Sexual Issues",
     'Mut\'ah, adult breastfeeding, azl with captives, thighing, "virgin\'s silence is consent," nine-wives-in-one-night.'),
    ("childmarriage", "Child Marriage",
     'Aisha at six and nine, "father may marry off a daughter not fully grown," Quran 65:4, dolls and playmates.'),
    ("lgbtq",         "LGBTQ / Gender",
     '"Kill the active and passive partner," Lot verses, men-imitating-women cursed, <em>mukhannath</em> exile, eunuchs.'),
    ("slavery",       "Slavery &amp; Captives",
     '"Right hand possesses," Safiyya, Mariyah, Awtas, the eight Abu Dawud chapters on captives, pregnant-slave rules.'),
    ("hudud",         "Hudud",
     "Stoning, hand amputation, 40 or 80 lashes for wine, alternate-side amputation, the pit for stoning, Ma'iz, Ghamid."),
    ("warfare",       "Warfare &amp; Jihad",
     'Banu Qurayza massacre, night raids, Ka\'b assassination, "strike the necks," Khaybar, "victorious with terror."'),
    ("apostasy",      "Apostasy &amp; Blasphemy",
     '"Kill whoever changes his religion," blood-in-three-cases, Ali burning apostates, death for insulting the Prophet.'),
    ("governance",    "Governance",
     'Twelve Quraysh caliphs, <em>dhimmi</em> rules, <em>jizya</em> humiliation, "land belongs to Allah and His Messenger."'),
    ("disbelievers",  "Disbelievers",
     "Polemic, exclusion, hostility toward non-Muslims broadly — curses, unclean status, the Sword Verse logic."),
    ("antisemitism",  "Antisemitism",
     "Gharqad hadith, Jews as apes and pigs, Ezra slander, expel-the-Jews, Isfahan Jews follow the Dajjal."),
    ("paradise",      "Paradise",
     "Houris, hollow-pearl tents 60 miles wide, rivers of wine, food becomes musk sweat, no excretion."),
    ("hell",          "Hell",
     "Skin roasted and replaced, molar the size of Mount Uhud, 999-out-of-1000 damned, women's hell-majority."),
    ("eschatology",   "Eschatology",
     "Dajjal, Gog and Magog, end-times signs, sun rising from the west, Ka'ba destroyed by an Abyssinian."),
    ("strange",       "Strange / Obscure",
     "Talking ants, sleepers for 300 years, worm eats Solomon's staff, apes and pigs, genuinely bizarre passages."),
    ("incest",        "Incest",
     "Zaynab bint Jahsh (adopted son's wife), adult breastfeeding as a kinship workaround, the Salim ruling, milk-mother rules weaponized."),
    ("gross-vile",    "Gross / Vile",
     "Camel urine as medicine, dip the fly in your drink, dog-saliva seven washes, menstrual-sex rules, paradise-sweat-is-musk, bestiality, masturbation, anal-sex curses."),
]

CATALOG_FILES = [
    ("quran.html",     "Quran"),
    ("bukhari.html",   "Sahih al-Bukhari"),
    ("muslim.html",    "Sahih Muslim"),
    ("abu-dawud.html", "Sunan Abi Dawud"),
    ("tirmidhi.html",  "Jami' at-Tirmidhi"),
    ("nasai.html",     "Sunan an-Nasa'i"),
    ("ibn-majah.html", "Sunan Ibn Majah"),
]

# Match each <div class="entry" ...>...</div class="entry"> block.
# Entries are flat (one level deep in entries-container), no nesting — so a
# greedy match up to the matching "</div>\n</div>" pattern works. But entries
# contain <section>...</section> and nested divs… use a proper match with a
# stack? Actually the existing entries have this structure:
#   <div class="entry" data-...>
#     <div class="entry-header">...</div>
#     <section>...</section>
#   </div>
# So each entry has exactly: outer div containing one header div and one
# section. Total nesting depth of 2 inside. Let me use a regex that matches
# "<div class=\"entry\"[^>]*>" through to the matching "</div>" that closes it.
# Simplest: find each "<div class=\"entry\"" and walk balanced braces.

ENTRY_START_RE = re.compile(r'<div class="entry"[^>]*data-category="([^"]+)"[^>]*>')


def extract_entries(html: str, source_label: str):
    """Return list of (categories_set, entry_html) tuples.
    Walks the HTML, finds each <div class="entry" ...>, tracks div nesting
    depth to capture the full block, and returns the raw HTML.
    """
    results = []
    i = 0
    while True:
        m = ENTRY_START_RE.search(html, i)
        if not m:
            break
        cats = set(m.group(1).split())
        start = m.start()
        # Walk forward counting <div> opens/closes.
        depth = 1
        j = m.end()
        while depth > 0 and j < len(html):
            next_open = html.find("<div", j)
            next_close = html.find("</div>", j)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                j = next_open + len("<div")
            else:
                depth -= 1
                j = next_close + len("</div>")
        entry_html = html[start:j]
        results.append((cats, entry_html, source_label))
        i = j
    return results


# Gather all entries from all catalog files.
all_entries = []  # list of (cats_set, html, source)
for fname, label in CATALOG_FILES:
    path = CATALOG_DIR / fname
    if not path.exists():
        print(f"WARN: {path} missing, skipping")
        continue
    html = path.read_text(encoding="utf-8")
    entries = extract_entries(html, label)
    all_entries.extend(entries)
    print(f"  {fname}: {len(entries)} entries extracted")

print(f"Total entries across all catalogs: {len(all_entries)}")


# Build each category page.
def build_page(token: str, name: str, desc: str, entries_html: list, total: int):
    entries_block = "\n\n".join(entries_html)
    return PAGE_TEMPLATE.format(
        title=name,
        title_plain=re.sub(r"<[^>]+>", "", name),
        description=desc,
        entries=entries_block,
        total=total,
    )


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{title_plain} — all entries in this category from the Analyzing Islam catalog.">
<title>{title_plain} — Analyzing Islam</title>
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="../index.html" class="active">Home</a>
      <a href="../catalog.html">Catalog</a>
      <a href="../read.html">Read</a>
      <a href="../about.html">About</a>
      <a href="../faq.html">FAQ</a>
    </div>
  </div>
</nav>

<main>

  <section class="hero" style="padding: 40px 0 24px;">
    <h1 style="font-size:44px;">{title}</h1>
    <p class="hero-tagline">{description}</p>
    <div class="hero-cta">
      <a href="../index.html" class="btn">← Back to home</a>
    </div>
  </section>

  <section>
    <div class="section-title">{total} entr{plural} in this category</div>
    <div id="entries-container">

{entries}

    </div>
  </section>

</main>

<footer class="site-footer">
  Every entry references a specific passage — verify before citing.
</footer>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="../assets/js/config.js"></script>
<script src="../assets/js/auth.js" defer></script>
<script src="../assets/js/auth-ui.js" defer></script>
<script src="../assets/js/bookmarks.js" defer></script>
<script src="../assets/js/entry-actions.js" defer></script>
<script src="../assets/js/goat.js" defer></script>
</body>
</html>
"""


def main():
    counts = {}
    for token, name, desc in CATEGORIES:
        matched = [h for cats, h, src in all_entries if token in cats]
        counts[token] = len(matched)
        total = len(matched)
        plural = "y" if total == 1 else "ies"
        html = PAGE_TEMPLATE.format(
            title=name,
            title_plain=re.sub(r"<[^>]+>", "", name).replace("&amp;", "&"),
            description=desc,
            entries="\n\n".join(matched) if matched else '<div class="empty">No entries in this category yet.</div>',
            total=total,
            plural=plural,
        )
        out = OUT_DIR / f"{token}.html"
        out.write_text(html, encoding="utf-8")
        print(f"  Wrote {out.name}: {total} entries")

    print(f"\nGenerated {len(CATEGORIES)} category pages in {OUT_DIR}")


if __name__ == "__main__":
    main()

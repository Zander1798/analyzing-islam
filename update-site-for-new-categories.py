#!/usr/bin/env python3
"""After adding the Incest + Gross/Vile categories, propagate the
changes across the site:

  1. Homepage index.html:
     - stat-card "28" -> "30" and meta description "28 categories" -> "30".
     - Update every "Browse by category" card count to reflect the
       recomputed counts from site/category/<slug>.html.
     - Append two new cards (Incest, Gross/Vile) to the grid.
     - Update total entries stat-card from the rebuild total.
  2. About page: "twenty-eight categories" -> "thirty categories".
     Add two <li> entries for Incest + Gross/Vile in the category list.
  3. FAQ: replace "twenty-eight" with "thirty" where used.
  4. Every catalog HTML file: append two <span class="chip"> entries
     for Incest + Gross/Vile next to the existing category chips.

Idempotent — rerunning is safe.
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


# Category definitions (kept in sync with build-category-pages.py)
NEW_CATS = [
    ("incest", "Incest",
     "Zaynab bint Jahsh (adopted son's wife), adult breastfeeding as a kinship workaround, the Salim ruling, milk-mother rules weaponized."),
    ("gross-vile", "Gross / Vile",
     "Camel urine as medicine, dip the fly in your drink, dog-saliva seven washes, menstrual-sex rules, paradise-sweat-is-musk, bestiality, masturbation, anal-sex curses."),
]

# slug -> (display_name, short_description) for all 30, in the order the
# homepage currently displays them. Used to rewrite the whole grid.
ALL_CATS_ORDER = [
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
     "Sun prostrating under the Throne, seven heavens, flat-earth imagery, 60-cubit Adam, moon split."),
    ("preislamic",    "Pre-Islamic Borrowings",
     "Dajjal from Christian apocalyptic, Buraq, Sleepers of Ephesus, Abraham in fire, camel through needle's eye."),
    ("magic",         "Magic &amp; Occult",
     "Evil eye, <em>ruqya</em>, jinn possession, Satan, tattoos cursed, the Prophet bewitched by a Jewish sorcerer."),
    ("ritual",        "Ritual Absurdities",
     "Dog-saliva seven washes, left/right-hand rules, yawn from Satan, Zamzam standing vs sitting, spit three times."),
    ("prophet",       "Prophetic Character",
     "Muhammad's conduct — marriages, warfare, personal dealings, unremorseful violence, immoral actions."),
    ("privileges",    "Prophetic Privileges",
     "More than four wives, <em>hiba</em> women, Zaynab authorization, honey affair, revelation-on-demand patterns."),
    ("jesus",         "Jesus / Christology",
     "The Quran's denial of the crucifixion, its portrait of Mary, misunderstanding of the Trinity, apocryphal borrowings."),
    ("women",         "Women",
     'Inheritance, testimony, veiling, beating, polygamy, <em>mahram</em>, "deficient in intellect and religion."'),
    ("sexual",        "Sexual Issues",
     'Mut\'ah, adult breastfeeding, azl with captives, thighing, "virgin\'s silence is consent," 9-wives-in-one-night.'),
    ("childmarriage", "Child Marriage",
     'Aisha at six and nine, "father may marry off a daughter not fully grown," Quran 65:4, dolls and playmates.'),
    ("lgbtq",         "LGBTQ / Gender",
     '"Kill the active and passive partner," Lot verses, men-imitating-women cursed, <em>mukhannath</em> exile, eunuchs.'),
    ("slavery",       "Slavery &amp; Captives",
     '"Right hand possesses," Safiyya, Mariyah, Awtas, 8 Abu Dawud chapters on captives, pregnant-slave rules.'),
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


# ---------- Counting ----------

def count_entries_per_category() -> dict[str, int]:
    """Read each site/category/<slug>.html and count <div class="entry">."""
    counts = {}
    for slug, _name, _desc in ALL_CATS_ORDER:
        p = SITE / "category" / f"{slug}.html"
        if not p.exists():
            counts[slug] = 0
            continue
        counts[slug] = p.read_text(encoding="utf-8").count('class="entry"')
    return counts


def count_total_entries() -> int:
    """Total unique entries across all 7 catalog files."""
    total = 0
    for f in ["quran.html", "bukhari.html", "muslim.html", "abu-dawud.html",
              "tirmidhi.html", "nasai.html", "ibn-majah.html"]:
        p = SITE / "catalog" / f
        total += p.read_text(encoding="utf-8").count('class="entry"')
    return total


# ---------- Homepage ----------

def rewrite_homepage(counts: dict[str, int], total: int) -> None:
    path = SITE / "index.html"
    text = path.read_text(encoding="utf-8")

    # stat-card: "1,501" total entries -> recomputed
    text = re.sub(
        r'(<span class="number">)[\d,]+(</span>\s*</div>\s*<div class="stat-card">\s*<span class="number">)28(</span>)',
        lambda m: f'{m.group(1)}{total:,}{m.group(2)}30{m.group(3)}',
        text,
        count=1,
    )
    # Meta description "28 categories" -> 30
    text = text.replace("1,501 curated entries across 28 categories",
                        f"{total:,} curated entries across 30 categories")

    # Rebuild the entire "Browse by category" card grid so counts and
    # membership are consistent.
    new_cards = []
    for slug, name, desc in ALL_CATS_ORDER:
        c = counts.get(slug, 0)
        new_cards.append(
            f'      <a href="category/{slug}.html" class="card">\n'
            f'        <h3>{name}</h3>\n'
            f'        <p>{desc}</p>\n'
            f'        <span class="count">{c} entries</span>\n'
            f'      </a>'
        )
    new_grid = "\n".join(new_cards)

    # Find the <section> that contains "Browse by category" and replace
    # its card-grid content.
    section_re = re.compile(
        r'(<section>\s*<h2>Browse by category</h2>\s*<div class="card-grid">\s*)'
        r'.*?'
        r'(\s*</div>\s*</section>)',
        re.DOTALL,
    )
    text, n = section_re.subn(r'\1' + new_grid + r'\2', text, count=1)
    if n != 1:
        print("  WARN: 'Browse by category' section not found/replaced.")

    path.write_text(text, encoding="utf-8")
    print(f"  index.html: rewrote stats + all {len(ALL_CATS_ORDER)} category cards.")


# ---------- About ----------

def update_about() -> None:
    path = SITE / "about.html"
    text = path.read_text(encoding="utf-8")
    # "twenty-eight" -> "thirty" (two forms: "twenty-eight categories" and "twenty-eight")
    text = re.sub(r"twenty-eight categories", "thirty categories", text)
    text = re.sub(r"\btwenty-eight\b", "thirty", text)
    # Add the two new <li> items to the list of categories, if not already present.
    if "<strong>Incest</strong>" not in text:
        insertion = (
            '    <li><strong>Incest</strong> — Zaynab bint Jahsh (adopted son\'s wife), adult breastfeeding as a kinship workaround, the Salim ruling.</li>\n'
            '    <li><strong>Gross / Vile</strong> — camel urine as medicine, dip the fly in your drink, dog-saliva seven washes, menstrual-sex rules, paradise-sweat-is-musk.</li>\n'
        )
        # Insert before the closing </ul> of the Strange category (the last
        # existing <li>... Strange / Obscure ... </li>).
        text = re.sub(
            r'(<li><strong>Strange(?: / Obscure|/Obscure)?</strong>[^<]*(?:<em>[^<]*</em>[^<]*)*</li>\s*)(</ul>)',
            r'\1' + insertion + r'\2',
            text,
            count=1,
        )
    path.write_text(text, encoding="utf-8")
    print("  about.html: updated category count and list.")


# ---------- FAQ ----------

def update_faq() -> None:
    path = SITE / "faq.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"twenty-eight topical categories", "thirty topical categories", text)
    text = re.sub(r"\btwenty-eight\b", "thirty", text)
    text = re.sub(r"across 28 categories", "across 30 categories", text)
    path.write_text(text, encoding="utf-8")
    print("  faq.html: updated count wording.")


# ---------- Catalog chips ----------

def add_catalog_chips() -> None:
    """Append the two new chips next to the existing category chips in every
    catalog HTML file, if not already present."""
    new_chip_incest = '<span class="chip" data-filter-type="category" data-filter-value="incest">Incest</span>'
    new_chip_gross  = '<span class="chip" data-filter-type="category" data-filter-value="gross-vile">Gross / Vile</span>'

    for f in ["quran.html", "bukhari.html", "muslim.html", "abu-dawud.html",
              "tirmidhi.html", "nasai.html", "ibn-majah.html"]:
        path = SITE / "catalog" / f
        text = path.read_text(encoding="utf-8")
        changed = False

        # Only add chips if the catalog actually has at least one entry with
        # that category — so we don't show filters that match zero rows.
        has_incest = 'data-category="[^"]*\\bincest\\b'
        has_gross  = 'data-category="[^"]*\\bgross-vile\\b'

        need_incest = (
            re.search(r'data-category="[^"]*\bincest\b', text) is not None
            and 'data-filter-value="incest"' not in text
        )
        need_gross = (
            re.search(r'data-category="[^"]*\bgross-vile\b', text) is not None
            and 'data-filter-value="gross-vile"' not in text
        )

        # Insert before the <!-- next filter-group --> or before </div> of filter-group
        # — use the last existing chip as anchor.
        # Look for the filter-group containing category chips and insert before its </div>.
        def insert_before_group_close(text: str, new_chip: str) -> str:
            # Find the group that contains a category chip, then its closing </div>.
            # Pattern: category chip ... whitespace </div> closing filter-group.
            pat = re.compile(
                r'(<span class="chip"[^>]*data-filter-type="category"[^<]*</span>\s*)'
                r'(</div>)',
                re.DOTALL,
            )
            # Replace the LAST occurrence by anchoring to the final chip before </div>.
            # We'll match greedy on the LAST category chip adjacent to </div>.
            # Simplest: replace the first " </div>" that *follows* all category chips.
            # A unique marker is "</span>\n        </div>" after category chips.
            # Fallback: plain replace via reversed match.
            matches = list(pat.finditer(text))
            if not matches:
                return text
            last = matches[-1]
            indent = "        "
            insertion = f"\n{indent}{new_chip}"
            return text[:last.end(1)] + insertion + text[last.end(1):]

        if need_incest:
            text = insert_before_group_close(text, new_chip_incest)
            changed = True
        if need_gross:
            text = insert_before_group_close(text, new_chip_gross)
            changed = True

        if changed:
            path.write_text(text, encoding="utf-8")
            print(f"  {f}: added chips (incest={need_incest}, gross-vile={need_gross}).")


# ---------- Main ----------

def main() -> None:
    counts = count_entries_per_category()
    total  = count_total_entries()
    print(f"Total entries across 7 catalogs: {total}")
    print(f"Counts loaded for {len(counts)} categories.")
    rewrite_homepage(counts, total)
    update_about()
    update_faq()
    add_catalog_chips()
    print("\nDone.")


if __name__ == "__main__":
    main()

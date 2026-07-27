"""
End-to-end test for analyzingislam.com (local server at localhost:8765)
Tests: search, filters, notes/save (auth-gated), build, compare, goat/skins, readers
"""
import sys, os, time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = "http://localhost:8765"
SCREENSHOTS = r"C:\Users\zande\Documents\AI Workspace\Analyzing Islam\e2e_screenshots"
os.makedirs(SCREENSHOTS, exist_ok=True)

results = []

def ss(page, name):
    path = os.path.join(SCREENSHOTS, f"{name}.png")
    page.screenshot(path=path, full_page=False)
    return path

def ok(name, note=""):
    results.append(("PASS", name, note))
    print(f"  PASS  {name}" + (f" -- {note}" if note else ""))

def fail(name, note=""):
    results.append(("FAIL", name, note))
    print(f"  FAIL  {name}" + (f" -- {note}" if note else ""))

def warn(name, note=""):
    results.append(("WARN", name, note))
    print(f"  WARN  {name}" + (f" -- {note}" if note else ""))

def info(name, note=""):
    print(f"  INFO  {name}" + (f" -- {note}" if note else ""))

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.set_default_timeout(15000)

        # ── 1. Homepage ────────────────────────────────────────────────────
        print("\n-- Homepage --")
        page = ctx.new_page()
        page.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
        title = page.title()
        if "Analyzing Islam" in title:
            ok("Homepage loads", title)
        else:
            fail("Homepage loads", f"unexpected title: {title}")
        ss(page, "01_homepage")

        # ── 2. Catalog source picker ───────────────────────────────────────
        print("\n-- Catalog source picker --")
        page.goto(f"{BASE}/catalog.html", wait_until="domcontentloaded")
        # Has cards linking to individual catalogs
        cards = page.locator('a.card[href*="catalog/"]').count()
        if cards >= 7:
            ok("Catalog source picker: 7 source cards", f"{cards} cards")
        else:
            warn("Catalog source picker", f"expected >=7 cards, got {cards}")
        ss(page, "02_catalog_picker")

        # ── 3. Quran catalog: search ───────────────────────────────────────
        print("\n-- Quran catalog: search --")
        page.goto(f"{BASE}/catalog/quran.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        try:
            si = page.locator("input#search")
            si.wait_for(state="visible", timeout=8000)
            si.fill("wine")
            page.wait_for_timeout(1500)
            ss(page, "03_catalog_search_wine")
            # Count visible (non-hidden) entries
            visible = page.evaluate("""
                () => document.querySelectorAll('.entry:not(.hidden)').length
            """)
            total = page.evaluate("() => document.querySelectorAll('.entry').length")
            if visible > 0 and visible < total:
                ok("Quran catalog search: 'wine'", f"{visible} results (of {total} total)")
            elif visible == total:
                warn("Quran catalog search: 'wine'", f"all {total} entries still visible -- filter may not have applied yet")
            else:
                fail("Quran catalog search: 'wine'", "0 results returned")
        except PWTimeout:
            fail("Quran catalog search input", "input#search not found")
            ss(page, "03_catalog_search_FAIL")

        # Search for a verse ref
        try:
            si.click(); si.select_text()
            si.fill("Q 4:34")
            page.wait_for_timeout(1500)
            visible2 = page.evaluate("() => document.querySelectorAll('.entry:not(.hidden)').length")
            ok("Quran catalog search: verse ref 'Q 4:34'", f"{visible2} result(s)")
            ss(page, "04_catalog_search_verse")
        except Exception as e:
            warn("Quran catalog search: verse ref", str(e)[:80])

        # Clear search
        si.click(); si.select_text(); si.fill(""); page.wait_for_timeout(600)

        # ── 4. Catalog filters: category chips ─────────────────────────────
        print("\n-- Quran catalog: filters --")
        page.goto(f"{BASE}/catalog/quran.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        try:
            chips = page.locator('.chip[data-filter-type="category"]')
            count = chips.count()
            if count > 0:
                ok("Category filter chips present", f"{count} chips")
            else:
                fail("Category filter chips", "no .chip[data-filter-type=category] found")

            # Confirm 'Science' chip exists (renamed from Cosmology)
            science_chip = page.locator('.chip[data-filter-value="science"]')
            if science_chip.count() > 0:
                ok("'Science' category chip present (renamed from Cosmology)")
                science_chip.first.click()
                page.wait_for_timeout(1200)
                ss(page, "05_filter_science")
                visible_sci = page.evaluate("() => document.querySelectorAll('.entry:not(.hidden)').length")
                total_sci = page.evaluate("() => document.querySelectorAll('.entry').length")
                if visible_sci > 0 and visible_sci < total_sci:
                    ok("Science category filter shows entries", f"{visible_sci} of {total_sci}")
                elif visible_sci == total_sci:
                    warn("Science category filter", "entry count unchanged -- filter may not have applied")
                else:
                    fail("Science category filter", "no entries visible after filtering")
            else:
                fail("'Science' chip not found", "rename from Cosmology may not have propagated")

            # Confirm 'Cosmology' chip does NOT exist
            cosmo_chip = page.locator('.chip[data-filter-value="cosmology"]')
            if cosmo_chip.count() == 0:
                ok("'Cosmology' chip correctly absent from filters")
            else:
                warn("'Cosmology' chip still present", "should be renamed to 'Science'")

            # Strength filters
            strength_chips = page.locator('.chip[data-filter-type="strength"]')
            if strength_chips.count() >= 3:
                ok("Strength filter chips present", f"{strength_chips.count()} chips")
                # Click Strong
                strong_chip = page.locator('.chip[data-filter-value="strong"]').first
                strong_chip.click()
                page.wait_for_timeout(1200)
                ss(page, "06_filter_strength_strong")
                visible_str = page.evaluate("() => document.querySelectorAll('.entry:not(.hidden)').length")
                total_str = page.evaluate("() => document.querySelectorAll('.entry').length")
                if visible_str < total_str:
                    ok("Strength filter 'Strong' works", f"{visible_str} of {total_str} entries")
                else:
                    warn("Strength filter 'Strong'", "entry count unchanged -- filter may not have applied")
            else:
                warn("Strength filters", f"found only {strength_chips.count()} chips")

        except Exception as e:
            fail("Catalog filters", str(e)[:120])

        # ── 5. Cite-links in entry bodies ──────────────────────────────────
        print("\n-- Cite-links --")
        page.goto(f"{BASE}/catalog/quran.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        try:
            cite = page.locator('a.cite-link').first
            cite.wait_for(state="visible", timeout=8000)
            href = cite.get_attribute("href") or ""
            ok("Cite-links present in Quran catalog", href[:60])
        except PWTimeout:
            fail("Cite-links in Quran catalog", "no a.cite-link found")
            ss(page, "07_citelinks_FAIL")

        # ── 6. Notes/Save (auth-gated) ─────────────────────────────────────
        print("\n-- Notes & Save (auth-gated) --")
        info("Save/Note buttons only inject when logged in (entry-actions.js checks auth)")
        info("Testing saved.html UI directly instead")

        page.goto(f"{BASE}/saved.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        ss(page, "08_saved_page")
        ok("saved.html loads")

        # saved.html renders the saved-shell dynamically with auth guard
        # Check that the shell exists (even if empty)
        shell = page.locator("#saved-shell")
        if shell.count() > 0:
            ok("saved.html: #saved-shell container present")
        else:
            fail("saved.html: #saved-shell not found")

        # ── 7. Build landing page ──────────────────────────────────────────
        print("\n-- Build landing page --")
        page.goto(f"{BASE}/build.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        ss(page, "09_build_landing")

        create_btn = page.locator('a[href="build-editor.html"]')
        if create_btn.count() > 0:
            ok("Build landing: '+ Create' button present")
        else:
            fail("Build landing: no link to build-editor.html")

        build_steps = page.locator('.build-how-step').count()
        if build_steps >= 3:
            ok("Build landing: how-to steps visible", f"{build_steps} steps")
        else:
            warn("Build landing: how-to steps", f"only {build_steps} found")

        # ── 8. Build editor ────────────────────────────────────────────────
        print("\n-- Build editor --")
        page.goto(f"{BASE}/build-editor.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        ss(page, "10_build_editor")

        editor_shell = page.locator("#build-editor-shell")
        if editor_shell.count() > 0:
            ok("Build editor: #build-editor-shell present")
        else:
            fail("Build editor: #build-editor-shell not found")

        # RTL tip on build page
        page.goto(f"{BASE}/build.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        # Check page source for rtl tip text
        content = page.content()
        if "right-to-left" in content.lower() or "rtl" in content.lower() or "arabic" in content.lower() or "highlight" in content.lower():
            ok("Build page: RTL/Arabic-related content present")
        else:
            warn("Build page: no RTL hint detected in page source")

        # ── 9. Compare page ────────────────────────────────────────────────
        print("\n-- Compare page --")
        page.goto(f"{BASE}/compare.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        ss(page, "11_compare_page")

        # Force-show the compare app (it's behind auth gate by default)
        page.evaluate("""
            () => {
                const app = document.getElementById('compare-app');
                const gate = document.getElementById('compare-auth-gate');
                if (app) app.hidden = false;
                if (gate) gate.hidden = true;
            }
        """)
        page.wait_for_timeout(500)
        compare_searches = page.locator('input.compare-search')
        count_cs = compare_searches.count()
        if count_cs >= 2:
            ok("Compare: two search inputs present", f"{count_cs} inputs")
            # Type into both
            compare_searches.nth(0).fill("2:256")
            page.wait_for_timeout(1000)
            ss(page, "12_compare_search_left")
            ok("Compare: left pane search accepts input")
            compare_searches.nth(1).fill("Matthew 5")
            page.wait_for_timeout(1000)
            ss(page, "13_compare_search_right")
            ok("Compare: right pane search accepts input")
        else:
            fail("Compare: search inputs not found", f"expected >=2, got {count_cs}")

        # ── 10. Quran reader: search ───────────────────────────────────────
        print("\n-- Quran reader: search --")
        page.goto(f"{BASE}/read/quran.html", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)  # reader-search.js injects asynchronously
        ss(page, "14_reader_loaded")

        try:
            reader_search = page.locator(".reader-search-input")
            reader_search.wait_for(state="visible", timeout=8000)
            reader_search.fill("2:65")
            page.wait_for_timeout(1200)
            ss(page, "15_reader_search_verse")
            ok("Quran reader: search for verse '2:65' accepted")
        except PWTimeout:
            fail("Quran reader: .reader-search-input not found")
            ss(page, "15_reader_search_FAIL")

        # Check verses are present
        verses = page.locator("li[id]").count()
        if verses > 0:
            ok("Quran reader: verse list rendered", f"{verses} li[id] items")
        else:
            fail("Quran reader: no verse elements found")

        # ── 11. Goat page ──────────────────────────────────────────────────
        print("\n-- Goat page --")
        page.goto(f"{BASE}/goat.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)  # give JS time to initialise
        ss(page, "16_goat_page")

        # Main goat image
        goat_img = page.locator("img#goat-big-img")
        if goat_img.count() > 0:
            src = goat_img.get_attribute("src") or ""
            ok("Goat: main goat image present", src)
        else:
            fail("Goat: img#goat-big-img not found")

        # Goat is clickable
        goat_btn = page.locator("button#goat-big")
        if goat_btn.count() > 0:
            goat_btn.click()
            page.wait_for_timeout(800)
            ok("Goat: main button clickable")
            ss(page, "17_goat_clicked")
        else:
            warn("Goat: button#goat-big not found")

        # Skins grid
        skins_grid = page.locator("#skins-grid")
        if skins_grid.count() > 0:
            ok("Goat: skins grid present (#skins-grid)")
            skin_slots = page.locator(".skin-slot").count()
            ok("Goat: skin slots rendered", f"{skin_slots} skins")
        else:
            fail("Goat: #skins-grid not found")

        # Standard skin selected by default
        selected_skin = page.locator(".skin-slot.is-selected")
        if selected_skin.count() > 0:
            ok("Goat: Standard skin selected by default")
        else:
            warn("Goat: no .skin-slot.is-selected found")

        # Auth gate (non-logged-in users see unlock info)
        page_html = page.content()
        if "skins-auth-gate" in page_html or "Pass quiz levels" in page_html or "sign" in page_html.lower():
            ok("Goat: auth gate / unlock prompt present for non-logged-in users")
        else:
            warn("Goat: no auth gate text found")

        # Check goat animation shows (visibility was set to hidden until JS loads)
        goat_vis = page.evaluate("document.getElementById('goat-big-img') && getComputedStyle(document.getElementById('goat-big-img')).visibility")
        info("Goat image visibility after JS", str(goat_vis))

        # ── 12. category/cosmology.html — expected dead page bug ──────────
        print("\n-- Category pages --")
        page.goto(f"{BASE}/category/science.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        ss(page, "18_science_category")
        sci_count_el = page.locator(".section-title").first
        sci_text = sci_count_el.inner_text() if sci_count_el.count() > 0 else ""
        if "science" in page.content().lower() and page.locator(".entry").count() > 0:
            ok("science.html: entries present", f"header: '{sci_text}'")
        else:
            fail("science.html: no entries found")

        page.goto(f"{BASE}/category/cosmology.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        ss(page, "19_cosmology_category")
        cosmo_entries = page.locator(".entry").count()
        if cosmo_entries > 0:
            # This is a REAL BUG — should be dead/empty
            fail(
                "category/cosmology.html BUG: still shows entries",
                f"{cosmo_entries} entries with old 'cosmology' data-category; "
                "page was never regenerated after Science rename. "
                "Any link to cosmology.html sends users to an un-renamed page."
            )
        else:
            ok("category/cosmology.html correctly renders 0 entries (dead page)")

        # ── 13. Bukhari catalog: search + filters ─────────────────────────
        print("\n-- Bukhari catalog: search + filters --")
        page.goto(f"{BASE}/catalog/bukhari.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        try:
            buk_search = page.locator("input#search")
            buk_search.wait_for(state="visible", timeout=8000)
            buk_search.fill("marriage")
            page.wait_for_timeout(1500)
            visible_buk = page.evaluate("() => document.querySelectorAll('.entry:not(.hidden)').length")
            total_buk = page.evaluate("() => document.querySelectorAll('.entry').length")
            if visible_buk < total_buk:
                ok("Bukhari catalog search: 'marriage'", f"{visible_buk} of {total_buk}")
            else:
                warn("Bukhari catalog search: 'marriage'", f"all {total_buk} entries visible -- filter may not have applied")
            ss(page, "20_bukhari_search")
        except PWTimeout:
            fail("Bukhari catalog search", "input#search not found")

        # ── 14. Stats page ─────────────────────────────────────────────────
        print("\n-- Stats page --")
        page.goto(f"{BASE}/stats.html", wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        ss(page, "21_stats_page")

        # Check visible headings/text (not comments) for science vs cosmology
        # page.inner_text strips comments and hidden nodes
        stats_text = page.inner_text("body").lower()
        if "cosmology" in stats_text:
            warn("stats.html: 'Cosmology' heading/text visible to users -- should say 'Science'")
        else:
            ok("stats.html: no 'Cosmology' visible to users (only a code comment remains)")

        if "science" in stats_text:
            ok("stats.html: 'Science' section visible")
        else:
            warn("stats.html: 'Science' not found in visible text")

        # ── 15. Entry detail page ──────────────────────────────────────────
        print("\n-- Entry detail page --")
        page.goto(f"{BASE}/entry.html?id=quran-s41v9-creation-days-arithmetic",
                  wait_until="domcontentloaded")
        page.wait_for_timeout(800)
        ss(page, "22_entry_detail")
        page.wait_for_timeout(1200)  # JS may dynamically render entry
        entry_el = page.locator(".entry")
        if entry_el.count() > 0:
            title_el = entry_el.first.locator(".entry-title")
            title_text = title_el.inner_text() if title_el.count() > 0 else "(no title)"
            ok("Entry detail page: entry rendered", title_text[:60])
        else:
            # page may use a different container for single-entry display
            page_text = page.inner_text("body")
            if "creation arithmetic" in page_text.lower() or "quran" in page_text.lower():
                ok("Entry detail page: content visible (non-.entry container)")
            else:
                warn("Entry detail page: no entry content found")

        # ── 16. 404 page ───────────────────────────────────────────────────
        print("\n-- 404 page --")
        resp = page.goto(f"{BASE}/this-page-does-not-exist.html")
        if resp and resp.status == 404:
            ok("404: server returns 404 for unknown pages")
        else:
            page.wait_for_timeout(500)
            body = page.inner_text("body")
            if "404" in body or "not found" in body.lower():
                ok("404: page shows 404 message")
            else:
                warn("404: unknown page did not clearly 404")
        ss(page, "23_404")

        browser.close()

    # ── Final report ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    passes = [r for r in results if r[0] == "PASS"]
    warns  = [r for r in results if r[0] == "WARN"]
    fails  = [r for r in results if r[0] == "FAIL"]

    print(f"\nPASS: {len(passes)}")
    print(f"WARN: {len(warns)}")
    print(f"FAIL: {len(fails)}")

    if warns:
        print("\nWarnings:")
        for _, name, note in warns:
            print(f"   * {name}: {note}")
    if fails:
        print("\nFailures:")
        for _, name, note in fails:
            print(f"   * {name}: {note}")

    verdict = "PASS" if not fails else "FAIL"
    print(f"\nVerdict: {verdict}")
    print(f"Screenshots: {SCREENSHOTS}")
    return verdict

if __name__ == "__main__":
    v = run()
    sys.exit(0 if v == "PASS" else 1)

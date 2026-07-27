#!/usr/bin/env python3
"""
Analyzing Islam Vol I — PDF Exporter
Converts book.html -> book.pdf using headless Chromium (Playwright).

Usage:
    python export-pdf.py              # exports and opens the PDF
    python export-pdf.py --no-open    # exports only, does not open
"""
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE    = Path(__file__).resolve().parent
HTML_IN = BASE / "book-design/vol1-quran/book.html"
PDF_OUT = BASE / "book-design/vol1-quran/book.pdf"

def export():
    if not HTML_IN.exists():
        print(f"ERROR: {HTML_IN} not found. Run build-book-html.py first.")
        sys.exit(1)

    # prefer_css_page_size=True tells Chromium to honour the CSS @page rule
    # (@page { size: 176mm 250mm; margin: 0 }) rather than doing its own
    # pixel-to-paper scaling.  The viewport is set to the B5 pixel equivalent
    # so the HTML renders at the correct width before printing.
    #
    # B5 at CSS 96 dpi: 1 mm = 96/25.4 px = 3.7795 px
    #   176 mm → 665.35 px  → use 665 px  (matches <meta viewport width=665>)
    #   250 mm → 945.28 px  → use 946 px
    # Chromium uses the @page paper size (176mm) for print layout, not this
    # viewport. The viewport only affects the headless session's screen render.
    B5_W_PX = 665
    B5_H_PX = 946

    print(f"Opening {HTML_IN.name} in headless Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page()

        # Set viewport to B5 paper size so content fills the page edge-to-edge
        page.set_viewport_size({"width": B5_W_PX, "height": B5_H_PX})

        # Load the HTML file
        page.goto(HTML_IN.as_uri())

        # Wait for fonts to load
        page.wait_for_load_state("networkidle", timeout=30000)

        print("Exporting PDF (B5, dark theme, all pages)...")
        # Write to a temp file first so an open PDF viewer doesn't block the save
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        page.pdf(
            path=tmp_path,
            width="176mm",
            height="250mm",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,   # prints dark background and colours
            display_header_footer=False,
        )
        browser.close()

    # Replace the output file (works even if the old one is open in Edge)
    shutil.move(tmp_path, str(PDF_OUT))

    size_mb = PDF_OUT.stat().st_size / 1_048_576
    print(f"Done -> {PDF_OUT}  ({size_mb:.1f} MB)")

    # Open the PDF automatically
    if "--no-open" not in sys.argv:
        print("Opening PDF...")
        subprocess.Popen(["start", "", str(PDF_OUT)], shell=True)

if __name__ == "__main__":
    export()

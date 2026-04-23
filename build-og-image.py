#!/usr/bin/env python3
"""Generate the Open Graph preview image for analyzingislam.com.

Writes site/assets/og-image.png (1200x630, editorial dark theme) and a
smaller square twitter-card.png. Re-run whenever the site's headline
statistics or tagline change."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
OUT = ROOT / "site" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

# Site palette.
BG        = (10, 10, 10)          # --bg
BG_PANEL  = (17, 17, 17)          # --panel
TEXT      = (245, 245, 245)       # --text
MUTED     = (154, 154, 154)       # --text-muted
DIM       = (90, 90, 90)          # --text-dim
ACCENT    = (122, 162, 247)       # --accent
BORDER    = (30, 30, 30)          # --border

# Windows Georgia — closest stable analogue to the site's Didot/Bodoni stack.
GEORGIA        = "C:/Windows/Fonts/georgia.ttf"
GEORGIA_BOLD   = "C:/Windows/Fonts/georgiab.ttf"
GEORGIA_ITALIC = "C:/Windows/Fonts/georgiai.ttf"
SANS           = "C:/Windows/Fonts/arial.ttf"
SANS_BOLD      = "C:/Windows/Fonts/arialbd.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def measure(draw, text, f):
    # Pillow 10+: textbbox returns (x0, y0, x1, y1).
    x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=f)
    return x1 - x0, y1 - y0


def build_main_og():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Thin accent bar along the left edge — editorial, Bloomberg-ish.
    d.rectangle([0, 0, 8, H], fill=ACCENT)

    # Top eyebrow label: small-caps kerned "ANALYZINGISLAM.COM"
    eyebrow = font(SANS_BOLD, 18)
    eyebrow_txt = "A N A L Y Z I N G I S L A M . C O M"
    ew, eh = measure(d, eyebrow_txt, eyebrow)
    d.text((60, 60), eyebrow_txt, fill=DIM, font=eyebrow)

    # Title — big serif.
    title_f = font(GEORGIA_BOLD, 108)
    title   = "Analyzing Islam"
    tw, th  = measure(d, title, title_f)
    d.text((60, 110), title, fill=TEXT, font=title_f)

    # Tagline — italic serif, two wrapped lines.
    tag_f = font(GEORGIA_ITALIC, 30)
    line1 = "A systematic analysis of textual, moral, historical, and"
    line2 = "logical problems in the Quran and the canonical hadith."
    d.text((60, 250), line1, fill=MUTED, font=tag_f)
    d.text((60, 292), line2, fill=MUTED, font=tag_f)

    # Stat row — divider line, then three stats.
    y_div = 400
    d.rectangle([60, y_div, W - 60, y_div + 1], fill=BORDER)

    stats = [
        ("1,500",  "ENTRIES"),
        ("30",     "CATEGORIES"),
        ("34,178", "HADITHS REVIEWED"),
    ]
    stat_num_f = font(GEORGIA_BOLD, 64)
    stat_lbl_f = font(SANS_BOLD,   15)
    col_w = (W - 120) // len(stats)
    for i, (num, lbl) in enumerate(stats):
        x = 60 + i * col_w
        d.text((x, y_div + 30), num, fill=TEXT, font=stat_num_f)
        # Wide-letter-spaced label below the number (Pillow has no
        # tracking, so we inject spaces).
        lbl_spaced = "  ".join(list(lbl))
        d.text((x + 4, y_div + 115), lbl_spaced, fill=DIM, font=stat_lbl_f)

    # Thin bottom rule — consistent with the top accent bar.
    d.rectangle([0, H - 6, W, H], fill=ACCENT)

    out = OUT / "og-image.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB)")


def build_square():
    """1200x1200 square variant for Twitter/X large summary cards and the
    odd LinkedIn / Slack renderer that prefers 1:1."""
    S = 1200
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, S, 10], fill=ACCENT)
    d.rectangle([0, S - 10, S, S], fill=ACCENT)

    eyebrow = font(SANS_BOLD, 22)
    eyebrow_txt = "A N A L Y Z I N G I S L A M . C O M"
    ew, _ = measure(d, eyebrow_txt, eyebrow)
    d.text(((S - ew) // 2, 120), eyebrow_txt, fill=DIM, font=eyebrow)

    title_f = font(GEORGIA_BOLD, 160)
    title   = "Analyzing"
    tw, _   = measure(d, title, title_f)
    d.text(((S - tw) // 2, 220), title, fill=TEXT, font=title_f)

    title2  = "Islam"
    tw2, _  = measure(d, title2, title_f)
    d.text(((S - tw2) // 2, 400), title2, fill=TEXT, font=title_f)

    tag_f = font(GEORGIA_ITALIC, 36)
    tag_lines = [
        "A systematic analysis",
        "of the Quran and",
        "the canonical hadith.",
    ]
    y = 650
    for line in tag_lines:
        lw, _ = measure(d, line, tag_f)
        d.text(((S - lw) // 2, y), line, fill=MUTED, font=tag_f)
        y += 56

    stats_f = font(SANS_BOLD, 22)
    stats = "1,500 ENTRIES  ·  30 CATEGORIES  ·  34,178 HADITHS"
    sw, _ = measure(d, stats, stats_f)
    d.text(((S - sw) // 2, S - 170), stats, fill=DIM, font=stats_f)

    out = OUT / "og-image-square.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build_main_og()
    build_square()

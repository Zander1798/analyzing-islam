#!/usr/bin/env python3
"""Generate the site's favicon set — the 'AI' monogram shown in the
browser tab, on iOS home-screen, and in Android's app-drawer.

Visual: editorial dark-theme tile matching the OG header — #0a0a0a
background, blue accent bar along the bottom, bold serif 'AI' in white.

Outputs into site/assets/icons/:
  favicon.ico              — multi-resolution 16 / 32 / 48
  favicon-16.png
  favicon-32.png
  favicon-48.png
  favicon-192.png          — Android home-screen (from manifest)
  favicon-512.png          — Android splash / PWA (from manifest)
  apple-touch-icon.png     — iOS home-screen (180x180)
  site.webmanifest         — minimal PWA manifest referencing the icons"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
OUT = ROOT / "site" / "assets" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

BG      = (10, 10, 10)
TEXT    = (245, 245, 245)
ACCENT  = (122, 162, 247)

GEORGIA_BOLD = "C:/Windows/Fonts/georgiab.ttf"


def render(size, monogram=True):
    """Render a single favicon at `size`x`size`."""
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)

    # Accent bar along the bottom — proportional to the tile, capped so it
    # doesn't vanish at 16px or dominate at 512px.
    bar = max(1, size // 16)
    d.rectangle([0, size - bar, size, size], fill=ACCENT)

    if not monogram:
        # Single-letter fallback (left for reference — we don't ship it).
        letter = "A"
    else:
        letter = "AI"

    # Pillow has no optical-size font, so we binary-search the font size
    # to fit ~70% of the width and 75% of the height.
    target_w = int(size * 0.72)
    target_h = int(size * 0.70)

    # Coarse initial guess: glyph height ~ point size for a serif.
    lo, hi = 4, size * 2
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(GEORGIA_BOLD, mid)
        x0, y0, x1, y1 = d.textbbox((0, 0), letter, font=f)
        w, h = x1 - x0, y1 - y0
        if w <= target_w and h <= target_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    f = ImageFont.truetype(GEORGIA_BOLD, best)
    x0, y0, x1, y1 = d.textbbox((0, 0), letter, font=f)
    w, h = x1 - x0, y1 - y0
    # Center the glyph box inside the tile, nudging up slightly to leave
    # breathing room above the accent bar.
    x = (size - w) // 2 - x0
    y = (size - h) // 2 - y0 - bar  # shift up by bar height
    d.text((x, y), letter, fill=TEXT, font=f)

    return img


def save_png(img, name):
    p = OUT / name
    img.save(p, "PNG", optimize=True)
    print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size // 1024 or 1} KB)")
    return p


def main():
    # Render a sharp reference image at 512, then downscale with LANCZOS
    # for the medium sizes. Render 16 / 32 / 48 natively — downscaling
    # a 512 sheet makes the serif terminals mushy at those sizes.
    ref = render(512)
    save_png(ref, "favicon-512.png")
    save_png(ref.resize((192, 192), Image.LANCZOS), "favicon-192.png")
    save_png(ref.resize((180, 180), Image.LANCZOS), "apple-touch-icon.png")

    px48 = render(48)
    px32 = render(32)
    px16 = render(16)
    save_png(px48, "favicon-48.png")
    save_png(px32, "favicon-32.png")
    save_png(px16, "favicon-16.png")

    # Multi-resolution .ico — Windows + legacy browsers still pick this up.
    ico_path = OUT / "favicon.ico"
    px48.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=[px32, px16],
    )
    print(f"  {ico_path.relative_to(ROOT)}  ({ico_path.stat().st_size // 1024 or 1} KB)")

    # Minimal web-app manifest so Android gives a proper home-screen icon
    # rather than a downscaled-website screenshot.
    manifest = {
        "name":             "Analyzing Islam",
        "short_name":       "Analyzing Islam",
        "icons": [
            {"src": "/assets/icons/favicon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icons/favicon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "theme_color":      "#0a0a0a",
        "background_color": "#0a0a0a",
        "display":          "browser",
    }
    man_path = OUT / "site.webmanifest"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  {man_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

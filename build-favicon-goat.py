#!/usr/bin/env python
"""Build the goat favicon/icon set for the Analyzing Islam site.

Takes a clean resting frame of the standard goat sprite and centers the whole
goat on a dark rounded-square tile (#0a0a0a, matching the site theme). The goat
is scaled to ~76% of the tile width so the entire sprite survives Google's
circular crop of the favicon while keeping comfortable padding.

Regenerates every file referenced by the site's <link rel="icon"> tags and the
web manifest. Run from the repo root:

    python build-favicon-goat.py [--out DIR]
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent
GIF = REPO / "site/assets/images/goat-standard.gif"
FRAME = 0            # clean standing pose (no crouch/blink)
BG = (10, 10, 10, 255)   # #0a0a0a — site theme / current favicon
GOAT_WIDTH = 0.76        # goat width as a fraction of the tile width
CORNER = 0.18            # rounded-corner radius as a fraction of tile size

# (filename, size, rounded, opaque-square)
#   apple-touch-icon must be an opaque square: iOS applies its own rounded mask.
TARGETS = [
    ("favicon-16.png", 16, True, False),
    ("favicon-32.png", 32, True, False),
    ("favicon-48.png", 48, True, False),
    ("favicon-192.png", 192, True, False),
    ("favicon-512.png", 512, True, False),
    ("apple-touch-icon.png", 180, False, True),
]
ICO_SIZES = [16, 32, 48]


def load_goat():
    """Frame FRAME of the sprite, cropped tight to the goat's pixels (RGBA)."""
    im = Image.open(GIF)
    im.seek(FRAME)
    goat = im.convert("RGBA")
    bbox = goat.getchannel("A").getbbox()
    return goat.crop(bbox)


def tile(goat, size, rounded, opaque_square):
    """Composite the goat, centered, on a dark tile of the given size."""
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg = Image.new("RGBA", (size, size), BG)
    if opaque_square:
        mask = Image.new("L", (size, size), 255)
    else:
        mask = Image.new("L", (size, size), 0)
        r = round(size * CORNER) if rounded else 0
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                               radius=r, fill=255)
    out.paste(bg, (0, 0), mask)

    gw, gh = goat.size
    tw = round(size * GOAT_WIDTH)
    th = round(tw * gh / gw)
    # keep the whole goat inside the tile if it is taller than wide
    max_h = round(size * GOAT_WIDTH)
    if th > max_h:
        th = max_h
        tw = round(th * gw / gh)
    g = goat.resize((tw, th), Image.LANCZOS)
    out.alpha_composite(g, ((size - tw) // 2, (size - th) // 2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "site/assets/icons"))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    goat = load_goat()
    tiles = {}
    for name, size, rounded, opaque in TARGETS:
        img = tile(goat, size, rounded, opaque)
        img.save(out_dir / name)
        tiles[size] = img
        print(f"wrote {name} ({size}x{size})")

    ico_path = out_dir / "favicon.ico"
    tiles[48].save(ico_path, sizes=[(s, s) for s in ICO_SIZES])
    print(f"wrote favicon.ico ({', '.join(map(str, ICO_SIZES))})")


if __name__ == "__main__":
    main()

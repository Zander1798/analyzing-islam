#!/usr/bin/env python3
"""Generate the Open Graph preview image for analyzingislam.com.

The card mirrors the live homepage hero: a frame lifted from
site/assets/hero-tawaf.mp4, desaturated and vignetted the way home.css
treats the hero video, the site grain on top, the red accent, the
Bodoni/Didot display face, and the same four metrics the homepage
counts up. The scrim gradients are lifted relative to the CSS ones —
a still card has no page scrolling out from under it, so the footage
has to stay readable rather than fade away.

Writes:
  site/assets/og-image-v2.jpg         1200x630  — the shared card
  site/assets/og-image-v2-square.jpg  1200x1200 — 1:1 renderers

JPEG, not PNG, on purpose: the same card as a PNG is ~360 KB, and
WhatsApp silently drops preview images over roughly 300 KB. At q88
this photographic card is ~110 KB and visually identical.

The filenames are versioned on purpose. WhatsApp, Facebook, Slack and
X cache preview images by URL, sometimes for weeks; publishing a new
card under the old name leaves most people looking at the stale one.
Bump the version, then run `python add-og-tags.py --repoint` so every
page points at the new file.

Re-run whenever the headline statistics, the tagline, or the hero
footage change.
"""
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont, ImageOps
from pathlib import Path
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
OUT = ROOT / "site" / "assets"
HERO = OUT / "hero-tawaf.mp4"
# Wide aerial of the tawaf with the Kaaba centred and small — the one
# composition in the clip that leaves the left half free for the title.
HERO_TIMESTAMP = "13.2"

VERSION = "v2"
MAIN_OUT = OUT / f"og-image-{VERSION}.jpg"
SQUARE_OUT = OUT / f"og-image-{VERSION}-square.jpg"
JPEG_QUALITY = 88

# --- Site palette (site/assets/css/home.css) -------------------------------
BG = (0, 0, 0)                # --bg
TEXT = (245, 245, 245)        # --text
MUTED = (154, 154, 154)       # --muted
DIM = (90, 90, 90)            # --dim
ACCENT = (198, 40, 40)        # --accent
ACCENT_HI = (239, 83, 80)     # --accent-hi

# --- Fonts -----------------------------------------------------------------
# The site stack is Didot / Bodoni 72 / Bodoni MT / Playfair. Bodoni Bd BT
# ships with Windows and is the closest available high-contrast display
# face; Georgia is the fallback the CSS stack itself names.
SERIF_CANDIDATES = [
    "C:/Windows/Fonts/Bodoni Bd BT Bold.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
]
SANS_CANDIDATES = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
SANS_BOLD_CANDIDATES = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def _pick(candidates):
    for path in candidates:
        if Path(path).exists():
            return path
    raise SystemExit(f"none of these fonts are installed: {candidates}")


SERIF = _pick(SERIF_CANDIDATES)
SANS = _pick(SANS_CANDIDATES)
SANS_BOLD = _pick(SANS_BOLD_CANDIDATES)


def font(path, size):
    return ImageFont.truetype(path, size)


def measure(draw, text, f):
    x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=f)
    return x1 - x0, y1 - y0


def tracked(draw, xy, text, f, fill, tracking):
    """Draw `text` with extra letter-spacing. Pillow has no tracking, so
    step glyph by glyph. Returns the advance width."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return x - xy[0] - tracking


def tracked_width(draw, text, f, tracking):
    return sum(draw.textlength(ch, font=f) for ch in text) + tracking * (len(text) - 1)


# --- Hero frame ------------------------------------------------------------
def _ramp(stops, size, horizontal=True):
    """Build a greyscale alpha ramp from (position, alpha) stops. Rendered
    small and resized — orders of magnitude faster than a pixel loop."""
    N = 512
    g = Image.new("L", (N, 1) if horizontal else (1, N))
    px = g.load()
    for i in range(N):
        t = i / (N - 1)
        a = stops[-1][1]
        for (t0, a0), (t1, a1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                a = a0 + (a1 - a0) * k
                break
        if horizontal:
            px[i, 0] = round(255 * a)
        else:
            px[0, i] = round(255 * a)
    return g.resize(size, Image.BILINEAR)


def _radial(size, inner=0.55, outer=1.0, strength=0.55):
    """Soft radial vignette, matching the hero's radial-gradient centre."""
    N = 160
    g = Image.new("L", (N, N))
    px = g.load()
    for y in range(N):
        dy = (y / (N - 1) - 0.42) / 0.50
        for x in range(N):
            dx = (x / (N - 1) - 0.5) / 0.62
            r = (dx * dx + dy * dy) ** 0.5
            k = min(1.0, max(0.0, (r - inner) / (outer - inner)))
            px[x, y] = round(255 * strength * k * k)
    return g.resize(size, Image.BILINEAR)


def hero_frame(size, scrim):
    """Pull the frame from the hero video and grade it the way home.css
    grades the hero: grayscale, slight contrast lift, dimmed. `scrim` is
    the extra darkening that keeps the card's text legible — a printed
    card has no page scrolling underneath it, so the gradients differ
    from the CSS ones by design."""
    W, H = size
    tmp = OUT / "_og-hero-frame.png"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", HERO_TIMESTAMP,
         "-i", str(HERO), "-frames:v", "1", str(tmp)],
        check=True,
    )
    src = Image.open(tmp).convert("RGB")
    tmp.unlink()

    # object-fit: cover.
    sw, sh = src.size
    scale = max(W / sw, H / sh)
    src = src.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    left = (src.width - W) // 2
    top = (src.height - H) // 2
    img = src.crop((left, top, left + W, top + H))

    img = ImageOps.grayscale(img).convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Brightness(img).enhance(1.05)

    black = Image.new("RGB", (W, H), BG)
    mask = Image.new("L", (W, H), 0)
    for layer in scrim:
        mask = ImageChops.screen(mask, layer(size))
    img = Image.composite(black, img, mask)

    return add_grain(img)


def add_grain(img):
    """The .grain overlay: fractal noise at 3.5%, screen-blended. Uniform
    noise is indistinguishable from the CSS feTurbulence at this size and
    needs no SVG filter."""
    import random

    rng = random.Random(20260827)  # fixed seed: reruns stay byte-stable
    W, H = img.size
    noise = Image.new("L", (W // 2, H // 2))
    noise.putdata([rng.randint(0, 255) for _ in range(noise.width * noise.height)])
    noise = noise.resize((W, H), Image.BILINEAR).convert("RGB")
    return Image.blend(img, ImageChops.screen(img, noise), 0.035)


# Scrims. The wide card carries all its type down the left, so the left
# column goes almost fully black and the footage stays visible on the
# right; the square card is centre-set, so it darkens from the edges in.
MAIN_SCRIM = [
    lambda s: _ramp([(0.0, 0.94), (0.34, 0.78), (0.64, 0.18), (1.0, 0.30)], s),
    lambda s: _ramp([(0.0, 0.46), (0.22, 0.08), (0.70, 0.18), (1.0, 0.78)], s,
                    horizontal=False),
    lambda s: _radial(s, strength=0.34),
]
SQUARE_SCRIM = [
    lambda s: _ramp([(0.0, 0.58), (0.16, 0.14), (0.84, 0.14), (1.0, 0.58)], s),
    lambda s: _ramp([(0.0, 0.52), (0.24, 0.10), (1.0, 0.16)], s, horizontal=False),
    lambda s: _radial(s, strength=0.30),
]


def save_card(img, path):
    # 4:4:4 chroma — the red accent rule and the small tracked labels
    # smear badly under the default 4:2:0 subsampling.
    img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True,
             progressive=True, subsampling=0)


# --- Headline numbers ------------------------------------------------------
# Must match the .metrics row on site/index.html.
STATS = [
    ("1,524", "ENTRIES"),
    ("31", "CATEGORIES"),
    ("6,236", "QURAN VERSES"),
    ("34,178", "HADITHS"),
]
TAGLINE = ("A systematic, filterable review of textual, moral, historical,",
           "and logical problems in the Quran and the Hadiths.")


def build_main():
    W, H = 1200, 630
    img = hero_frame((W, H), MAIN_SCRIM)
    d = ImageDraw.Draw(img)

    PAD = 64

    # Eyebrow — the hero .kicker: uppercase, .34em tracking, accent red.
    kicker_f = font(SANS_BOLD, 19)
    tracked(d, (PAD, PAD), "ANALYZINGISLAM.COM", kicker_f, ACCENT_HI, 6.5)

    # Title — hero h1, two lines, line-height 1.0.
    title_f = font(SERIF, 116)
    d.text((PAD - 4, 120), "Analyzing", fill=TEXT, font=title_f)
    d.text((PAD - 4, 236), "Islam", fill=TEXT, font=title_f)

    # Tagline — hero .sub.
    sub_f = font(SANS, 25)
    d.text((PAD, 382), TAGLINE[0], fill=MUTED, font=sub_f)
    d.text((PAD, 416), TAGLINE[1], fill=MUTED, font=sub_f)

    # Metric row — each stat sits under a 2px rule, exactly like
    # .metric { border-top: 2px solid var(--border-hi) }.
    y_rule = 500
    num_f = font(SERIF, 52)
    lbl_f = font(SANS, 15)
    col_w = (W - PAD * 2) // len(STATS)
    for i, (num, lbl) in enumerate(STATS):
        x = PAD + i * col_w
        d.rectangle([x, y_rule, x + col_w - 26, y_rule + 1], fill=(58, 58, 58))
        d.text((x, y_rule + 18), num, fill=TEXT, font=num_f)
        tracked(d, (x + 2, y_rule + 84), lbl, lbl_f, MUTED, 1.2)

    # Accent rule along the bottom edge.
    d.rectangle([0, H - 5, W, H], fill=ACCENT)

    save_card(img, MAIN_OUT)
    print(f"wrote {MAIN_OUT.relative_to(ROOT)}  ({MAIN_OUT.stat().st_size // 1024} KB)")


def build_square():
    """1:1 variant for the renderers that crop wide cards badly.

    The footage is 848x400, so filling a 1200x1200 frame with it means a
    3x upscale and visible mush. Instead the hero runs as a band across
    the top and dissolves into black, and the type sits in the black —
    the same two-part composition the homepage makes as you scroll off
    the hero into the metrics."""
    S = 1200
    BAND = 660
    img = Image.new("RGB", (S, S), BG)
    band = hero_frame((S, BAND), SQUARE_SCRIM)
    # Dissolve the bottom of the band into the page black.
    band = Image.composite(
        Image.new("RGB", (S, BAND), BG), band,
        _ramp([(0.0, 0.0), (0.55, 0.06), (0.88, 0.70), (1.0, 1.0)],
              (S, BAND), horizontal=False),
    )
    img.paste(band, (0, 0))
    d = ImageDraw.Draw(img)

    PAD = 80

    kicker_f = font(SANS_BOLD, 22)
    tracked(d, (PAD, PAD), "ANALYZINGISLAM.COM", kicker_f, ACCENT_HI, 7.5)

    title_f = font(SERIF, 140)
    d.text((PAD - 5, 560), "Analyzing", fill=TEXT, font=title_f)
    d.text((PAD - 5, 700), "Islam", fill=TEXT, font=title_f)

    sub_f = font(SANS, 30)
    lines = ("A systematic, filterable review of textual, moral,",
             "historical, and logical problems in the Quran",
             "and the Hadiths.")
    y = 880
    for line in lines:
        d.text((PAD, y), line, fill=MUTED, font=sub_f)
        y += 42

    # Two stat columns — four are too cramped at this width.
    y_rule = 1040
    num_f = font(SERIF, 56)
    lbl_f = font(SANS, 16)
    col_w = (S - PAD * 2) // 2
    for i, (num, lbl) in enumerate((STATS[0], STATS[3])):
        x = PAD + i * col_w
        d.rectangle([x, y_rule, x + col_w - 40, y_rule + 1], fill=(58, 58, 58))
        d.text((x, y_rule + 20), num, fill=TEXT, font=num_f)
        tracked(d, (x + 2, y_rule + 96), lbl, lbl_f, MUTED, 1.3)

    d.rectangle([0, S - 6, S, S], fill=ACCENT)

    save_card(img, SQUARE_OUT)
    print(f"wrote {SQUARE_OUT.relative_to(ROOT)}  ({SQUARE_OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if not HERO.exists():
        raise SystemExit(f"missing hero footage: {HERO}")
    build_main()
    build_square()

# catalog_render.py — render a book entry dict into the site's catalog
# entry-block HTML. Stdlib only. Citation linking is validate-before-link
# (see render_ref_html / link helpers in later tasks).
import hashlib
import html
import importlib.util as _ilu
import re
import sys
from pathlib import Path as _Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Load refs module for citation resolution.
_refs_spec = _ilu.spec_from_file_location("refs", _Path(__file__).parent / "refs.py")
refs = _ilu.module_from_spec(_refs_spec)
_refs_spec.loader.exec_module(refs)

CATEGORY_SLUGS = {
    "Strange / Obscure": "strange", "Women": "women",
    "Prophetic Character": "prophet", "Logical Inconsistency": "logic",
    "Treatment of Disbelievers": "disbelievers", "Science": "science",
    "Contradictions": "contradiction", "Moral Problems": "morality",
    "Eschatology": "eschatology", "Governance": "governance",
    "Warfare & Jihad": "warfare", "Jesus / Christology": "jesus",
    "Allah's Character": "allah", "Hudud": "hudud",
    "Ritual Absurdities": "ritual", "Abrogation": "abrogation",
    "Magic & Occult": "magic", "Antisemitism": "antisemitism",
    "Sexual Issues": "sexual", "Scripture Integrity": "scripture",
    "Slavery & Captives": "slavery", "Prophetic Privileges": "privileges",
    "Pre-Islamic Borrowings": "preislamic", "Hell": "hell",
    "Paradise": "paradise", "Apostasy & Blasphemy": "apostasy",
    "LGBTQ / Gender": "lgbtq", "Child Marriage": "childmarriage",
    "Gross / Vile": "gross-vile", "Incest": "incest", "Animals": "animals",
}


def category_slug(name: str) -> str:
    return CATEGORY_SLUGS[name.strip()]


def strength_class(strength: str) -> str:
    return (strength or "").strip().lower()


def esc(s: str) -> str:
    return html.escape(s, quote=True) if s else ""


def slugify(s: str, max_len: int = 60) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[̀-ͯ]", "", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:max_len].rstrip("-")


def entry_slug(title: str, source: str) -> str:
    h = hashlib.sha256(f"{source}::{title}".encode("utf-8")).hexdigest()[:8]
    return f"{slugify(title)}-{h}"


# Leading prose words sometimes prefix a ref inside a multi-ref string.
_PROSE = re.compile(r"(?i)^(?:contrast|see also|see|cf\.?|also|and|vs\.?|compare)\s+")


# Colon-form hadith: "abudawud:2311" -> slug + number. Reuse refs.COLLECTION_SLUGS
# values to recognise the left side.
_SLUG_TO_NAME = {
    "bukhari": "Bukhari",
    "muslim": "Muslim",
    "abu-dawud": "Abu Dawud",
    "tirmidhi": "Tirmidhi",
    "nasai": "Nasa'i",
    "ibn-majah": "Ibn Majah",
}
# Accept the compact JSON keys too (abudawud, ibnmajah)
_COMPACT = {"abudawud": "Abu Dawud", "ibnmajah": "Ibn Majah"}


def normalize_ref_part(part: str) -> str:
    """Strip leading prose words and rewrite colon-form hadith and no-space Qur'an refs.

    Returns "" if the part has no parseable ref token.
    """
    p = part.strip()
    p = _PROSE.sub("", p).strip()
    if not p:
        return ""
    # no-space Qur'an: Q4:92 -> Q 4:92
    m = re.match(r"(?i)^q(\d+:\d+.*)$", p)
    if m:
        return "Q " + m.group(1)
    # colon-form hadith: abudawud:2311 -> Abu Dawud 2311
    m = re.match(r"^([a-z-]+):(\d+[a-z]?)$", p, re.I)
    if m:
        key = m.group(1).lower()
        name = _SLUG_TO_NAME.get(key) or _COMPACT.get(key)
        if name:
            return f"{name} {m.group(2)}"
    return p


def link_one_ref(ref: str, anchor_sets: dict) -> str:
    """Return <a> with cite-link if anchor exists in anchor_sets[slug], else plain text.

    RefError or unknown -> plain text.
    """
    try:
        slug, anchor = refs.primary_anchor(ref)
    except refs.RefError:
        return esc(ref)
    if anchor in anchor_sets.get(slug, set()):
        return f'<a class="cite-link" href="../read/{slug}.html#{anchor}">{esc(ref)}</a>'
    return esc(ref)


def render_ref_html(verse_refs: list, anchor_sets: dict) -> str:
    """Join each verse_refs element (after splitting on ,/; and normalizing) with comma.

    Each is linked-or-plain; this is the <span class="ref"> inner HTML.
    """
    out = []
    for raw in verse_refs:
        for part in re.split(r"[;,]", raw):
            norm = normalize_ref_part(part)
            if norm:
                out.append(link_one_ref(norm, anchor_sets))
    return ", ".join(out)


_HADITH_NAMES = sorted(
    ["Bukhari", "Muslim", "Abu Dawud", "Tirmidhi", "Nasa'i", "Nasai", "Ibn Majah"],
    key=len, reverse=True)
_HADITH_ALT = "|".join(re.escape(n) for n in _HADITH_NAMES)
_QURAN_INLINE = re.compile(r"Q (\d+):(\d+)(?:[–\-]\d+)?")
_HADITH_INLINE = re.compile(rf"({_HADITH_ALT}) (\d+[a-z]?)")


def link_inline(text_html: str, anchor_sets: dict) -> str:
    """Wrap inline Qur'an and hadith refs in <a class="cite-link"> if anchor exists.

    Input is already HTML-escaped. Routes each candidate through link_one_ref
    so no broken inline link is produced. Display text unchanged.
    """
    def q(m):
        return link_one_ref(m.group(0), anchor_sets)

    def h(m):
        return link_one_ref(m.group(0), anchor_sets)

    text_html = _QURAN_INLINE.sub(q, text_html)
    text_html = _HADITH_INLINE.sub(h, text_html)
    return text_html

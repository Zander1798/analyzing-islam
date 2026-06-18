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


_QREF_TIGHTEN = re.compile(r"\bQ (\d+):(\d+)")


def tighten_qrefs(s: str) -> str:
    """Render Qur'an reference display tight: 'Q 2:25' -> 'Q2:25'. Display only;
    link hrefs ('#s2v25') contain no 'Q ' and are unaffected."""
    return _QREF_TIGHTEN.sub(r"Q\1:\2", s)


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
    """Render each verse_refs element verbatim with per-citation links in place.

    Uses link_inline so prose, parentheticals, and punctuation are preserved
    verbatim while each Q/hadith token is individually linked if its anchor
    exists. This is the <span class="ref"> inner HTML.
    """
    return ", ".join(link_inline(esc(raw), anchor_sets) for raw in (verse_refs or []))


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


def render_paragraphs(text: str, anchor_sets: dict) -> str:
    """Split text on \n\n, esc each block, inline-link it, wrap in <p>…</p>, join with \n      ."""
    blocks = [b.strip() for b in (text or "").split("\n\n") if b.strip()]
    out = []
    for b in blocks:
        out.append("<p>" + link_inline(esc(b), anchor_sets) + "</p>")
    return "\n      ".join(out)


def says_heading(source: str, n_refs: int) -> str:
    """Return heading text for what-it-says section.

    For quran: "What the verse says" if n_refs <= 1, else "What the verses say".
    For hadith: "What the hadith says".
    """
    if source == "quran":
        return "What the verse says" if n_refs <= 1 else "What the verses say"
    return "What the hadith says"


def render_entry(entry: dict, source: str, anchor_sets: dict) -> str:
    """Render a book entry dict into <div class="entry">…</div> block.

    Omits "The Muslim response" h4+paras when muslim_response is null/empty.
    Omits "Why it fails" block when why_fails is null/empty.
    """
    title = entry["title"]
    cats = entry.get("categories") or []
    slugs = [category_slug(c) for c in cats]
    strength = entry.get("strength") or ""
    scls = strength_class(strength)
    eid = entry_slug(title, source)
    refs_list = entry.get("verse_refs") or []
    ref_html = render_ref_html(refs_list, anchor_sets)

    parts = [
        f'<div class="entry" id="{eid}" data-category="{esc(" ".join(slugs))}" data-strength="{scls}">',
        '  <div class="entry-header">',
        f'    <span class="entry-title">{esc(title)}</span>',
    ]
    for c in cats:
        parts.append(f'    <span class="tag">{esc(c)}</span>')
    parts.append(f'    <span class="tag strength-{scls}">{esc(strength)}</span>')
    parts.append(f'    <span class="ref">{ref_html}</span>')
    parts.append('  </div>')
    parts.append('  <section>')
    parts.append(f'    <blockquote>{esc(entry.get("verse_quote") or "")}</blockquote>')
    parts.append(f'    <h4>{says_heading(source, len(refs_list))}</h4>')
    parts.append(f'    {render_paragraphs(entry.get("what_it_says"), anchor_sets)}')
    parts.append('    <h4>Why this is a problem</h4>')
    parts.append(f'    {render_paragraphs(entry.get("why_problem"), anchor_sets)}')
    if (entry.get("muslim_response") or "").strip():
        parts.append('    <h4>The Muslim response</h4>')
        parts.append(f'    {render_paragraphs(entry["muslim_response"], anchor_sets)}')
    if (entry.get("why_fails") or "").strip():
        parts.append('    <h4>Why it fails</h4>')
        parts.append(f'    {render_paragraphs(entry["why_fails"], anchor_sets)}')
    parts.append('  </section>')
    parts.append('</div>')
    # Tighten Qur'an reference DISPLAY ("Q 2:25" -> "Q2:25") site-wide style.
    # Applied last, after link_inline has matched the spaced form, so links are
    # created then their visible text is tightened. hrefs are "#sNvV" (no "Q "),
    # so this never touches a link target — display only.
    return tighten_qrefs("\n".join(parts))

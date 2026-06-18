# catalog_render.py — render a book entry dict into the site's catalog
# entry-block HTML. Stdlib only. Citation linking is validate-before-link
# (see render_ref_html / link helpers in later tasks).
import hashlib
import html
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

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

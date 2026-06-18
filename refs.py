# refs.py — canonical citation ref -> read-page anchor mapping.
# Single source of truth binding book/entry citations to the rebuilt read
# pages. Consumed by the catalog generator (to emit links) and the link
# validator (to check them). Stdlib only.
import re

QURAN_SLUG = "quran"


class RefError(ValueError):
    """Raised when a citation string cannot be parsed."""


def quran_anchor(surah: int, verse: int) -> str:
    return f"s{surah}v{verse}"


# One "S:V" or "S:V-V" / "S:V–V" token; capture surah + first verse.
_QV = re.compile(r"\s*(\d+)\s*:\s*(\d+)")


def parse_quran_ref(ref: str) -> list[tuple[int, int]]:
    s = ref.strip()
    if not re.match(r"(?i)^q\b", s):
        raise RefError(f"Not a Qur'an ref: {ref!r}")
    body = re.sub(r"(?i)^q\s*", "", s)
    pairs: list[tuple[int, int]] = []
    for token in body.split(","):
        m = _QV.match(token)
        if not m:
            raise RefError(f"Unparseable Qur'an token {token!r} in {ref!r}")
        pairs.append((int(m.group(1)), int(m.group(2))))
    if not pairs:
        raise RefError(f"No verses in {ref!r}")
    return pairs


# Normalized collection name (lowercased, apostrophes/diacritics stripped to
# ASCII) -> read-page slug. Keys cover the spellings used in book verse_refs.
COLLECTION_SLUGS = {
    "bukhari": "bukhari",
    "muslim": "muslim",
    "abu dawud": "abu-dawud",
    "abudawud": "abu-dawud",
    "tirmidhi": "tirmidhi",
    "nasai": "nasai",
    "ibn majah": "ibn-majah",
    "ibnmajah": "ibn-majah",
}


def hadith_anchor(id_in_book: int) -> str:
    return f"h{id_in_book}"


def _normalize_collection(name: str) -> str:
    n = name.strip().lower()
    # Strip apostrophes/diacritic markers that appear in transliterations.
    n = n.replace("'", "").replace("`", "").replace("'", "")
    n = n.replace("ʾ", "").replace("ʿ", "")
    n = re.sub(r"\s+", " ", n)
    return n


def parse_hadith_ref(ref: str) -> tuple[str, int]:
    s = ref.strip()
    m = re.match(r"^(.+?)\s+(\d+)", s)
    if not m:
        raise RefError(f"No collection+number in {ref!r}")
    name = _normalize_collection(m.group(1))
    if name not in COLLECTION_SLUGS:
        raise RefError(f"Unknown collection {m.group(1)!r} in {ref!r}")
    return COLLECTION_SLUGS[name], int(m.group(2))

#!/usr/bin/env python3
"""Ingest STEPBible TAHOT (Hebrew OT) + TAGNT (Greek NT) into per-book
JSON files + a unified Strong's dictionary JSON + a concordance index.

Output structure:
  .tmp/bible-data/
    strongs-hebrew.json          { "H1234": {lemma, translit, gloss, definition}, ... }
    strongs-greek.json           { "G5678": {lemma, translit, gloss, definition}, ... }
    concordance.json             { "H1234": [["Gen",1,1,5], ["Gen",2,3,2]], ... }
    books/
      gen.json, exo.json, ...    { book, chapters: [ {num, verses:[{num, words:[...]}] } ] }

Each word:
  {
    "orig":     "בְּ/רֵאשִׁ֖ית",      # surface form
    "trans":    "be./Re.shit",        # transliteration
    "gloss":    "in/ [the] beginning", # word-by-word English
    "strongs":  ["H9003", "H7225"],   # one or more Strong's numbers
    "morph":    "HR/Ncfsa",           # raw morph code
    "morph_en": ["Preposition", ...]  # parsed morph description
  }
"""
import json
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
SRC = ROOT / ".tmp" / "bible-sources"
OUT = ROOT / ".tmp" / "bible-data"
OUT_BOOKS = OUT / "books"

TAHOT_FILES = [
    SRC / "STEPBible-Data" / "Translators Amalgamated OT+NT" / f
    for f in [
        "TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
        "TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
        "TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
        "TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    ]
]
TAGNT_FILES = [
    SRC / "STEPBible-Data" / "Translators Amalgamated OT+NT" / f
    for f in [
        "TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
        "TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
    ]
]

STRONGS_HEBREW_JS = SRC / "strongs" / "hebrew" / "strongs-hebrew-dictionary.js"
STRONGS_GREEK_JS = SRC / "strongs" / "greek" / "strongs-greek-dictionary.js"

# STEPBible uses its own book-code convention in the line refs — "Gen.1.1".
# Map to our slug + display name + section.
BOOK_META = [
    # OT
    ("Gen",  "gen",      "Genesis",        "OT-Torah"),
    ("Exo",  "exo",      "Exodus",         "OT-Torah"),
    ("Lev",  "lev",      "Leviticus",      "OT-Torah"),
    ("Num",  "num",      "Numbers",        "OT-Torah"),
    ("Deu",  "deu",      "Deuteronomy",    "OT-Torah"),
    ("Jos",  "jos",      "Joshua",         "OT-History"),
    ("Jdg",  "jdg",      "Judges",         "OT-History"),
    ("Rut",  "rut",      "Ruth",           "OT-History"),
    ("1Sa",  "1sa",      "1 Samuel",       "OT-History"),
    ("2Sa",  "2sa",      "2 Samuel",       "OT-History"),
    ("1Ki",  "1ki",      "1 Kings",        "OT-History"),
    ("2Ki",  "2ki",      "2 Kings",        "OT-History"),
    ("1Ch",  "1ch",      "1 Chronicles",   "OT-History"),
    ("2Ch",  "2ch",      "2 Chronicles",   "OT-History"),
    ("Ezr",  "ezr",      "Ezra",           "OT-History"),
    ("Neh",  "neh",      "Nehemiah",       "OT-History"),
    ("Est",  "est",      "Esther",         "OT-History"),
    ("Job",  "job",      "Job",            "OT-Wisdom"),
    ("Psa",  "psa",      "Psalms",         "OT-Wisdom"),
    ("Pro",  "pro",      "Proverbs",       "OT-Wisdom"),
    ("Ecc",  "ecc",      "Ecclesiastes",   "OT-Wisdom"),
    ("Sng",  "sng",      "Song of Songs",  "OT-Wisdom"),
    ("Isa",  "isa",      "Isaiah",         "OT-Major-Prophets"),
    ("Jer",  "jer",      "Jeremiah",       "OT-Major-Prophets"),
    ("Lam",  "lam",      "Lamentations",   "OT-Major-Prophets"),
    ("Ezk",  "ezk",      "Ezekiel",        "OT-Major-Prophets"),
    ("Dan",  "dan",      "Daniel",         "OT-Major-Prophets"),
    ("Hos",  "hos",      "Hosea",          "OT-Minor-Prophets"),
    ("Jol",  "jol",      "Joel",           "OT-Minor-Prophets"),
    ("Amo",  "amo",      "Amos",           "OT-Minor-Prophets"),
    ("Oba",  "oba",      "Obadiah",        "OT-Minor-Prophets"),
    ("Jon",  "jon",      "Jonah",          "OT-Minor-Prophets"),
    ("Mic",  "mic",      "Micah",          "OT-Minor-Prophets"),
    ("Nam",  "nam",      "Nahum",          "OT-Minor-Prophets"),
    ("Nah",  "nam",      "Nahum",          "OT-Minor-Prophets"),
    ("Hab",  "hab",      "Habakkuk",       "OT-Minor-Prophets"),
    ("Zep",  "zep",      "Zephaniah",      "OT-Minor-Prophets"),
    ("Hag",  "hag",      "Haggai",         "OT-Minor-Prophets"),
    ("Zec",  "zec",      "Zechariah",      "OT-Minor-Prophets"),
    ("Mal",  "mal",      "Malachi",        "OT-Minor-Prophets"),
    # NT
    ("Mat",  "mat",      "Matthew",        "NT-Gospels"),
    ("Mrk",  "mrk",      "Mark",           "NT-Gospels"),
    ("Luk",  "luk",      "Luke",           "NT-Gospels"),
    ("Jhn",  "jhn",      "John",           "NT-Gospels"),
    ("Act",  "act",      "Acts",           "NT-History"),
    ("Rom",  "rom",      "Romans",         "NT-Pauline"),
    ("1Co",  "1co",      "1 Corinthians",  "NT-Pauline"),
    ("2Co",  "2co",      "2 Corinthians",  "NT-Pauline"),
    ("Gal",  "gal",      "Galatians",      "NT-Pauline"),
    ("Eph",  "eph",      "Ephesians",      "NT-Pauline"),
    ("Php",  "php",      "Philippians",    "NT-Pauline"),
    ("Col",  "col",      "Colossians",     "NT-Pauline"),
    ("1Th",  "1th",      "1 Thessalonians","NT-Pauline"),
    ("2Th",  "2th",      "2 Thessalonians","NT-Pauline"),
    ("1Ti",  "1ti",      "1 Timothy",      "NT-Pauline"),
    ("2Ti",  "2ti",      "2 Timothy",      "NT-Pauline"),
    ("Tit",  "tit",      "Titus",          "NT-Pauline"),
    ("Phm",  "phm",      "Philemon",       "NT-Pauline"),
    ("Heb",  "heb",      "Hebrews",        "NT-General"),
    ("Jas",  "jas",      "James",          "NT-General"),
    ("1Pe",  "1pe",      "1 Peter",        "NT-General"),
    ("2Pe",  "2pe",      "2 Peter",        "NT-General"),
    ("1Jn",  "1jn",      "1 John",         "NT-General"),
    ("2Jn",  "2jn",      "2 John",         "NT-General"),
    ("3Jn",  "3jn",      "3 John",         "NT-General"),
    ("Jud",  "jud",      "Jude",           "NT-General"),
    ("Rev",  "rev",      "Revelation",     "NT-Apocalypse"),
]

# Build code -> (slug, name, section) lookup — one canonical per slug,
# but also allow aliases (like Nam -> Nah both point to Nahum).
CODE_TO_BOOK = {}
SLUG_SEEN = set()
BOOK_ORDER = []
for code, slug, name, section in BOOK_META:
    CODE_TO_BOOK[code] = (slug, name, section)
    if slug not in SLUG_SEEN:
        BOOK_ORDER.append((slug, name, section))
        SLUG_SEEN.add(slug)


# ============================================================
#  Strong's dictionary loader
# ============================================================

def load_strongs(js_path: Path, prefix: str) -> dict:
    """Parse the strongs-{hebrew|greek}-dictionary.js file.
    File is JS: `var strongs{Hebrew|Greek}Dictionary = { "H1": {...}, ... };`
    Strip the JS wrapper and parse the object as JSON.
    """
    text = js_path.read_text(encoding="utf-8", errors="replace")
    # Opening brace — the assignment target
    m = re.search(r"=\s*({)", text)
    if not m:
        return {}
    start = m.start(1)
    # Closing `};` — scan from the END of the file (the object ends with "};").
    end = text.rfind("};")
    if end == -1:
        end = text.rfind("}")
    obj_text = text[start:end + 1]
    try:
        return json.loads(obj_text)
    except json.JSONDecodeError as e:
        print(f"  WARN parsing {js_path.name}: {e}", file=sys.stderr)
        # Attempt to remove trailing commas etc.
        cleaned = re.sub(r",(\s*[}\]])", r"\1", obj_text)
        try:
            return json.loads(cleaned)
        except Exception as e2:
            print(f"  ERROR parsing {js_path.name}: {e2}", file=sys.stderr)
            return {}


def normalize_strongs(raw: dict, prefix: str) -> dict:
    """Normalize to a compact shape we care about."""
    out = {}
    for k, v in raw.items():
        # Keys are "H1", "H10", "G1", "G4999" — ensure prefix
        key = k if k.startswith(prefix) else f"{prefix}{k}"
        # Pad numeric portion to 4 digits to match STEPBible "H0001" style
        m = re.match(rf"^{prefix}(\d+)([A-Za-z]?)$", key)
        if m:
            key = f"{prefix}{int(m.group(1)):04d}{m.group(2)}"
        out[key] = {
            "lemma": v.get("lemma", "") or v.get("xlit", ""),
            "translit": v.get("xlit", "") or v.get("translit", ""),
            "pron": v.get("pron", ""),
            "derivation": v.get("derivation", ""),
            "strongs_def": v.get("strongs_def", "") or v.get("strongsdef", ""),
            "kjv_def": v.get("kjv_def", "") or v.get("kjv", ""),
        }
    return out


# ============================================================
#  Morphology code expansion
# ============================================================

HEB_POS = {
    "A": "Adjective", "C": "Conjunction", "D": "Adverb",
    "N": "Noun", "P": "Pronoun", "R": "Preposition",
    "S": "Suffix", "T": "Particle", "V": "Verb",
}
HEB_NOUN_TYPE = {
    "c": "common", "p": "proper", "g": "gentilic",
}
HEB_NOUN_GENDER = {"m": "masculine", "f": "feminine", "b": "both", "c": "common"}
HEB_NUMBER = {"s": "singular", "p": "plural", "d": "dual"}
HEB_STATE = {"a": "absolute", "c": "construct", "d": "determined"}
HEB_STEM = {
    "q": "Qal", "N": "Niphal", "p": "Piel", "P": "Pual",
    "h": "Hiphil", "H": "Hophal", "t": "Hithpael",
    "o": "Polel", "O": "Polal", "r": "Polpal",
    "m": "Poel", "M": "Poal", "k": "Palel",
    "L": "Pilpel", "f": "Hithpolel", "D": "Tiphil",
    "j": "Hishtaphel", "i": "Nithpael",
    "u": "Hothpael", "c": "Pealal", "v": "Pilel",
    "w": "Polpel", "y": "Poalal",
    "z": "Peilal", "b": "Pilpal",
    "n": "Nithpalpel", "e": "Hothpalpel", "l": "Pulal",
    "a": "Afel", "s": "Shaphel", "x": "Ishtaphel",
    "g": "Hishaphel", "T": "Ethpaal", "E": "Ethpael",
    "I": "Ethpeel", "F": "Ettaphal", "Q": "Peal",
    "G": "Pael", "J": "Aphel", "S": "Saphel",
}
HEB_ASPECT = {
    "p": "perfect", "q": "sequential perfect",
    "i": "imperfect", "w": "sequential imperfect",
    "h": "cohortative", "j": "jussive", "v": "imperative",
    "r": "participle active", "s": "participle passive",
    "a": "infinitive absolute", "c": "infinitive construct",
}
HEB_PERSON = {"1": "1st", "2": "2nd", "3": "3rd", "x": ""}
HEB_PARTICLE = {
    "a": "affirmation", "d": "definite article", "e": "exhortation",
    "i": "interrogative", "j": "interjection", "m": "demonstrative",
    "n": "negative", "o": "direct object marker", "r": "relative",
}

GRK_POS = {
    "N": "Noun", "V": "Verb", "A": "Adjective", "R": "Pronoun",
    "RA": "Article", "C": "Conjunction", "P": "Preposition",
    "X": "Particle", "D": "Adverb", "I": "Interjection",
    "RR": "Relative Pronoun", "RD": "Demonstrative Pronoun",
    "RI": "Interrogative Pronoun", "RP": "Personal Pronoun",
    "RX": "Indefinite Pronoun", "RF": "Reflexive Pronoun",
}
GRK_TENSE = {
    "P": "Present", "I": "Imperfect", "F": "Future", "A": "Aorist",
    "X": "Perfect", "Y": "Pluperfect", "E": "Future Perfect",
}
GRK_VOICE = {"A": "Active", "M": "Middle", "P": "Passive",
             "E": "Either middle or passive", "D": "Deponent",
             "N": "Middle deponent", "O": "Passive deponent"}
GRK_MOOD = {
    "I": "Indicative", "S": "Subjunctive", "O": "Optative",
    "M": "Imperative", "N": "Infinitive", "P": "Participle",
}
GRK_PERSON = {"1": "1st", "2": "2nd", "3": "3rd"}
GRK_NUMBER = {"S": "singular", "P": "plural", "D": "dual"}
GRK_CASE = {
    "N": "Nominative", "G": "Genitive", "D": "Dative",
    "A": "Accusative", "V": "Vocative",
}
GRK_GENDER = {"M": "masculine", "F": "feminine", "N": "neuter"}


def parse_heb_morph(code: str) -> list[str]:
    """Return human-readable expansion of a STEPBible Hebrew morph code.
    Code example: HVqp3ms = Hebrew / Verb / Qal / perfect / 3rd / masculine singular
                  HNcmpa = Hebrew / Noun / common / masculine plural / absolute
                  HTd    = Hebrew / definite article
    """
    if not code or not code.startswith("H"):
        return []
    body = code[1:]
    out = []
    if not body:
        return out
    pos = body[0]
    out.append(HEB_POS.get(pos, pos))
    rest = body[1:]

    if pos == "V" and rest:
        if rest and rest[0] in HEB_STEM:
            out.append(HEB_STEM[rest[0]]); rest = rest[1:]
        if rest and rest[0] in HEB_ASPECT:
            out.append(HEB_ASPECT[rest[0]]); rest = rest[1:]
        if rest and rest[0] in HEB_PERSON:
            p = HEB_PERSON[rest[0]]
            if p: out.append(p + " person")
            rest = rest[1:]
        if rest and rest[0] in HEB_NOUN_GENDER:
            out.append(HEB_NOUN_GENDER[rest[0]]); rest = rest[1:]
        if rest and rest[0] in HEB_NUMBER:
            out.append(HEB_NUMBER[rest[0]]); rest = rest[1:]
    elif pos == "N" and rest:
        if rest and rest[0] in HEB_NOUN_TYPE:
            out.append(HEB_NOUN_TYPE[rest[0]]); rest = rest[1:]
        if rest and rest[0] in HEB_NOUN_GENDER:
            out.append(HEB_NOUN_GENDER[rest[0]]); rest = rest[1:]
        if rest and rest[0] in HEB_NUMBER:
            out.append(HEB_NUMBER[rest[0]]); rest = rest[1:]
        if rest and rest[0] in HEB_STATE:
            out.append(HEB_STATE[rest[0]]); rest = rest[1:]
    elif pos == "T" and rest and rest[0] in HEB_PARTICLE:
        out.append(HEB_PARTICLE[rest[0]]); rest = rest[1:]
    return out


def parse_grk_morph(code: str) -> list[str]:
    """Parse TAGNT Greek morph codes.

    Format — hyphen-separated sections:
      V-PAI-3P       = Verb, Present Active Indicative, 3rd Plural
      V-2AAI-3S      = Verb, 2nd Aorist Active Indicative, 3rd Singular
      V-AAP-NSM      = Verb, Aorist Active Participle, Nominative Singular Masculine
      N-NSF          = Noun, Nominative Singular Feminine
      N-GSM-P        = Noun, Genitive Singular Masculine, Proper
      A-NSM          = Adjective, Nominative Singular Masculine
      P-NSF          = Pronoun (or Personal, context-dependent), Nom Sg Fem
      T-NSM          = arTicle, Nom Sg Masc
      PREP           = preposition (no further features)
      CONJ           = conjunction
    """
    if not code:
        return []
    # Normalise special 1-word POS codes
    simple_pos_map = {
        "PREP": "Preposition", "CONJ": "Conjunction", "ADV": "Adverb",
        "ADJ": "Adjective", "INJ": "Interjection", "PRT": "Particle",
        "ARAM": "Aramaic", "HEB": "Hebrew",
    }
    if code in simple_pos_map:
        return [simple_pos_map[code]]

    parts = code.split("-")
    if not parts:
        return []
    pos = parts[0]
    out = []
    # POS table with TAGNT-specific codes
    grk_pos_ext = dict(GRK_POS)
    grk_pos_ext.update({
        "T": "Article", "P": "Preposition or Personal Pronoun",
        "ADJ": "Adjective", "PREP": "Preposition", "CONJ": "Conjunction",
    })
    out.append(grk_pos_ext.get(pos, pos))

    if pos == "V" and len(parts) >= 2:
        tvm = parts[1]
        # Strip leading digit (2nd aorist etc.)
        prefix_digit = ""
        if tvm[0].isdigit():
            prefix_digit = tvm[0]
            tvm = tvm[1:]
        if len(tvm) >= 3:
            t, v, m = tvm[0], tvm[1], tvm[2]
            tense_desc = GRK_TENSE.get(t, t)
            if prefix_digit == "2":
                tense_desc = "2nd " + tense_desc
            out.append(tense_desc)
            if v in GRK_VOICE: out.append(GRK_VOICE[v])
            if m in GRK_MOOD:  out.append(GRK_MOOD[m])
            # Person/number or case/num/gender follows
            if len(parts) >= 3:
                suffix = parts[2]
                if m in ("I", "S", "O", "M") and len(suffix) >= 2:
                    if suffix[0] in GRK_PERSON: out.append(GRK_PERSON[suffix[0]] + " person")
                    if suffix[1] in GRK_NUMBER: out.append(GRK_NUMBER[suffix[1]])
                elif m == "P" and len(suffix) >= 3:
                    if suffix[0] in GRK_CASE:   out.append(GRK_CASE[suffix[0]])
                    if suffix[1] in GRK_NUMBER: out.append(GRK_NUMBER[suffix[1]])
                    if suffix[2] in GRK_GENDER: out.append(GRK_GENDER[suffix[2]])
    elif pos in ("N", "A", "T", "R", "P") and len(parts) >= 2:
        suffix = parts[1]
        if len(suffix) >= 3:
            c_, n_, g_ = suffix[0], suffix[1], suffix[2]
            if c_ in GRK_CASE:   out.append(GRK_CASE[c_])
            if n_ in GRK_NUMBER: out.append(GRK_NUMBER[n_])
            if g_ in GRK_GENDER: out.append(GRK_GENDER[g_])
    return out


# ============================================================
#  TAHOT / TAGNT parser
# ============================================================

WORD_LINE_RE = re.compile(
    r"^(?P<ref>[A-Za-z0-9]+)\.(?P<ch>\d+)\.(?P<vs>\d+)"
    r"(?:\(\d+\.\d+\))?"           # optional alt versification like "(32.2)"
    r"(?:\[\w+\])?"                # optional bracketed edition tag
    r"#(?P<w>\d+)(?:=\w+)?\s+(?P<rest>.+)$"
)


def clean_strongs_list(raw: str, lang: str) -> list[str]:
    """Extract Strong's numbers from the STEPBible dStrongs column.
    Examples:
      "H9002/{H0776G}"    → ["H9002","H0776G"]
      "H9009/{H0776}\\H9016" → ["H9009","H0776","H9016"]
      "{H0430G}"          → ["H0430G"]
    Splits on `/` (morpheme separator) AND `\\` (appended punctuation
    marker), drops `{` `}` wrappers, strips `_A/_B` instance suffixes.
    """
    if not raw:
        return []
    # Split on `/` first, then on `\` within each piece
    cleaned = raw.replace("{", "").replace("}", "")
    tokens = []
    for part in cleaned.split("/"):
        tokens.extend(part.split("\\"))
    out = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # Strip trailing instance markers (_A, _B, etc.)
        t = re.sub(r"_[A-Za-z]+$", "", t)
        if re.match(r"^[HG]\d+[A-Za-z]?$", t):
            out.append(t)
    return out


def normalize_strongs_key(s: str) -> str:
    """Ensure H/G prefix + 4-digit pad. H1 → H0001; H9003 → H9003."""
    m = re.match(r"^([HG])(\d+)([A-Za-z]?)$", s)
    if not m:
        return s
    prefix, num, suffix = m.groups()
    return f"{prefix}{int(num):04d}{suffix}"


GREEK_TRANSLIT_RE = re.compile(r"^(.*?)\s*\(([^)]+)\)\s*$")


def parse_tahot_line(line: str, lang: str):
    """Parse one word line. Returns dict or None.

    TAHOT (Hebrew) columns:
      0: Hebrew word
      1: Transliteration
      2: English gloss
      3: dStrongs (with / and \\ separators, braces, etc.)
      4: Grammar code (HC/Td/Ncfsa)

    TAGNT (Greek) columns:
      0: Greek word + translit in parens, e.g. "Βίβλος (Biblos)"
      1: English gloss
      2: Strong's=Morph, e.g. "G0976=N-NSF"
      3: Lemma=gloss, e.g. "βίβλος=book"
      4: Edition tags
    """
    line = line.rstrip("\n").rstrip("\r")
    if not line or line.startswith("#") or line.startswith("Eng "):
        return None
    m = WORD_LINE_RE.match(line)
    if not m:
        return None
    cols = m.group("rest").split("\t")

    def c(i): return cols[i] if i < len(cols) else ""

    if lang == "heb":
        orig = c(0).strip()
        trans = c(1).strip()
        gloss = c(2).strip()
        strongs_raw = c(3).strip()
        morph = c(4).strip()
    else:  # grk
        orig_field = c(0).strip()
        gloss = c(1).strip()
        strongs_field = c(2).strip()
        # Split word + translit
        t = GREEK_TRANSLIT_RE.match(orig_field)
        if t:
            orig = t.group(1).strip()
            trans = t.group(2).strip()
        else:
            orig = orig_field
            trans = ""
        # Split "G0976=N-NSF" → strongs="G0976", morph="N-NSF"
        if "=" in strongs_field:
            strongs_raw, morph = strongs_field.split("=", 1)
        else:
            strongs_raw, morph = strongs_field, ""

    strongs = [normalize_strongs_key(s) for s in clean_strongs_list(strongs_raw, lang)]
    # Only real (non-H9xxx, non-G9xxx) Strong's get concordance entries.
    real_strongs = [s for s in strongs
                    if not (s.startswith("H9") or s.startswith("G9"))]

    morph_en = parse_heb_morph(morph) if lang == "heb" else parse_grk_morph(morph)

    return {
        "ref": (m.group("ref"), int(m.group("ch")), int(m.group("vs")), int(m.group("w"))),
        "orig": orig,
        "trans": trans,
        "gloss": gloss,
        "strongs": strongs,
        "real_strongs": real_strongs,
        "morph": morph,
        "morph_en": morph_en,
    }


def parse_stepbible_file(path: Path, lang: str):
    """Yield parsed word records from a TAHOT/TAGNT file."""
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            rec = parse_tahot_line(line, lang)
            if rec:
                yield rec


# ============================================================
#  Main build
# ============================================================

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_BOOKS.mkdir(parents=True, exist_ok=True)

    # 1. Load Strong's dictionaries
    print("Loading Strong's dictionaries…")
    heb_raw = load_strongs(STRONGS_HEBREW_JS, "H")
    grk_raw = load_strongs(STRONGS_GREEK_JS, "G")
    heb_dict = normalize_strongs(heb_raw, "H")
    grk_dict = normalize_strongs(grk_raw, "G")
    (OUT / "strongs-hebrew.json").write_text(json.dumps(heb_dict, ensure_ascii=False), encoding="utf-8")
    (OUT / "strongs-greek.json").write_text(json.dumps(grk_dict, ensure_ascii=False), encoding="utf-8")
    print(f"  Hebrew: {len(heb_dict)} entries, Greek: {len(grk_dict)} entries")

    # 2. Walk TAHOT + TAGNT; bucket by book
    concordance = {}  # strongs_id → list of [book_slug, ch, vs, wi]
    books_data = {}   # slug → {name, section, chapters:{ch:{vs:{wi:word}}}}

    def ingest(files, lang):
        for fp in files:
            if not fp.exists():
                print(f"  MISSING {fp}")
                continue
            print(f"  Reading {fp.name}…")
            count = 0
            for rec in parse_stepbible_file(fp, lang):
                code, ch, vs, wi = rec["ref"]
                if code not in CODE_TO_BOOK:
                    continue
                slug, name, section = CODE_TO_BOOK[code]
                if slug not in books_data:
                    books_data[slug] = {
                        "slug": slug, "name": name, "section": section,
                        "lang": lang,
                        "chapters": {},
                    }
                chapters = books_data[slug]["chapters"]
                chapters.setdefault(ch, {}).setdefault(vs, {})[wi] = rec
                for sid in rec["real_strongs"]:
                    concordance.setdefault(sid, []).append([slug, ch, vs, wi])
                count += 1
            print(f"    {count:,} words ingested")

    print("Parsing Hebrew OT (TAHOT)…")
    ingest(TAHOT_FILES, "heb")
    print("Parsing Greek NT (TAGNT)…")
    ingest(TAGNT_FILES, "grk")

    # 3. Write per-book JSON and compute totals
    print("Writing per-book JSON…")
    total_words = 0
    total_verses = 0
    manifest = []
    for slug, name, section in BOOK_ORDER:
        if slug not in books_data:
            continue
        bk = books_data[slug]
        # Sort chapters and verses; flatten to compact structure
        chapters_out = []
        book_word_count = 0
        book_verse_count = 0
        for ch_num in sorted(bk["chapters"].keys()):
            verses_out = []
            for vs_num in sorted(bk["chapters"][ch_num].keys()):
                words = bk["chapters"][ch_num][vs_num]
                word_list = [words[wi] for wi in sorted(words.keys())]
                # Strip transient keys, keep only what the reader needs
                clean_words = []
                for w in word_list:
                    clean_words.append({
                        "orig": w["orig"],
                        "trans": w["trans"],
                        "gloss": w["gloss"],
                        "strongs": w["real_strongs"],   # only real ones for click
                        "morph": w["morph"],
                        "morph_en": w["morph_en"],
                    })
                verses_out.append({"n": vs_num, "w": clean_words})
                book_word_count += len(clean_words)
                book_verse_count += 1
            chapters_out.append({"n": ch_num, "v": verses_out})
        book_json = {
            "slug": slug, "name": name, "section": section, "lang": bk["lang"],
            "chapters": chapters_out,
        }
        (OUT_BOOKS / f"{slug}.json").write_text(
            json.dumps(book_json, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        manifest.append({
            "slug": slug, "name": name, "section": section, "lang": bk["lang"],
            "chapters": len(chapters_out),
            "verses": book_verse_count,
            "words": book_word_count,
        })
        total_words += book_word_count
        total_verses += book_verse_count
        print(f"    {name}: {len(chapters_out)} ch, {book_verse_count:,} v, {book_word_count:,} w")

    # 4. Write concordance + manifest
    # Trim concordance to only Strong's that exist in our dictionaries to
    # avoid dangling references.
    known_strongs = set(heb_dict.keys()) | set(grk_dict.keys())
    trimmed = {k: v for k, v in concordance.items() if k in known_strongs}
    (OUT / "concordance.json").write_text(
        json.dumps(trimmed, separators=(",", ":")),
        encoding="utf-8",
    )
    (OUT / "manifest.json").write_text(
        json.dumps({
            "books": manifest,
            "total_verses": total_verses,
            "total_words": total_words,
            "unique_strongs": len(trimmed),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nTotals: {len(manifest)} books, {total_verses:,} verses, {total_words:,} words, "
          f"{len(trimmed):,} unique Strong's numbers with occurrences")


if __name__ == "__main__":
    build()

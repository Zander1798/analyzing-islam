"""
Extract Lane's Lexicon definitions for each of the 1651 Quranic roots.
Outputs: site/read-external/quran/data/definitions.json
"""
import sqlite3, json, re, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\.tmp\lanes-lexicon-extracted\lexicon.sqlite'
LEXICON_PATH = r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site\read-external\quran\data\lexicon.json'
OUT_PATH = r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\site\read-external\quran\data\definitions.json'


# ── Arabic normalisation ──────────────────────────────────────────────────────
# Strip harakat (U+064B–U+065F) and normalize alef variants to bare alef
DIACRITICS = re.compile(r'[ً-ٰٟ]')
ALEF_VARIANTS = str.maketrans('أإآٱ', 'ااaa'.replace('a', 'ا'))

def normalize(s):
    s = DIACRITICS.sub('', s)
    s = s.translate(ALEF_VARIANTS)
    return s


# ── Build lookup: normalized root → Lane's root id ───────────────────────────
db = sqlite3.connect(DB_PATH)
cur = db.cursor()
cur.execute('SELECT id, word FROM root')
norm_to_id = {}
for rid, word in cur.fetchall():
    key = normalize(word)
    if key not in norm_to_id:
        norm_to_id[key] = rid


# ── XML → plain English extraction ───────────────────────────────────────────
def strip_xml(xml):
    """Remove all XML tags, decode common entities."""
    text = re.sub(r'<[^>]+>', ' ', xml)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_italic(xml):
    """Return text inside <hi rend=\"ital\">...</hi> tags, joined."""
    parts = re.findall(r'<hi rend="ital">(.*?)</hi>', xml, re.DOTALL)
    result = []
    for p in parts:
        t = strip_xml(p).strip()
        if t:
            result.append(t)
    return ' '.join(result)

def clean_definition(raw, max_chars=320):
    """Trim to a readable length, ending at a sentence boundary if possible."""
    if not raw:
        return ''
    raw = raw.strip()
    # Try to end at a sentence boundary within max_chars
    if len(raw) <= max_chars:
        return raw
    truncated = raw[:max_chars]
    # Find last period/semicolon before the limit
    for sep in ('.', ';', ','):
        idx = truncated.rfind(sep)
        if idx > max_chars // 2:
            return truncated[:idx + 1]
    return truncated.rstrip() + '…'


# ── Main ──────────────────────────────────────────────────────────────────────
with open(LEXICON_PATH, encoding='utf-8') as f:
    lexicon = json.load(f)

hit = 0
miss = 0
definitions = {}

def fallback_keys(root):
    """Return alternative normalized keys to try for a root."""
    key = normalize(root)
    yield key
    if key.endswith('ي'):
        yield key[:-1] + 'ى'   # ي → ى (alef maqsura)
        yield key[:-1] + 'و'   # ي → و (waw weak roots)
    if key.endswith('و'):
        yield key[:-1] + 'ى'
        yield key[:-1] + 'ي'
    if key.endswith('ى'):
        yield key[:-1] + 'ي'
        yield key[:-1] + 'و'
    # Doubled final consonant → undoubled (ربب → رب, ضلل → ضل)
    if len(key) == 3 and key[1] == key[2]:
        yield key[:2]
    elif len(key) == 3 and key[0] == key[1]:
        yield key[1:]


# Build bword → root-word lookup (for cross-reference resolution)
cur.execute('SELECT bword, word FROM root')
bword_to_word = {}
for bword, word in cur.fetchall():
    if bword not in bword_to_word:
        bword_to_word[bword] = word

PTR_RE = re.compile(r'<ptr[^>]+pointing="([^"]+)"')

for root, lex_entry in lexicon.items():
    rid = None
    for key in fallback_keys(root):
        rid = norm_to_id.get(key)
        if rid is not None:
            break

    if rid is None:
        miss += 1
        definitions[root] = None
        continue

    # Get all entries for this root, ordered by nodenum/id
    cur.execute(
        'SELECT xml FROM entry WHERE root IN (SELECT word FROM root WHERE id=?) ORDER BY id LIMIT 5',
        (rid,)
    )
    rows = cur.fetchall()
    if not rows:
        miss += 1
        definitions[root] = None
        continue

    # Try to extract italic (English definition) text from entries in order
    # Follow cross-references (See <ptr pointing="bword">)
    visited_rids = {rid}
    queue_rids = [rid]
    rows_all = list(rows)

    for (xml,) in rows:
        if not xml:
            continue
        ptr_match = PTR_RE.search(xml)
        if ptr_match:
            target_bword = ptr_match.group(1)
            target_word = bword_to_word.get(target_bword)
            if target_word:
                target_norm = normalize(target_word)
                target_rid = norm_to_id.get(target_norm)
                if target_rid and target_rid not in visited_rids:
                    visited_rids.add(target_rid)
                    cur.execute(
                        'SELECT xml FROM entry WHERE root IN (SELECT word FROM root WHERE id=?) ORDER BY id LIMIT 5',
                        (target_rid,)
                    )
                    rows_all.extend(cur.fetchall())

    defn = ''
    for (xml,) in rows_all:
        if not xml:
            continue
        # Skip pure cross-references
        if PTR_RE.search(xml) and '<hi rend' not in xml:
            continue
        italic = extract_italic(xml)
        if italic and len(italic) > 15:
            defn = clean_definition(italic)
            break

    if defn:
        hit += 1
        definitions[root] = defn
    else:
        miss += 1
        definitions[root] = None

print(f'Matched: {hit}/{len(lexicon)}  Missing: {miss}')

# Check how many are None
none_count = sum(1 for v in definitions.values() if v is None)
print(f'Definitions found: {len(definitions) - none_count}  No definition: {none_count}')

# Print a few samples
samples = [(k, v) for k, v in definitions.items() if v][:5]
for root, defn in samples:
    print(f'\n{root}: {defn[:120]}')

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(definitions, f, ensure_ascii=False, indent=None, separators=(',', ':'))

print(f'\nWrote {OUT_PATH}')

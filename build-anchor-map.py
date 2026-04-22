#!/usr/bin/env python3
"""Build old-anchor → sunnah.com idInBook mapping for Bukhari and Muslim.

The existing site/read/bukhari.html and muslim.html use legacy anchor schemes:
  Bukhari: v{vol}b{book}n{num}    (Muhsin Khan Vol/Book/Number)
  Muslim:  b{book}n{num:04d}      (Abd al-Baqi Book/Number)

We're switching to sunnah.com's idInBook scheme (#h{idInBook}). The sunnah.com
JSON doesn't carry the legacy reference numbers, so we fingerprint hadith
English text — both sources share the Muhsin Khan / Darussalam translation
verbatim (modulo pdftotext hyphenation artifacts) — and match them up.

Output: anchor-map-bukhari.json, anchor-map-muslim.json
Format: {"v1b1n1": 1, "v5b58n234": 3731, ...}

Any hadith that can't be confidently matched is logged for manual review.
"""
import html as html_lib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
OLD_BUKHARI = ROOT / "site" / "read" / "bukhari.html.old"
OLD_MUSLIM = ROOT / "site" / "read" / "muslim.html.old"
NEW_BUKHARI_JSON = ROOT / "hadith-json" / "bukhari.json"
NEW_MUSLIM_JSON = ROOT / "hadith-json" / "muslim.json"

OUT_BUKHARI = ROOT / "anchor-map-bukhari.json"
OUT_MUSLIM = ROOT / "anchor-map-muslim.json"


# Systematic translation differences between the old Darussalam PDF text and
# the sunnah.com version. Both use the Muhsin Khan translation — but sunnah.com
# applies a "messenger"-over-"apostle" substitution throughout, plus a few
# other small normalisations. Applying these BEFORE fingerprinting lets the
# same content match.
_SYNONYMS = [
    (r"\bapostles?\b", "messenger"),   # "Apostle" -> "Messenger"
    (r"\bhis apostle\b", "his messenger"),
    (r"\ballahs apostle\b", "allahs messenger"),
]
_SYNONYM_RES = [(re.compile(pat), repl) for pat, repl in _SYNONYMS]


def normalize(s: str) -> str:
    """Lowercase, decode HTML entities, undo soft-hyphen line-break artifacts,
    apply synonym map, strip punctuation, collapse whitespace."""
    s = html_lib.unescape(s)
    # Undo "re- vealed" -> "revealed" style PDF hyphenation
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)
    # Strip diacritics so "Allāh" == "Allah"
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Remove salawat marker (ﷺ) and related artifacts
    s = s.replace("(ﷺ)", "").replace("ﷺ", "")
    # Drop all non-alnum -> space
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    # Apply synonym normalisation
    for pat, repl in _SYNONYM_RES:
        s = pat.sub(repl, s)
    # Collapse whitespace
    s = " ".join(s.split())
    return s


def fingerprint(s: str, word_count: int = 12) -> str:
    return " ".join(normalize(s).split()[:word_count])


def word_bag(s: str, top_n: int = 20) -> frozenset:
    """Distinctive content words: drop common stopwords and take first N unique."""
    words = normalize(s).split()
    stop = {
        "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at",
        "for", "with", "by", "from", "as", "is", "are", "was", "were", "be",
        "been", "being", "he", "she", "it", "they", "we", "i", "you", "me",
        "him", "her", "them", "us", "his", "hers", "its", "their", "our", "my",
        "your", "that", "this", "these", "those", "said", "says", "asked",
        "then", "so", "not", "no", "do", "does", "did", "has", "have", "had",
        "if", "when", "who", "what", "which", "how", "why", "will", "would",
        "may", "can", "could", "should", "shall", "also", "any", "some", "one",
        "two", "all", "upon", "about", "like", "such", "there", "here",
    }
    seen = []
    for w in words:
        if len(w) > 2 and w not in stop and w not in seen:
            seen.append(w)
            if len(seen) >= top_n:
                break
    return frozenset(seen)


# --- Parse old readers ---

OLD_HADITH_RE = re.compile(
    r'<article class="hadith" id="(?P<id>[^"]+)">.*?'
    r'(?:<div class="hadith-narrator">(?P<narrator>.*?)</div>)?'
    r'\s*(?P<paras>(?:<p>.*?</p>\s*)+)'
    r'</div>\s*</article>',
    re.S,
)
OLD_PARA_RE = re.compile(r"<p>(.*?)</p>", re.S)


def parse_old_reader(path: Path) -> list[dict]:
    """Return list of {id, narrator, text, fp_body, bag} for each hadith."""
    txt = path.read_text(encoding="utf-8")
    out = []
    for m in OLD_HADITH_RE.finditer(txt):
        hid = m.group("id")
        narrator = (m.group("narrator") or "").strip()
        paras = OLD_PARA_RE.findall(m.group("paras"))
        body = " ".join(paras).strip()
        combined = (narrator + " " + body).strip() if narrator else body
        out.append({
            "id": hid,
            "narrator": narrator,
            "body": body,
            "fp_narr_body": fingerprint(combined, 12),
            "fp_body": fingerprint(body, 12),
            "fp_body_long": fingerprint(body, 24),
            "bag": word_bag(combined, 20),
        })
    return out


# --- Load new JSON and index ---

def load_new_hadiths(json_path: Path) -> list[dict]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    out = []
    for h in data["hadiths"]:
        eng = h.get("english") or {}
        narrator = (eng.get("narrator") or "").strip()
        text = (eng.get("text") or "").strip()
        combined = (narrator + " " + text).strip() if narrator else text
        out.append({
            "idInBook": h["idInBook"],
            "narrator": narrator,
            "text": text,
            "fp_narr_text": fingerprint(combined, 12),
            "fp_text": fingerprint(text, 12),
            "fp_text_long": fingerprint(text, 24),
            "bag": word_bag(combined, 20),
        })
    # Sort by idInBook for positional matching.
    out.sort(key=lambda x: x["idInBook"])
    return out


def build_indexes(new_hadiths: list[dict]) -> dict:
    """Multiple-key indexes for cascading match strategies."""
    by_narr_text = {}
    by_text = {}
    by_text_long = {}
    for h in new_hadiths:
        for key, d in [
            (h["fp_narr_text"], by_narr_text),
            (h["fp_text"], by_text),
            (h["fp_text_long"], by_text_long),
        ]:
            if not key:
                continue
            d.setdefault(key, []).append(h["idInBook"])
    return {"narr_text": by_narr_text, "text": by_text, "text_long": by_text_long}


def try_fingerprint(old: dict, idx: dict) -> int | None:
    """Fast path: unique fingerprint match. Return idInBook or None."""
    for key, field in [("text_long", "fp_body_long"),
                       ("narr_text", "fp_narr_body"),
                       ("text", "fp_body")]:
        cands = idx[key].get(old[field], [])
        if len(cands) == 1:
            return cands[0]
    return None


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def sliding_window_best(old: dict, new_list: list[dict], center_id: int,
                        window: int = 80, min_jaccard: float = 0.45) -> int | None:
    """Search within [center_id - window, center_id + window] in new_list (which
    is sorted by idInBook) for the best-Jaccard match. Return idInBook of the
    best match if its similarity beats `min_jaccard` and outpaces the
    runner-up by a margin."""
    # Binary-search-ish: find index whose idInBook >= center_id.
    # Since idInBook is dense 1..N, we can just index directly.
    n = len(new_list)
    # Find position — new_list[pos]["idInBook"] == center_id if present.
    lo = max(0, center_id - window - 1)
    hi = min(n, center_id + window)
    best = (0.0, None)
    runner_up = 0.0
    old_bag = old["bag"]
    for i in range(lo, hi):
        score = jaccard(old_bag, new_list[i]["bag"])
        if score > best[0]:
            runner_up = best[0]
            best = (score, new_list[i]["idInBook"])
        elif score > runner_up:
            runner_up = score
    if best[0] >= min_jaccard and (best[0] - runner_up) >= 0.05:
        return best[1]
    return None


def build_map(old: list[dict], idx: dict, new_list: list[dict], label: str):
    m = {}
    phase1 = 0
    phase2 = 0
    ambiguous = []
    missing = []
    for i, o in enumerate(old):
        # Phase 1: deterministic fingerprint.
        hit = try_fingerprint(o, idx)
        if hit is not None:
            m[o["id"]] = hit
            phase1 += 1
            continue
        # Phase 2: positional word-bag Jaccard. Use the old reader's sequence
        # position `i` as the expected idInBook center (old + new both ordered
        # roughly the same way).
        center = i + 1
        hit = sliding_window_best(o, new_list, center_id=center)
        if hit is not None:
            m[o["id"]] = hit
            phase2 += 1
        else:
            # Record best candidate lists we have for review.
            cands = (
                idx["text_long"].get(o["fp_body_long"])
                or idx["narr_text"].get(o["fp_narr_body"])
                or idx["text"].get(o["fp_body"])
                or []
            )
            if cands:
                ambiguous.append((o["id"], cands[:10]))
            else:
                missing.append(o["id"])
    print(f"  {label}: total={len(old)}  phase1-fingerprint={phase1}  "
          f"phase2-positional={phase2}  ambiguous={len(ambiguous)}  unmatched={len(missing)}")
    if ambiguous:
        print(f"    sample ambiguous: {ambiguous[:3]}")
    if missing:
        print(f"    sample unmatched: {missing[:5]}")
    return m, ambiguous, missing


def refine_with_difflib(old_list: list[dict], map_so_far: dict,
                        new_list: list[dict], cited_anchors: set[str]) -> int:
    """For every CITED anchor not yet mapped, do a quality difflib match
    against the full new list. Returns number of additional matches added
    directly to `map_so_far`."""
    from difflib import SequenceMatcher
    added = 0
    unmapped_cited = [o for o in old_list
                      if o["id"] in cited_anchors and o["id"] not in map_so_far]
    for o in unmapped_cited:
        old_norm = normalize(o["narrator"] + " " + o["body"])[:400]
        best_ratio = 0.0
        best_id = None
        for n in new_list:
            new_norm = normalize(n["narrator"] + " " + n["text"])[:400]
            sm = SequenceMatcher(None, old_norm, new_norm, autojunk=False)
            r = sm.ratio()
            if r > best_ratio:
                best_ratio = r
                best_id = n["idInBook"]
        if best_ratio >= 0.70 and best_id is not None:
            map_so_far[o["id"]] = best_id
            added += 1
    return added


def main() -> None:
    print("Parsing old readers...")
    old_b = parse_old_reader(OLD_BUKHARI)
    old_m = parse_old_reader(OLD_MUSLIM)
    print(f"  Bukhari: {len(old_b)} hadiths in old HTML")
    print(f"  Muslim:  {len(old_m)} hadiths in old HTML")

    print("\nLoading sunnah.com JSON...")
    new_b = load_new_hadiths(NEW_BUKHARI_JSON)
    new_m = load_new_hadiths(NEW_MUSLIM_JSON)
    print(f"  Bukhari: {len(new_b)} hadiths in sunnah.com JSON")
    print(f"  Muslim:  {len(new_m)} hadiths in sunnah.com JSON")

    print("\nBuilding indexes...")
    idx_b = build_indexes(new_b)
    idx_m = build_indexes(new_m)

    print("\nMatching...")
    map_b, amb_b, miss_b = build_map(old_b, idx_b, new_b, "Bukhari")
    map_m, amb_m, miss_m = build_map(old_m, idx_m, new_m, "Muslim")

    # Phase 3: for anchors actually cited by the catalog but still unmapped,
    # spend more effort with difflib ratio matching against all new hadiths.
    print("\nPhase 3: difflib refinement for cited-but-unmapped anchors...")
    cited_b = _load_cited_anchors(r'href="\.\./read/bukhari\.html#(v\d+b\d+n\d+)"')
    cited_m = _load_cited_anchors(r'href="\.\./read/muslim\.html#(b\d+n\d+)"')
    added_b = refine_with_difflib(old_b, map_b, new_b, cited_b)
    added_m = refine_with_difflib(old_m, map_m, new_m, cited_m)
    print(f"  Bukhari: refined +{added_b} (cited-unmapped pool)")
    print(f"  Muslim:  refined +{added_m} (cited-unmapped pool)")

    # Report final cited coverage.
    b_cov = sum(1 for a in cited_b if a in map_b)
    m_cov = sum(1 for a in cited_m if a in map_m)
    print(f"\nFinal cited-anchor coverage:")
    print(f"  Bukhari: {b_cov}/{len(cited_b)} "
          f"({100*b_cov/max(1,len(cited_b)):.1f}%)  "
          f"unmapped: {sorted(a for a in cited_b if a not in map_b)}")
    print(f"  Muslim:  {m_cov}/{len(cited_m)} "
          f"({100*m_cov/max(1,len(cited_m)):.1f}%)  "
          f"unmapped: {sorted(a for a in cited_m if a not in map_m)}")

    OUT_BUKHARI.write_text(
        json.dumps({"map": map_b}, indent=2),
        encoding="utf-8",
    )
    OUT_MUSLIM.write_text(
        json.dumps({"map": map_m}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {OUT_BUKHARI.name} and {OUT_MUSLIM.name}")


def _load_cited_anchors(href_pattern: str) -> set[str]:
    """Walk site/catalog/*.html + site/category/*.html, return the set of
    anchor fragments that appear in hrefs matching `href_pattern`."""
    import os
    out = set()
    for root in [ROOT / "site" / "catalog", ROOT / "site" / "category"]:
        if not root.exists():
            continue
        for f in os.listdir(root):
            if not f.endswith(".html"):
                continue
            txt = (root / f).read_text(encoding="utf-8")
            out.update(re.findall(href_pattern, txt))
    return out


if __name__ == "__main__":
    main()

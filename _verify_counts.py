import re, json
from pathlib import Path
from collections import defaultdict

source_map = {
    "bukhari.html":"bukhari","muslim.html":"muslim","abu-dawud.html":"abu-dawud",
    "tirmidhi.html":"tirmidhi","nasai.html":"nasai","ibn-majah.html":"ibn-majah",
}
catalog_dir = Path("site/catalog")
catalog = json.loads(Path("site/assets/data/catalog-entries.json").read_text(encoding="utf-8"))
json_counts = defaultdict(int)
for e in catalog:
    json_counts[e["source"]] += 1

pattern = re.compile(r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=')
print("Source         HTML   JSON   OK")
all_ok = True
for fname, source in source_map.items():
    content = (catalog_dir / fname).read_text(encoding="utf-8", errors="ignore")
    html_count = len(pattern.findall(content))
    jc = json_counts.get(source, 0)
    ok = html_count == jc
    if not ok:
        all_ok = False
    print(f"  {source:<14} {html_count:>4}   {jc:>4}   {'YES' if ok else 'MISMATCH'}")

print()
print(f"Total JSON entries: {len(catalog)}")
print(f"All counts match:   {all_ok}")

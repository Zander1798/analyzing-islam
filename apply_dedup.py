import re, json, shutil
from pathlib import Path
from collections import defaultdict

source_map = {
    "quran.html":"quran","bukhari.html":"bukhari","muslim.html":"muslim",
    "abu-dawud.html":"abu-dawud","tirmidhi.html":"tirmidhi",
    "nasai.html":"nasai","ibn-majah.html":"ibn-majah",
}
catalog_dir = Path("site/catalog")
html_entries = []
for fname, source in source_map.items():
    content = (catalog_dir / fname).read_text(encoding="utf-8", errors="ignore")
    opens = list(re.finditer(r'<div\s+class=["\'][^"\']*\bentry\b[^"\']*["\'][^>]+id=["\']([^"\']+)["\'][^>]*>', content))
    for i, m in enumerate(opens):
        eid = m.group(1)
        tag_text = m.group(0)
        end = opens[i+1].start() if i+1 < len(opens) else m.start()+3000
        chunk = content[m.start():min(end, m.start()+3000)]
        cat_m = re.search(r'data-category=["\']([^"\']*)["\']', tag_text)
        str_m = re.search(r'data-strength=["\']([^"\']*)["\']', tag_text)
        title_m = re.search(r'class=["\'][^"\']*entry-title[^"\']*["\'][^>]*>(.*?)</span>', chunk, re.DOTALL)
        ref_m = re.search(r'class=["\'][^"\']*\bref\b[^"\']*["\'][^>]*>.*?<a[^>]*>(.*?)</a>', chunk, re.DOTALL)
        html_entries.append({
            "id": eid, "source": source,
            "title": re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else "",
            "ref": re.sub(r'<[^>]+>', '', ref_m.group(1)).strip() if ref_m else "",
            "categories": cat_m.group(1).split() if cat_m else [],
            "strength": str_m.group(1).strip() if str_m else "",
            "url": f"catalog/{fname}#{eid}",
        })

remove_set = {
    # BUKHARI
    "fly-wing-dip-drink-cure","prophet-fondled-menstruating-wife","flee-battle-major-sin",
    "nine-wives-one-round","muslim-not-killed-for-kafir-diya","allah-visits-earth-third-of-night",
    "prophet-kissed-aisha-during-fast","prophet-cursed-those-making-pictures",
    "bukhari-3151-satan-touches-every-newborn-except-jesus","angels-avoid-dog-picture",
    "uthman-burned-variant-codices","bukhari-4785-quran-seven-recitations-both-valid",
    "dog-donkey-women-pass-prayer","bukhari-5659-effeminate-cursed-expelled",
    "muhammad-threats-burn-houses","banu-qurayza-massacre-detail","bukhari-2807-stones-betray-jews",
    "aisha-six-nine-consummation","bukhari-2076-slave-girl-flogged-sold","muhammad-suicide",
    "allah-changes-mind-prayer-count","allah-changed-mind-prayers","urine-splash-torture",
    "cupping-specific-days",
    # ABU DAWUD
    "fly-dunk-dawud-confirms","convert-circumcision-hair","abu-dawud-riba-curses",
    "whoever-changes-religion-execute","four-month-waiting-period","hell-seven-gates-dawud",
    "safiyyah-emancipation-mahr-dawud","abu-dawud-4404-hand-theft-quarter-dinar",
    "black-dog-shaitan-invalidates-prayer","night-raid-children-women-dawud",
    # IBN MAJAH
    "ibnmajah-kill-whoever-abandons-islam","ibnmajah-pen-first-created-write",
    "ibnmajah-prophet-cursed-paint-artist","ibnmajah-allah-descends-end-night-cry",
    "ibnmajah-amputation-thief-hand-dinar","ibnmajah-aisha-young",
    "ibnmajah-jinn-eavesdrop-soothsayers","ibnmajah-wife-refuse-bed-angels-curse-morning",
    # MUSLIM
    "the-dajjal-will-be-followed-by-70-000-jews-of-isfahan-wearin-882183da",
    "muslim-kill-jews-dajjal-army","muslim-silver-gold-utensils-forbidden-men",
    "muslim-jesus-descends-kills-swine-breaks-cross","expel-arabia-multi-religion",
    "tree-stone-tell-hiding-jew","gecko-hundred-rewards","ibn-sayyad-dajjal-child",
    "satan-blood-circulation","muslim-apostate-three-categories-kill","muslim-spit-left-after-dream",
    "muslim-sun-prostrates-beneath-throne",
    "the-sun-prostrates-under-allah-s-throne-every-night-and-asks-b0b69753",
    "muslim-women-children-night-raid-incidental","muslim-woman-refuses-bed-angels-curse",
    # NASAI
    "nasai-whoever-changes-religion-kill-him","nasai-fornicator-flogged-exiled",
    "nasai-slave-marriage-no-wali-fornicator","nasai-wife-ghusl-husband-command",
    "nasai-wife-as-tilth-however-you-wish","nasai-khutbah-last-words-final-sermon",
    "nasai-urine-left-hand-not-right","nasai-jihad-women-cannot-lead-prayer",
    "nasai-wife-deserts-bed-angels-curse",
    # QURAN
    "quran-recite-jealousy-envy-refuge","quran-unjust-acquittal-womens-lashes",
    "quran-slaves-half-hudud","quran-private-parts-except-captives",
    "quran-adultery-hundred-lashes","quran-harut-marut-teaching-magic",
    "quran-qiblah-abrogation","quran-qisas-slave-free-unequal","quran-wives-tilth-field",
    "quran-halala-intermediate-husband","quran-two-women-one-man-witness","quran-zaynab-detailed",
    "quran-male-double-inheritance","quran-muhsanat-captive-exception","quran-marry-two-three-four",
    "quran-beat-wife-after-admonish","quran-moon-split-miracle","quran-jews-most-hostile",
    "quran-iddah-prepubescent-divorce","quran-no-changing-words","quran-strike-necks-polytheists",
    "quran-20-vs-200-abrogated","quran-captives-massacre-first","quran-allah-locks-hearts",
    "do-not-compel-your-slave-girls-to-prostitution-if-they-desir-40074e30",
    "quran-good-evil-from-yourself-contradiction","quran-arabs-lovers-of-arabic",
    # TIRMIDHI
    "tirmidhi-food-mention-allah","tirmidhi-hijab-cover-face","tirmidhi-hell-complains-breath-heat",
    "tirmidhi-prayer-fire-paradise","tirmidhi-sodomy-death-penalty",
    "tirmidhi-seventy-thousand-paradise-no-reckoning","tirmidhi-kaaba-black-stone",
    "tirmidhi-cat-pure-unique-ruling","tirmidhi-adultery-100-lashes",
    "tirmidhi-3617-jesus-buried-next-to-muhammad","tirmidhi-newborn-cry-satan-pinch",
    "tirmidhi-evil-eye-touching",
}

# Exact-ID duplicates within same source (keep first occurrence)
exact_dup_same_source = {"tirmidhi-masturbation-punishment","tirmidhi-prophets-body-no-decay"}

# Load existing JSON for richer metadata
with open("site/assets/data/catalog-entries.json","r",encoding="utf-8") as f:
    existing = {e["id"]: e for e in json.load(f)}

# Build final list from HTML order, skip removes, deduplicate exact-ID same-source
seen_source_id = set()
final = []
for e in html_entries:
    eid = e["id"]
    src = e["source"]
    key = (src, eid)
    if eid in remove_set:
        continue
    if eid in exact_dup_same_source and key in seen_source_id:
        continue
    seen_source_id.add(key)
    final.append(existing.get(eid, e))

shutil.copy("site/assets/data/catalog-entries.json","site/assets/data/catalog-entries.backup2.json")
with open("site/assets/data/catalog-entries.json","w",encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

by_source = defaultdict(int)
for e in final:
    by_source[e["source"]] += 1

print(f"Final catalog-entries.json: {len(final)} entries")
for s,c in sorted(by_source.items()):
    print(f"  {s}: {c}")
print(f"\nRemoved: {len(remove_set) + len(exact_dup_same_source)} entries total")
print(f"  - {len(remove_set)} same-topic duplicates")
print(f"  - {len(exact_dup_same_source)} exact-ID duplicates")

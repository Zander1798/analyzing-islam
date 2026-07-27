import re, json
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
        title_m = re.search(r'class=["\'][^"\']*entry-title[^"\']*["\'][^>]*>(.*?)</span>', chunk, re.DOTALL)
        ref_m = re.search(r'class=["\'][^"\']*\bref\b[^"\']*["\'][^>]*>.*?<a[^>]*>(.*?)</a>', chunk, re.DOTALL)
        html_entries.append({
            "id": eid, "source": source,
            "title": re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else "",
            "ref": re.sub(r'<[^>]+>', '', ref_m.group(1)).strip() if ref_m else "",
        })

confirmed_removes = [
    # BUKHARI
    ("fly-wing-dip-drink-cure","fly-in-drink"),
    ("prophet-fondled-menstruating-wife","wife-sex-body-during-menses"),
    ("flee-battle-major-sin","seven-destructive-sins-listed"),
    ("nine-wives-one-round","thirty-men-strength"),
    ("muslim-not-killed-for-kafir-diya","muslim-killer-protection"),
    ("allah-visits-earth-third-of-night","allah-descends-nightly"),
    ("prophet-kissed-aisha-during-fast","kiss-while-fasting"),
    ("prophet-cursed-those-making-pictures","picture-makers-painful"),
    ("bukhari-3151-satan-touches-every-newborn-except-jesus","satan-pinches-newborn"),
    ("angels-avoid-dog-picture","angels-pictures"),
    ("uthman-burned-variant-codices","uthman-quran-committee"),
    ("bukhari-4785-quran-seven-recitations-both-valid","quran-seven-readings"),
    ("dog-donkey-women-pass-prayer","dog-donkey-woman"),
    ("bukhari-5659-effeminate-cursed-expelled","effeminate-men-cursed"),
    ("muhammad-threats-burn-houses","burn-house-absent"),
    ("banu-qurayza-massacre-detail","banu-qurayza-hadith"),
    ("bukhari-2807-stones-betray-jews","trees-stones-jew-genocide"),
    ("aisha-six-nine-consummation","aisha-age"),
    ("bukhari-2076-slave-girl-flogged-sold","scourge-sell-slave-girl"),
    ("muhammad-suicide","bukhari-fatrat-wahy-suicide-attempts"),
    ("allah-changes-mind-prayer-count","fifty-prayers-negotiation"),
    ("allah-changed-mind-prayers","fifty-prayers-negotiation"),
    ("urine-splash-torture","grave-torture-urine"),
    ("cupping-specific-days","cupping-cauterization-day"),
    # ABU DAWUD
    ("fly-dunk-dawud-confirms","fly-immerse-fully-dawud"),
    ("convert-circumcision-hair","circumcision-required-fitra"),
    ("abu-dawud-riba-curses","riba-ten-parties-cursed"),
    ("whoever-changes-religion-execute","abudawud-apostasy-kill-those-who-change-their-religion"),
    ("four-month-waiting-period","iddah-widow-house-confined"),
    ("hell-seven-gates-dawud","abu-dawud-hell-seven-gates"),
    ("safiyyah-emancipation-mahr-dawud","abudawud-safiyya-manumission-dower"),
    ("abu-dawud-4404-hand-theft-quarter-dinar","amputation-quarter-dinar-thief"),
    ("black-dog-shaitan-invalidates-prayer","prayer-invalidate-dog-woman"),
    ("night-raid-children-women-dawud","abu-dawud-attack-at-night-answer"),
    # IBN MAJAH
    ("ibnmajah-kill-whoever-abandons-islam","ibnmajah-apostate-death"),
    ("ibnmajah-pen-first-created-write","ibnmajah-allah-writes-pen-destiny"),
    ("ibnmajah-prophet-cursed-paint-artist","ibnmajah-cursed-pictures"),
    ("ibnmajah-allah-descends-end-night-cry","ibnmajah-allah-descends-third-night"),
    ("ibnmajah-amputation-thief-hand-dinar","ibnmajah-amputate-hand-dinar"),
    ("ibnmajah-aisha-young","ibnmajah-aisha-marriage-nine-consummation"),
    ("ibnmajah-jinn-eavesdrop-soothsayers","ibnmajah-angels-chain-throne-demons"),
    ("ibnmajah-wife-refuse-bed-angels-curse-morning","ibnmajah-wife-bed-refuse-curse"),
    # MUSLIM
    ("the-dajjal-will-be-followed-by-70-000-jews-of-isfahan-wearin-882183da","dajjal-isfahan-jews"),
    ("muslim-kill-jews-dajjal-army","dajjal-isfahan-jews"),
    ("muslim-silver-gold-utensils-forbidden-men","women-silk-gold"),
    ("muslim-jesus-descends-kills-swine-breaks-cross","jesus-breaks-cross"),
    ("expel-arabia-multi-religion","expel-jews-christians"),
    ("tree-stone-tell-hiding-jew","kill-jews-end-times"),
    ("gecko-hundred-rewards","killing-geckos-earns-religious-reward-472dae67"),
    ("ibn-sayyad-dajjal-child","ibn-sayyad-umar-wanted-to-kill-a-child-suspected-of-being-th-91dd651a"),
    ("satan-blood-circulation","muslim-satan-circulates-in-body-like-blood"),
    ("muslim-apostate-three-categories-kill","apostasy-three-cases"),
    ("muslim-spit-left-after-dream","spit-three-times-to-your-left-side-if-you-have-a-bad-dream-755c5503"),
    ("muslim-sun-prostrates-beneath-throne","muslim-sun-stop-prayer"),
    ("the-sun-prostrates-under-allah-s-throne-every-night-and-asks-b0b69753","muslim-sun-stop-prayer"),
    ("muslim-women-children-night-raid-incidental","night-raid-children"),
    ("muslim-woman-refuses-bed-angels-curse","a-wife-who-refuses-her-husband-s-bed-is-cursed-by-angels-unt-2b91ed75"),
    # NASAI
    ("nasai-whoever-changes-religion-kill-him","nasai-apostate-executed"),
    ("nasai-fornicator-flogged-exiled","nasai-unmarried-100-lashes"),
    ("nasai-slave-marriage-no-wali-fornicator","nasai-slave-cannot-marry-without-master"),
    ("nasai-wife-ghusl-husband-command","nasai-wife-ghusl-cannot-refuse"),
    ("nasai-wife-as-tilth-however-you-wish","nasai-sex-positions-tilth-apology"),
    ("nasai-khutbah-last-words-final-sermon","nasai-khutbah-last-words"),
    ("nasai-urine-left-hand-not-right","nasai-right-hand-private-parts"),
    ("nasai-jihad-women-cannot-lead-prayer","nasai-women-best-prayer-home"),
    ("nasai-wife-deserts-bed-angels-curse","nasai-woman-refusing-bed-curse"),
    # QURAN
    ("quran-recite-jealousy-envy-refuge","quran-evil-eye-protection"),
    ("quran-unjust-acquittal-womens-lashes","quran-slander-80-lashes"),
    ("quran-slaves-half-hudud","quran-slave-woman-half-punishment"),
    ("quran-private-parts-except-captives","quran-right-hand-sex-captive-wife"),
    ("quran-adultery-hundred-lashes","one-hundred-lashes-for-fornication-yet-the-hadith-demands-st-f805f912"),
    ("quran-harut-marut-teaching-magic","angels-teaching-magic-at-babylon-0339d548"),
    ("quran-qiblah-abrogation","the-qibla-change-allah-changes-direction-of-prayer-9fddc906"),
    ("quran-qisas-slave-free-unequal","unequal-retaliation-based-on-social-class-and-sex-8bea2fbf"),
    ("quran-wives-tilth-field","wives-as-a-place-of-cultivation-come-to-them-however-you-wis-8d27a4ac"),
    ("quran-halala-intermediate-husband","nikah-halala-forced-intermediate-marriage-before-remarriage-c8234da7"),
    ("quran-two-women-one-man-witness","two-women-equal-one-man-as-witnesses-2340a3cf"),
    ("quran-zaynab-detailed","zaynab-affair"),
    ("quran-male-double-inheritance","male-inheritance-is-double-female-inheritance-db0a739d"),
    ("quran-muhsanat-captive-exception","sexual-access-to-married-female-slaves-right-hand-possesses-25cd8f4b"),
    ("quran-marry-two-three-four","polygamy-permitted-marry-up-to-four-wives-1e0b5cf4"),
    ("quran-beat-wife-after-admonish","strike-them-permission-to-beat-disobedient-wives-64519343"),
    ("quran-moon-split-miracle","the-moon-was-split-in-two-de5cbd36"),
    ("quran-jews-most-hostile","jews-and-polytheists-are-most-intense-in-animosity-toward-be-d7e2e208"),
    ("quran-iddah-prepubescent-divorce","divorce-rules-for-girls-who-have-not-yet-menstruated-1e9638b8"),
    ("quran-no-changing-words","no-one-can-change-the-words-of-allah-yet-tahrif-is-the-centr-d98f36e4"),
    ("quran-strike-necks-polytheists","cast-terror-into-the-hearts-strike-upon-the-necks-caf4bc42"),
    ("quran-20-vs-200-abrogated","military-prediction-twenty-muslims-defeat-two-hundred-4fd0e052"),
    ("quran-captives-massacre-first","prophet-should-not-take-captives-until-he-inflicts-a-massacr-75d23fb1"),
    ("quran-allah-locks-hearts","allah-seals-disbelievers-hearts-then-punishes-them-for-disbe-cfacf617"),
    ("do-not-compel-your-slave-girls-to-prostitution-if-they-desir-40074e30","quran-not-compel-to-prostitution"),
    ("quran-good-evil-from-yourself-contradiction","good-from-allah-evil-from-yourself-two-verses-apart-direct-c-fe9c886a"),
    ("quran-arabs-lovers-of-arabic","we-have-made-it-an-arabic-quran-why-would-god-prefer-a-langu-ba1f293d"),
    # TIRMIDHI
    ("tirmidhi-food-mention-allah","tirmidhi-bismillah-quran-baraka"),
    ("tirmidhi-hijab-cover-face","tirmidhi-wife-obey-paradise"),
    ("tirmidhi-hell-complains-breath-heat","tirmidhi-hell-complains-heat"),
    ("tirmidhi-prayer-fire-paradise","tirmidhi-hell-complains-heat"),
    ("tirmidhi-sodomy-death-penalty","kill-doer-done-to-tirmidhi"),
    ("tirmidhi-seventy-thousand-paradise-no-reckoning","tirmidhi-seventy-thousand-paradise"),
    ("tirmidhi-kaaba-black-stone","tirmidhi-black-stone-paradise-sins-whitened-blackened"),
    ("tirmidhi-cat-pure-unique-ruling","tirmidhi-cat-pure-purity"),
    ("tirmidhi-adultery-100-lashes","tirmidhi-adultery-100-lashes-graded"),
    ("tirmidhi-3617-jesus-buried-next-to-muhammad","jesus-buried-next-muhammad"),
    ("tirmidhi-newborn-cry-satan-pinch","tirmidhi-newborn-satan-cry"),
    ("tirmidhi-evil-eye-touching","tirmidhi-ruqya-evil-eye"),
]

remove_set = set(r[0] for r in confirmed_removes)
html_ids = {e["id"] for e in html_entries}

present = sum(1 for rid,_ in confirmed_removes if rid in html_ids)
missing_removes = [rid for rid,_ in confirmed_removes if rid not in html_ids]
missing_keeps = [(rid,kid) for rid,kid in confirmed_removes if kid not in html_ids]

print(f"Total in remove list: {len(confirmed_removes)}")
print(f"Present in HTML (to actually remove): {present}")
print(f"Not found in HTML (already gone or wrong ID): {len(missing_removes)}")
if missing_removes:
    for r in missing_removes:
        print(f"  not found: {r}")
print(f"Keep targets missing from HTML: {len(missing_keeps)}")
if missing_keeps:
    for rid,kid in missing_keeps:
        print(f"  PROBLEM: keep={kid} not found (for remove={rid})")

# Exact same-source ID duplicates
seen = {}
exact_dups = []
for e in html_entries:
    key = (e["source"], e["id"])
    if key in seen:
        exact_dups.append((e["source"], e["id"]))
    else:
        seen[key] = True
print(f"\nExact same-source ID duplicates: {len(exact_dups)}")
for s,eid in exact_dups:
    print(f"  [{s}] {eid}")

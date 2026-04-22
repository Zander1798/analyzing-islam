#!/usr/bin/env python3
"""Retag all catalog entries using the 28-category system."""
import re
from pathlib import Path

CATALOG_DIR = Path(r"c:/Users/zande/Documents/AI Workspace/Islam Analysed/site/catalog")

# Canonical 28-category display labels (in chip order)
CATEGORIES = [
    ("abrogation",     "Abrogation"),
    ("scripture",      "Scripture Integrity"),
    ("contradiction",  "Contradictions"),
    ("logic",          "Logical Inconsistency"),
    ("morality",       "Moral Problems"),
    ("allah",          "Allah's Character"),
    ("cosmology",      "Cosmology"),
    ("preislamic",     "Pre-Islamic Borrowings"),
    ("magic",          "Magic & Occult"),
    ("ritual",         "Ritual Absurdities"),
    ("prophet",        "Prophetic Character"),
    ("privileges",     "Prophetic Privileges"),
    ("jesus",          "Jesus / Christology"),
    ("women",          "Women"),
    ("sexual",         "Sexual Issues"),
    ("childmarriage",  "Child Marriage"),
    ("lgbtq",          "LGBTQ / Gender"),
    ("slavery",        "Slavery & Captives"),
    ("hudud",          "Hudud"),
    ("warfare",        "Warfare & Jihad"),
    ("apostasy",       "Apostasy & Blasphemy"),
    ("governance",     "Governance"),
    ("disbelievers",   "Disbelievers"),
    ("antisemitism",   "Antisemitism"),
    ("paradise",       "Paradise"),
    ("hell",           "Hell"),
    ("eschatology",    "Eschatology"),
    ("strange",        "Strange / Obscure"),
]

CATEGORY_TOKENS = [t for t, _ in CATEGORIES]

# Old tag -> baseline new tags (guaranteed migration)
OLD_BASELINE = {
    "abrogation":    ["abrogation"],
    "disbelievers":  ["disbelievers"],
    "jesus":         ["jesus"],
    "women":         ["women"],
    "science":       ["cosmology"],
    "prophet":       ["prophet"],
    "logic":         ["logic"],
    "contradiction": ["contradiction"],
    "strange":       ["strange"],
    "sexual":        ["sexual"],
    "violence":      [],  # will resolve via keywords to hudud / warfare
    "antisemitism":  ["antisemitism"],
    "eschatology":   ["eschatology"],
    "medical":       ["magic"],
}
# Self-mapping for every new token so reruns preserve already-migrated tags
for _tok, _ in CATEGORIES:
    OLD_BASELINE.setdefault(_tok, [_tok])

# Keyword rules: token -> list of regex patterns; if ANY match on (title + ref + category) text, add token
# Patterns are case-insensitive.
KEYWORD_RULES = {
    "cosmology": [
        r"seven heavens", r"seven earths", r"sun.*muddy", r"muddy spring",
        r"sun.*rest", r"sun.*glides", r"sun.*throne", r"sun prostrat",
        r"sperm.*between", r"backbone and ribs", r"embryo", r"leech.?like",
        r"clot of blood", r"mountains.*pegs", r"pegs.*earth",
        r"mountain.*peg", r"moon.*split", r"moon was cleft",
        r"heavens.*joined", r"joined entity", r"\bfingertips\b",
        r"earth.*spread", r"earth.*expanse", r"bed.*spread",
        r"forelock.*lying", r"milk.*between", r"shooting stars",
        r"stars as protection", r"stars.*devils", r"\b60 cubits\b",
        r"sixty cubits", r"adam.*cubits", r"adam.*tall",
        r"six days", r"eight days", r"creation in.*days",
        r"noah.*flood", r"flood covered", r"fever.*hell",
        r"hell.*summer", r"eclipse.*sun", r"eclipse.*moon",
        r"cosmology", r"embryology", r"heavens.*earth.*joined",
        r"big bang", r"\bexpanding\b",
        r"fingerprints", r"know.*wombs", r"wombs.*allah",
        r"flat.?earth", r"day.*1000 years", r"day.*50,?000 years",
        r"day.*fifty thousand", r"day.*thousand years",
        r"science claims", r"no bad effect", r"black seed cures",
        r"nigella seed", r"honey cures", r"camel urine",
        r"fly.*drink", r"fly.*dip", r"fly.*wing",
        r"frontal.lobe", r"solar eclipse",
    ],
    "childmarriage": [
        r"\baisha\b.*\bsix\b", r"\baisha.*nine\b", r"consummat.*nine",
        r"not fully grown", r"girls who have not.*menstruat",
        r"beat them.*ten\b", r"\bdolls\b", r"prepubescent",
        r"marry.*daughter.*not fully", r"admitted to his house",
        r"six years? old", r"seven years? old", r"nine years? old",
        r"ten years? old", r"\bswing\b", r"\bplaymate", r"tender age",
        r"girl of (six|seven|eight|nine|ten)",
        r"before puberty", r"before.*menstruat", r"young (bride|girl)",
        r"father.*marry.*daughter", r"age of.*nine", r"age of.*six",
        r"consummation at nine", r"consummation.*young",
        r"child.*marriage", r"child.*bride",
    ],
    "slavery": [
        r"\bslave\b", r"\bslaves\b", r"\bcaptive\b", r"\bcaptives\b",
        r"right hand.*possess", r"what.*right hand", r"safiy?yah?\b",
        r"mariyah\b", r"awtas", r"concubin", r"emancipat", r"ransom",
        r"bondwoman", r"bondmaid", r"war captive", r"slave.?girl",
        r"prostitut.*slave", r"expedition.*mustaliq", r"intercourse with",
    ],
    "lgbtq": [
        r"\bgay\b", r"homosexual", r"sodom", r"active and passive partner",
        r"\blot\b", r"effeminat", r"mukhannath", r"castrat", r"eunuch",
        r"imitate.*men\b", r"imitate.*women\b", r"transgender",
        r"men who imitate", r"women who imitate", r"old male.*without vigor",
        r"kill.*active.*passive", r"people of lut", r"people of lot",
        r"practice.*lot", r"lust for men", r"approach men",
        r"approach males", r"receptive partner", r"passive partner",
        r"lesbian", r"approach.*men.*desire", r"men.*desire.*men",
        r"lewdness.*people",
    ],
    "apostasy": [
        r"apostas", r"apostate", r"changes his religion",
        r"whoever changes.*religion", r"burned apostates", r"ali burned",
        r"blood.*muslim.*lawful", r"muslim magician", r"insult.*prophet",
        r"blasphem", r"kill.*ka.b\b", r"ka.?b.*ashraf",
        r"assassinat", r"critic.*killed", r"poet.*killed", r"abu afak",
        r"asma bint marwan", r"change his religion", r"change.*faith",
        r"left islam", r"leave islam", r"left the religion",
        r"turn.*back.*faith", r"mocked.*prophet", r"insulted muhammad",
        r"insulted allah", r"killed.*for.*speech", r"killed.*for.*poet",
        r"killed.*for.*criticizing", r"assassination.*ka", r"ka.?b ibn",
        r"poet.*murder", r"death.*for.*change",
    ],
    "hudud": [
        r"stoning", r"stoned", r"stone.*death", r"stone to death",
        r"\blash(es|ing|ed|)\b", r"amputat", r"hand.*cut off",
        r"cut.*hand", r"flog", r"crucifi", r"100 lash",
        r"one hundred lash", r"forty stripes", r"eighty stripes",
        r"pit for stoning", r"\bghamid\b", r"\bma.?iz\b", r"\bhudud\b",
        r"urayna?\b", r"eye.*brand", r"quarter of a dinar",
        r"cauteri[sz]", r"thief.*cut", r"fatima.*steal",
        r"alternate sides", r"opposite sides",
    ],
    "warfare": [
        r"banu qurayza", r"banu quraiza", r"qurayza", r"quraiza",
        r"khaybar", r"khaibar", r"battle of", r"\bbadr\b", r"\buhud\b",
        r"expedition", r"\braid\b", r"\braids\b", r"\bjihad\b",
        r"martyr", r"\bsword\b", r"swords", r"strike.*neck",
        r"strike their neck", r"slaughter", r"fight against", r"fought",
        r"conquest", r"date palms", r"banu nadir", r"banu qainuqa",
        r"made victorious.*terror", r"victorious with terror",
        r"commanded to fight", r"ordered to fight", r"massacre",
        r"combatant", r"night raid", r"polytheist.*children",
        r"children.*night raids?", r"they are from them",
        r"war spoils", r"spoils of war", r"military",
        r"behead", r"strike \[them\] upon",
    ],
    "governance": [
        r"twelve caliph", r"caliph.*qurays?h", r"qurays?h.*caliph",
        r"\bdhimmi\b", r"narrowest.*road", r"\bjizya\b",
        r"ethiopian.*raisin", r"raisin head", r"bai.?ah\b",
        r"land belongs.*allah", r"treaty", r"obedience.*leader",
        r"obey your leader", r"caliphate", r"muslim.*state",
        r"jurisdiction", r"leadership", r"sword verse",
        r"fight until they pay", r"pay the jizya",
        r"humiliation tax", r"rulers of ", r"conquest of mecca",
        r"fight the people", r"the people.*testify",
        r"commanded to fight.*testify", r"ordered to fight",
        r"political", r"ruler", r"chieftain", r"leader",
        r"expelled.*jews.*christians.*arabian",
    ],
    "paradise": [
        r"\bparadise\b", r"\bhouri\b", r"\bhouris\b", r"hur al.?ayn",
        r"large.?eyed", r"pearl tent", r"hollow pearl",
        r"\bmusk\b", r"green bird", r"70,?000", r"seventy.?thousand",
        r"72 virgin", r"rivers of (wine|milk|honey)",
        r"purified spouses", r"sixty miles", r"no excretion",
        r"sweat.*musk", r"food.*musk", r"eternal virgins",
        r"gates of paradise", r"ranks in paradise", r"paradise reward",
        r"paradise.*architecture",
    ],
    "hell": [
        r"\bhell\b", r"hellfire", r"hell-fire", r"eternal.*tormen",
        r"\bmolar\b", r"uhud.*tooth", r"tooth.*uhud", r"allah.?s foot",
        r"skin.*roasted", r"skin.*replaced", r"\b999\b",
        r"nine hundred.*ninety", r"prophet's mother",
        r"suicide.*hell", r"suicide.*fire", r"grave.*tortur",
        r"torture.*grave", r"denizens of hell", r"inmates of hell",
        r"fire of hell", r"fire forever", r"eternal fire",
        r"damnation", r"damned",
    ],
    "eschatology": [
        r"\bdajj?al\b", r"\bgog\b", r"\bmagog\b", r"ya.?juj",
        r"majuj", r"last hour", r"end.*times", r"end of times",
        r"sun ris.*west", r"ka.?ba.*destroy", r"abyssinian.*ka",
        r"jesus.*return", r"jesus.*descend",
        r"jesus.*break.*cross", r"ibn sayyad", r"ibn saiyad",
        r"ten signs", r"portent", r"gharqad", r"final hour",
        r"beast of", r"\bmahdi\b", r"smoke.*dajjal",
        r"judgment day", r"day of resurrection",
    ],
    "preislamic": [
        r"\bburaq\b", r"night journey", r"sleepers", r"ephesus",
        r"raven.*burial", r"crow.*burial", r"abraham.*fire",
        r"fire.*cool.*abraham", r"camel.*eye.*needle",
        r"needle.?s eye", r"moses.*angel", r"moses slaps",
        r"mary.*palm", r"clay birds", r"alexander.*muslim",
        r"dhul.?qarnayn", r"ascent", r"birth under.*palm",
        r"samiri", r"babylon", r"protoevangelium", r"midrash",
        r"apocryph", r"lifted.*legend", r"borrow", r"pre.islamic",
        r"sister of aaron", r"mary.*aaron", r"\bezra\b",
        r"son of allah.*ezra", r"jewish legend",
        r"christian apocalypt", r"jewish apocalypt",
        r"holy spirit.*gabriel", r"gabriel.*holy spirit",
        r"cow.*revive", r"abraham.*birds", r"four.*birds.*assemble",
        r"village.*hundred years", r"dead for.*years",
        r"infancy gospel", r"proto-?evangelium",
        r"jewish source", r"christian source", r"syriac",
        r"alexander the great", r"haman", r"persian.*from esther",
        r"solomon.*ants", r"solomon.*jinn",
        r"abraham.*muslim", r"abraham.*furnace",
        r"cain.*abel.*raven", r"quran.*jesus.*not crucif",
    ],
    "magic": [
        r"evil eye", r"\bruqya\b", r"\bamulet\b", r"incantation",
        r"\bjinn\b", r"\bjinns\b", r"\bsatan\b", r"bewitch",
        r"sorcer", r"\bmagic\b", r"talisman", r"\bdevil\b",
        r"tattoo", r"pluck.*eyebrow", r"black dog.*devil",
        r"\bharut\b", r"\bmarut\b", r"whisper", r"shaitan",
        r"\bspell\b", r"\bsihr\b", r"\bajwa\b", r"possession",
        r"protective", r"curse of allah", r"allah cursed",
        r"cursed.*women.*false hair",
    ],
    "ritual": [
        r"dog.*saliv", r"wash.*seven", r"seven times",
        r"right hand\b.*eat", r"left hand\b.*eat", r"satan.*left hand",
        r"satan eats", r"\byawn\b", r"\bsneeze\b",
        r"stand.*drink", r"drink.*stand", r"ghusl\b",
        r"wet dream", r"ablution", r"\bpurification\b",
        r"urinat.*standing", r"spit.*three", r"three times.*left",
        r"qibla\b.*toilet", r"nullif.*prayer", r"invalid.*prayer",
        r"menstruat", r"gecko\b", r"kill.*gecko", r"\bfitra\b.*bath",
        r"bathing", r"prayer.*cut.*by",
    ],
    "privileges": [
        r"\bnine wives\b", r"more than four", r"\bhiba\b",
        r"special marriage", r"exemption.*prophet",
        r"prophet's.*privilege", r"strength of thirty",
        r"allah hastens", r"your lord hastens",
        r"\bzaynab\b", r"honey affair", r"\bmaghafir\b",
        r"widow.*remarry", r"prophet's.*wives",
        r"curtain verse", r"seclusion.*revealed",
        r"visits all.*wives", r"nine.*wives.*single",
        r"muhammad's (wife|wives)", r"muhammad's marriage",
        r"prophet's marriage", r"prophet's wife",
        r"mariyah", r"mariya", r"safiy?yah?\b.*prophet",
        r"convenient revelation", r"revelation.*personal",
        r"personal.*revelation", r"exempted", r"exemption",
        r"privilege.*above", r"above other believers",
        r"\btaqiyya\b", r"permission to deceive", r"permit.*lie",
        r"muhammad's.*cut.*spoils", r"\bkhums\b",
        r"four wives.*marry", r"hastens.*wishes",
        r"adopted son.*wife", r"zaynab.*jahsh",
        r"prophet.*gave himself", r"hiba women",
        r"privilege.*prophet",
    ],
    "allah": [
        r"best of deceivers", r"best of planners", r"\bmakr\b",
        r"seals.*hearts", r"allah.*seal.*heart", r"allah descends",
        r"allah.?s foot", r"allah.?s throne", r"mercy.*100 parts",
        r"mercy.*one hundred parts", r"in his own image",
        r"\bqadar\b", r"anthropomorph", r"predestin",
        r"allah.*confer blessing", r"allah.*bless.*prophet",
        r"allah is.*best", r"allah.*hastens", r"allah.*commanded",
        r"allah.*created", r"allah.*hands", r"allah.*shin",
        r"allah.*face", r"our lord.*descend", r"allah's character",
        r"allah cursed", r"allah.*curse", r"\bfoot of allah\b",
        r"allah.*laugh", r"allah.*pleased", r"allah.*angry",
        r"allah.*wrath", r"allah.*destroyed", r"allah.*sends",
        r"every.*decreed", r"fate.*written", r"destiny.*written",
        r"all things.*predest", r"judgment.*predest",
        r"angel.*writes.*soul", r"angel.*destin",
        r"divine decree", r"all things.*decreed",
    ],
    "scripture": [
        r"verse of stoning", r"stoning verse", r"\btahrif\b",
        r"ten sucklings", r"five sucklings", r"sucklings.*abrogat",
        r"uthman.*burn", r"variant.*quran", r"quran.*preserv",
        r"verse.*lost", r"verse.*missing", r"preserved tablet",
        r"no one knows.*interpretation", r"clarity.*interpret",
        r"abrogat.*text", r"islamic dilemma", r"preservation claim",
        r"corrupt.*bible", r"tahrif doctrine",
        r"no one can change the words", r"no change.*words",
        r"quran.*clear", r"quran.*clarity", r"today.*perfected",
        r"perfected your religion", r"no contradiction",
        r"piecemeal revelation", r"asbab al.nuzul", r"occasions of revelation",
        r"lost.*quran", r"once in the quran", r"missing.*quran",
        r"completeness", r"revelation came just in time",
        r"gabriel.*revealed", r"revelation arriv", r"timely revelation",
        r"convenient revelation", r"in the book of allah",
        r"judge by.*book", r"what is.*in the book",
    ],
    "morality": [
        r"eternal.*disproport", r"collective punishment",
        r"\bfitra\b", r"parents.*make.*jew", r"fatalist",
        r"responsibility.*dissolved", r"born.*jew.*christ",
        r"pre.?islamic.*damnation", r"predestin.*punishment",
        r"accountab.*dissolv", r"moral account",
        r"unequal retaliat", r"punishes.*disbelief",
        r"punishment.*chose", r"disproportion",
        r"seals.*hearts.*punish", r"punish.*disbelief",
        r"seal.*hearts.*punish", r"moral.*responsib",
        r"moral reputation", r"moral exemplar", r"moral philosophy",
        r"ethical problem", r"eternal disproportionate",
        r"eternal.*rape", r"eternal.*torture", r"pain.*maxim",
        r"rigged justice", r"unjust", r"injustice", r"not just",
        r"punishing the innocent", r"no choice", r"cannot choose",
        r"choice.*impossib", r"problem.*evil", r"origin.*evil",
        r"moral tens", r"moral dilem", r"burden.*beyond",
        r"war crime", r"collective.*guilt",
        r"soul.*predestin", r"fate.*written.*birth",
        r"every.*fate.*written", r"punishes them for",
        r"moral.*intuition", r"defeating.*mercy", r"sadist",
        r"creative cruelty", r"engineered.*suffer",
    ],
    "sexual": [
        r"aisha.*six", r"aisha.*nine", r"adult breastfeed",
        r"suckle.*grown", r"\bmut.?ah\b", r"temporary marriage",
        r"\bazl\b", r"coitus", r"sexual access", r"intercourse",
        r"right hand.*possess", r"virgin.*silence", r"concubin",
        r"\bsex\b", r"sexually", r"fornicat", r"adulter",
        r"thighing", r"tafkhid", r"menstruat.*intercourse",
        r"bed of her husband", r"refus.*husband.*bed",
        r"purified spouses", r"sucklings", r"houris", r"large.?eyed",
    ],
}

# Compile once
COMPILED_RULES = {
    tok: [re.compile(p, re.IGNORECASE) for p in patterns]
    for tok, patterns in KEYWORD_RULES.items()
}

# Regex to find entries
ENTRY_RE = re.compile(
    r'(<div class="entry"[^>]*data-category=")([^"]*)("[^>]*>)(.*?)(</section>\s*</div>)',
    re.DOTALL
)
TITLE_RE = re.compile(r'<span class="entry-title">(.*?)</span>', re.DOTALL)
REF_RE = re.compile(r'<span class="ref">(.*?)</span>', re.DOTALL)


def derive_new_categories(old_cats: str, title: str, ref: str) -> list:
    """Return deduplicated list of new category tokens."""
    new_tags = []
    # 1. Baseline from existing tags
    for tok in old_cats.strip().split():
        for new_tok in OLD_BASELINE.get(tok, []):
            if new_tok not in new_tags:
                new_tags.append(new_tok)

    # 2. Keyword rules — check against title + ref
    search_text = f"{title} {ref}"
    for new_tok, patterns in COMPILED_RULES.items():
        if new_tok in new_tags:
            continue
        for p in patterns:
            if p.search(search_text):
                new_tags.append(new_tok)
                break

    # 3. Ensure at least one tag: fallback to 'strange'
    if not new_tags:
        new_tags = ["strange"]

    # 4. Filter to known tokens only and preserve CATEGORIES order
    ordered = [t for t in CATEGORY_TOKENS if t in new_tags]
    return ordered


def retag_entries(html: str) -> tuple[str, int]:
    count = 0
    def replace_entry(m):
        nonlocal count
        count += 1
        prefix, old_cats, middle, inner, closing = m.groups()
        title_m = TITLE_RE.search(inner)
        ref_m = REF_RE.search(inner)
        title = re.sub(r'<[^>]+>', '', title_m.group(1)) if title_m else ""
        ref = re.sub(r'<[^>]+>', '', ref_m.group(1)) if ref_m else ""
        new_cats = " ".join(derive_new_categories(old_cats, title, ref))
        return f'{prefix}{new_cats}{middle}{inner}{closing}'

    new_html = ENTRY_RE.sub(replace_entry, html)
    return new_html, count


# Build the filter chip HTML
def build_chip_html() -> str:
    chips = ['        <span class="chip active" data-filter-type="category" data-filter-value="all">All</span>']
    for tok, label in CATEGORIES:
        chips.append(f'        <span class="chip" data-filter-type="category" data-filter-value="{tok}">{label}</span>')
    return "\n".join(chips)


# Regex for the filter group block containing the category chips
FILTER_GROUP_RE = re.compile(
    r'(<span class="controls-label">Category</span>\s*<div class="filter-group">)(.*?)(</div>)',
    re.DOTALL
)


def rewrite_filter_chips(html: str) -> str:
    new_chips = build_chip_html()
    def replace(m):
        open_tag, _, close_tag = m.groups()
        return f'{open_tag}\n{new_chips}\n      {close_tag}'
    return FILTER_GROUP_RE.sub(replace, html, count=1)


def process_file(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    html, n = retag_entries(html)
    html = rewrite_filter_chips(html)
    path.write_text(html, encoding="utf-8")
    print(f"  {path.name}: {n} entries retagged")


def main():
    print("Retagging catalog files...")
    for name in ["quran.html", "bukhari.html", "muslim.html", "abu-dawud.html"]:
        process_file(CATALOG_DIR / name)
    print("Done.")


if __name__ == "__main__":
    main()

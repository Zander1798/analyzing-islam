#!/usr/bin/env python3
"""Apply bespoke Muslim response + refutation content to specific catalog
entries identified by anchor-in-blockquote (first few words of the
blockquote content). Safer than line-number targeting.

Each entry in BATCH is a dict: file, anchor_substr (something unique
to identify the entry — typically a verse ID string or blockquote phrase),
response (HTML), refutation (HTML).
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent


def apply_content(path, anchor, response, refutation):
    text = path.read_text(encoding="utf-8")
    # Find the entry block via the anchor
    anchor_idx = text.find(anchor)
    if anchor_idx < 0:
        return False, f"anchor not found: {anchor[:60]}"
    # Find the next </section> after the anchor
    end_idx = text.find("</section>", anchor_idx)
    if end_idx < 0:
        return False, f"no </section> after anchor"
    # Inject the new sections before </section>
    # Preserve indent by finding the last newline + whitespace before </section>
    line_start = text.rfind("\n", 0, end_idx)
    indent = ""
    for c in text[line_start + 1:end_idx]:
        if c in " \t":
            indent += c
        else:
            break
    block = (
        f"{indent}<h4>The Muslim response</h4>\n"
        f"{indent}<p>{response}</p>\n"
        f"{indent}<h4>Why it fails</h4>\n"
        f"{indent}<p>{refutation}</p>\n"
    )
    # Also check: does this entry already have "The Muslim response"?
    # Scan from anchor to end_idx for an existing h4
    segment = text[anchor_idx:end_idx]
    if "<h4>The Muslim response</h4>" in segment:
        return False, "entry already has Muslim response section"
    new_text = text[:end_idx] + block + text[end_idx:]
    path.write_text(new_text, encoding="utf-8")
    return True, None


# NOTE: Anchor is something unique to each entry — typically a distinctive
# phrase from its blockquote. Kept short to avoid HTML-entity matching issues.
BATCH = [
    {
        "file": "site/catalog/quran.html",
        "anchor": "We do not abrogate a verse or cause it to be forgotten",
        "response": (
            "The standard defense frames abrogation (<em>naskh</em>) as pedagogical rather than "
            "corrective. Allah does not \"change His mind\"; rather He legislates progressively, "
            "guiding a community from where they are toward where they should be. The verse itself "
            "insists the replacement is \"better than\" or \"similar to\" the original, so nothing "
            "genuinely valuable is lost. On this view, it is human ethical capacity that changes "
            "over time, not divine knowledge, and staged revelation reflects divine wisdom in "
            "pedagogy rather than divine revision."
        ),
        "refutation": (
            "The pedagogical defense collapses under the Quran's own ambitions. A book claimed to "
            "be the eternal, unchanging word of an omniscient God cannot honestly be both perfectly "
            "preserved <em>and</em> contain verses Allah caused to be forgotten (the verse's own "
            "language). Classical scholars (al-Suyuti, al-Nahhas) produced lists of abrogation "
            "relationships running into the hundreds — and the lists disagree with each other. A "
            "reader cannot know which rulings are operative without centuries of legal commentary "
            "the text itself does not contain. A divine legislator who knew the end from the "
            "beginning would not need this scaffolding; He would simply reveal the final form. "
            "\"Progressive revelation\" is exactly what you would expect from a human author whose "
            "community's needs evolved — not from an eternal being whose wisdom does not."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "And to Allah belongs the east and the west. So wherever you [might] turn",
        "response": (
            "Apologists typically offer two defenses. First, that 2:115 speaks to Allah's "
            "omnipresence in general while 2:144 addresses the specific legal direction of ritual "
            "prayer — two different questions answered at two different levels. Second, that the "
            "qibla change was itself a test of the community's loyalty (the Quran admits as much "
            "at 2:143), deliberately distinguishing those who would follow Muhammad from those "
            "who would balk at a practical shift. On this reading the change is not political "
            "recalibration but a deliberate sifting mechanism."
        ),
        "refutation": (
            "The two-levels defense is interpretively possible but textually unmotivated — nothing "
            "in the text flags the distinction and readers have to supply it. The "
            "\"test of loyalty\" framing concedes the deeper point: the qibla change is presented as "
            "arbitrary, with the spiritual content of prayer unchanged by direction, yet the "
            "command to face a specific geography is treated as absolute. A genuinely direction-"
            "indifferent God would not invalidate prayer over direction. The historical timing — "
            "the shift away from Jerusalem exactly when the Medinan Jewish alliance collapsed — "
            "is what a political explanation predicts. Even the Quran's own admission that this "
            "was a test is doing explanatory work that should not need to be done if the change "
            "were theologically neutral."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "And they ask you about menstruation. Say, 'It is harm",
        "response": (
            "Apologists argue <em>adha</em> does not mean \"filth\" but \"discomfort\" or "
            "\"something bothersome\" — a medical observation that menstruation is physically "
            "difficult for women and that ordinary marital relations should be suspended out of "
            "consideration. On this reading the verse is not stigma but protection. The "
            "restrictions on prayer, fasting, and similar ritual obligations are framed not as "
            "exclusion but as relief — menstruating women are exempted from burdens they would "
            "otherwise have to carry."
        ),
        "refutation": (
            "<em>Adha</em> is used elsewhere in the Quran in senses closer to ritual-moral "
            "uncleanness than mere physical discomfort, and the classical jurists — native "
            "Arabic speakers — did not read it as \"minor inconvenience\" but as a state of ritual "
            "impurity that disqualifies the woman from religious action. The \"protection\" "
            "reading cannot account for the scope of classical disqualification built on this "
            "verse: bars on prayer, on entering mosques, on touching the Quran, on fasting in "
            "some schools. None of those relates to physical difficulty. A regime that exempts "
            "women from ritual \"for their comfort\" would not also prohibit them from religious "
            "spaces where no physical demand is at issue. The reading is a modern rescue that "
            "erases the hierarchy the classical tradition read directly off the text."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "And those who are taken in death among you and leave wives behind",
        "response": (
            "Classical scholarship distinguishes abrogation of the <em>text</em> "
            "(<em>naskh al-tilawa</em>) from abrogation of the <em>ruling</em> "
            "(<em>naskh al-hukm</em>). Here the ruling is abrogated while the text remains — not "
            "because of editorial incompetence but because the text retains recitational value "
            "as worship. Muslims gain spiritual reward (<em>thawab</em>) from reciting even "
            "abrogated verses. On this view the Quran is simultaneously law and liturgy, and its "
            "liturgical function preserves text that has served its legal purpose."
        ),
        "refutation": (
            "This defense sacrifices the Quran's claim to be a clear, complete, and accessible "
            "guide. A reader who does not already know the abrogation tradition cannot tell which "
            "commands are binding — the text gives no internal signal that 2:240 has been "
            "overridden by 2:234 and 4:12. Worse, the \"liturgical value\" argument implies "
            "Allah deliberately preserved canceled instructions in a book of guidance for "
            "stylistic reasons, accepting that ordinary readers would need centuries of juristic "
            "commentary to navigate it safely. That is a human-editorial pattern, not a divine "
            "one. An omniscient author writing a book of guidance would not require the guidance "
            "to be decoded against an external abrogation key before it can be followed."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "I design for you from clay [that which is] like the form of a bird",
        "response": (
            "The apologetic response runs two directions. First, the miracle could be historical "
            "and preserved in a non-canonical Christian source precisely because the canonical "
            "Gospels represent a later, corrupted Christianity — on this view the Quran is "
            "confirming a genuine event the church lost. Second, even if the <em>Infancy Gospel "
            "of Thomas</em> is legendary, the Quranic version differs in detail (notably the "
            "explicit \"by permission of Allah\" framing), so direct literary borrowing is not "
            "established."
        ),
        "refutation": (
            "The \"Quran preserves true history the church lost\" defense commits the Muslim to "
            "taking the <em>Infancy Gospel of Thomas</em> seriously as a source — but IGT is "
            "universally dated to the 2nd century or later, centuries after Jesus, and its Greek "
            "composition betrays its provenance as Hellenistic Christian legend, not suppressed "
            "apostolic memory. If IGT is reliable here, the Muslim has no principled way to pick "
            "the clay-birds story as historical while dismissing the adjacent material (child "
            "Jesus striking playmates dead, cursing teachers) as legend. The \"different details\" "
            "point is itself telling: tradents reshaping a borrowed story add theological gloss "
            "(\"by permission of Allah\"); what remains the same is the distinctive narrative, "
            "which is exactly what one predicts from legend entering new scripture through oral "
            "circulation."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "They saw them [to be] twice their [own] number by [their] eyesight.",
        "response": (
            "Classical commentators resolve this by positing a temporal sequence in perception. "
            "8:44 describes the initial engagement, when Allah made each side appear small to the "
            "other to embolden the believers and lure the Meccans into overconfident attack. 3:13 "
            "describes a later moment, after the true strengths became visible through sustained "
            "combat — by then the believers saw the enemy accurately as more numerous. On this "
            "sequential reading the two verses record two moments, not one, and the apparent "
            "contradiction dissolves."
        ),
        "refutation": (
            "The sequence reading is available but textually unsupplied — the Quran does not "
            "signal the temporal shift, and importing it to save a contradiction is the kind of "
            "special pleading that can rescue any scripture from any contradiction. Even granting "
            "the sequence, 3:13's \"twice\" claim fails as a factual report: the traditional "
            "sources have the Meccan force at three-times-plus, not two-times — which the Saheeh "
            "footnote itself concedes. A divine narrator describing an event He orchestrated "
            "would not produce a two-verse account that later commentators must reconcile with "
            "interpretive scaffolding. A human redactor working with conflicting oral traditions "
            "about the same battle would."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "Men are in charge of women by right of what Allah has given",
        "response": (
            "Apologists argue several lines. The step sequence is meant to be <em>limiting</em>, "
            "not permissive: verbal counsel first, then separation in bed, and strike only as a "
            "last resort — with the classical tradition adding that the strike must be with a "
            "<em>miswak</em> or light implement, must not injure, must not land on the face, and "
            "must not leave a mark. Muhammad himself is reported to have discouraged striking. "
            "Some contemporary scholars (including Laleh Bakhtiar) render <em>daraba</em> as "
            "\"separate from\" rather than \"strike.\" And the verse addresses the specific "
            "disobedience of <em>nushuz</em> (marital fidelity), not ordinary disagreement."
        ),
        "refutation": (
            "The \"last resort with limitations\" defense concedes the central point: the Quran "
            "permits a husband to strike his wife under divinely-specified conditions. The "
            "limitations are not in the verse — they are apologetic scaffolding added by jurists "
            "centuries later. The alternative translation (\"separate from\") is grammatically "
            "unsupported: <em>daraba</em> in this verbal form consistently means \"strike\" "
            "throughout the Quran, and the classical Arabic-speaking commentators (Tabari, Ibn "
            "Kathir, Qurtubi) unanimously read 4:34 as authorizing physical correction. Modern "
            "retranslations are driven by the desire to reconcile the verse with contemporary "
            "norms, not by grammar or textual evidence. The deeper moral asymmetry stands "
            "untouched: eternal divine law gives husbands a license of corrective violence that "
            "wives do not possess in reverse. A God whose guidance was meant to transcend its "
            "cultural moment would not have embedded the gender hierarchy of 7th-century Arabia "
            "into eternal law."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "They wish you would disbelieve as they disbelieved so you would be alike",
        "response": (
            "The standard response distinguishes apostasy <em>per se</em> from apostasy combined "
            "with treason, rebellion, or public waging of war against the Muslim community. 4:89 "
            "addresses hypocrites who had revealed military information to Muhammad's enemies "
            "after pretending conversion — a political betrayal, not a private belief change. "
            "Bukhari 6922 is similarly narrowed: traditional jurists read it as public apostasy "
            "in contexts of open hostility, while private apostates who keep quiet are, on some "
            "classical readings, left alone. The contradiction with 2:256 (\"no compulsion in "
            "religion\") is thereby dissolved: compulsion is forbidden; treason is punished."
        ),
        "refutation": (
            "The treason-not-belief framing is post-hoc. The hadith's language is categorical — "
            "\"whoever changes his religion\" — not \"whoever changes his religion and takes up "
            "arms.\" Classical jurists of all four Sunni schools and Shia Jaʿfari law codified "
            "apostasy itself as a capital crime without requiring an additional act of war. "
            "Contemporary jurisdictions enforcing apostasy death penalties (Saudi Arabia, Iran, "
            "Mauritania, parts of Somalia) regularly apply them to private belief change. The "
            "narrow-treason reading is a modern apologetic construction, not the reading the "
            "Islamic legal tradition delivered. And the tension with 2:256 is real: \"no "
            "compulsion\" and \"leaving Islam is punishable by death\" cannot coherently both "
            "operate, regardless of framing. The classical solution was to abrogate 2:256 — a "
            "solution modern apologists quietly abandon while still invoking 2:256 as evidence "
            "of Islamic tolerance."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "O People of the Scripture, do not commit excess in your religion",
        "response": (
            "Two apologetic lines are available. Some argue the Quran is not misidentifying the "
            "Trinity at all — it is confronting a genuine heretical sect (the Collyridians, or "
            "similar Marian-veneration groups in Arabia) whose practice was indistinguishable "
            "from mainstream Christianity to outsiders. Others argue 5:116's phrasing "
            "(\"take me and my mother as deities\") addresses the <em>functional</em> theology of "
            "Arab Christianity: in practice Mary was often treated as divine, whatever the "
            "official creeds said, so the Quran is describing lived religion rather than failing "
            "to know the orthodox doctrine."
        ),
        "refutation": (
            "The Collyridian hypothesis rests on a sect so marginal we know of it primarily "
            "through a single entry in Epiphanius's <em>Panarion</em>, with no independent "
            "evidence it existed at scale in 7th-century Arabia. Even if it did, an omniscient "
            "God correcting Christian theology for all time should be addressing the "
            "Christianity that Christians actually confess — not a fringe Yemeni Marian devotion. "
            "The \"functional Trinity\" move is anthropological speculation about lay piety, not "
            "a defense of a divine book that names specific doctrinal errors. Most damning: "
            "orthodox Christianity — Catholic, Protestant, Eastern Orthodox, Oriental, all of "
            "them, across all creeds and councils — has never identified the Trinity as Father, "
            "Mary, Jesus. A divine author correcting Christian theology from above the human "
            "fray should not be attacking a belief no organized Christian communion has ever "
            "held."
        ),
    },
    {
        "file": "site/catalog/quran.html",
        "anchor": "And [also prohibited to you are all] married women except those your right hands possess",
        "response": (
            "The classical position is that capture in war effectively dissolved the prior "
            "marriage (defended by Ibn Kathir and al-Qurtubi), so the woman was not "
            "simultaneously married and available — the capture <em>was</em> the dissolution. "
            "Apologists note that sex with a captive required a waiting period (<em>istibra</em>) "
            "to confirm she was not pregnant, which amounts to a minimum procedural protection. "
            "Modern apologists further argue that slavery and concubinage were the 7th-century "
            "norm, and that Islam progressively tightened the constraints (permitting manumission "
            "as redemption, forbidding sex without ownership) in a direction that would have "
            "reached abolition had the community continued the trajectory."
        ),
        "refutation": (
            "The \"capture dissolves marriage\" claim has no basis in the Quran itself; it is a "
            "juristic construction added later to make the sexual ethics intelligible. The verse "
            "exempts married women from forbidden categories <em>because</em> their right-hand-"
            "possessed status overrides their marriage — the verse presupposes the marriage "
            "still exists, and the sexual access is Quranically authorized regardless. "
            "<em>Istibra</em> is about lineage clarity, not consent; the captive's agreement is "
            "nowhere required. The \"progressive abolition\" narrative is a modern frame: the "
            "Quran could have abolished slavery but did not, and for 1,400 years the tradition "
            "did not read it as abolitionist. This is not a dead issue — ISIS's 2014 sexual "
            "enslavement of Yazidi women was grounded in this exact verse, with explicit "
            "classical-legal justification published in their magazine <em>Dabiq</em>. If the "
            "verse were genuinely incompatible with its exploitative application, the classical "
            "jurisprudence should have made that clear over fourteen centuries. It did not."
        ),
    },
]


applied = 0
for spec in BATCH:
    path = ROOT / spec["file"]
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['file']}: {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['file']}: {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

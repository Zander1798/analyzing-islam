"""Fill in the "Why it fails" sections of every Sahih Muslim entry that
currently reads only "(Needs expansion.)" with a targeted rebuttal of
the apologetic response shown immediately above.

Each rebuttal is entry-specific: it engages the particular concession
or deflection in "The Muslim Response" for that hadith rather than a
generic boilerplate.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass


# Entry id → rebuttal HTML. Each rebuttal is one <p>…</p>; multi-paragraph
# rebuttals chain <p> blocks.
REBUTTALS: dict[str, str] = {

    "aisha-age": (
        "<p>The apologist's own framing — <em>if this can't be trusted, "
        "nothing can</em> — is precisely the point. The critic is not "
        "asking Muslims to distrust hadith science arbitrarily; the critic "
        "is showing that hadith science, applied consistently, produces "
        "a picture that contemporary ethics rejects. A transmission system "
        "whose strongest-possible attestation lands on a nine-year-old's "
        "consummation is not vindicated by being robust; it is indicted by "
        "it. The dilemma — revise the ethics or revise the method — is "
        "the apologist's to resolve, and every move available makes the "
        "classical doctrine of preserved Sunna less defensible, not more.</p>"
    ),

    "stoning-adulterers": (
        "<p>The <em>naskh al-tilawa</em> doctrine was built specifically "
        "to absorb embarrassments of this shape, and the stoning verse is "
        "its textbook case. As a defense it fails on its own terms: it "
        "concedes that the present Qurʾān is missing revelation while "
        "simultaneously asserting the Qurʾān is divinely preserved (15:9), "
        "and it asks the believer to accept that Allāh deliberately "
        "removed wording while keeping the wording's ruling. The simplest "
        "hypothesis that fits ʿUmar's own testimony — the verse existed, "
        "and it did not survive compilation — is rejected because it "
        "breaks preservation theology. Every alternative costs the "
        "tradition more than the simple reading would.</p>"
    ),

    "hand-amputation-quarter-dinar": (
        "<p>The \"rarely applied\" defense surrenders the principle in "
        "order to save appearances: a law is morally evaluated by what it "
        "prescribes, not by how often prescribers flinch from using it. "
        "The \"stringent conditions\" defense is worse — those conditions "
        "were added by later jurists precisely because the rule as stated "
        "was unlivable, which is an implicit concession by the jurists "
        "themselves that the text left to itself produces injustice. A "
        "revealed law that requires post-hoc juristic mitigation to avoid "
        "being monstrous is a law whose moral authority its own "
        "interpreters have already compromised.</p>"
    ),

    "mutah-temporary-marriage": (
        "<p>The response frames the dispute as \"both sides cannot be "
        "right\"; the underlying problem is deeper. A corpus presented "
        "as preserved divine authority should not leave a basic "
        "sexual-law question this contested at all. The hadith record "
        "contains both permission and revocation, each attested in "
        "<em>ṣaḥīḥ</em> material. Either the authentication system "
        "produces contradictory output — in which case it cannot ground "
        "binding law — or one of the two sides has been knowingly "
        "transmitting falsehood as <em>ṣaḥīḥ</em> for fourteen centuries. "
        "Neither option leaves the doctrine of preserved Sunna intact.</p>"
    ),

    "night-raid-children": (
        "<p>\"Civilians could not be distinguished\" has no operational "
        "content when the attacker is the one judging distinguishability. "
        "Every jihadist group that has cited this hadith — ISIS, al-Qaʿida, "
        "Boko Haram — has claimed it applied to their attacks, and the "
        "text offers no procedural check on that claim. The restrictions "
        "the apologist invokes live entirely in later juristic commentary, "
        "not in the hadith itself. A theological blanket that needs "
        "downstream jurists to write the conditions under which it "
        "<em>won't</em> apply is not a rule restricting the killing of "
        "children; it is a rule permitting it with deniable qualifications.</p>"
    ),

    "expel-jews-christians": (
        "<p>Relabeling the expulsion as \"spatial purification\" rather "
        "than \"religious hostility\" is a semantic move, not a defense. "
        "The effect is identical either way: entire religious communities "
        "are removed from a territory solely because of their religion. "
        "The apologist's own observation — no equivalent Christian or "
        "Jewish doctrine exists for Jerusalem or Rome — is telling: Islam "
        "alone among the three Abrahamic traditions theologizes a "
        "sacred-land clearance of other faiths. Modern enforcement under "
        "Saudi Arabia (non-Muslim worship banned outside compounds; Mecca "
        "and Medina closed to non-Muslims altogether) shows the doctrine "
        "is not a historical curiosity but a live, currently-implemented "
        "policy.</p>"
    ),

    "dajjal-one-eyed": (
        "<p>The apologist concedes the prophecy is unfalsifiable and "
        "treats this as a feature. It is not: an unfalsifiable prophecy "
        "is indistinguishable from no prophecy at all, and cannot be "
        "evidence for the divine origin of the source that issued it. "
        "The Dajjāl apparatus actually contains plenty of falsifiable "
        "claims — a physical man with KFR on his forehead, blind in one "
        "eye, visible to believers — which have not materialized in 1,400 "
        "years. When the specifics thrill, they are invoked; when they "
        "are challenged, they retreat into \"symbolic future events.\" "
        "A doctrine that deploys specificity and abandons it on demand "
        "is not a description of reality.</p>"
    ),

    "five-sucklings-lost": (
        "<p>This case is worse than the stoning verse: ʿĀʾisha testifies "
        "that the five-sucklings verse was still being recited as Qurʾān "
        "at the Prophet's death — which places missing revelation inside "
        "his own household at the moment of the final recitation. The "
        "<em>naskh al-tilawa</em> defense therefore requires all of: "
        "(a) that Allāh removed wording after the Prophet's lifetime, "
        "(b) that the Prophet's own widow did not get the memo, and "
        "(c) that this is consistent with <em>\"indeed, it is We who "
        "sent down the Qurʾān, and indeed, We will be its guardian\"</em> "
        "(15:9). These cannot all hold simultaneously.</p>"
    ),

    "yawn-from-devil": (
        "<p>The \"pedagogical\" reading is unstable in exactly the way "
        "the apologist concedes. If \"yawning is from the devil\" is "
        "literal it is wrong, since yawning is a thermoregulatory / "
        "arousal-transition reflex with a well-understood neurophysiology. "
        "If it is motivational, the Prophet is deploying a false "
        "supernatural claim to shape behavior — an odd practice for a "
        "messenger claiming perfect truth-telling. Either way the text "
        "has no flattering reading: literally wrong, or pedagogically "
        "built on a fiction.</p>"
    ),

    "ten-signs-last-hour": (
        "<p>If any sufficiently bad event \"fulfills\" a sign then the "
        "prophecy is consistent with every possible future — and "
        "therefore predicts nothing. A prediction compatible with its own "
        "opposite is not a prediction. The apologist's interpretive "
        "flexibility saves the hadith's face at the cost of its "
        "evidential content: specificity is required for a prophecy to "
        "count, and unlimited reinterpretation removes specificity. You "
        "cannot run both moves at once.</p>"
    ),

    "date-palms-burned": (
        "<p>That Qurʾān 59:5 was revealed to authorize what had already "
        "been done — and was already contested by the Prophet's own "
        "companions — is not incidental background: it is the "
        "indictment. Revelation arriving to legitimize a contested act "
        "does not exonerate it; it documents a pattern in which the "
        "Prophet's choices generate matching divine endorsements after "
        "the fact. The companions' discomfort is contemporaneous evidence "
        "that the act was morally controversial by the nascent "
        "<em>umma</em>'s own standards. \"The enemy deserved it\" does "
        "not answer why destroying agricultural infrastructure required "
        "a freshly-revealed verse to settle.</p>"
    ),

    "three-lies-permitted": (
        "<p>The apologist admits the exemptions have been \"applied "
        "broadly\" across 1,400 years of Islamic diplomacy and warfare. "
        "That is not a defense of the principle; it is a documentation "
        "of its operational consequence. A rule is evaluated by how "
        "rule-following communities actually deploy it, not by the most "
        "flattering interpretation a later defender can supply. If the "
        "narrow reading were adequate, the wider reading would not have "
        "produced a stable juristic category (<em>taqiyya</em>) and a "
        "stable wartime doctrine (<em>khadʿa</em>) with documented use "
        "for over a millennium.</p>"
    ),

    "hundred-lashes-contradiction": (
        "<p>The apologist concedes the Qurʾān is \"elliptical\" — but "
        "the Qurʾān denies being elliptical. 6:38: \"We have neglected "
        "nothing in the Book.\" 16:89: \"We have sent down to you the "
        "Book as clarification for all things.\" The defense therefore "
        "requires the Qurʾān to be wrong about itself. Worse, the hadith "
        "doesn't clarify a missing verse; it contradicts the Qurʾānic "
        "penalty (100 lashes, 24:2) by adding banishment and stoning. "
        "\"Clarifying\" is a euphemism for \"overruling\" when the "
        "clarification prescribes execution where the text prescribes "
        "flogging.</p>"
    ),

    "nine-wives-one-night": (
        "<p>The apologist concedes the Prophet's practice cannot be a "
        "general model. But the tradition also insists — on the authority "
        "of 33:21 — that the Prophet <em>is</em> the model for all "
        "believers. These two commitments are incompatible. Either the "
        "exemplar's practice is normative (in which case the eleven "
        "wives and the one-night rotation are binding templates), or it "
        "is not (in which case citing the Prophet as moral pattern on "
        "any other topic requires a case-by-case argument that <em>this</em> "
        "topic is exempt-from-exemption). The apologetic strategy has to "
        "pick, and neither choice preserves the classical doctrine.</p>"
    ),

    "dog-vessel-seven-times": (
        "<p>The hygiene defense collapses the moment it is examined. "
        "Cats carry rabies, toxoplasmosis, and ringworm; sheep, goats, "
        "and camels carry their own zoonoses — several transmissible to "
        "humans — and yet all are ritually clean. If the Prophetic rule "
        "were tracking pathogen load it would not single out dogs. "
        "Singling out dogs is not biology; it is a cultural preference "
        "widely shared across the pre-Islamic Near East and re-authorized "
        "as divine law. The apologist cannot keep both the specificity "
        "(dogs, not cats) and the hygiene rationale (which does not map "
        "to dogs uniquely).</p>"
    ),

    "prophet-cursed-tribes": (
        "<p>Even granting the precipitating massacre by specific "
        "individuals, the hadith preserves a full month of public "
        "cursing of <em>entire named tribes</em> in the dawn prayer. "
        "That is collective imprecation — liturgical collective "
        "punishment. Set against standards the tradition elsewhere "
        "claims (\"no soul shall bear the burden of another\" — 6:164; "
        "\"Allāh does not burden a soul beyond what it can bear\" — 2:286), "
        "a month of tribal curses does not cohere. The apologist's "
        "\"just cause\" framing justifies <em>a</em> response — it does "
        "not justify <em>this</em> response.</p>"
    ),

    "best-men-best-to-wives": (
        "<p>The distinction between \"acceptable light discipline\" and "
        "\"abuse\" is drawn entirely by male scholars; the wife is never "
        "the arbiter. The Prophet's own recorded blow caused ʿĀʾisha "
        "pain by her own testimony — yet classical jurisprudence files "
        "it under \"light\" because the Prophet is doing it. The "
        "standard is circular: whatever the Prophet does defines the "
        "acceptable, so \"acceptable\" has no independent content. A "
        "kindness ethic (\"the best of you is the best to your wives\") "
        "that cannot criticize the exemplar's blow to a female "
        "subordinate in her own house is not an ethic; it is hagiography.</p>"
    ),

    "good-omen-only": (
        "<p>The defense concedes the exact distinction that is in "
        "question. Which pre-Islamic beliefs count as \"superstition\" "
        "(evil omens, contagion) and which as \"real spiritual "
        "realities\" (jinn, evil eye, the Prophet bewitched, Satan "
        "urinating in the ear) is decided by whether the hadith happens "
        "to affirm them. A principled anti-superstition stance would "
        "have to eliminate the whole supernatural-causal machinery that "
        "pervades the same corpus. The hadith instead picks and chooses "
        "— and calls the choices revelation.</p>"
    ),

    "ramadan-devils-chained": (
        "<p>The hadith says devils are chained — external agency, "
        "external restraint. The apologist relocates the agency to the "
        "believer's increased spiritual focus. That is not a metaphorical "
        "reading; it is a substitution of subject. Classical tafsīr "
        "accepts the literal chaining; modern apologetics substitutes "
        "the internal-focus reading precisely because the literal reading "
        "requires defending a demonological claim about the lunar "
        "calendar. The need to choose between the two readings is the "
        "evidence of the problem: the text asserts one thing, the "
        "modern apologist asserts another, and \"metaphor\" is the "
        "bridge smuggled between them.</p>"
    ),

    "bathing-after-intercourse": (
        "<p>The critic's complaint is not that law exists but that a "
        "message presented as divine allocated substantial bandwidth to "
        "the minutiae of ritual bathing, nocturnal discharge, and "
        "genital etiquette — detail no plausible theory of revelation "
        "requires. A text that specifies five degrees of wet-dream "
        "purification before it specifies a principled theory of "
        "justice has a priority structure that is itself a datapoint. "
        "\"God cares about everything\" is not a defense of the "
        "allocation — it is an admission that the distribution of what "
        "God cared to say about is worth examining, and what one finds "
        "when one examines it is not flattering.</p>"
    ),

    "women-silk-gold": (
        "<p>The apologist admits \"no principled answer has ever been "
        "offered\" — and the admission is the whole case. \"Modesty for "
        "men, beauty for women\" is stipulated, not derived: it does "
        "not explain why a silver ring is modest but a gold ring sinful, "
        "or why silk (a particular fibre) carries moral content where "
        "linen does not. A sex-specific dress code presented as divine "
        "law but lacking even a post-hoc justification after fourteen "
        "centuries of scholarship is not a moral principle — it is a "
        "cultural taboo granted religious authority.</p>"
    ),

    "every-child-is-born-on-fitra-his-parents-make-him-jew-christ-11596bc8": (
        "<p>The hadith explicitly lists Judaism, Christianity, and "
        "Zoroastrianism — all monotheistic or quasi-monotheistic traditions "
        "— as corruptions <em>of</em> <em>fiṭra</em>. The \"fitra means "
        "generic monotheism\" reading is therefore textually impossible: "
        "the hadith is treating other monotheisms as departures from "
        "fiṭra, which requires fiṭra to be narrower than monotheism. The "
        "soft modern reading cannot simultaneously hold that (a) fiṭra "
        "is generic monotheism and (b) the hadith lists monotheisms as "
        "non-fiṭra. It is a retroactive edit, not an interpretation of "
        "what the text says.</p>"
    ),

    "the-sun-and-moon-do-not-eclipse-for-anyone-s-death-a-correct-ed8833cb": (
        "<p>The Prophet's stance on superstition is not a principled "
        "position; it is a list. He rejected eclipse-omens and affirmed "
        "the evil eye; rejected contagion and affirmed demonic ear-"
        "urination; rejected bird divination and affirmed jinn possession. "
        "The pattern tracks what he happened to reject on which occasions, "
        "not a coherent rule. Calling one subset \"superstition\" and "
        "another \"real spiritual causation\" gives divine authority to "
        "a pre-modern Near Eastern demonology while claiming scientific "
        "modesty only about the parts that would embarrass a modern "
        "reader. The apologist inherits both halves of the ledger, and "
        "cannot redeem one half by pretending the other is not there.</p>"
    ),

    "do-not-drink-while-standing-vomit-if-you-forget-but-the-prop-950705b2": (
        "<p>The apologist offers neither dignity nor health as a "
        "coherent justification: dignity does not require vomiting, and "
        "health does not require vomiting water already in the stomach. "
        "Adjacent hadiths in the <em>same</em> book record the Prophet "
        "himself drinking while standing — so either the prohibition is "
        "wrong, the Prophetic example is wrong, or the rule is not what "
        "it appears to be. No scholastic tradition has produced a "
        "reading that preserves both sides. A ritual-purity rule that "
        "contradicts its own exemplar and supplies no coherent rationale "
        "is a datapoint about how the corpus was assembled — not a "
        "guide to drinking.</p>"
    ),

    "muslims-fast-ashura-because-jews-fasted-ashura-we-have-a-clo-1ad26525": (
        "<p>Chronology refutes the theology. Muhammad arrived in Medina "
        "in 622 CE; the Ashura fast he observed was established Jewish "
        "practice for centuries before that. Adopting a foreign ritual "
        "and then claiming precedence <em>over</em> the community whose "
        "ritual it is is a polemical inversion, not a historical "
        "priority. This pattern recurs across early Medinan Islam — "
        "direction of prayer, fasting, sabbath-adjacent practices — and "
        "is one of the strongest indicators that the tradition grew "
        "<em>from</em> its Jewish and Christian neighbours rather than "
        "originating before them.</p>"
    ),

    "ibn-sayyad-umar-wanted-to-kill-a-child-suspected-of-being-th-91dd651a": (
        "<p>The apologist frames Umar's proposal as \"zeal\" — but "
        "\"zeal\" is a virtue-word, not an explanation. What the hadith "
        "documents is a normative culture in which executing a child on "
        "suspicion requires not an ethical objection (\"that would be "
        "wrong\") but an instrumental one (\"if he is the Dajjāl, it "
        "wouldn't work\"). The Prophet's refusal is operational. No "
        "child-protection principle is enunciated — not by Umar, not by "
        "the Prophet. An apologetic that wants such a principle has to "
        "smuggle it in from outside the text, which is the critic's "
        "whole point.</p>"
    ),

    "umar-kissed-the-black-stone-knowing-it-was-just-a-stone-e8396c69": (
        "<p>The rescue introduces the problem it was meant to avoid. If "
        "the Black Stone really is a Paradise-sent object that acts as "
        "a cosmic witness on Judgment Day, then Umar's public declaration "
        "— <em>\"By Allāh, I know you are a stone\"</em> — was wrong, "
        "and the caliph famous for his robust monotheism was publicly "
        "mistaken about a key piece of Islamic metaphysics. If Umar was "
        "right, the Paradise-stone hadith is wrong. The tradition "
        "preserves both without reconciliation, which means it does not "
        "itself know which claim is true — and therefore cannot ground "
        "a coherent theology of the Stone either way.</p>"
    ),

    "on-judgment-day-humans-are-raised-naked-and-uncircumcised-bu-0298d9be": (
        "<p>The devotional gloss does not answer the specifics the text "
        "volunteers: nudity, sex-mixing at resurrection, uncircumcised "
        "state. The hadith is specific because it is describing an "
        "event, not painting a metaphor — if the event were merely "
        "symbolic, ʿĀʾisha's follow-up (\"will men and women look at "
        "each other?\") would make no sense, and the Prophet's reply "
        "(\"matters will be too terrifying for that\") would be beside "
        "the point. The devotional reading only works if the text "
        "stops being specific. The text does not stop.</p>"
    ),

    "the-prophet-s-special-marriage-privileges-more-than-four-wiv-d0e13363": (
        "<p>Each \"specific purpose\" may have some force taken alone; "
        "cumulatively, the exemptions describe a marital regime that "
        "required bespoke divine authorization to operate — eleven "
        "wives simultaneously, waived dowers, captive-women concubinage, "
        "a veto over the Prophet's in-laws, divine endorsement of the "
        "Zaynab marriage, and so on. That is the critic's point: "
        "ordinary rules would not have authorized these arrangements, "
        "so new rules were revealed to authorize them, as and when "
        "needed, in the Prophet's favour. The apologetic list of "
        "justifications is the documentation of the pattern, not its "
        "rebuttal.</p>"
    ),

    "if-a-man-finds-his-wife-with-another-should-he-kill-him-no-w-dd7cc59d": (
        "<p>If the Prophet were teaching \"emotional reactions "
        "understandable, legally forbidden,\" we would expect the "
        "narrative to reassert the legal rule after Saʿd's outburst. It "
        "does not. \"Listen to what your chief says\" is a socially "
        "conciliatory move — the Prophet defers to a tribal leader on a "
        "question of immediate killing. The apologetic concedes the "
        "formal ruling is right while admitting the rhetorical handling "
        "is wrong: a moral exemplar whose in-the-moment signal "
        "systematically softens the very rule he has just uttered is "
        "not teaching the rule — he is undercutting it.</p>"
    ),

    "gog-and-magog-breach-the-wall-release-a-flood-of-destruction-953e29b1": (
        "<p>Same failure mode as the Dajjāl case: \"symbolic\" rescues "
        "the prophecy at the cost of its content. A description with "
        "giant worms, bodies disposed of by birds, specific geographic "
        "sequences, and specific lakes drunk dry cannot be <em>both</em> "
        "specific enough to constitute a distinctive prophecy <em>and</em> "
        "flexible enough to absorb every possible future without failure. "
        "In practice the Gog-Magog narrative is invoked specifically when "
        "it can thrill (in preaching, in popular eschatology) and "
        "symbolically when it must defend (in apologetics). That is not "
        "how a true description behaves — it is how a mythology behaves.</p>"
    ),

    "muhammad-personally-supervised-the-beheadings-at-banu-qurayz-77563418": (
        "<p>The apologist's concession — \"the Prophet acted by the laws "
        "of his time\" — is the move the tradition cannot afford to "
        "make. 33:21 presents the Prophet as a trans-historical "
        "exemplar (\"indeed, in the Messenger of Allāh you have a good "
        "example\"); that claim cannot coexist with a 7th-century "
        "ethical ceiling. If the Prophet's personal supervision of "
        "600-plus beheadings was ethical <em>for 622 CE but not today</em>, "
        "then either 33:21 is false (he is not the timeless exemplar) "
        "or 7th-century Arabian battlefield ethics remain binding now. "
        "The apologist cannot accept either horn: the first abandons "
        "Prophetic exemplarity, the second is morally indefensible. "
        "\"Laws of his time\" is the whole point, conceded.</p>"
    ),
}


# ----- Application ------------------------------------------------------

ENTRY_RE = re.compile(
    r'(<div class="entry"[^>]*id="([^"]+)"[^>]*>)(.*?)(</div>\s*(?=<div class="entry"|</main|<footer|$))',
    re.DOTALL,
)
PLACEHOLDER_RE = re.compile(
    r'<p><em>\(Needs expansion\.\)</em></p>', re.IGNORECASE
)


def process(path: Path, write: bool) -> int:
    html = path.read_text(encoding="utf-8")

    changed = 0
    out = []
    last = 0
    # Find every entry div and check if it needs replacement.
    for m in ENTRY_RE.finditer(html):
        out.append(html[last:m.start()])
        open_tag, eid, body, close = m.group(1), m.group(2), m.group(3), m.group(4)
        rebuttal = REBUTTALS.get(eid)
        if rebuttal and "Needs expansion" in body:
            new_body, n = PLACEHOLDER_RE.subn(rebuttal, body)
            if n:
                changed += n
                body = new_body
        out.append(open_tag + body + close)
        last = m.end()
    out.append(html[last:])

    new_html = "".join(out)

    # Fall-back: if the regex didn't reach every entry (e.g. the last
    # entry's closing </div> is adjacent to something we didn't anticipate),
    # do a global replace for any id still listed in REBUTTALS.
    if new_html == html and "Needs expansion" in html:
        for eid, rebuttal in REBUTTALS.items():
            # Target the placeholder inside a specific entry.
            rx = re.compile(
                r'(<div class="entry"[^>]*id="' + re.escape(eid)
                + r'"[^>]*>[\s\S]*?)<p><em>\(Needs expansion\.\)</em></p>'
            )
            new_html, n = rx.subn(r"\1" + rebuttal, new_html)
            changed += n

    if write and new_html != html:
        path.write_text(new_html, encoding="utf-8")
    return changed


def main() -> None:
    write = "--write" in sys.argv[1:]
    path = SITE / "catalog" / "muslim.html"
    n = process(path, write=write)
    mode = "APPLIED" if write else "DRY-RUN"
    print(f"{mode}: {n} 'Why it fails' sections updated in {path.name}")


if __name__ == "__main__":
    main()

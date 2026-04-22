#!/usr/bin/env python3
"""Batch 14: Quran Moderate entries 41-80."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent


def apply_content(path, anchor, response, refutation):
    text = path.read_text(encoding="utf-8")
    anchor_idx = text.find(anchor)
    if anchor_idx < 0:
        return False, f"anchor not found: {anchor[:60]}"
    end_idx = text.find("</section>", anchor_idx)
    if end_idx < 0:
        return False, "no </section> after anchor"
    line_start = text.rfind("\n", 0, end_idx)
    indent = ""
    for c in text[line_start + 1:end_idx]:
        if c in " \t":
            indent += c
        else:
            break
    segment = text[anchor_idx:end_idx]
    if "<h4>The Muslim response</h4>" in segment:
        return False, "entry already has Muslim response section"
    block = (
        f"{indent}<h4>The Muslim response</h4>\n"
        f"{indent}<p>{response}</p>\n"
        f"{indent}<h4>Why it fails</h4>\n"
        f"{indent}<p>{refutation}</p>\n"
    )
    new_text = text[:end_idx] + block + text[end_idx:]
    path.write_text(new_text, encoding="utf-8")
    return True, None


BATCH = [
    {
        "anchor": "Infant Jesus:",
        "response": (
            "Classical apologetics harmonises 19:33 with 4:157-158 by positing Jesus's future "
            "death: he was taken up alive, will return at the end times, and will die then — "
            "so \"the day I die\" is prospective, not retrospective. The two verses describe "
            "different events in an extended timeline rather than contradicting each other."
        ),
        "refutation": (
            "Reading 19:33's \"the day I die\" as referring to an event 2,000+ years after the "
            "verse's context (infant Jesus speaking) stretches the natural reading beyond "
            "recognition. The harmonisation exists because the alternative — that Jesus did "
            "die, consistent with all Christian and historical sources — would undermine "
            "Islamic Christology. The apologetic rescue requires importing a future death-"
            "event the passage does not mention to save the Quran from its own textual "
            "structure."
        ),
    },
    {
        "anchor": "The Messiah, son of Mary, was not but a messenger",
        "response": (
            "Classical apologetics argues the verse uses the eating observation to draw "
            "attention to Jesus and Mary's ordinary human physicality — contrasting this with "
            "the divine status Christians claim for Jesus. The argument form is rhetorical "
            "\"mother and son both need food, therefore neither is divine in the sense of "
            "being above creaturely needs.\""
        ),
        "refutation": (
            "\"Divine beings don't eat\" is not a premise of Christian theology. Christians "
            "hold Jesus is <em>incarnate</em> — fully divine and fully human — which means "
            "eating is exactly what incarnation entails. The Quran's argument refutes a "
            "Christology Christians do not hold (a docetic view where Jesus only appears to "
            "be human). A divine author correcting Christian theology should be engaging the "
            "theology Christians confess, not the version easiest to refute."
        ),
    },
    {
        "anchor": "Abide in your houses and do not display yourselves as",
        "response": (
            "Classical apologetics limits 33:33 to Muhammad's wives (\"O wives of the "
            "Prophet\"), not all Muslim women. The <em>Ummahat al-Mu'minin</em> had "
            "distinctive public-religious roles that warranted specific conduct guidelines. "
            "Modern apologists emphasise that the broader female-public-life restrictions "
            "classical jurisprudence extracted from this verse are misapplications, not "
            "the text's intent."
        ),
        "refutation": (
            "Classical jurisprudence (across Sunni schools) consistently extended the "
            "principle to all Muslim women, treating 33:33 as the textual basis for public-"
            "space restrictions. Modern Saudi-style confinement, Taliban-era Afghan home-"
            "confinement policies, and Iranian public-attire regulation all cite this "
            "verse as warrant. The \"only Muhammad's wives\" narrowing is modern reformist "
            "work against the classical grain. The verse's \"former times of ignorance\" "
            "framing presupposes pre-Islamic Arabian female public life was degraded — "
            "itself a characterisation that advances a specific social model."
        ),
    },
    {
        "anchor": "Do not make difficulties for them in order to take [back] part",
        "response": (
            "Classical apologetics frames the \"flagrant immorality\" exception as "
            "protective: the mahr-reclamation is permitted only in extreme cases of "
            "marital misconduct that would warrant divorce on the husband's side. The "
            "rule prevents divorce-extortion by husbands while allowing legitimate "
            "financial adjustment when serious misconduct occurs."
        ),
        "refutation": (
            "The \"flagrant immorality\" (<em>fahishatin mubayyina</em>) category is "
            "defined broadly across classical jurisprudence — covering not only adultery "
            "but various marital disobediences (refusing sex, leaving home without "
            "permission, etc.). Modern courts applying classical fiqh have used the "
            "exception extensively to justify mahr-reclamation cases where the "
            "\"immorality\" is disputed. The exception's existence creates exactly the "
            "extortion opportunity the rule claims to prevent: husbands can threaten "
            "immorality accusations as leverage."
        ),
    },
    {
        "anchor": "And We made the sky a protected ceiling (saqfan mahfuzan).",
        "response": (
            "Modern apologetic readings interpret \"protected ceiling\" as the atmosphere's "
            "protective function against cosmic radiation, ultraviolet rays, and meteors — "
            "retrofitting the verse to correspond with atmospheric science. The ancient "
            "vocabulary of a \"ceiling\" is translated into the modern understanding of "
            "the atmosphere as protective shell."
        ),
        "refutation": (
            "The \"atmospheric protection\" reading is pure retrofit. Classical tafsir "
            "(Tabari, Ibn Kathir) read <em>saqfan mahfuzan</em> as a literal physical "
            "canopy — consistent with the pre-Islamic Near Eastern cosmology where the "
            "sky was a solid vault above the earth. The reading aligned with Genesis 1:7's "
            "<em>raqia</em> (firmament) and the Mesopotamian cosmology Islam inherited. "
            "Modern atmospheric retrofit reads modern science back into 7th-century "
            "cosmological vocabulary; the classical readers did not — because the "
            "atmosphere-as-protective-shell was not within their conceptual range."
        ),
    },
    {
        "anchor": "And We adorned the nearest heaven with lamps and as protection.",
        "response": (
            "Modern apologetics reads the stars-as-lamps imagery as poetic description of "
            "their visual function for human observers, not a claim about their physical "
            "nature or location. Some apologists cite the verse's \"protection\" clause "
            "as anticipating the ionosphere's role in deflecting cosmic radiation — a "
            "scientific miracle embedded in the ancient vocabulary."
        ),
        "refutation": (
            "Classical tafsir treated the lamps imagery as cosmology, not poetry: stars "
            "were physically located in the \"lowest heaven\" and functioned as projectiles "
            "against jinn attempting to eavesdrop on angelic councils (37:7-10 pairs "
            "with this verse). The seven-heavens cosmology is Mesopotamian; stars-in-"
            "the-lowest-level is how pre-Islamic Arabian and Jewish apocalyptic literature "
            "described the visible sky. Stars are not lamps, are not in any lowest heaven, "
            "and are at distances that make \"lowest\" meaningless. The retrofit is "
            "modern apologetic work; the classical framework was flat-Earth cosmology."
        ),
    },
    {
        "anchor": "We sent down iron, wherein is great military might",
        "response": (
            "Modern apologetic literature (Naik, Bucaille) argues \"sent down iron\" "
            "anticipates the discovery that Earth's iron originated from supernova "
            "explosions and was literally \"sent down\" from stellar nucleosynthesis. "
            "The verse is read as scientific miracle predating nuclear astrophysics."
        ),
        "refutation": (
            "<em>Anzalna</em> (\"we sent down\") is used throughout the Quran for "
            "scripture, rain, cattle, garments, and divine mercy — none of which "
            "originate in supernovae. The word means \"we bestowed\" or \"we caused to "
            "descend\" in generic metaphorical senses. The iron-from-supernova retrofit "
            "requires the verse to use <em>anzalna</em> in a sense contrary to its "
            "normal Quranic usage, specifically when the modern astrophysical claim "
            "makes the retrofit attractive. That is pattern-matching after the fact, "
            "not linguistic analysis."
        ),
    },
    {
        "anchor": "We did not send any messenger except [speaking] in the language",
        "response": (
            "Classical apologetics argues 14:4 establishes a general principle (prophets "
            "are sent to their immediate communities in their language), while 34:28 "
            "establishes a specific exception (Muhammad is the universal prophet). The "
            "Arabic medium of the Quran is for its original community, but its message "
            "is universal through translation — which Islamic tradition has endorsed "
            "in practice."
        ),
        "refutation": (
            "The Quran simultaneously claims local-language prophethood as the standing "
            "rule (14:4) and universal prophethood for Muhammad specifically (34:28). "
            "The two positions cannot both be comprehensively true: either each "
            "community gets its own prophet in its language (in which case Muhammad's "
            "Arabic is not for non-Arabs) or Muhammad is universal (in which case 14:4's "
            "rule is overridden specifically for him). The apologetic exception-making "
            "exposes what the text will not simply say: universality requires either "
            "translation (which compromises the revelation's Arabic-perfection claim) "
            "or Arabic-learning by non-Arabs (which is not how Islam has operated)."
        ),
    },
    {
        "anchor": "If you are in doubt about that which We have revealed to you",
        "response": (
            "Classical apologetics reads 10:94 as addressed to Muhammad's "
            "contemporaries rather than to Muhammad himself — the People of the Book "
            "would recognise Muhammad's prophethood through indicators in their own "
            "scriptures (regardless of later corruption). The verse is evidence for "
            "Muhammad's prophethood via external confirmation, not a statement that "
            "Jewish/Christian texts were reliable on all matters."
        ),
        "refutation": (
            "The verse addresses Muhammad in the second person (\"if <em>you</em> are "
            "in doubt\") and directs him to \"ask those who read the Scripture before "
            "you.\" The apologetic redirection to \"Muhammad's contemporaries\" requires "
            "the verse to mean something other than what it says. And the premise — "
            "that Jewish and Christian scriptures can answer doubts about Quranic "
            "revelation — presupposes their reliability, which is the Islamic Dilemma's "
            "core tension: if reliable, they contradict the Quran's Christology; if "
            "corrupted, consulting them resolves nothing."
        ),
    },
    {
        "anchor": "No one can change His words.",
        "response": (
            "Classical apologetics distinguishes <em>tahrif al-ma'na</em> (corruption of "
            "meaning) from <em>tahrif al-nass</em> (corruption of text): Allah's words "
            "remain unchanged textually, but Jewish and Christian interpretation "
            "distorted the meaning. This preserves the \"unchangeable\" claim while "
            "allowing Islamic critique of what those communities believe about their "
            "own scripture."
        ),
        "refutation": (
            "The <em>tahrif al-ma'na</em> rescue does not save the polemic: if the "
            "words are unchanged and only interpretation is distorted, Muslims could "
            "simply consult the unchanged text and extract Allah's intent — which they "
            "do not, because the unchanged text (Jesus's divinity, crucifixion, "
            "Trinity) contradicts the Quran on every major Christian doctrine. Classical "
            "polemic (Ibn Hazm, al-Biruni) oscillated between <em>ma'na</em> and "
            "<em>nass</em> depending on the argument being made — moving goalposts, "
            "not a principled theory."
        ),
    },
    {
        "anchor": "He took attendance of the birds and said, 'Why do I not see the hoopoe",
        "response": (
            "Classical tafsir treats the Solomon-hoopoe story as genuine prophetic "
            "history preserved in Islamic tradition after it was lost or simplified in "
            "the Biblical canon. Jewish midrashic parallels (Targum Sheni on Esther) "
            "are cited as evidence of an authentic oral tradition that both Jewish "
            "and Islamic sources draw on."
        ),
        "refutation": (
            "The Targum Sheni on Esther — where the hoopoe-and-Sheba story originates — "
            "is post-biblical Jewish haggadic literature, legendary in genre, with no "
            "claim to historical authenticity even within Jewish tradition. The Quran's "
            "inclusion of this story is borrowing from Jewish folk-tradition, not "
            "confirmation of a historical event. The \"both sources preserve authentic "
            "tradition\" framing grants legitimacy to material Islam elsewhere rejects "
            "as post-biblical embellishment when it serves other polemical purposes."
        ),
    },
    {
        "anchor": "And We did certainly create the heavens and earth and what is between",
        "response": (
            "Classical apologetics argues the Quran is correcting a popular misreading "
            "of Genesis rather than the Hebrew text itself — some Jewish devotional "
            "literature had treated \"rested\" anthropomorphically, and the Quran "
            "clarifies Allah's transcendent non-exhaustion. Modern apologists emphasise "
            "that Jewish interpretive literature did contain passages implying divine "
            "fatigue, which the Quran corrects."
        ),
        "refutation": (
            "\"Shavat\" in Hebrew (Genesis 2:2-3) means \"ceased\" or \"stopped\" — "
            "not \"rested from fatigue.\" Mainstream Jewish theology has never held "
            "that Allah tired; the Sabbath rest is modeled on divine cessation, not "
            "divine exhaustion. The Quran is refuting a Jewish doctrine no Jewish "
            "community has held — a straw man. \"Popular misreading\" defense requires "
            "identifying a specific community that actually held the view being "
            "refuted, which apologetic literature has not produced."
        ),
    },
    {
        "anchor": "They remained in their cave for three hundred years and exceeded by ni",
        "response": (
            "Classical apologetics argues the \"309 years, Allah knows best\" pattern "
            "serves theological teaching: specific numerical details provide context "
            "while the disclaimer emphasises that ultimate temporal knowledge belongs "
            "to Allah. The verse models epistemic humility — human narration reports "
            "what is known while acknowledging divine knowledge exceeds human frames."
        ),
        "refutation": (
            "A specific number followed by an immediate disclaimer is a narrative "
            "structure that doesn't match the epistemic humility framing: either the "
            "309 is precise (disclaimer is superfluous) or it is uncertain (number is "
            "misleading). The combination reads as a text recording a traditional "
            "number from circulating sources (the Christian legend gave various "
            "ranges) while hedging about certainty. That is textual behaviour "
            "consistent with a human author working from inherited material, not "
            "independent divine knowledge."
        ),
    },
    {
        "anchor": "O you who have believed, indeed, among your wives and your children ar",
        "response": (
            "Classical tafsir contextualises 64:14 as addressing specific 7th-century "
            "situations where family members pressured new converts to abandon Islam. "
            "The \"enemy\" language is functional — family as obstacle to faith in "
            "specific circumstances — not a blanket definition of spouses as adversaries. "
            "Modern apologists emphasise parallel verses (30:21) describing marital "
            "affection, demonstrating the text's broader vision of positive marriage."
        ),
        "refutation": (
            "The \"specific 7th-century context\" framing is the standard apologetic "
            "move for verses whose plain content is ethically awkward. The verse's "
            "language is categorical (\"among your wives and your children\"), and "
            "classical tafsir applied the principle broadly — warning believers that "
            "family relationships could become obstacles to faith. The combination of "
            "30:21's marital affection and 64:14's family-as-enemy is exactly the "
            "tension the tradition has had to manage: a scripture that uses both "
            "registers has communicated conflicting visions rather than one coherent "
            "ethics of family."
        ),
    },
    {
        "anchor": "We made from the drop a clinging clot, and from the clot a chewed lump",
        "response": (
            "Classical apologetics and modern <em>i'jaz 'ilmi</em> literature argue "
            "the embryological sequence in 23:14 anticipates modern embryology — with "
            "the stages corresponding to zygote, blastocyst, embryo, bone formation, "
            "and muscle development. Some modern embryologists (Keith Moore, cited by "
            "Islamic apologists) have been quoted endorsing the Quran's sequence."
        ),
        "refutation": (
            "Modern embryology shows muscle tissue (myoblasts) differentiates before "
            "or alongside bone ossification — not after bones are \"clothed with "
            "flesh.\" The Quran's specific sequence mirrors Galen's 2nd-century "
            "medical model (already standard in the Arab-speaking Near East centuries "
            "before Muhammad), with bones formed first and flesh added after. The "
            "Keith Moore endorsement is complicated — his involvement with Islamic "
            "apologetic literature is documented, and his positive comments were in "
            "Islamic-funded publications, not in peer-reviewed embryology journals. "
            "The retrofit is pattern-matching to inherited Greek physiology."
        ),
    },
    {
        "anchor": "And indeed, a day with your Lord is like a thousand years",
        "response": (
            "Classical tafsir harmonises 22:47 (1,000 years) and 70:4 (50,000 years) "
            "through contextual reading: different verses describe different temporal "
            "scales for different events (worldly days, judgment-day extension, "
            "eschatological duration). The \"day\" is a flexible term, and the "
            "numbers are rhetorical rather than precise — conveying vastness, not "
            "measurement."
        ),
        "refutation": (
            "If both numbers are rhetorical, the verses are not numerically specific — "
            "but the Quran uses them in contexts where the specificity matters (one as "
            "measurement of Allah's temporal perspective, one as measurement of "
            "ascent). If both are literal, they contradict. The apologetic harmonisation "
            "requires assigning each number to a different contextual referent the "
            "text does not draw. That is rescue by stipulation, not by reading."
        ),
    },
    {
        "anchor": "We have certainly created for Hell many of the jinn and mankind.",
        "response": (
            "Classical Ash'arite theology affirms divine foreknowledge and creation "
            "without denying human moral responsibility — the <em>khalq/kasb</em> "
            "distinction (Allah creates, human acquires) resolves the apparent "
            "conflict. The verse expresses Allah's knowledge of who will choose "
            "damnation, not predetermination that overrides choice."
        ),
        "refutation": (
            "The verse says Allah \"created\" (<em>dhara'na</em>) them for hell — "
            "which is causal language, not mere foreknowledge. The Ash'arite <em>"
            "khalq/kasb</em> distinction is the scholastic patch developed centuries "
            "later specifically to manage this problem, and its opacity is proverbial. "
            "If moral responsibility requires genuine alternative possibilities, and "
            "Allah creates some for hell, their alternatives are not genuine — and "
            "classical theodicy has not satisfactorily resolved this tension. The "
            "verse's plain sense has been a problem the tradition has had to defuse "
            "repeatedly."
        ),
    },
    {
        "anchor": "Whatever befalls you of good is from Allah, and whatever befalls you o",
        "response": (
            "Classical tafsir harmonises 4:78-79 through different-aspect reading: "
            "4:78 refers to existential occurrence (both good and evil happen under "
            "divine sovereignty), while 4:79 refers to moral authorship (evil comes "
            "from human choice). The Ash'arite distinction between divine creation "
            "and human acquisition preserves both verses."
        ),
        "refutation": (
            "The text does not draw the existential/moral distinction — readers must "
            "import it. Both verses use the same word (<em>sayyi'ah</em>, bad thing/"
            "misfortune), and the context is the same (discussing Muhammad's "
            "critics). The harmonisation is an interpretive invention produced by "
            "theologians to manage the surface contradiction. A text that requires "
            "invented distinctions to avoid contradicting itself within two "
            "consecutive verses has a clarity problem the tradition has worked hard "
            "to paper over."
        ),
    },
    {
        "anchor": "Indeed, those who disbelieve in Our verses — We will drive them into a",
        "response": (
            "Classical theology reads hell's skin-replacement as eschatological reality "
            "preserving the proportion between sin's severity and its consequence. "
            "The apparent cruelty reflects the gravity of rejecting Allah's truth; "
            "the mercy-precedes-wrath principle operates alongside justice, not "
            "instead of it. Modern apologists emphasise that hell is chosen by the "
            "damned, not imposed arbitrarily."
        ),
        "refutation": (
            "Proportionality fails when finite earthly wrongdoing is met with infinite "
            "torture specifically engineered for maximum pain extension. The skin-"
            "replacement detail exists for one purpose: to prevent the body from "
            "becoming desensitised and allowing the torture to remain maximally "
            "painful. That is intentional pain-maximisation, not proportionate "
            "justice. \"Mercy precedes wrath\" is rhetorically maintained while "
            "wrath's operational content is engineered cruelty — which means the "
            "precedence claim is decorative rather than substantive."
        ),
    },
    {
        "anchor": "We gave David from Us bounty. 'O mountains, repeat Our praises with",
        "response": (
            "Classical apologetics frames the mountains-and-birds praise as miraculous "
            "event demonstrating Allah's power over the natural world — part of "
            "David's prophetic credentials. The Quran preserves a tradition found in "
            "Jewish imagination (Psalm 98's poetic imagery) but treats it as "
            "literal historical event rather than figurative celebration."
        ),
        "refutation": (
            "Psalm 98:8 (\"let the rivers clap their hands, let the mountains sing "
            "together\") is Hebrew poetic personification — a standard literary "
            "device, not a literal claim. The Quran literalises the imagery as "
            "historical event featuring David. That transformation — poetic "
            "personification becomes reported miracle — is exactly what happens "
            "when literary language crosses cultural boundaries and is absorbed "
            "into different genre conventions. It is the signature of oral-"
            "transmission repurposing, not independent witness."
        ),
    },
    {
        "anchor": "Bring me sheets of iron... until, when he had leveled [them] between t",
        "response": (
            "Classical tafsir proposes various identifications for Dhul-Qarnayn's "
            "wall: the Iron Gate near Derbent (Caucasus), the Great Wall of China, "
            "or structures in Armenia or Turkestan. Modern apologists have pointed "
            "to the Caspian Iron Gate (Derbent) as physical candidate. The "
            "archaeology of remote or lost structures does not definitively "
            "refute the claim."
        ),
        "refutation": (
            "None of the proposed candidates matches the Quran's description (iron-"
            "and-molten-copper wall sealing a mountain pass against eschatological "
            "Gog and Magog). The Gog-Magog mythology is directly borrowed from "
            "Ezekiel 38-39 — post-exilic Jewish apocalyptic. The Dhul-Qarnayn "
            "narrative itself shows structural parallels to the Syriac Alexander "
            "Legend (c. 629 CE), composed shortly before the Quran's revelation, "
            "which features Alexander building an iron gate against Gog and Magog. "
            "The wall is legendary, not archaeological, and the parallel sources "
            "the Quran is drawing from are identifiable."
        ),
    },
    {
        "anchor": "Allah revealed to the angels: 'I am with you, so strengthen those who",
        "response": (
            "Classical apologetics contextualises 8:12 to the specific Battle of Badr "
            "— the \"strike upon the necks\" and \"every fingertip\" language is "
            "battlefield-tactical imagery for disabling enemy combat capacity, not "
            "execution instruction. Modern apologists emphasise that pre-modern "
            "battlefield vocabulary was inherently graphic without implying unique "
            "cruelty."
        ),
        "refutation": (
            "\"Strike upon the necks\" (<em>fadribu fawqa al-a'naq</em>) in classical "
            "Arabic idiom specifically denotes decapitation, not generic combat "
            "disabling. Classical Islamic military tradition (al-Shaybani, "
            "al-Mawardi) developed the imagery into operational principles. Modern "
            "jihadist groups cite these verses accurately within classical "
            "exegetical norms. The \"battlefield imagery only\" apologetic requires "
            "dismissing fourteen centuries of literal application."
        ),
    },
    {
        "anchor": "And the two who commit it among you, dishonor them both.",
        "response": (
            "Classical apologetics argues the Quranic punishment for same-sex acts is "
            "deliberately vague (\"dishonor them both\"), showing Islamic mildness "
            "relative to what the hadith corpus supplied later. The verse's vagueness "
            "is evidence Islam did not initially prescribe capital punishment for "
            "homosexuality — that was a later juristic development based on additional "
            "hadith."
        ),
        "refutation": (
            "The Quranic vagueness is exactly what made the hadith-supplied death "
            "penalty structurally available. If the Quran were silent or "
            "non-punitive, classical jurisprudence would have had no Quranic hook "
            "for the elaborated death penalty. Instead, the Quran's \"dishonor "
            "them both\" (4:16) provides the legal framework into which hadith-"
            "supplied specifics were inserted. Modern Muslim-majority states "
            "executing for same-sex acts cite 4:16 alongside hadith; the classical "
            "doctrine rests on both."
        ),
    },
    {
        "anchor": "He said, 'O my people, these are my daughters; they are purer for you.",
        "response": (
            "Classical tafsir offers two defenses: (1) \"my daughters\" is idiomatic "
            "for \"the women of my tribe\" rather than Lot's literal biological "
            "children; (2) Lot offered marriage, not gang rape — suggesting the "
            "mob accept his daughters as lawful wives rather than violently assault "
            "his male guests. Neither reading is endorsed as ideal moral conduct; "
            "both preserve Lot's prophetic character by removing the offer-of-"
            "daughters as literal violation of parental ethics."
        ),
        "refutation": (
            "The \"women of my tribe\" reading is not supported by Arabic usage — "
            "<em>banati</em> (my daughters) is literal across Quranic and general "
            "Arabic. The \"marriage not gang rape\" reading requires the mob to be "
            "interested in marital proposals during a scene where they are "
            "demanding access to sexually assault the male guests. Neither rescue "
            "is plausible on the text. The underlying story is Genesis 19's, and "
            "the moral problem (Lot protecting guest-law by offering his daughters) "
            "is inherited along with the narrative. A divine retelling could have "
            "edited the detail; it preserved it instead."
        ),
    },
    {
        "anchor": "The [unmarried] woman or [unmarried] man found guilty of sexual interc",
        "response": (
            "Classical apologetics defends the 100-lashes-with-no-pity rule as "
            "graduated severity: public, communal, deterrent, but survivable. "
            "The \"let no pity move you\" language is not theologisation of "
            "cruelty but legal procedural caution — judges should not avoid "
            "execution due to personal sympathy when the evidence supports "
            "conviction. The four-witness evidentiary bar makes actual application "
            "rare."
        ),
        "refutation": (
            "100 lashes can kill, depending on the lashing method — this is not "
            "merely survivable corporal punishment. The \"no pity\" framing is "
            "theologisation of harshness: legal systems in most times and places "
            "build in judicial discretion to mitigate severity; this verse "
            "explicitly instructs judges to suppress that instinct. \"Effective "
            "deterrent through public execution\" is the standard apologetic for "
            "this kind of punishment; it is also the standard apologetic given "
            "for every other public-torture system, from Roman crucifixion to "
            "medieval European breaking-wheel. The rhetoric does not "
            "distinguish this case."
        ),
    },
    {
        "anchor": "Fight those who do not believe in Allah or the Last Day",
        "response": (
            "Classical apologetics argues the jizya framework offered protection under "
            "specific legal terms — retained religious practice, property, and "
            "judicial autonomy in exchange for the tax. The <em>saghirun</em> "
            "(\"while they are humbled\") language reflects the political reality "
            "of subject-status, not prescriptive ritual humiliation. Modern "
            "apologists emphasise that dhimmi communities often flourished under "
            "Muslim rule."
        ),
        "refutation": (
            "Classical jurists (Ibn Kathir, al-Qurtubi, across Sunni schools) "
            "explicitly codified ritual degradation at the moment of jizya payment: "
            "standing while the Muslim sat, coins thrown on the ground, a slap on "
            "the neck in some formulations. This is not anti-Muslim slander — it "
            "is the classical legal manual's own prescription. The \"dhimmi "
            "flourishing\" argument mixes periods of genuine tolerance with "
            "periods of brutal enforcement (Almohads, late-Ottoman pogroms, "
            "massacres in Yemen and Morocco). The verse encodes a 7th-century "
            "political arrangement as eternal law."
        ),
    },
    {
        "anchor": "all married women, except those your right hands possess",
        "response": (
            "Classical tafsir argues capture in war effectively dissolved prior "
            "marriages (defended by Ibn Kathir and al-Qurtubi), so the captive "
            "woman was not simultaneously married and sexually available — the "
            "capture <em>was</em> the dissolution. Modern apologists add that "
            "Islamic reform of slavery was progressive: regulation tightened over "
            "time, pointing toward an abolition the tradition did not complete."
        ),
        "refutation": (
            "The \"capture dissolves marriage\" claim has no basis in the Quran "
            "itself — it is juristic invention added later to make the sexual "
            "ethics intelligible. The verse's grammar presupposes the marriage "
            "still exists when it exempts \"married women\" from forbidden "
            "categories. The \"progressive regulation\" narrative is 20th-century "
            "apologetic frame; classical jurisprudence treated concubinage as "
            "permanent permission. ISIS's 2014 enslavement of Yazidi women cited "
            "this verse with explicit classical legal footnoting — correctly "
            "applying the classical reading."
        ),
    },
    {
        "anchor": "Those who disbelieve after their belief",
        "response": (
            "Classical apologetics notes that the Quran itself does not prescribe an "
            "earthly death penalty for apostasy — it describes divine punishment in "
            "the Hereafter. The hadith-supplied capital punishment is an additional "
            "legal development. Modern reformists argue the Quranic framework alone "
            "supports religious-freedom reform, with apostasy as a matter between "
            "the individual and Allah."
        ),
        "refutation": (
            "The Quranic curse-and-Hellfire framework sets the theological weight "
            "that made the hadith-supplied death penalty structurally available. "
            "If the Quran had explicitly protected religious freedom (rather than "
            "merely describing divine post-mortem punishment), the classical "
            "apostasy-death jurisprudence would have had no Quranic foothold. "
            "Thirteen-plus Muslim-majority countries still have apostasy laws; "
            "classical consensus across all four Sunni schools treated apostasy as "
            "capital. The \"Quran doesn't command execution\" defense is "
            "technically accurate but ignores the surrounding corpus the "
            "tradition has treated as unified."
        ),
    },
    {
        "anchor": "Allah has set a seal upon their hearts and upon their hearing",
        "response": (
            "Classical theology treats the sealing as <em>consequence</em> of prior "
            "rejection — Allah seals hearts that have already chosen disbelief, "
            "formalising a state the person has already produced. The seal is "
            "confirmation of the individual's settled disposition, not "
            "predetermined incapacity. The Ash'arite compatibilist framework "
            "preserves both divine action and human responsibility."
        ),
        "refutation": (
            "The \"consequence not cause\" reading is the apologetic patch; the "
            "text gives no temporal sequence between disbelief and sealing. The "
            "verse states that the sealed person will not believe <em>because</em> "
            "Allah has sealed them — which is causal. If the sealing came after "
            "rejection, the verse would say so; it does not. Classical Ash'arite "
            "theology accepts the causal reading and dissolves free will through "
            "the <em>khalq/kasb</em> distinction — the modern \"just a consequence\" "
            "reading requires a stronger free-will doctrine than the tradition "
            "actually maintains."
        ),
    },
    {
        "anchor": "There will circulate among them [servant] boys [especially] for them",
        "response": (
            "Classical tafsir treats the boy-servants as dedicated paradise-staff — "
            "eternal young attendants serving the blessed, without sexual implication. "
            "The aesthetic description (pearls) is generic praise of beauty in pre-"
            "modern literary convention, not sensual sexualisation. Modern apologists "
            "emphasise that serving-youths appear in paradise descriptions across "
            "religious traditions without implying erotic content."
        ),
        "refutation": (
            "Classical tafsir itself is uncomfortable with these verses — "
            "commentators (Tabari, Ibn Kathir) discuss the sensual register at "
            "length, with some preserving interpretations that read the "
            "descriptions as including ephebephilic content. The parallels to "
            "Persian and Hellenistic paradise-feast imagery (where beautiful "
            "serving-youths function as aesthetic-erotic décor) are specific. The "
            "\"generic praise\" defense works only if one ignores the "
            "cross-cultural genre conventions the Quran's imagery participates "
            "in."
        ),
    },
    {
        "anchor": "Humiliation will be their portion wheresoever they are found",
        "response": (
            "Classical tafsir reads the verse as description of historical "
            "circumstance (the Jews who rejected Muhammad's prophethood in 7th-"
            "century Medina) rather than permanent divine curse. The "
            "\"wheresoever they are found\" language is rhetorical emphasis on "
            "the specific community's condition at a specific historical moment, "
            "not eternal decree."
        ),
        "refutation": (
            "The verse's phrasing is universalising (\"wheresoever they are "
            "found\"), not historically bounded. Classical tafsir applied the "
            "language broadly to Jewish communities across time, which is why the "
            "verse has anchored centuries of Islamic anti-Jewish sentiment in "
            "popular religious discourse. Modern apologetic narrowing to a "
            "specific 7th-century context is reformist work against fourteen "
            "centuries of categorical application. A scripture that stamps an "
            "entire ethnoreligious community with \"humiliation wherever found\" "
            "has done theological work no amount of context-narrowing removes."
        ),
    },
    {
        "anchor": "[You hid] within yourself that which Allah is to disclose.",
        "response": (
            "Classical apologetics frames the Zaynab episode as deliberate legal "
            "reform — abolishing the pre-Islamic taboo against marrying an adopted "
            "son's ex-wife — accomplished through a specific case. Muhammad's "
            "\"concealment\" was of the coming reform, not improper desire. The "
            "marriage demonstrates that adopted-son status does not create "
            "biological-son affinity restrictions."
        ),
        "refutation": (
            "The verse explicitly says Muhammad concealed something he feared the "
            "people's judgment of — which is natural reading language for personal "
            "desire, not legal reform anticipation. Earliest tafsir (Tabari) is "
            "explicit: Muhammad saw Zaynab in an unguarded moment and was "
            "captivated. Allah's revelation arrived precisely when Muhammad's "
            "desire and the social prohibition collided, resolving the tension in "
            "his favor. A universal lawgiver abolishing adoption-affinity "
            "restrictions could have done so without simultaneously marrying the "
            "specific woman in question. The \"legal reform\" framing does not "
            "remove what the text concedes."
        ),
    },
    {
        "anchor": "And his wife [as well] — the carrier of firewood.",
        "response": (
            "Classical tafsir preserves the specific curse as historical record of "
            "the divine-authorised rebuke to Muhammad's specific opponents — Abu "
            "Lahab and his wife Umm Jamil actively persecuted Muhammad and his "
            "followers, and the eternal Quranic record memorialises this "
            "opposition as warning to future enemies of Islam. The specific detail "
            "(firewood-carrier) references Umm Jamil's reported practice of placing "
            "thorny branches in Muhammad's path."
        ),
        "refutation": (
            "An eternal scripture includes a named curse of a specific 7th-century "
            "Arab woman, preserving her personal opposition-behavior in permanent "
            "memorial. Every Muslim in Jakarta, Dakar, or Istanbul recites the "
            "surah, directing a curse at a woman most have never heard of in any "
            "other context. A book addressed to all humanity for all time should "
            "not embed revenge-oracles against specific individuals whose "
            "significance is parochial to one man's biography. The personal-feud "
            "content reveals the compositional context of the surah."
        ),
    },
    {
        "anchor": "Say: 'I seek refuge in the Lord of daybreak",
        "response": (
            "Classical theology accepts magic (<em>sihr</em>) as a real causal "
            "phenomenon within the created order — a form of spiritual-material "
            "interaction that Allah permits but that believers should seek refuge "
            "from. The Surah al-Falaq addresses specific forms of malicious magic "
            "(knot-tying rituals) documented in pre-Islamic Arabian practice; the "
            "verse's acknowledgment of the threat is not endorsement of its "
            "cosmological ontology, but protection against it."
        ),
        "refutation": (
            "\"Real causal phenomenon in the created order\" is precisely the "
            "concession: Islam's holiest text confirms knot-magic as a supernatural "
            "threat requiring divine protection. The historical context (Muhammad "
            "bewitched by Labid's knot-magic per Bukhari 5763) embeds the folk "
            "cosmology into Islam's canonical origin stories. A revelation that "
            "corrected superstition would not simultaneously authenticate knot-"
            "magic as real supernatural attack; it would dismiss the folk belief. "
            "The Quran does the opposite."
        ),
    },
    {
        "anchor": "[I seek refuge] from the evil of the retreating whisperer",
        "response": (
            "Classical theology treats the whisperer (<em>al-waswas</em>) as Satan "
            "inserting intrusive suggestions into human consciousness — a real "
            "spiritual attack described in the Quran's cosmology of temptation. "
            "The protection-prayer framework is pastoral-psychological: when "
            "intrusive thoughts occur, the believer has verbal resources for "
            "spiritual response. Modern Islamic psychology distinguishes between "
            "spiritual waswasa and medical OCD, recommending clinical treatment "
            "for the latter."
        ),
        "refutation": (
            "The framework attributes intrusive thoughts — many of which modern "
            "neurology identifies as ordinary cognitive phenomena or symptoms of "
            "conditions like OCD — to external demonic attack. This "
            "misattribution has concrete consequences: Muslim OCD patients are "
            "often told to perform more <em>ruqya</em> rather than seek clinical "
            "care, with the <em>waswas</em> framework providing theological "
            "grounding for the delay. Modern reformist Islamic psychology "
            "separating the categories is welcome reform but requires reading the "
            "Quranic framework as metaphorical rather than ontological — which "
            "is not how the classical tradition has treated it."
        ),
    },
    {
        "anchor": "He who is given his record in his right hand will say",
        "response": (
            "Classical theology treats the deeds-scroll imagery as eschatological "
            "reality expressed in vocabulary 7th-century listeners could grasp — "
            "divine record-keeping rendered as physical scroll-delivery for "
            "pedagogical effect. The right/left symbolism is common to many "
            "pre-modern religions (Jewish apocalyptic, Zoroastrian, Christian) "
            "because it reflects a universal human symbolic vocabulary for "
            "moral-favorable versus moral-unfavorable."
        ),
        "refutation": (
            "\"Universal human symbolic vocabulary\" is the apologetic framing for "
            "what is more simply direct borrowing. Daniel 7:10 and Revelation 20:12 "
            "(both pre-Quranic Jewish-Christian apocalyptic) describe the same "
            "scroll-based judgment imagery. The Quranic version is downstream of "
            "this tradition, reshaped into Arabic-rhetorical form. A divine "
            "revelation whose eschatological vocabulary is indistinguishable from "
            "the surrounding apocalyptic tradition has preserved the genre, not "
            "corrected or transcended it."
        ),
    },
    {
        "anchor": "Never have We sent a messenger or a prophet before you but when he spo",
        "response": (
            "Classical tafsir reads 22:52 as describing the general danger of "
            "satanic interference in prophetic recitation — a warning about "
            "temptation to misstate divine revelation — without necessarily "
            "confirming the specific Satanic Verses incident. The verse "
            "establishes the category of satanic interference while Allah's "
            "subsequent correction preserves prophetic integrity."
        ),
        "refutation": (
            "The verse's explicit statement — Satan inserts suggestions into "
            "prophetic recitation, which Allah then removes — is exactly the "
            "mechanism the Satanic Verses narrative preserves. 22:52 exists in "
            "the canonical Quran because it was revealed in response to exactly "
            "that incident (the earliest biographical sources — Ibn Ishaq, al-"
            "Waqidi, al-Tabari — unanimously preserve this connection). The "
            "\"general warning\" reading is apologetic narrowing that severs the "
            "verse from its historical occasion; the classical tradition itself "
            "did not make this severance."
        ),
    },
    {
        "anchor": "There were men from mankind who sought refuge in men from the jinn",
        "response": (
            "Classical theology accepts jinn as real intermediate beings created "
            "by Allah, described repeatedly in the Quran (especially Surah "
            "al-Jinn). Pre-Islamic Arabian practice sometimes involved seeking "
            "jinn protection; the Quran redirects this impulse toward Allah "
            "alone while preserving the jinn's ontological reality. The "
            "correction is theological (shift the object of refuge), not "
            "cosmological (jinn remain real)."
        ),
        "refutation": (
            "Preserving jinn while redirecting allegiance does not correct the "
            "underlying cosmology — it retains pre-Islamic Arabian belief in a "
            "class of invisible intelligent beings while reassigning them "
            "theologically. The \"correction\" concedes the ontological premise "
            "and adjusts only the worship-relation. A revelation that genuinely "
            "dismantled pre-Islamic supernaturalism would dismiss jinn as "
            "folk-demonology; the Quran confirms their reality and merely "
            "restructures how Muslims relate to them. The cosmology has been "
            "inherited, not transcended."
        ),
    },
    {
        "anchor": "Nor [is it for you] to marry his wives after him, ever.",
        "response": (
            "Classical apologetics frames 33:53 as honor-preserving restriction: "
            "the Prophet's wives are <em>Ummahat al-Mu'minin</em> (Mothers of the "
            "Believers), a unique status that precluded ordinary remarriage out "
            "of respect for their distinctive religious role. The restriction is "
            "privilege-related, not punishment; their status prevents being "
            "reclassified back to ordinary marriageable women."
        ),
        "refutation": (
            "\"Honor-preservation\" fixes women's lifelong marital status by "
            "their husband's identity, effectively removing their autonomy over "
            "remarriage for decades — Aisha was approximately eighteen at "
            "Muhammad's death and would be bound by the restriction for the "
            "remaining ~50 years of her life. The verse calls being-with-the-"
            "Prophet's-widows an \"enormity\" (<em>'azim</em>), placing the rule "
            "under prohibition-by-gravity. Modern reformist reading that this is "
            "\"privilege\" for the women misreads the direction of constraint: "
            "it is a lifelong restriction on female remarriage, framed as "
            "honor-status, with the honored parties given no choice in the "
            "matter."
        ),
    },
    {
        "anchor": "Indeed, Safa and Marwa are among the symbols of Allah.",
        "response": (
            "Classical apologetics argues Safa and Marwa were originally Abrahamic "
            "sites corrupted by pre-Islamic paganism; Islam's inclusion of them "
            "in Hajj restores their original meaning (Hagar's frantic search for "
            "water for Ishmael). The pagan accretion (the idols Isaf and Na'ila "
            "placed at the sites) was removed by Islam; the ritual's core "
            "commemoration is Abrahamic."
        ),
        "refutation": (
            "The Hagar-Ishmael story is itself post-biblical Islamic elaboration; "
            "the Hebrew Bible does not place Hagar at Mecca (she is located in "
            "the wilderness of Beersheba per Genesis 21:14). The Safa-Marwa "
            "ritual existed in pre-Islamic Arabian polytheistic practice, with "
            "Muslim devotees uncomfortable enough about continuing it that the "
            "Quran reassures them (\"there is no blame on him who walks between "
            "them\" — 2:158). That reassurance reveals exactly the discomfort the "
            "apologetic wishes to dismiss: early Muslims knew the ritual was "
            "pagan in origin, and the verse exists to resolve their hesitation. "
            "Rebadging is not abolition."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/quran.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

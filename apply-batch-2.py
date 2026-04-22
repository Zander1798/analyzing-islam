#!/usr/bin/env python3
"""Batch 2: 20 more Strong Quran entries (11-30)."""
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
        "anchor": "Those who commit immorality of your women",
        "response": (
            "The classical defense is standard abrogation theology: 4:15 was a preliminary rule for "
            "a young community, replaced by the more specific and fair 24:2 (lashing for both men "
            "and women equally). The framework is \"progressive revelation\" — the community's legal "
            "capacity matured, and the final rule reflects equality. The asymmetry between 4:15 "
            "(women confined) and 4:16 (men addressed leniently) is read as Allah speaking to each "
            "sex's social situation in that context, not prescribing permanent inequality."
        ),
        "refutation": (
            "The \"progressive revelation\" frame concedes the point: the original rule was neither "
            "optimal nor eternal, which sits awkwardly with the Quran's self-description as the "
            "eternal word of an omniscient God. Even if one grants the abrogation logic, 4:15 was "
            "never retracted from the text — it sits in the Quran as recited scripture, and readers "
            "must import an external abrogation tradition to know not to apply it. And the original "
            "gender asymmetry is exactly what a human author embedded in 7th-century Arabian "
            "patriarchy would produce — the harsher penalty directed only at women is the "
            "fingerprint of its origin, and no theological rescue removes it from the text."
        ),
    },
    {
        "anchor": "And when the sacred months have passed, then kill the polytheists wherever you find them",
        "response": (
            "The mainstream apologetic response is contextual. 9:5 was revealed at the end of the "
            "truce period following the Treaty of Hudaybiyyah, directed at specific pagan tribes "
            "that had repeatedly broken their covenants with the Muslim community. The phrase "
            "\"when the sacred months have passed\" anchors the verse in that specific ceasefire. "
            "The following verse (9:6) commands that any polytheist who seeks safety must be "
            "granted protection and safely conveyed — a provision that would be nonsensical if "
            "9:5 licensed universal slaughter. Classical jurists read the two verses together as a "
            "rule of engagement against treaty-breakers, not a standing commandment."
        ),
        "refutation": (
            "The \"contextual\" reading is textually defensible but historically overridden. "
            "Classical Muslim scholarship (al-Suyuti, al-Baghawi, Ibn Kathir, the Hanafi and Shafi'i "
            "schools) classified 9:5 as the <em>abrogator</em> of the tolerance verses that preceded "
            "it, which means the situational reading was not the classical reading. Because Surah 9 "
            "is one of the latest Medinan surahs, on abrogation logic 9:5 overrides earlier "
            "tolerance as standing doctrine. The 9:6 escape clause provides a narrow exception for "
            "individuals seeking safety; it does not cancel the primary command. Modern jihadist "
            "organizations are not misreading this verse — they are applying the dominant classical "
            "reading. The apologetic rescue requires a modern hermeneutic the tradition did not "
            "itself deliver."
        ),
    },
    {
        "anchor": "Fight those who do not believe in Allah or in the Last Day and who do not consider unlawfu",
        "response": (
            "Apologists argue jizya was not uniquely humiliating but a standard protection-tax "
            "comparable to Byzantine and Persian tributes of the era — indeed, it replaced zakat "
            "(which only Muslims paid), so the fiscal burden on non-Muslims was roughly comparable "
            "to that on Muslims. The phrase <em>wa hum saghirun</em> (\"while they are humbled\") "
            "is read by some modern scholars as simply acknowledging the political reality that "
            "non-Muslims were second-tier subjects of the state, not as prescribing ritual "
            "humiliation. Historically, dhimmi communities often flourished economically and "
            "culturally under Muslim rule (Andalusian Jews, Coptic Christians), which they argue "
            "shows the system was liveable in practice."
        ),
        "refutation": (
            "The \"standard tribute of the era\" defense concedes that the Quran encodes a "
            "7th-century political arrangement into eternal divine law — which is precisely the "
            "problem with claiming Islam is a universal revelation for all time. The classical "
            "jurists (Ibn Kathir, al-Qurtubi, and across the Sunni schools) explicitly interpreted "
            "<em>wa hum saghirun</em> as requiring ritual degradation at the moment of payment: "
            "standing while the Muslim sat, coins thrown on the ground, sometimes a slap on the "
            "neck. That is not anti-Muslim slander; it is the tradition's own reading, codified in "
            "classical legal manuals. The \"dhimmis flourished\" argument mixes periods of "
            "genuine tolerance with periods of brutal enforcement (Almohads, late-Ottoman pogroms, "
            "massacres in Yemen and Morocco). An eternal divine law cannot be rehabilitated by "
            "pointing to the eras when it was softened or ignored."
        ),
    },
    {
        "anchor": "The Jews say, 'Ezra is the son of Allah'",
        "response": (
            "The classical reply — defended by al-Tabari, Ibn Kathir, and al-Qurtubi — is that "
            "the verse refers to a specific Jewish group in Medina (sometimes identified as a "
            "faction among the Banu Qurayza, or a fringe Yemeni sect) who allegedly held this "
            "view, and that the Quranic phrasing uses idiomatic Arabic rhetoric generalizing from "
            "a specific instance for polemical effect. Some modern apologists add that \"son of "
            "Allah\" need not imply literal divine sonship — the phrase could translate a Hebrew "
            "honorific (<em>ben Elohim</em>, \"sons of God\") occasionally applied to righteous "
            "figures including Ezra, especially in mystical texts like 4 Ezra."
        ),
        "refutation": (
            "There is no historical evidence — in rabbinic literature, in archaeology, in "
            "comparative religion — that any Jewish community ever held Ezra to be the son of God "
            "in any sense parallel to Christian Christology. 4 Ezra (2 Esdras) does contain one "
            "passage where Ezra is addressed as \"my son\" (14:9), but this is a generic divine "
            "address, not a doctrinal claim of divine sonship, and no Jewish community made it a "
            "tenet of belief. The \"specific fringe group\" defense relies on a group whose "
            "existence is unattested outside the defensive claim itself — a classic unfalsifiable "
            "rescue. The Quranic verse generalizes without qualification (\"The Jews say…\"), not "
            "\"a certain faction.\" A divine speaker correcting Jewish theology for all time "
            "should know what Jews actually believe; attributing to the whole community a doctrine "
            "no community has held is what a human author in 7th-century Arabia, relying on "
            "polemical rumor, would produce."
        ),
    },
    {
        "anchor": "I am with you, so strengthen those who have believed. I will cast terror",
        "response": (
            "Classical and modern apologists argue the verse addresses a specific battle (Badr) "
            "and is not a universal prescription — it is divine reassurance to believers in a "
            "life-or-death military situation, with graphic language typical of pre-modern "
            "battlefield rhetoric. \"Strike upon the necks\" and \"cut off every fingertip\" are "
            "idiomatic for \"disable the enemy in combat,\" not detailed instructions in execution "
            "method; every pre-modern culture used similar graphic war-speech. 8:60's call to "
            "prepare military strength \"to terrify the enemy\" is read by modern scholars as a "
            "deterrent doctrine — peace through preparedness — not terrorism against civilians."
        ),
        "refutation": (
            "The \"specific battle\" reading is textually possible but historically minority: "
            "classical jurists extracted general rules of warfare from Surah 8 and applied them as "
            "standing doctrine, not as a one-time speech. The \"idiomatic\" defense of \"strike "
            "upon the necks\" runs against fourteen centuries of Islamic military application — "
            "the phrase has been understood literally in <em>fiqh</em> and in actual practice, and "
            "no major classical school reduced it to mere figure. The modern \"deterrent\" reading "
            "of 8:60 is a humane gloss, but the verse literally says accumulate forces so \"you may "
            "terrify\" (<em>turhibuna</em>) — the linguistic root from which contemporary Arabic "
            "draws <em>irhab</em> (terrorism). Modern jihadist groups cite these verses accurately "
            "within classical exegetical norms. The apologetic defense requires surrendering "
            "either the classical exegesis or the modern moral framing; it usually tries to keep "
            "both."
        ),
    },
    {
        "anchor": "And you did not kill them, but it was Allah who killed them",
        "response": (
            "The classical theological reading is compatibilist: the verse affirms that ultimate "
            "metaphysical causation belongs to Allah without denying human moral agency. In the "
            "Ash'arite tradition, Allah creates the act (<em>khalq</em>) while the human "
            "\"acquires\" (<em>kasb</em>) the moral weight — resolving the surface paradox. "
            "Modern apologists frame the verse as a psychological support for traumatized "
            "warriors: it reminds believers that victory and death are ultimately in Allah's "
            "hands, not in their own strength, so they should remain humble rather than boastful. "
            "On this reading, the verse does not dissolve agency; it rightsizes human pride."
        ),
        "refutation": (
            "The Ash'arite <em>khalq</em>/<em>kasb</em> distinction is a theological scaffold "
            "invented centuries after the Quran to manage exactly this problem — and its obscurity "
            "is proverbial even within Islamic theology itself. More critically, the "
            "\"dissolved agency\" reading is not a paranoid misreading; it is how the verse has "
            "been weaponized for fourteen centuries. Jihadist ideology relies on exactly this "
            "logic: the fighter does not bear moral responsibility for his killings because Allah "
            "is the true agent. If the apologetic reading were textually obvious, this use would "
            "be impossible. The text plainly states that the killing and the throwing were done by "
            "Allah, not by humans — and no reading-in of compatibilism erases the plain sense. A "
            "divine text claiming to ground objective morality cannot also tell fighters they did "
            "not do what they did."
        ),
    },
    {
        "anchor": "If there are among you twenty [who are] steadfast, they will overcome two hundred",
        "response": (
            "The apologetic reading holds that the two verses describe two spiritual-historical "
            "phases: the 1:10 standard was for the foundational community with its extraordinary "
            "faith, while 1:2 reflects the realistic expectation once the community grew and "
            "included weaker believers. The \"revision\" is not Allah correcting Himself but "
            "Allah adapting a standing command to a changed community. The prediction is "
            "spiritual rather than empirical — about what sufficient faith can accomplish, not "
            "about battlefield arithmetic. The \"weakness\" language acknowledges moral reality, "
            "not divine miscalculation."
        ),
        "refutation": (
            "The explanation requires Allah to have set a bar calibrated to \"extraordinary faith\" "
            "without knowing whether that faith would persist — which concedes either ignorance "
            "or a retroactive redefinition. If Allah knew the weakness was coming, He did not "
            "need to lighten the requirement; He should have set it at the eventual level from "
            "the start. The linguistic formulation of verse 66 (\"now Allah has lightened…for He "
            "knows there is weakness\") is explicitly a revision — the verb <em>khaffafa</em> "
            "means \"He lightened,\" a word no theology can retrofit as timeless precaution. The "
            "\"spiritual, not empirical\" reading strips the verse of content: either the 1:2 "
            "ratio is a real claim (falsifiable by military history, which it is) or it is a "
            "metaphor about faith, in which case the explicit revision of the ratio across verses "
            "is nonsensical. The verse says what it says, and what it says does not track what "
            "subsequently happened in Muslim military history."
        ),
    },
    {
        "anchor": "indeed the polytheists are unclean (najas)",
        "response": (
            "Apologists argue <em>najas</em> here is spiritual or doctrinal uncleanness, not "
            "ritual-physical impurity — a statement about the polytheists' idolatry rather than "
            "their bodies. Modern Sunni interpretations (Shafi'i, Hanafi) treat <em>najas</em> as "
            "a metaphor for spiritual state, supported by the fact that Muslims historically did "
            "business with, ate food with, and lived among non-Muslims without contamination "
            "rituals. The restriction on entering the Sacred Mosque is a bounded sacred-geography "
            "rule, not a general segregation mandate — analogous to how non-Jews were restricted "
            "from entering certain parts of the Jerusalem Temple in antiquity."
        ),
        "refutation": (
            "The \"spiritual not physical\" reading is a contemporary apologetic frame. Classical "
            "jurists and traditionalist schools (particularly Shia Twelver jurisprudence) have "
            "historically enforced <em>najas</em> as ritual-physical impurity — non-Muslims could "
            "not prepare certain food, handle certain utensils, or in some rulings share water "
            "supplies. Saudi Arabia's continuing ban on non-Muslims entering Mecca and Medina "
            "applies this verse directly, at the level of physical geography, and is enforced at "
            "the city perimeter as a matter of state law. Classifying an entire class of human "
            "beings as ritually polluting — regardless of their personal hygiene, morality, or "
            "conduct — is classification by religion alone, which is what the verse prescribes. "
            "The bounded-geography comparison breaks down when the geography is the religion's "
            "holiest site, permanently closed to every non-Muslim on earth as a matter of divine "
            "law."
        ),
    },
    {
        "anchor": "fight those adjacent to you of the disbelievers",
        "response": (
            "The apologetic reading is defensive, not expansionist. 9:123 was revealed during a "
            "period of active military threat from surrounding tribes; it exhorts the community "
            "to fight those immediately threatening them. \"Adjacent to you\" is read as \"those "
            "in proximity with hostile intent,\" not as a territorial-conquest doctrine. Classical "
            "jurists did develop <em>Dar al-Harb</em> (the House of War), but under specific legal "
            "conditions — not as automatic warrant for invading peaceful non-Muslim societies. "
            "Modern Muslim-majority states overwhelmingly reject the Dar al-Harb / Dar al-Islam "
            "binary as incompatible with contemporary international law."
        ),
        "refutation": (
            "The \"defensive\" reading cannot extract the aggression from the verse. The command "
            "is to fight \"those adjacent to you of the disbelievers\" without any condition of "
            "their hostility — only of their disbelief and their proximity. The instruction to "
            "\"find in you harshness\" is not defensive rhetoric; it is a call to severity. "
            "Classical jurisprudence built the Dar al-Harb doctrine not by misreading this verse "
            "but by reading it alongside the broader late-Medinan military passages with which it "
            "is consonant. Modern Muslim rejection of the doctrine is real, but it is a modern "
            "rejection, not a classical one, and it relies on an implicit abrogation of verses the "
            "tradition treated as standing. Defending 9:123 as purely defensive requires reading "
            "a hostility into \"adjacent\" that the text does not supply."
        ),
    },
    {
        "anchor": "O sister [i.e., descendant] of Aaron",
        "response": (
            "Two standard defenses. (1) \"Sister\" (<em>ukht</em>) in ancient Semitic usage often "
            "meant \"descendant of\" or \"kinswoman of\" — so Mary is being identified as a "
            "descendant of Aaron's priestly line, fitting her priestly-family background. "
            "(2) \"Aaron\" (<em>Harun</em>) here is not Moses's brother but a different, righteous "
            "Aaron contemporary with Mary, whose association with her was meant as moral praise. "
            "The hadith in Sahih Muslim 2135 — where Muhammad explains to a Christian that Arabs "
            "named their children after earlier prophets — is cited as prophetic confirmation of "
            "the second reading."
        ),
        "refutation": (
            "\"Sister\" (<em>ukht</em>) is used elsewhere in the Quran for literal sisters, and "
            "ancient Semitic \"descendant\" usage is rare and context-specific — it does not "
            "naturally apply where the family is immediately named. The Quran identifies Mary's "
            "father as Imran (3:35), which is the Arabic form of Amram, the same Amram who in the "
            "Hebrew Bible is the father of the original Miriam. The conflation is complete: "
            "father Amram, sister of Aaron, name Miriam — these are the features of Moses's "
            "sister, not Jesus's mother. The \"different Aaron\" hadith is an after-the-fact "
            "explanation that addresses a specific Christian encounter but does not dissolve the "
            "systematic confusion across three separate Quranic passages. A divine author "
            "narrating Jesus's mother's life should not repeatedly attribute to her the lineage "
            "of a woman who lived 1,300 years earlier. The identification is simply wrong, and "
            "the apologetic rescues require stipulating usages and persons unattested in any "
            "independent source."
        ),
    },
    {
        "anchor": "And the pains of childbirth drove her to the trunk of a palm tree",
        "response": (
            "The classical apologetic holds that the Quran corrects and preserves genuine "
            "historical events that the canonical Gospels either omitted or lost through "
            "transmission. If the palm-tree birth and the infant-Jesus-speaking episode are "
            "preserved in apocryphal texts (Pseudo-Matthew, Arabic Infancy Gospel) that circulated "
            "widely, this could be because those texts preserved authentic traditions the "
            "canonical Gospels excluded. Alternatively, specific details of the Quranic narrative "
            "differ from the apocryphal versions in ways that suggest independent revelation "
            "rather than literary borrowing — the palm-shaking miracle and the infant's defense of "
            "his mother's honor are distinctively Quranic contributions."
        ),
        "refutation": (
            "Both the Arabic Infancy Gospel and Pseudo-Matthew are demonstrably late and "
            "legendary — the former is dated to the 5th–7th century, the latter to the late "
            "6th or 7th century — and both bear the hallmarks of legendary embellishment "
            "(cradle speech, miraculous trees, preternatural feats) that mainstream Christianity "
            "rejected precisely because they had no apostolic basis. The claim that they preserved "
            "\"authentic lost tradition\" is unverifiable and runs against the standard "
            "historical-critical methodology Muslim scholars apply freely to the New Testament "
            "they critique. The \"different details\" defense is itself diagnostic: tradents "
            "borrowing legendary material reshape it with local enhancements. What stays constant "
            "is the distinctive legendary kernel (virgin birth in isolation, infant speech from "
            "the cradle), which is exactly what Pseudo-Matthew and the Arabic Infancy Gospel "
            "share with the Quran. A divine author composing a Jesus narrative should not be "
            "drawing from the 6th-century apocryphal bookshelf of the Christian Near East."
        ),
    },
    {
        "anchor": "And [remember, O Muhammad], when you said to the one on whom Allah bestowed favor",
        "response": (
            "The mainstream apologetic reading treats the Zaynab episode as a deliberate divine "
            "intervention to abolish a specific pre-Islamic custom — the taboo against marrying "
            "the ex-wife of an adopted son. Classical commentators (Tabari, Ibn Kathir) frame "
            "Zayd's divorce and Muhammad's subsequent marriage as legal precedent needed to break "
            "the Arab convention of treating adoptive relations as blood relations. The marriage "
            "was already strained; Muhammad did not engineer it. The revelation was not a "
            "personal accommodation but a public demonstration that adopted-son status does not "
            "create the same affinity restrictions as biological sonship, freeing future Muslim "
            "men from a similar prohibition."
        ),
        "refutation": (
            "The \"abolition of a custom\" framing is a theological frame laid over a biographical "
            "account the Quran itself does not sanitize. The verse acknowledges that Muhammad "
            "\"concealed within\" himself what Allah was about to reveal — the natural reading of "
            "which is that he had desires for Zaynab he wished hidden. The earliest tafsir "
            "(Tabari) is explicit: Muhammad saw Zaynab in an unguarded moment, was captivated, "
            "and Zayd subsequently pressed for divorce. Allah's intervention comes precisely "
            "where Muhammad's desire and the social prohibition collide, and the resolution gives "
            "him what he wanted. A universal lawgiver rewriting Arab adoption-law to free all "
            "Muslims could have done so without simultaneously marrying the specific woman in "
            "question — the legal principle does not require the personal transaction. Aisha's "
            "own remark that Allah \"rushes to fulfill\" Muhammad's desires is a structural "
            "observation about the pattern, and 33:37 is among its clearest cases. No amount of "
            "legal-reform framing removes the fact that a revelation convenient to the Prophet's "
            "marriage arrived precisely when needed."
        ),
    },
    {
        "anchor": "indeed We have made lawful to you your wives to whom you have given their due",
        "response": (
            "Apologists offer two main defenses. First, the verse's exceptional permissions are "
            "grants for Muhammad's specific historical situation — the wives had special "
            "political and educational roles in the community, the captive concubines reflected "
            "war conditions, and the cousin allowances closed a specific lineage question. "
            "Second, the following verse (33:53) places substantial restrictions on Muhammad as "
            "well — his wives cannot remarry after his death, his household must veil from "
            "non-kin — suggesting the arrangement is a burden specific to his role rather than a "
            "generalized privilege. On this reading, the verse configures his specific "
            "constraints and permissions, not a sexual exemption from ordinary rules."
        ),
        "refutation": (
            "The \"burdens balance the permissions\" defense does not erase the pattern of "
            "asymmetric sexual privilege. 33:50's special permissions (unrestricted number of "
            "wives, free sexual access to captive concubines, specific cousins permitted) grant "
            "Muhammad latitude no ordinary believer has — in direct tension with the immediately "
            "preceding 4:3 limiting others to four wives. 33:52's subsequent freezing of further "
            "marriages is a timeline specification (no more wives going forward), not a moral "
            "symmetry with rank-and-file believers. The pattern Aisha identified — revelations "
            "specifically timed to accommodate the Prophet's personal situation — is structural "
            "across multiple verses, of which these are the most explicit. A divine legal system "
            "claiming universality cannot produce targeted exemptions for its messenger without "
            "conceding that the messenger's personal situation shaped the law, not the other way "
            "round."
        ),
    },
    {
        "anchor": "And He brought down those who supported them among the People of the Scripture",
        "response": (
            "The apologetic reading stresses historical context: the Banu Qurayza had allegedly "
            "allied with the besieging Quraysh during the Battle of the Trench, constituting "
            "treason against their treaty with Muhammad. The judgment was rendered by Sa'd ibn "
            "Mu'adh applying the Jewish community's own existing law (Deuteronomy 20:13–14), not "
            "by Muhammad imposing an Islamic ruling. The Quranic verse merely records a historical "
            "outcome without endorsing it as a paradigm. Revisionist historians (W.N. Arafat) have "
            "questioned whether the traditional figure (600–900 killed) is exaggerated, arguing "
            "the numbers derive from later tradents with rhetorical purposes."
        ),
        "refutation": (
            "Even granting every apologetic assumption, the Quranic verse does more than record — "
            "it credits the outcome as divine provision (\"Allah brought down,\" \"He cast "
            "terror,\" \"He caused you to inherit\"). A text that frames a mass execution as "
            "divine gift is endorsing it, regardless of the contemporary legal mechanism. The "
            "\"Sa'd applied Jewish law\" framing is questionable history — the cited Deuteronomic "
            "provisions concern besieged cities that refused peace, not surrendered internal "
            "allies — and shifts responsibility to a human judge who was a close companion "
            "personally selected by Muhammad for his known severity. The revisionist case against "
            "the numbers is speculative; the canonical sources (Ibn Ishaq, al-Tabari) agree on "
            "the core events and the scale. Even if one accepts a smaller number, the moral "
            "question is identical: a day-long execution of hundreds of surrendered prisoners by "
            "the prophet's community, theologically endorsed, is not a paradigm that improves the "
            "text's claim to universal moral authority."
        ),
    },
    {
        "anchor": "do not compel your slave girls to prostitution, if they desire chastity",
        "response": (
            "The classical response points out that the verse addresses a specific abuse — "
            "Abdullah ibn Ubayy's pimping of his slaves — and is a condemnation of that practice, "
            "not a permission. The conditional phrase (\"if they desire chastity\") is idiomatic "
            "rather than licensing; it simply acknowledges that the prohibition applies in the "
            "natural case. Modern commentators argue the phrasing reflects 7th-century Arabic "
            "grammar, where conditional clauses could function as causal explanations rather than "
            "exceptions: \"don't compel them, since their desire for chastity is being violated.\" "
            "The preceding verse (24:32) encourages marriage of slaves, pointing toward a broader "
            "Islamic trajectory away from concubinage."
        ),
        "refutation": (
            "The \"idiomatic\" reading is philologically strained. In Arabic, as in any language, "
            "a conditional phrase (<em>in aradna</em>) most naturally specifies when the command "
            "applies, and classical commentators (including Tabari, al-Qurtubi, and Ibn Kathir) "
            "recognized and discussed the disturbing implication — which is why the question "
            "appears in classical tafsir literature at all. Had the verse unambiguously prohibited "
            "forced slave prostitution in general, there would be nothing to explain away. The "
            "\"specific abuse, specific condemnation\" framing concedes the central point: the "
            "Quran did not issue a blanket prohibition on forcing slaves into sexual service; it "
            "issued a narrow conditional. The broader Islamic legal tradition systematically "
            "permitted the sexual use of female slaves whose consent was legally irrelevant to "
            "their owners. The conditional does real work — it is the difference between "
            "prohibiting an act and prohibiting only a particular form of it."
        ),
    },
    {
        "anchor": "And they ask you, [O Muhammad], about Dhul-Qarnayn",
        "response": (
            "The scholarly apologetic response is that Dhul-Qarnayn is not identical with the "
            "historical Alexander — the identification is a later exegetical guess, and the "
            "Quranic narrative differs substantially from the historical Alexander (monotheist, "
            "travels to the ends of the earth, builds a wall against Gog and Magog). Alternative "
            "identifications in classical tafsir include Cyrus the Great (known for religious "
            "tolerance and monumental construction) and several pre-Islamic Yemeni kings. On this "
            "view, the Quranic figure is a composite or distinct monotheist king whose narrative "
            "happens to share motifs with the legendary Alexander of Syriac Christian romance — a "
            "typological resemblance, not a genealogical borrowing."
        ),
        "refutation": (
            "The alternative identifications (Cyrus, Yemeni kings) have even weaker evidentiary "
            "support than the Alexander reading, and none matches the Quranic narrative as closely "
            "as the Syriac Alexander Legend of c. 629 CE — a text that circulated in the Arab-"
            "Christian orbit during Muhammad's lifetime and depicts Alexander as a devout "
            "monotheist who travels to the earth's ends and builds an iron wall against Gog and "
            "Magog. The specific narrative elements of 18:83–98 track the Syriac Legend to a "
            "remarkable degree, and no pre-Islamic Cyrus or Yemeni tradition produces this "
            "combination. The \"it's a different person\" defense is the same move as \"the "
            "Alexander Romance borrowed from Islamic material\" — but the chronology runs the "
            "other way: the Syriac Legend predates Surat al-Kahf. A divine narrator composing a "
            "history lesson should not be pulling narrative architecture from a contemporary "
            "Christian legend whose historical claims about Alexander are themselves fictional."
        ),
    },
    {
        "anchor": "O Prophet, why do you prohibit [yourself from] what Allah has made lawful",
        "response": (
            "The apologetic framing treats the episode as a moral lesson on marital honesty and "
            "loyalty to the Prophet's household. Muhammad had made a private vow to abstain from "
            "something permissible (honey, or intimacy with Mariyah, depending on the source) to "
            "placate his wives; the revelation corrects this as needless self-denial and rebukes "
            "the wives who were gossiping and applying social pressure. The lesson is not about "
            "Muhammad's sexual indulgence but about the principle that believers should not "
            "impose restrictions Allah has not imposed, and that the Prophet's household bore "
            "special responsibilities of discretion."
        ),
        "refutation": (
            "Whatever the pedagogical gloss, the historical occasion is unambiguous: Muhammad's "
            "wives were upset that he was having sexual relations with a concubine in one of "
            "their rooms, and a revelation arrived rebuking them for objecting and threatening "
            "them with divine replacement. A universal ethical lesson about \"don't forbid "
            "yourself what Allah permits\" does not need the specific setting of a concubinage "
            "dispute. The more parsimonious explanation is the one Aisha herself gives (\"I see "
            "your Lord hastens to fulfill your wishes\"): the Prophet had personal difficulties, "
            "and divine revelation arrived to resolve them in his favor. The pattern repeats "
            "across the Zaynab affair, the special marriage privileges, the rules on captives — "
            "each time a personal contest is resolved by a new verse. Either the Creator of the "
            "universe is deeply concerned with Muhammad's household arrangements, or the "
            "revelations are generated in service of them."
        ),
    },
    {
        "anchor": "And those who no longer expect menstruation among your women",
        "response": (
            "The apologetic response is twofold. First, the verse does not <em>institute</em> "
            "child marriage but provides a legal framework for handling a practice that already "
            "existed across the 7th-century Near East — the Quran contains the practice within "
            "rules of <em>'iddah</em> (waiting period) rather than actively authorizing "
            "consummation. Second, modern interpreters (Muhammad Abduh, and more contemporary "
            "scholars) argue the category \"those who have not menstruated\" could describe women "
            "with a medical condition preventing menstruation, not specifically pre-pubescent "
            "girls — a reading the classical commentators missed but the text permits. On this "
            "view, the verse is about procedural completeness, not pre-pubescent marriage."
        ),
        "refutation": (
            "The classical commentators (Tabari, Ibn Kathir, al-Qurtubi) were unanimous and "
            "explicit that \"those who have not yet menstruated\" means girls who have not "
            "reached puberty — a reading Muslim scholars native to Arabic arrived at without "
            "controversy. The modern \"medical condition\" reading is a post-Enlightenment "
            "apologetic, not tradition-grounded exegesis; it is the same pattern of reading "
            "modern sensibilities back into the text. The \"contains existing practice\" "
            "argument is not a defense but an admission: the Quran could have forbidden child "
            "marriage and did not; instead, it codified divorce procedures for it. That "
            "codification is the textual foundation on which fourteen centuries of Islamic law "
            "permitted such marriages, including in contemporary jurisdictions. The verse's "
            "eternity as divine law means the practice it legitimates has a permanent religious "
            "warrant, regardless of whether any specific society chooses to exercise it."
        ),
    },
    {
        "anchor": "And [for them are] fair women with large, [beautiful] eyes",
        "response": (
            "Apologists argue the houri passages are allegorical or at least metaphorical — "
            "describing the indescribable joys of paradise in language suited to the audience. "
            "The \"large-eyed\" maidens (<em>hur 'in</em>) are symbols of divine beauty, not "
            "literal sexual partners. Modern interpretations (notably Christoph Luxenberg's "
            "controversial reading) even propose that Arabic <em>hur</em> may originally have "
            "meant \"white grapes\" (from Syriac), reducing the eroticism to a scribal error. "
            "Mainstream scholarship rejects Luxenberg but allows non-literal readings. For female "
            "believers, paradise is equally described as supreme happiness — the Quran does not "
            "dwell on gendered rewards because both sexes receive the fundamental reward of "
            "proximity to Allah."
        ),
        "refutation": (
            "The allegorical reading cannot be sustained across the combined Quranic and hadith "
            "corpus. The hadith literature (Tirmidhi 1663, Bukhari 3327, and many others) gives "
            "extensive concrete descriptions of the houris — their bodies, their sexual "
            "receptivity, the specific number given to martyrs — that make no sense as allegory. "
            "Classical tafsir (al-Tabari, Ibn Kathir) read the passages literally, and the "
            "mainstream Sunni tradition has done so for fourteen centuries. The Luxenberg \"white "
            "grapes\" thesis is a marginal philological speculation rejected by both Muslim and "
            "non-Muslim Quranic scholarship. And the gender asymmetry is stark: the Quran and "
            "hadith describe specific sexual rewards for men and describe paradise for women "
            "largely in terms of reunion with their earthly husband — with no parallel "
            "abundance. A religion whose eternal afterlife has sex-partner inventory for one sex "
            "and not the other has embedded into the cosmos exactly the gender hierarchy of its "
            "cultural moment."
        ),
    },
    {
        "anchor": "May the hands of Abu Lahab be ruined",
        "response": (
            "The apologetic reading treats Surah 111 as a divine prophecy-curse — a prediction "
            "that Abu Lahab and his wife would die in disbelief, which turned out to be true. As "
            "such, it is not merely a personal revenge-curse but a miraculous demonstration of "
            "divine foreknowledge: had Abu Lahab publicly converted to Islam even insincerely, "
            "the surah would have been falsified and the whole revelation discredited. Classical "
            "commentators (Tabari, Ibn Kathir) frame the passage as evidence for the Quran's "
            "prophetic character, noting that Abu Lahab lived for years after the surah's "
            "revelation and had every opportunity — and every incentive to spite Muhammad — to "
            "convert, yet did not."
        ),
        "refutation": (
            "The \"prediction\" defense elevates a trivially cheap falsification test. Abu Lahab "
            "had no incentive to fake a conversion — he was a wealthy Meccan notable whose social "
            "and political standing depended on his opposition to Muhammad; public conversion "
            "would have destroyed him socially and, from his own perspective, would have validated "
            "a man he openly despised. The psychological improbability of his conversion makes "
            "the \"prophecy\" cheap to fulfill. More fundamentally, the defensive reading does "
            "not explain why the Quran — which claims to be the eternal word of Allah — includes "
            "a personal curse of a specific 7th-century individual whose significance is "
            "parochial to one man's biography. Every Muslim in Jakarta, Dakar, or Istanbul recites "
            "this surah as scripture, directing a curse at an Arabian man most have never heard of "
            "in any other context. A book addressed to all humanity for all time should not embed "
            "a revenge-oracle into a specific family feud. The classical defense converts the "
            "parochialism into a \"miracle\" only by accepting that divine eternal scripture is "
            "primarily about settling the Prophet's enemy relations."
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

#!/usr/bin/env python3
"""Batch 10: All 43 Ibn Majah Strong entries."""
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
        "anchor": "Whoever changes his religion, kill him.",
        "response": (
            "The standard apologetic narrows the hadith to public political apostasy "
            "combined with hostility to the Muslim state — not private belief change. "
            "Reformist scholars argue Quran 2:256 takes priority and the classical "
            "application reflected specific 7th-century political conditions rather than "
            "eternal rule. Several Muslim-majority states have removed apostasy from "
            "criminal law."
        ),
        "refutation": (
            "The classical consensus across all four Sunni schools and Jaʿfari Shia law "
            "treated apostasy itself as capital, without requiring additional hostility. "
            "Six canonical collections preserve the command — the \"fringe hadith\" "
            "dismissal is categorically impossible given the cross-collection "
            "attestation. Current enforcement in Saudi Arabia, Iran, Mauritania, and "
            "elsewhere applies the rule to private belief change. The tension with 2:256 "
            "is real; the classical resolution was to abrogate 2:256 — which modern "
            "apologists quietly abandon while still citing it as evidence of Islamic "
            "tolerance."
        ),
    },
    {
        "anchor": "The married adulterer: a hundred lashes and stoning to death.",
        "response": (
            "Classical apologetics frames the stacked punishment as a hadith elaboration on "
            "the Quranic lashing rule — the stoning supplement derives from the "
            "abrogated \"verse of stoning\" (<em>ayat al-rajm</em>) whose text was removed "
            "while its ruling remained (<em>naskh al-tilawa duna al-hukm</em>). The "
            "evidentiary bar (four eyewitnesses to actual penetration) makes the penalty "
            "effectively inapplicable in ordinary life. The rule is symbolic of the "
            "gravity of adultery rather than routinely applied."
        ),
        "refutation": (
            "<em>Naskh al-tilawa duna al-hukm</em> is the doctrinal rescue that concedes "
            "the substantive problem: the Quran's current text does not contain the "
            "stoning rule, meaning the most severe punishment in Islamic criminal law "
            "rests on a claimed-removed verse preserved only in hadith. That undermines "
            "the Quran's self-description as complete and preserved (15:9). The "
            "\"effectively inapplicable\" framing does not hold where it is applied — "
            "Iran, Saudi Arabia, parts of Sudan, Nigeria, and Afghanistan have continued "
            "stoning executions in recent decades. A penal code stacking flogging with "
            "stoning for consensual adult sex has a design, not merely an accident of "
            "enforcement."
        ),
    },
    {
        "anchor": "I looked into the Fire and saw that most of its inhabitants were women.",
        "response": (
            "Classical theology reads the hadith as prophetic observation of the women of "
            "his community in his specific era — correcting behaviors (ingratitude, "
            "cursing) that were addressable faults rather than essential deficiencies. "
            "The cited reasons are behavioural, not essentialist; the implication is "
            "that women who avoid these faults are equally eligible for paradise. "
            "Apologists pair the hadith with Quran 33:35's explicit spiritual equality."
        ),
        "refutation": (
            "Cross-collection preservation (Bukhari, Muslim, Tirmidhi, Ibn Majah) lifts the "
            "\"local observation\" defense above plausibility — if the demographic is "
            "local, the hadith should not appear as eternal teaching in four canonical "
            "sources. The \"addressable faults\" framing does not explain the structural "
            "claim: gender-majority damnation as prophetic report, coupled with reasons "
            "(ingratitude, cursing) whose distribution is contingent on the social roles "
            "available to women. A religion whose eschatology reports a disproportionate "
            "female hell-majority has articulated something about its view of half its "
            "adherents that spiritual-equality verses do not neutralise."
        ),
    },
    {
        "anchor": "If a woman prays her five daily prayers, fasts her month, guards her chastity",
        "response": (
            "Apologists read the hadith as including husband-obedience in the path to "
            "paradise specifically as a positive encouragement for women whose social "
            "roles at the time were heavily marital — not as essentialising female "
            "paradise on spousal relations. The general prayer/fasting/chastity/obedience "
            "formula is framed as offering <em>additional</em> ease rather than defining "
            "women's paradise-eligibility only through the husband."
        ),
        "refutation": (
            "The \"additional ease\" framing does not change what the hadith says: "
            "husband-obedience is ranked equal with the five pillars in the paradise-"
            "entry formula. No parallel rule exists for men requiring wife-obedience. "
            "The asymmetry places one quarter of the female salvation criteria on the "
            "spouse, which effectively routes women's religious standing through "
            "marital compliance. A paradise criterion that makes wife-obedience coequal "
            "with prayer is a criterion whose design the apologetic frame cannot "
            "rehabilitate."
        ),
    },
    {
        "anchor": "Wherever you find them, kill them. For in killing them there is a reward",
        "response": (
            "Classical apologetics restricts the hadith to the historical Khawarij who "
            "practiced <em>takfir</em> against other Muslims and legitimised killing "
            "them — a specific armed movement, not a template for ongoing intra-Muslim "
            "violence. The command is framed as lawful response to an armed rebellion "
            "that had formally declared war on the Muslim community, not a standing "
            "license for sectarian killing."
        ),
        "refutation": (
            "The \"specific armed movement\" framing cannot remove the hadith's "
            "template-setting function: it established that a Muslim faction can be "
            "pre-damned as eschatologically illegitimate and killed with divine reward. "
            "That template has been deployed against every reform and dissent movement "
            "in subsequent Islamic history (Mutazilites, Ismailis, Ahmadis, and in "
            "contemporary Sunni-Shia polemic on both sides). A prophetic precedent of "
            "authorised intra-Muslim killing is what makes mutual <em>takfir</em> "
            "structurally available — the structure outlasts any original target."
        ),
    },
    {
        "anchor": "When Allah decrees a matter in heaven, the angels beat their wings",
        "response": (
            "Classical theology affirms the hadith's cosmological picture as describing "
            "realities beyond ordinary observation — angels communicate decrees, jinn "
            "attempt to eavesdrop, and shooting stars are physical manifestations of the "
            "cosmic barrier system. The mythology is real in the Islamic metaphysical "
            "framework; the folk cosmology is corrected rather than fabricated."
        ),
        "refutation": (
            "Shooting stars are cosmic debris entering Earth's atmosphere — their "
            "physics is well understood and does not involve demon-projection. A "
            "cosmology that preserves meteors as anti-jinn artillery has retained the "
            "pre-Islamic folk astronomy of the region while relabeling the actors. The "
            "soothsayer mechanism (genuine intel from jinn eavesdropping, embroidered "
            "by the seer) is indistinguishable from the pre-Islamic conception of "
            "oracular knowledge, and the \"correction\" Islam claims to make is "
            "cosmetic — the same framework with different names attached to the same "
            "roles."
        ),
    },
    {
        "anchor": "A man said: 'I have a slave girl. Should I do azl with her?'",
        "response": (
            "Classical apologetics argues the hadith's focus on contraception is evidence "
            "of Islamic regulation of an existing 7th-century practice, not a moral "
            "endorsement of concubinage. The tradition registered concubinage as it "
            "existed and progressively tightened its conditions — permitting marriage "
            "to slaves (<em>kitaba</em>), forbidding sex without ownership, encouraging "
            "manumission. Modern abolition is the trajectory's eventual destination, "
            "left incomplete by historical circumstance."
        ),
        "refutation": (
            "The \"gradual trajectory to abolition\" framing is a 20th-century apologetic "
            "invention without support in fourteen centuries of classical Islamic "
            "jurisprudence, which treated concubinage as permanent permission. The "
            "hadith answers a question whose premise (sex with slave girls is "
            "permitted) was accepted without objection; the only regulated matter was "
            "technique. ISIS cited such hadiths with explicit classical-legal footnoting "
            "when enslaving Yazidi women in 2014. A religion that regulates the "
            "technique of sex with captives has ratified the transaction and moved on."
        ),
    },
    {
        "anchor": "When any of you wakes from sleep, let him perform Istinthar three times",
        "response": (
            "Classical apologetics treats the \"Satan spends the night in your nose\" "
            "line as symbolic rather than physical: the morning nasal cleansing is "
            "hygienic (removing accumulated mucus), and the Satan-reference frames the "
            "cleansing as spiritually meaningful. The hadith is practical hygiene "
            "advice given in the theological vocabulary of the 7th century, not a "
            "claim about Satan's anatomical location."
        ),
        "refutation": (
            "The \"symbolic\" reading cannot absorb classical tafsir and hadith "
            "commentary (al-Nawawi, Ibn Hajar) which treated the Satan-in-nose "
            "localisation literally. Cross-collection preservation (Bukhari, Muslim, "
            "Ibn Majah) at <em>sahih</em> grade establishes the claim as authoritative "
            "teaching, not folk aside. The hygiene-advice framing is retrofitted — if "
            "the hadith were simply hygiene, it would not need demonology. A "
            "revelation that locates Satan's overnight residence in the sleeper's "
            "nose and prescribes water to displace him has communicated folk "
            "demonology under a hygiene banner."
        ),
    },
    {
        "anchor": "Have I not seen anyone more deficient in reason and religion than you",
        "response": (
            "Modern apologists argue the hadith's \"deficient in intellect\" phrase "
            "addresses the specific observation that women's legal testimony is half a "
            "man's in financial matters — a narrow contextual observation rather than "
            "a general claim about cognition. The \"deficient in religion\" refers to "
            "menstruation-exemption from prayer, a physical circumstance not a spiritual "
            "fault. Both framings are contextual rather than essentialist."
        ),
        "refutation": (
            "\"Deficient in intellect\" in direct prophetic speech, with explanation that "
            "the deficiency justifies halving testimony, is a claim about cognition — "
            "not a narrow commercial observation. Modern apologetic narrowing does not "
            "match what classical jurisprudence extracted from the hadith, which "
            "applied the 2:1 ratio broadly. The \"deficient in religion\" framing is "
            "worse, not better: a biological function (menstruation) is classified as "
            "religious deficiency, which is not a contingent social observation but a "
            "theological ranking. A prophetic statement explicitly calling women "
            "deficient on both counts is not saved by rebranding each count as "
            "contextual."
        ),
    },
    {
        "anchor": "That is a man in whose ear Satan has urinated.",
        "response": (
            "Classical apologetics treats the Satan-urination language as idiomatic "
            "rebuke for oversleeping and missing dawn prayer — a colourful 7th-century "
            "expression for the spiritual heaviness that prevented wakefulness, not a "
            "literal anatomical claim about supernatural excretion. Modern apologists "
            "emphasise that the hadith's point is the importance of prayer-punctuality, "
            "framed in memorable rhetorical imagery."
        ),
        "refutation": (
            "Cross-collection preservation (Bukhari, Abu Dawud, Ibn Majah) at "
            "<em>sahih</em> grade precludes the \"folk idiom\" defense. The classical "
            "commentators (Ibn Hajar, al-Nawawi) discussed whether Satan's urine is "
            "actually physical or symbolic, which tells us the plain reading was "
            "physical enough to require substantive theological debate. A tradition "
            "in which Satan has a urinary tract and targets the ears of the negligent "
            "has preserved folk demonology at the authoritative level — the "
            "\"idiomatic rhetoric\" framing is a modern comfort, not the classical "
            "reading."
        ),
    },
    {
        "anchor": "Jesus son of Mary will descend, kill the pig, break the cross, and abolish",
        "response": (
            "Classical eschatology treats the hadith as describing Jesus's final role as "
            "a Muslim prophet completing his earthly mission, which apologists argue "
            "Christians distorted. \"Abolishing jizya\" follows from the universal "
            "acceptance of Islam in Jesus's eschatological era — no <em>dhimmi</em> "
            "arrangement is needed when all have converted. The pig-killing and "
            "cross-breaking are symbolic corrections of Christian deviations from "
            "what the Quran presents as Jesus's original monotheism."
        ),
        "refutation": (
            "\"Abolishing jizya\" means the converted-or-fight binary — non-Muslims "
            "cannot opt out. The return of the Christian messiah as an anti-Christian "
            "warrior destroying his followers' symbols is pointed theological "
            "reversal, not reconciliation. Cross-collection preservation across three "
            "major Sunni canons (Tirmidhi, Ibn Majah, Bukhari parallels) establishes "
            "the doctrine as core eschatological teaching. A religion whose "
            "eschatological vision culminates in the forced elimination of "
            "alternative religious options is a religion whose \"global Jesus\" ends "
            "other faiths by design."
        ),
    },
    {
        "anchor": "The Mahdi is from my family, from the descendants of Fatima.",
        "response": (
            "Classical theology presents the Mahdi as a specific eschatological figure "
            "whose arrival is foretold in the hadith canon, with detailed descriptions "
            "that allow eventual identification. Sectarian differences (Twelver Shia "
            "expect the Twelfth Imam; Sunnis expect an unidentified future figure) "
            "reflect different readings of the same tradition rather than doctrinal "
            "incoherence. The tradition does not require identification of the Mahdi "
            "in advance; believers will recognise him when he arrives."
        ),
        "refutation": (
            "\"Eventually recognisable\" is unfalsifiable. 1,400 years of false "
            "claimants — from al-Mu'tasim's era through the Sudanese Mahdi, the "
            "Ahmadiyya founder, and contemporary claimants — demonstrates that the "
            "identification criteria are porous enough to admit numerous candidates "
            "without adjudication. The Sunni-Shia division over Mahdi identity is not "
            "a minor variation but a substantive doctrinal split that has produced "
            "1,400 years of sectarian division. A religion's eschatological "
            "centerpiece should not be structurally ambiguous enough to generate "
            "competing eternal messiahs without the text itself resolving which is "
            "genuine."
        ),
    },
    {
        "anchor": "There are three whose prayer does not pass beyond their ears",
        "response": (
            "Classical apologetics frames the hadith as addressing specific relational "
            "dysfunctions: a wife whose husband is displeased and a runaway slave "
            "have each disrupted the social order they are embedded in, and "
            "reconciliation with that order is a prerequisite for spiritual access. "
            "The rule is not about women and slaves as categories but about the "
            "spiritual consequences of unresolved relational breach."
        ),
        "refutation": (
            "Pairing the wife and the runaway slave in the same theological category "
            "— neither can have prayer accepted until they restore submission — is "
            "diagnostic. The rule presupposes the rightness of the wife's subordination "
            "to the husband's mood and the slave's subordination to the master's "
            "ownership. There is no parallel rule rejecting the husband's prayer when "
            "his wife is angry, or the master's prayer when the slave objects. The "
            "asymmetry defines what \"breach\" means: deviation from hierarchical "
            "subordination, not mutual relational failure."
        ),
    },
    {
        "anchor": "Whoever drinks khamr, flog him... If he repeats it the fourth time, kill him.",
        "response": (
            "Classical apologetics argues the fourth-offense death penalty was "
            "superseded by consensus: although the text preserves it, practical "
            "jurisprudence operated without capital punishment for repeat drinking, "
            "with Muhammad's own flogging-only precedent (not executions) governing "
            "the actual sentence. The hadith's preservation reflects the tradition's "
            "honesty about its received material, not current practice."
        ),
        "refutation": (
            "\"Superseded by consensus\" is itself an admission that the hadith's plain "
            "content required silent abandonment. A divine legal code whose explicit "
            "capital punishment was informally dropped through scholarly drift — "
            "without the text ever being amended — is a code whose rulings are "
            "effectively at the discretion of subsequent jurists. If the fourth-"
            "offense execution can be suspended by consensus, other <em>hudud</em> "
            "could theoretically be as well. The preservation of the discarded "
            "sentence on the books means it remains legally available to anyone who "
            "wishes to revive it, which is what defines its status — eternal law by "
            "<em>formal</em> retention."
        ),
    },
    {
        "anchor": "If a woman goes out of her house without her husband's permission",
        "response": (
            "Apologists read the hadith within the 7th-century context of "
            "household-management economics: the husband was responsible for "
            "provision and protection, so his knowledge of household members' "
            "movements was a matter of household security rather than a patriarchal "
            "control mechanism. Modern apologetic readings frame \"permission\" as "
            "mutual notification in a collaborative household, not unilateral "
            "authority."
        ),
        "refutation": (
            "The modern \"mutual notification\" framing is not what the hadith says. "
            "The text locates the angelic curse on the woman crossing her own "
            "threshold without her husband's permission — a unilateral permission "
            "structure with theological enforcement. Classical jurisprudence across "
            "Sunni schools treated the rule as substantively restricting women's "
            "movement, and contemporary conservative Muslim discourse continues to "
            "cite it. A religion whose heavens curse a woman for crossing her own "
            "threshold has built a household architecture in which female "
            "autonomy is a theological offense."
        ),
    },
    {
        "anchor": "The Prophet married me when I was six years old, and he consummated the marriage",
        "response": (
            "The standard apologetic responses (physical maturity, cultural norms, "
            "revisionist redating) are covered under earlier collections. For Ibn "
            "Majah's preservation specifically, apologists cite the collection's "
            "independent chain of transmission as confirmation rather than "
            "multiplication — the age report appears in four canonical sources "
            "because it is well-attested, not because it is legendary accretion."
        ),
        "refutation": (
            "Cross-collection confirmation is precisely the problem for revisionist "
            "redating: \"Aisha was older\" apologetics requires rejecting four "
            "canonical sources at once. The hadith-science framework Islamic "
            "scholarship uses elsewhere treats cross-collection attestation as a "
            "reliability indicator — apologists cannot selectively abandon it for "
            "this case. Classical fiqh built the permission of child-marriage on "
            "precisely this precedent, and modern jurisdictions permitting very "
            "young marriage cite it directly. A fact preserved at the foundation of "
            "Sunni law cannot be selectively deleted when it becomes embarrassing."
        ),
    },
    {
        "anchor": "The Messenger of Allah cursed men who imitate women and women who imitate men.",
        "response": (
            "Classical apologetics narrows the curse to deliberate cross-gender "
            "presentation for inappropriate purposes — social access to opposite-sex "
            "spaces, deception — not innate gender variation. The <em>mukhannathun</em> "
            "category addressed specific 7th-century social roles in which effeminate "
            "men occupied intermediary positions, with the curse targeting the "
            "performance, not the person."
        ),
        "refutation": (
            "The \"deliberate performance only\" reading does not match the hadith's "
            "scope: \"men who imitate women and women who imitate men\" is a "
            "categorical curse on cross-gender presentation as such. Classical "
            "jurisprudence extended it to gender-nonconforming persons generally, "
            "and contemporary anti-LGBTQ enforcement in multiple Muslim-majority "
            "states cites it. A religion whose prophet cursed an entire class of "
            "humans for how they move through the world has aimed its disapproval "
            "at the shape of personality — the \"only the deliberate\" narrowing "
            "cannot be extracted from the text."
        ),
    },
    {
        "anchor": "The prophetic-medicine tradition in Ibn Majah includes reports of instant healin",
        "response": (
            "Classical apologetics preserves prophetic medicine (<em>tibb nabawi</em>) "
            "as a genuine therapeutic tradition — both natural remedies and "
            "spiritually-mediated healing (spit, recitation, blessing). The instant-"
            "healing reports are authenticated through chains of transmission and "
            "represent demonstrations of prophetic authority, not retroactive "
            "legend. Quran 17:59's denial of miracles applies to the "
            "<em>taunt-based</em> demands for specific signs, not to spontaneous "
            "miracles that occurred in the Prophet's life."
        ),
        "refutation": (
            "17:59 does not support the distinction apologists want: the verse says "
            "signs were not sent <em>because people denied them</em>, implying "
            "Muhammad was not sent with miracle-performing credentials in the mode of "
            "earlier prophets. The hadith's instant-healings (spit curing broken "
            "legs, etc.) are indistinguishable in structure from earlier prophetic "
            "miracle-genres (Jesus's healings, Elisha's works) — exactly what "
            "hagiographic development predicts over time. A Quran that denies "
            "Muhammad miracles and a hadith corpus that accumulates them after his "
            "death is the pattern of community-generated supplementation, not "
            "independent corroboration."
        ),
    },
    {
        "anchor": "Whoever changes his religion, then kill him.",
        "response": (
            "See the standard apologetic above: narrow to political apostasy combined "
            "with hostility, prioritise Quran 2:256, treat classical application as "
            "contextual. For Ibn Majah specifically, apologists cite the "
            "collection's chain verification as part of a <em>corpus-level</em> "
            "attestation that confirms the command's authenticity without requiring "
            "agreement on application scope."
        ),
        "refutation": (
            "Cross-collection attestation at four of six canonical sources is what "
            "makes the command structural in Islamic law — exactly why the "
            "narrowing has failed to take hold in practice. Current enforcement in "
            "Saudi Arabia, Iran, and elsewhere applies the rule to private belief "
            "change. When the same command appears in four canonical collections, "
            "\"fringe hadith\" is not available as a dismissal. The \"no "
            "compulsion\" Quran verse cannot coexist operationally with death "
            "for leaving — one or the other is governing, and the tradition's "
            "answer for fourteen centuries has been the death penalty."
        ),
    },
    {
        "anchor": "Two angels come to the deceased and say: 'Who is your Lord, what is your religion",
        "response": (
            "Classical theology accepts Munkar and Nakir's post-death questioning as "
            "genuine eschatological reality. The questions test not mere memorisation "
            "but the internalised faith of the deceased — a person of genuine faith "
            "answers naturally, while a person of pretended or confused faith fails. "
            "The iron-rod consequence is symbolic of spiritual consequence, not "
            "physical torture, in the theologically sophisticated readings."
        ),
        "refutation": (
            "The \"symbolic not physical\" reading does not match classical "
            "theology, which debated the specifics of grave-torture extensively as "
            "physical-spiritual reality. The examination structure tests faith "
            "formulas — the righteous pagan who led a moral life but did not profess "
            "the Islamic creed fails; the memorised Muslim who knows the formulas "
            "passes. That is salvation by trivia, not by moral life. An "
            "eschatological screening process that evaluates creedal "
            "recall rather than ethical substance has told us what the religion "
            "prioritises in the sorting of human lives."
        ),
    },
    {
        "anchor": "A man came to the Prophet and said: 'Be just, O Muhammad!'",
        "response": (
            "Classical apologetics reads the episode as prophetic foresight: Muhammad "
            "identified Dhul Khuwaisira's future sectarian deviation and pre-emptively "
            "warned the community about the Khawarij lineage that would emerge from "
            "such rhetoric. The response is evidence of prophetic insight, not "
            "silencing of dissent — Dhul Khuwaisira's challenge was not a "
            "principled accountability-ask but the first symptom of a disease that "
            "would produce extremist violence."
        ),
        "refutation": (
            "\"Prophetic foresight\" is the retroactive framing that converts a "
            "defensive response to criticism into a sagacious warning. The text "
            "shows a man asking for justice and the Prophet responding with a "
            "generational curse and a request (denied) to kill the speaker. A "
            "religion whose founder cursed the unborn descendants of a man who "
            "asked for accountability has pre-damned the category of critics — "
            "and the \"Khawarij\" label has subsequently been applied to every "
            "dissent movement. Self-fulfilling prophecies emerge when the "
            "prophecy's content is \"anyone who challenges the established power "
            "is the cursed future sect.\""
        ),
    },
    {
        "anchor": "The first thing Allah created was the Pen, and He said to it: 'Write.'",
        "response": (
            "Classical theology treats the Pen-creation as symbolic — the Pen "
            "represents the instrument of divine decree, which writes the "
            "measurements of all things in the Preserved Tablet. Scribal imagery is "
            "metaphorical for divine ordaining, not literal stationery. The "
            "parallels to Egyptian Thoth and Mesopotamian scribal gods reflect a "
            "universal human perception of divine ordering that Islam preserves in "
            "pure form."
        ),
        "refutation": (
            "\"Universal human perception preserved in pure form\" grants theological "
            "legitimacy to Egyptian, Mesopotamian, and other ancient religious "
            "imagination as sources of real cosmic knowledge — at which point "
            "Islam's distinctiveness dissolves into continuity with the "
            "pre-existing Near Eastern religious imaginary. The more honest "
            "account is simpler: scribal-creation motifs are widespread because "
            "ancient scribal cultures imagined cosmology in the terms of their own "
            "profession. Islam inherited one such framing. A creation that begins "
            "with stationery has told us what kind of mind authored the account — "
            "the mind of a scribe."
        ),
    },
    {
        "anchor": "In the time of the Messenger of Allah, three divorces pronounced at once",
        "response": (
            "Classical apologetics treats Umar's edict as legitimate <em>ijtihad</em> "
            "(independent legal reasoning) applied to changing social circumstances "
            "— people were treating triple-pronouncement as a convenient shortcut, "
            "and Umar's ruling restored the weight of divorce. The change was "
            "caliphal application within the framework of prophetic principle, not "
            "an amendment of divine rule. Modern reforms (India's 2019 ban, "
            "Egypt's 1929 and 1985 reforms) are seen as continuing the "
            "protective impulse Umar introduced."
        ),
        "refutation": (
            "<em>Ijtihad</em> adjusts unresolved cases; it cannot amend explicit "
            "prophetic practice. In Muhammad's lifetime, three divorces pronounced "
            "at once counted as one — Umar's edict changed that to three, "
            "overriding the prophetic rule. If caliphal discretion can alter divine "
            "marriage law, the \"divine\" status of the law is at the jurist's "
            "discretion. The fact that instant triple talaq subsequently destroyed "
            "millions of marriages in Muslim societies, requiring state "
            "intervention to reform, is not a vindication of Umar's edict — it is "
            "evidence that the caliph's modification introduced a structural harm "
            "the prophetic rule had not imposed."
        ),
    },
    {
        "anchor": "The martyr has six things with Allah: forgiveness from the first drop",
        "response": (
            "Apologists note the six-favours list has multiple layers — forgiveness, "
            "vision of paradise, security, the crown, marriage to houris, and "
            "intercession for seventy family members. The houris are mentioned in a "
            "theological framework of spiritual reward, with the specific number "
            "(72) being one hadith's framing, not the only one. Modern apologists "
            "argue the promises are metaphorical sayings designed to console martyrs' "
            "families and encourage righteousness, not mechanical transaction."
        ),
        "refutation": (
            "The 72-virgin promise is <em>sahih</em> in Ibn Majah, not apocryphal or "
            "marginal. Cross-collection attestation places the specific number "
            "within the canonical framework, not outside it. Modern extremist "
            "recruitment materials cite the number verbatim and accurately — the "
            "\"metaphorical saying\" defense is apologetic retrofit, not classical "
            "reading. A religion whose canonical martyrdom-reward economy includes "
            "specific sexual inventory has designed an incentive structure for "
            "violence in exactly the way the evidence shows it has functioned."
        ),
    },
    {
        "anchor": "A morning spent in the cause of Allah is better than the world and all",
        "response": (
            "Classical apologetics frames the hadith as encouragement for defensive "
            "warfare and self-sacrifice in the cause of the community's protection "
            "— not aggressive expansion. The \"cause of Allah\" (<em>fi sabil "
            "Allah</em>) covers a broad range of pious undertakings, including "
            "scholarship, charity, and personal struggle, not exclusively combat. "
            "Modern reformist readings emphasise the non-military "
            "interpretations available in classical sources."
        ),
        "refutation": (
            "The broad-reading apologetic is available but has not been the "
            "operative interpretation. Classical fiqh treated <em>fi sabil Allah</em> "
            "in this specific context as military activity, and the hadith has "
            "been cited in every major recruitment tradition from medieval jihad "
            "letters to modern extremist pamphlets. A calculus that rates one "
            "morning of combat above all creation has given recruitment rhetoric a "
            "scriptural warrant no amount of modern reinterpretation removes. The "
            "broad-reading move rescues contemporary apologetics at the cost of "
            "abandoning the tradition's own consistent application."
        ),
    },
    {
        "anchor": "The Prophet forbade selling pregnant she-slaves",
        "response": (
            "Classical apologetics notes that the pregnant-slave ruling was part of "
            "Islam's progressive tightening of slavery: the <em>umm walad</em> "
            "doctrine protected slaves impregnated by their owners from sale and "
            "obligated eventual manumission. Umar and Ali's debate represents "
            "legitimate juristic disagreement about specific exception cases, not "
            "disagreement about whether slavery itself was permissible — which "
            "everyone in the 7th-century framework accepted."
        ),
        "refutation": (
            "The <em>umm walad</em> doctrine is a real protection but it is "
            "structurally internal to the institution: it protects slaves who "
            "become pregnant by their owners from resale, while leaving the "
            "underlying ownership and sexual-access structure intact. Umar and "
            "Ali's debate preserves slave-trading as a core religious discussion "
            "with canonical weight. The modern \"progressive trajectory\" framing "
            "requires reading into Islam a gradualism the fourteen-century "
            "jurisprudence did not deliver: the tradition regulated concubinage "
            "and slave-trading extensively without ever abolishing either."
        ),
    },
    {
        "anchor": "The thief's hand is to be cut off for theft of a quarter-dinar and upwards.",
        "response": (
            "The standard apologetic is covered in the Quran 5:38 and Abu Dawud "
            "parallels: the classical jurisprudence added procedural restrictions "
            "(<em>nisab</em>, <em>hirz</em>, Umar's famine suspension), the "
            "deterrent effect was primary, and literal amputation was "
            "extraordinarily rare in practice. For Ibn Majah's repetition "
            "specifically, apologists cite the cross-collection consistency as "
            "authentication of a hadith that was moderated in application, not in "
            "text."
        ),
        "refutation": (
            "Cross-collection consistency without modification of the text is "
            "precisely the problem — the punishment remains canonical, and "
            "Saudi Arabia, Iran, northern Nigerian states, and parts of Sudan have "
            "continued judicial amputations into the modern era. \"Rare in "
            "practice\" is not a defense of the rule; it is an observation about "
            "its enforcement frequency. A penalty that calibrates lifetime "
            "disability to the price of a small coin — with class-blind "
            "application — has an ethical profile that procedural scaffolding "
            "cannot absorb."
        ),
    },
    {
        "anchor": "I used to play with dolls in the presence of the Prophet. I had a horse",
        "response": (
            "See the standard apologetic for Aisha's dolls under Abu Dawud: the "
            "doll-playing is framed as evidence of Muhammad's affectionate "
            "household management and his flexible application of the "
            "picture-making prohibition. For Ibn Majah's preservation, apologists "
            "add that the hadith documents the tradition's honesty — it did not "
            "sanitise the incongruity between a wife old enough for consummation "
            "and young enough for toys."
        ),
        "refutation": (
            "The preservation is the problem, not the solution. A household where "
            "a wife is the age of her dolls has a moral profile the canonical "
            "record has documented in detail across multiple collections. "
            "Apologetic moves either accept the consummation age and reject the "
            "doll-playing, or accept the doll-playing and reject the consummation "
            "age — the tradition preserves both, and any consistent apologetic "
            "reading must choose one. The tradition's choice to preserve both "
            "without editorial conflict is exactly what reveals the ethics: "
            "pediatric sexuality was not a problem the community saw."
        ),
    },
    {
        "anchor": "The father is more entitled than the virgin in deciding her marriage",
        "response": (
            "Classical jurisprudence developed the <em>wilaya al-ijbar</em> "
            "(guardianship of compulsion) as a limited paternal authority applied "
            "specifically to prepubescent girls, with consummation required to be "
            "deferred until physical maturity. Modern apologists argue the rule "
            "has been increasingly narrowed in contemporary Islamic jurisprudence, "
            "with many Muslim-majority states requiring minimum marriage ages and "
            "effective consent regardless of prior paternal authority."
        ),
        "refutation": (
            "The <em>wilaya al-ijbar</em> doctrine is a real piece of classical "
            "law, not a modern misreading. Its operational logic — the father's "
            "marriage-decision authority, girl's silence interpreted as consent — "
            "has underwritten child marriage across Islamic history, and "
            "contemporary jurisdictions permitting very young marriage (parts of "
            "Yemen, rural Nigeria, Afghanistan) cite it. Modern narrowing is a "
            "welcome reform but is not textual in origin; it is pressure against "
            "the classical framework. A legal system that takes silence as "
            "agreement has defined consent as the absence of rebellion — which is "
            "the definition of coercion."
        ),
    },
    {
        "anchor": "I can still feel the pain caused by the food I ate at Khaybar.",
        "response": (
            "Classical apologetics holds that the poisoning affected Muhammad's "
            "body but not his prophetic function — Allah's protection (Quran 5:67) "
            "is preserved because the poison did not kill him immediately or "
            "corrupt revelation, and his eventual death years later illustrates "
            "his humanity rather than divine abandonment. The decades-long effect "
            "is read as a miraculous slow-acting ordeal that confirmed prophetic "
            "status through suffering."
        ),
        "refutation": (
            "5:67 says Allah will \"protect you from the people,\" without the "
            "\"partial protection\" qualification apologists add. A prophet "
            "reportedly poisoned by a woman from Khaybar and affected for years "
            "is not \"protected\"; he is harmed in the specific way the verse "
            "promises protection against. The three-year delayed death is also "
            "medically implausible for most known poisons — which pushes the "
            "explanation toward either miraculous slow-poisoning (which concedes "
            "the point that Allah did not prevent the harm) or folkloric "
            "attribution (which undermines the hadith's reliability). Either way "
            "the protection promise fails."
        ),
    },
    {
        "anchor": "There is no marriage except with a guardian (wali).",
        "response": (
            "Classical jurisprudence establishes the guardian requirement to protect "
            "women from coercion, exploitation, or disadvantageous matches in a "
            "7th-century social context where women's independent legal capacity was "
            "limited. The guardian acts as advocate, not authority — his role is "
            "representation of the woman's best interest. The Hanafi school, in "
            "fact, permitted adult women to contract their own marriages without a "
            "guardian, demonstrating internal juristic flexibility."
        ),
        "refutation": (
            "The \"protection\" framing does not match the operational structure: the "
            "guardian has the legal authority to <em>contract</em> the marriage, "
            "not merely to advise. In most schools, a woman's marriage without her "
            "guardian is void — the exit option is not her refusal but his "
            "non-participation. The Hanafi counter-example is real but is the "
            "minority position; the mainstream rule has been enforced across "
            "Islamic history. A legal system that requires a male signature for "
            "a woman's marriage has declared that the woman alone is not legally "
            "sufficient to marry — which is a claim about female legal "
            "personhood, not about protection."
        ),
    },
    {
        "anchor": "Umm Ruman came to me — I was on a swing with my girlfriends.",
        "response": (
            "The Abu Dawud parallel's apologetic applies here as well: the "
            "narrative is Aisha's own first-person account, which apologists cite "
            "as evidence that her marriage was not traumatic (otherwise she "
            "would not narrate it in such domestic detail). The swing-to-bride "
            "transition represents cultural-normal progression into adult roles in "
            "a society where such transitions occurred at earlier ages than "
            "modern Western norms."
        ),
        "refutation": (
            "The first-person preservation is the epistemically strong evidence for "
            "the historicity of the event — and its content makes apologetic "
            "rescues impossible. Aisha remembers the swing, the preparation, the "
            "handover. There is no adult recognition in her memory of what was "
            "happening; she narrates it as a child would remember an interruption "
            "of play. The cultural-normal framing concedes that the ethics are "
            "historical rather than eternal. A \"marriage\" whose vivid memory is "
            "the loss of a swing has preserved, in the bride's own voice, the "
            "developmental disjunction apologetics cannot paper over."
        ),
    },
    {
        "anchor": "If a husband calls his wife to his bed and she refuses, and he spends",
        "response": (
            "Classical apologetics reads the hadith as addressing marital disharmony "
            "— the angelic curse applies when the refusal is <em>unjust</em>, not "
            "when the wife has legitimate reasons (illness, menstruation, pain). "
            "The text's \"refuses without excuse\" qualification (in some "
            "transmissions) frames the ethic as condemning arbitrary rejection "
            "rather than all refusal. Modern apologists emphasise that the hadith "
            "is situated within a broader framework requiring kindness and "
            "consideration in marital relations."
        ),
        "refutation": (
            "The \"legitimate reasons\" exception is juristically elaborated, but "
            "the hadith's plain text does not include it — the curse falls on the "
            "wife whose refusal angers the husband, with the standard for "
            "legitimacy being the husband's mood. Classical jurisprudence "
            "extracted from this and parallel hadiths the doctrine of <em>tamkeen</em> "
            "(sexual access as the husband's right, enforceable by withholding "
            "maintenance), which in several classical formulations effectively "
            "removes wife's consent from the marriage relation. A heavens whose "
            "angels curse a wife for saying no is a heavens in which marital "
            "coercion has already been sanctified."
        ),
    },
    {
        "anchor": "The Prophet exiled Hit, the mukhannath, to a place called Naqi'a.",
        "response": (
            "Classical apologetics contextualises the Hit exile as response to a "
            "specific privacy violation — he had described a woman's anatomy to a "
            "potential male client in ways that violated mixed-gender norms. The "
            "exile was a public-safety decision, not a general persecution of "
            "gender-nonconformity. Modern apologists emphasise the narrow scope "
            "of the incident and argue classical jurists over-generalised it into "
            "broader exile precedents."
        ),
        "refutation": (
            "The specific incident may have had a specific trigger, but the hadith "
            "functioned as prophetic precedent for 1,400 years of exclusionary "
            "jurisprudence against gender-nonconforming persons. Classical jurists "
            "did not \"over-generalise\" an innocent episode; they applied the "
            "prophetic exile as template in cases where no privacy violation was "
            "involved. Contemporary state-level enforcement against "
            "gender-nonconforming people in multiple Muslim-majority jurisdictions "
            "cites Hit's exile as warrant. A religion whose founder's precedent is "
            "used to exile a category of people for their mannerisms has supplied "
            "jurisprudential grounds for exclusion regardless of the incident's "
            "original specifics."
        ),
    },
    {
        "anchor": "May Allah curse the Jews and Christians, for they took the graves of their proph",
        "response": (
            "Classical apologetics frames the deathbed utterance as critique of a "
            "<em>practice</em> (grave-veneration) rather than a curse on the "
            "communities themselves. Salafi reformist traditions specifically cite "
            "this hadith against Muslim shrine-veneration, applying the warning "
            "to Muslims who imitate the practice. The deathbed weight emphasises "
            "the importance of avoiding the practice, not the damnation of the "
            "communities as such."
        ),
        "refutation": (
            "The distinction between \"cursing a practice\" and \"cursing communities\" "
            "does not hold in the hadith's language — \"may Allah curse the Jews and "
            "Christians\" is collective, not behavioural. Classical commentators "
            "(Ibn Taymiyyah, al-Nawawi) treated the deathbed utterance with the "
            "weight of final testament, substantively applied to the communities "
            "for their practice. The apologetic selectivity is telling: the "
            "\"curse\" is applied outward (to Jews and Christians) but not inward "
            "(to Muslim practice at Muhammad's tomb, which is identical in "
            "structure). A founder who spent his last breath cursing two other "
            "religions has defined his legacy by the rivals he outlived."
        ),
    },
    {
        "anchor": "An apostate is given three days. If he repents, he is left",
        "response": (
            "Classical apologetics frames the three-day grace period as evidence of "
            "Islamic legal mercy — the death penalty is not imposed immediately, "
            "but only after sincere opportunity for repentance has been extended. "
            "The rule places the decision in the apostate's hands during the "
            "grace period; execution is the outcome only of sustained, public "
            "rejection. Modern reformist scholars argue the rule should be read "
            "alongside Quran 2:256's principle against compulsion."
        ),
        "refutation": (
            "The three-day mercy is procedural delay before the killing — it is "
            "not mercy in the moral sense of abstaining from the killing. A "
            "legal system that offers three days to reconsider before executing "
            "you for your beliefs has communicated exactly what it thinks the "
            "appropriate response to belief change is. Modern jurisdictions (Iran, "
            "Saudi Arabia, Mauritania) continue to apply this framework. The "
            "\"no compulsion\" reading requires treating the apostasy rules as "
            "non-binding, which classical jurisprudence did not."
        ),
    },
    {
        "anchor": "A blind man had an umm walad who used to insult the Prophet.",
        "response": (
            "Classical apologetics contextualises the Prophet's response (no "
            "retribution against the blind man) within specific legal reasoning: "
            "the woman had committed the serious offense of persistent blasphemy "
            "after repeated warnings, which classical jurisprudence treated as a "
            "capital matter. The blind man's action was extrajudicial but the "
            "underlying offense warranted death through proper channels; the "
            "Prophet's refusal to punish him reflects recognition that the "
            "outcome was just even if the means were irregular."
        ),
        "refutation": (
            "\"Just outcome even if irregular means\" is the framework that has "
            "grounded fourteen centuries of private-vigilante blasphemy violence "
            "in Muslim-majority societies. The hadith established that a Muslim "
            "who kills a blasphemer faces no legal consequence — which is the "
            "operational engine of contemporary Pakistan's blasphemy-law "
            "vigilantism, where accusers and mob-killers routinely escape "
            "prosecution. The unborn child killed alongside the umm walad is "
            "not considered in the hadith's moral accounting. A religion whose "
            "founder exonerated a master for killing his pregnant slave over "
            "her speech has sanctified private retribution — and the "
            "consequences have been visible for fourteen centuries."
        ),
    },
    {
        "anchor": "Jesus son of Mary will descend at the white minaret east of Damascus",
        "response": (
            "Classical eschatology treats the Damascus descent as specific "
            "geographic detail strengthening the prophecy's verifiability — "
            "future generations will recognise its fulfilment when Jesus descends "
            "at the identified location. The \"white minaret\" reference reflects "
            "divine foreknowledge of the architectural development of Damascus, "
            "which is a form of prophetic miracle embedded in the text."
        ),
        "refutation": (
            "The \"white minaret east of Damascus\" did not exist in 7th-century "
            "Damascus — it was constructed after the hadith's composition. The "
            "\"divine foreknowledge of future architecture\" defense turns the "
            "anachronism into retroactive prophecy, which is the structure of "
            "unfalsifiable back-filled prediction rather than genuine foresight. "
            "A prophecy whose specific props (a named architectural feature) "
            "postdate the prophecy's composition is a prophecy whose dating has "
            "drifted — exactly what you predict from tradition accumulating "
            "specifics after the fact to make a general prediction more vivid."
        ),
    },
    {
        "anchor": "The canon preserves the criticism:",
        "response": (
            "Classical historiography treats the Umayyad hereditary shift as a "
            "political development rather than a theological one — the "
            "<em>rashidun</em> (rightly-guided) caliphate ended with Ali, and "
            "Mu'awiyah's transition to dynastic rule was a departure from ideal "
            "prophetic governance without being a repudiation of Islamic "
            "principles. The preservation of the criticism is evidence of the "
            "tradition's honesty about its own institutional history."
        ),
        "refutation": (
            "The candour is to the tradition's credit — but the content is "
            "damaging. The transition from \"rightly-guided\" to dynastic "
            "monarchy happened within fifty years of Muhammad, which means the "
            "\"pure early Islam\" narrative collapses almost immediately after "
            "the founder. A religion whose political golden age lasted less "
            "than a generation has a template-problem: the model governance "
            "Muhammad supposedly established did not survive, and what "
            "replaced it (hereditary monarchy with religious legitimation) is "
            "what became normative Islamic political practice across fourteen "
            "centuries. The ideal was rhetorical; the reality was Umayyad and "
            "Abbasid dynasties."
        ),
    },
    {
        "anchor": "The fornicator is not a believer at the moment he fornicates",
        "response": (
            "Classical theology reads the hadith as emphasising the severity of "
            "major sins without intending strict theological oscillation — the "
            "\"is not a believer\" framing is rhetorical intensification, meaning "
            "the sinner's faith is weakened or incomplete, not that belief is "
            "literally suspended during the sinful act. Ash'arite and Maturidite "
            "theology developed this reading, which distinguishes "
            "<em>kufr</em> (disbelief) from <em>fisq</em> (grave sin) in "
            "doctrinal status."
        ),
        "refutation": (
            "Classical theology's frantic interpretive work — Ash'arite, "
            "Maturidite, Mu'tazilite, and Khariji all produced competing "
            "readings — is itself evidence that the hadith's plain meaning "
            "created a theological crisis. The Kharijites took it literally and "
            "used it to excommunicate sinful Muslims and legitimize killing "
            "them; the Ash'arites relativised it to prevent that outcome. A "
            "hadith requiring multiple centuries of interpretive defense to "
            "prevent its natural reading from producing violence is a hadith "
            "whose content is not stable. The tradition's 1,400-year debate is "
            "not sophistication; it is the cost of including the hadith in the "
            "first place."
        ),
    },
    {
        "anchor": "Adam and Moses argued. Moses said: 'You are the one whose sin drove humanity",
        "response": (
            "Classical theology (particularly Ash'arite) reads the hadith as "
            "establishing divine foreknowledge without undermining human moral "
            "agency. Adam's \"written before I was created\" defense operates at "
            "the metaphysical level of eternal divine knowledge, while human "
            "responsibility operates at the empirical level of actual choices. "
            "The <em>khalq</em>/<em>kasb</em> distinction (Allah creates, human "
            "acquires) resolves the apparent tension between foreknowledge and "
            "responsibility."
        ),
        "refutation": (
            "If \"it was written\" is a valid defense for Adam, it is a valid "
            "defense for every subsequent sinner — which would dissolve the "
            "Quran's entire moral and judicial framework. The "
            "<em>khalq</em>/<em>kasb</em> distinction is the scholastic "
            "scaffolding invented specifically to manage this contradiction, "
            "and its opacity is proverbial. The hadith preserves a defense whose "
            "valid application would collapse the theodicy of eternal hell, and "
            "the tradition has spent fourteen centuries trying to prevent that "
            "collapse through increasingly technical distinctions. A religion "
            "whose founding argument-winner is \"I was programmed to sin\" has "
            "conceded the theodicy problem at its root."
        ),
    },
    {
        "anchor": "The first thing Allah created was the Pen, and He said to it: 'Write.'",
        "response": (
            "Classical theology treats the Pen-creation as the first act of "
            "divine decree, with the Pen representing the instrument by which "
            "Allah records the measurements of all things. The scribal imagery "
            "is metaphorical for divine ordaining rather than literal, and "
            "parallels to Egyptian and Mesopotamian scribal gods reflect "
            "humanity's common intuition of divine ordering preserved in the "
            "Abrahamic tradition in its purified form."
        ),
        "refutation": (
            "The \"humanity's common intuition in purified form\" is apologetic "
            "theological universalism that simultaneously grants legitimacy to "
            "Egyptian, Mesopotamian, and other ancient religious cosmology as "
            "sources of genuine divine knowledge — at which point Islam's "
            "distinctiveness collapses into continuity with the pre-existing "
            "Near Eastern religious imagination. The simpler account: scribal-"
            "creation motifs are widespread because scribal cultures imagined "
            "cosmology in terms of their own profession. Islam inherited the "
            "Near Eastern framing. A creation whose first moment is stationery "
            "has communicated the imagination that authored the account."
        ),
    },
    {
        "anchor": "With him will be a mountain of bread, and rivers of water; people will follow",
        "response": (
            "Classical eschatology treats the Dajjal narrative as genuine "
            "prophetic warning about a future figure whose supernatural powers "
            "will test the faith of believers. The \"kill and revive\" detail is "
            "cited as a specific eschatological feature that will distinguish "
            "the Dajjal from legitimate prophetic miracle, because believers will "
            "recognise the deception despite the apparent power. The detailed "
            "imagery is pedagogical — preparing the community to resist "
            "supernatural deception."
        ),
        "refutation": (
            "The kill-and-revive signature is structurally identical to the "
            "miracles attributed to the Islamic prophetic tradition itself — "
            "healings, resurrections, supernatural displays. If the Dajjal can "
            "do these things deceptively, the criteria for distinguishing "
            "genuine prophetic miracle from diabolic mimicry are collapsed. "
            "Believers are asked to recognise \"true\" miracle from \"false\" "
            "miracle through criteria the text does not supply — which is "
            "exactly the apologetic position every supernatural claimant takes "
            "against rivals. A theology whose end-time antagonist can "
            "perform the same sort of signs as its genuine messengers has not "
            "distinguished the categories; it has rendered them indistinguishable."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/ibn-majah.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

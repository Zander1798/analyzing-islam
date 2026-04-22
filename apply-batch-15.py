#!/usr/bin/env python3
"""Batch 15: Final 34 Quran Moderate entries (81-114)."""
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
        "anchor": "Purify My House for those who perform Tawaf",
        "response": (
            "Classical apologetics argues the Ka'ba was originally Abraham's "
            "construction, corrupted over centuries by Arab polytheism. Islam's "
            "preservation of the site's central role restores its Abrahamic meaning; "
            "the idols were cleared away, but the sanctuary returns to its authentic "
            "function."
        ),
        "refutation": (
            "The Abraham-founded-Mecca narrative has no independent historical or "
            "archaeological support outside Islamic sources. The Hebrew Bible places "
            "Abraham in Canaan, not Arabia. Pre-Islamic polytheistic veneration of the "
            "Ka'ba is documented in early Arab sources; the Islamic claim that the "
            "site is originally Abrahamic is intra-Islamic assertion, not independent "
            "evidence. The circumambulation, Black Stone kiss, and sacred-precinct "
            "concepts are continuous with pre-Islamic Arab practice — rebadged rather "
            "than replaced."
        ),
    },
    {
        "anchor": "There is no creature on [or within] the earth or bird that flies",
        "response": (
            "Classical apologetics reads \"nations\" metaphorically — a description "
            "of how Allah orders His creation into cohesive groups with their own "
            "patterns. Modern apologists frame the verse as an early insight into "
            "animal community behavior, compatible with ethological findings about "
            "social structure across many species."
        ),
        "refutation": (
            "Modern ethology distinguishes genuinely social species (wolves, bees, "
            "primates) from solitary species (tigers, most cats, many reptiles and "
            "fish). The Quran's universalising claim that every animal species forms "
            "\"nations like you\" fails the biological distinction. The "
            "anthropocentric framing is exactly what a 7th-century author observing "
            "animals from human-social categories would produce, not what modern "
            "biological knowledge supports."
        ),
    },
    {
        "anchor": "My Lord, because You have put me in error, I wi",
        "response": (
            "Classical theology frames Satan's mission as divinely permitted temptation "
            "that tests and refines human faith — Allah allows the adversary "
            "to operate within limits, and human moral development requires the "
            "possibility of temptation. The arrangement is pedagogical, not unfair, "
            "because Allah also provides guidance to resist."
        ),
        "refutation": (
            "Divinely authorised tempter + divine responsibility for human failure is "
            "the theodicy problem the verse makes explicit. Allah permits the "
            "adversary to beautify disobedience; humans are set up for combat against "
            "an opponent with systemic advantages. Classical compatibilism "
            "(<em>khalq/kasb</em>) patches the problem by dividing creation from "
            "acquisition, but the patch concedes that the game is structurally "
            "weighted — which is exactly what makes \"fair judgment\" on the "
            "eternal scale incoherent."
        ),
    },
    {
        "anchor": "It has been revealed to me that a group of the jinn listene",
        "response": (
            "Classical theology accepts jinn as real intermediate beings — a distinct "
            "creation mentioned throughout the Quran. The jinn's conversion upon "
            "hearing recitation confirms the universality of Islamic call; jinn are "
            "bound by the same moral framework as humans, with their own Muslims and "
            "non-Muslims."
        ),
        "refutation": (
            "The Quran's confirmation of jinn-reality preserves pre-Islamic Arabian "
            "demonology under Islamic framing. Modern Muslim psychiatric practice "
            "continues to diagnose possession cases and prescribe <em>ruqya</em> "
            "as treatment, with theological grounding in this surah. Mental-health "
            "conditions misidentified as jinn-possession receive spiritual "
            "intervention rather than clinical care. A scripture that validates "
            "the ontology of invisible intelligent beings who can interact with "
            "humans has preserved the cosmology, not corrected it."
        ),
    },
    {
        "anchor": "Fasting has been prescribed for you, as it was prescribed for tho",
        "response": (
            "Classical apologetics frames the shared fasting practice as evidence of "
            "continuity across the Abrahamic traditions — Allah's commands are "
            "consistent across prophets, so fasting has been prescribed to all "
            "communities of faith. The Ramadan fast's specific timing and form are "
            "distinctively Islamic, even while the principle is shared."
        ),
        "refutation": (
            "The verse explicitly frames Islamic fasting as inherited rather than "
            "novel — \"as it was prescribed for those before you.\" That is "
            "historical self-description, not independent revelation. If the "
            "practice is shared, the question is whether it originated in Islamic "
            "revelation or was absorbed from prior communities' observance. The "
            "verse's language points to the latter: fasting was already there, and "
            "Islam joined an existing religious practice."
        ),
    },
    {
        "anchor": "And if [slave women] commit immorality, their punishment is half",
        "response": (
            "Classical apologetics argues the half-punishment reflects mitigation "
            "for slaves' reduced social autonomy — they had less control over their "
            "own circumstances, so the law adjusts penalty to their situation. The "
            "principle is accommodation, not endorsement of slavery's justice "
            "framework."
        ),
        "refutation": (
            "\"Mitigation\" preserves the punishment framework (<em>zina</em> "
            "penalties, including stoning for the married) and merely adjusts the "
            "slave's allocation within it. If stoning cannot be halved — which "
            "classical jurists acknowledged — the half-punishment framework reveals "
            "the scheme's inconsistency. A legal system that calibrates penalty by "
            "slave/free status encodes that status into divine law. The "
            "\"mitigation\" framing accepts the ranking and discounts its consequence "
            "without removing the ranking."
        ),
    },
    {
        "anchor": "Do not compel your slave girls to prostitution, if they desire ch",
        "response": (
            "Classical apologetics argues the conditional phrase is idiomatic rather "
            "than licensing: the Quran rebukes a specific abuse (Abdullah ibn Ubayy's "
            "pimping) without intending the conditional to permit coercion in other "
            "cases. The verse's spirit forbids all forced prostitution, with the "
            "specific conditional reflecting the rebuke's original context."
        ),
        "refutation": (
            "Classical commentators (Tabari, Ibn Kathir, al-Qurtubi) recognised and "
            "discussed the disturbing implication of the conditional, which is why "
            "the question appears in tafsir at all. The \"idiomatic\" defense is "
            "philologically weak — Arabic conditionals most naturally specify when "
            "the command applies. A scripture that issues a conditional prohibition "
            "on forced sexual service, rather than a categorical one, has done real "
            "legal work: the conditional is the difference between blanket "
            "prohibition and narrow-case rebuke."
        ),
    },
    {
        "anchor": "Let him free a believing slave...",
        "response": (
            "Classical apologetics treats the manumission-as-atonement framework as "
            "evidence of Islam's pro-emancipation trajectory: the Quran creates "
            "spiritual incentive for freeing slaves by making manumission an "
            "expiation for major sins (accidental killing, broken oaths, "
            "<em>dhihar</em>). The economy is designed to dissolve slavery through "
            "religious motivation."
        ),
        "refutation": (
            "The atonement economy presupposes the institution it claims to dissolve "
            "— you need slaves to free as expiation. Removing slavery from the "
            "economy would remove the expiation mechanism. Classical jurisprudence "
            "did not treat Islamic law as requiring slavery's abolition; the "
            "manumission rules operated within a standing institution for 1,400 "
            "years. \"Trajectory toward abolition\" is apologetic retrofit; the "
            "tradition never reached the endpoint because it never moved toward "
            "it as doctrinal requirement."
        ),
    },
    {
        "anchor": "[Classical law derived from Q 4:24:]",
        "response": (
            "Classical jurisprudence developed the <em>umm walad</em> doctrine as "
            "protection for slaves who bore their masters' children: such women "
            "became un-sellable and had to be freed on the master's death. This "
            "is cited by apologists as evidence of Islam's slave-welfare "
            "evolution — motherhood-through-child-bearing elevated the slave's "
            "status."
        ),
        "refutation": (
            "The <em>umm walad</em> protection is triggered only by producing a "
            "male-owner's child — pre-birth, the slave's status is full. A "
            "\"welfare\" system that requires involuntary pregnancy as the "
            "mechanism for eventual manumission has structured the institution "
            "around the owner's reproductive use of the slave. The child becomes "
            "the key to the mother's freedom, which ties her liberation to her "
            "exploitation. Modern welfare frameworks would reject this design; "
            "classical Islamic law built it as divinely-sanctioned protocol."
        ),
    },
    {
        "anchor": "[Classical Islamic tafsir inherited from Jewish midrash:]",
        "response": (
            "Classical tafsir's engagement with the Ham story reflects the broader "
            "exegetical tradition's absorption of Jewish midrashic material. Modern "
            "Muslim scholarship has increasingly distanced itself from "
            "<em>israiliyyat</em> (Jewish-borrowed traditions) in Quranic commentary, "
            "rejecting racial curse-of-Ham readings as not authentically Islamic."
        ),
        "refutation": (
            "Rejecting <em>israiliyyat</em> is reformist work against fourteen "
            "centuries of classical tafsir that freely incorporated such material. "
            "The curse-of-Ham framework operated in the Islamic slave trade for "
            "over a millennium, providing theological justification for Arab "
            "enslavement of Africans. The African slave trade from Arab-Muslim "
            "powers to the Indian Ocean economy was larger in duration and "
            "comparable in scale to the Atlantic trade, and its religious "
            "legitimation drew on exactly this classical tafsir tradition."
        ),
    },
    {
        "anchor": "We have made it an Arabic Quran that you might understand.",
        "response": (
            "Classical apologetics argues Arabic was the most linguistically capable "
            "language for preserving divine nuance — its morphological richness, "
            "semantic precision, and consonantal structure made it uniquely suited "
            "to carry the revelation. Non-Arabs are not second-class; they are "
            "invited to learn the language of revelation, as many have done."
        ),
        "refutation": (
            "\"Most linguistically capable\" is theological self-praise without "
            "linguistic foundation — every natural language has features useful "
            "for precise communication. The operational effect is that non-Arab "
            "Muslims (the vast majority of the global Muslim population) are "
            "expected to learn Arabic for meaningful Quranic access, creating a "
            "linguistic hierarchy within the religion. A universal revelation "
            "privileging one human language has structured access asymmetrically — "
            "which is not what genuine universality would look like."
        ),
    },
    {
        "anchor": "He created man from a sperm drop, and at once he is a clear adver",
        "response": (
            "Classical apologetics argues the \"sperm drop\" language reflects 7th-"
            "century observational vocabulary and is not a claim about exclusive "
            "male contribution. Other Quranic verses (76:2, 22:5) refer to "
            "\"mingled fluids,\" which modern apologists read as acknowledgment of "
            "both male and female contribution."
        ),
        "refutation": (
            "The specific embryological passages (16:4, 75:37, 23:14) uniformly "
            "describe the origin as <em>nutfah</em> — the male seminal drop — with "
            "no parallel female contribution mentioned. This matches Aristotelian "
            "male-only-seed theory (which held the female provided only passive "
            "material) that was standard in the Greek-medical tradition circulating "
            "in the 7th-century Arab world. Modern genetics shows equal genetic "
            "contribution from both parents. The \"mingled fluids\" retrofit "
            "reinterprets a phrase about semen's own mixture into a modern "
            "equal-contribution reading."
        ),
    },
    {
        "anchor": "You will not find a people who believe in Allah and the Last Day",
        "response": (
            "Classical apologetics frames 58:22 as describing specific historical "
            "wartime conditions — Badr and similar battles, where some Muslims "
            "faced family members on the enemy side. The verse addresses "
            "extraordinary conflict situations, not ordinary family relationships. "
            "Other verses command kindness to parents and family (17:23-24, 31:14)."
        ),
        "refutation": (
            "The verse's categorical language (\"you will not find a people who "
            "believe... and still love those who oppose Allah, even if they are "
            "their fathers or sons\") is universal, not contextual. Classical "
            "tafsir applied the principle broadly: religious allegiance trumps "
            "family bonds when they conflict. Modern Muslim families facing "
            "apostate members still experience this framework — many converts and "
            "ex-Muslims report family-severance experiences grounded in this "
            "verse's logic. \"Extraordinary wartime\" is modern apologetic "
            "narrowing; the text speaks in permanent terms."
        ),
    },
    {
        "anchor": "And a believing woman if she gives herself to the Prophet [and] i",
        "response": (
            "Classical apologetics notes the verse's carefully limited scope: it "
            "applies <em>specifically to Muhammad</em>, not to all Muslim men, and "
            "requires the woman's voluntary gift. The arrangement reflects "
            "Muhammad's unique social-political role and the specific consent "
            "mechanism (she gives herself, he accepts). It is not general license "
            "for men; it is a particular permission for a specific person."
        ),
        "refutation": (
            "\"Sexual access without contract\" being limited to Muhammad is not a "
            "defense of the permission; it is the observation that the revelation "
            "privileges its messenger. Aisha's observation (\"your Lord hastens to "
            "fulfill your wishes\") is preserved in canonical hadith precisely "
            "because the pattern was visible to her. The verse gives Muhammad a "
            "sexual privilege no other Muslim man possesses — which, framed within "
            "\"eternal divine law,\" communicates that the eternal law served the "
            "lawgiver's specific circumstances."
        ),
    },
    {
        "anchor": "He presents to you an example from yourselves.",
        "response": (
            "Classical apologetics reads the slave-partner rhetorical question as "
            "illustrating Allah's uniqueness — just as one would not treat slaves "
            "as equals in business partnership (in the 7th-century framework), "
            "Allah should not be treated as having partners. The rhetorical force "
            "depends on the audience's familiarity with slavery, not on "
            "endorsement of the institution."
        ),
        "refutation": (
            "The rhetorical argument depends on slavery being the assumed framework "
            "— the slave/free distinction is the backdrop against which Allah's "
            "uniqueness is demonstrated. Divine rhetoric that leans on \"slave-"
            "master inequality as obvious\" is rhetoric that ratifies the "
            "institution it uses as scaffolding. A revelation for all time should "
            "not depend on slavery's assumed moral givenness to communicate its "
            "theological point."
        ),
    },
    {
        "anchor": "And Allah has favored some of you over others in provision.",
        "response": (
            "Classical apologetics reads 16:71 as realistic description of economic "
            "inequality combined with theological framing — material differences are "
            "tests for both wealthy and poor. The verse does not celebrate "
            "inequality; it explains it as part of Allah's ordering, within which "
            "charity (zakat) and manumission (<em>itq</em>) are commanded as "
            "redistributive responses."
        ),
        "refutation": (
            "The verse's logic asks rhetorically: would the wealthy share provision "
            "with their slaves equally? — with the implied answer \"obviously not,\" "
            "as if this is a self-evident absurdity. That rhetorical move "
            "theologises the slave/master inequality as part of divine ordering, "
            "framing material inequality as intrinsic rather than as human "
            "injustice. \"Zakat\" and other mitigations operate within the framework "
            "this verse sanctifies; they do not challenge the framework itself."
        ),
    },
    {
        "anchor": "And those who seek a contract [for eventual emancipation] from am",
        "response": (
            "Classical apologetics treats <em>mukataba</em> (contract-for-freedom) "
            "as pro-emancipation mechanism within the existing institution: slaves "
            "could purchase their freedom through agreed installments, with the "
            "master required to facilitate if \"good\" was seen in the slave. The "
            "rule is incentive structure for manumission, not confirmation of "
            "slavery's permanence."
        ),
        "refutation": (
            "Freedom under this framework is conditional on the master's "
            "assessment — \"if you see good in them\" is the text's standard. A "
            "universal emancipation rule would not make freedom contingent on the "
            "owner's subjective evaluation. The contrast with Islamic "
            "abolition-language elsewhere is diagnostic: when the Quran wants to "
            "forbid something categorically (alcohol, idolatry), it does so "
            "without \"if the master sees good.\" The <em>mukataba</em> provision "
            "operates within, and thus preserves, slavery as standing institution."
        ),
    },
    {
        "anchor": "I will mislead them, and I will arouse in them [sinful] desires",
        "response": (
            "Classical tafsir reads \"change the creation of Allah\" as metaphor for "
            "moral-spiritual distortion rather than literal bodily modification. "
            "Some classical jurists applied the verse to specific practices "
            "(tattooing, plucking eyebrows for cosmetic effect) while modern "
            "apologists distinguish these from medical or naturally-varying bodily "
            "features that do not fall under the prohibition."
        ),
        "refutation": (
            "The classical jurisprudence derived from this verse is not limited to "
            "cosmetic modification — it has been applied across centuries to "
            "prohibit gender-nonconforming presentation, gender-reassignment care, "
            "and transgender identity, framing these as \"changing Allah's "
            "creation\" and thus satanic. The \"only cosmetic\" narrowing is modern "
            "reformist apologetics; contemporary anti-trans enforcement in Muslim-"
            "majority states cites this verse as theological warrant. A scripture "
            "that pathologises bodily variation as demonic has supplied the "
            "framework for persecution."
        ),
    },
    {
        "anchor": "And do not wish for that by which Allah has made some of you excee",
        "response": (
            "Classical apologetics reads the verse as endorsement of contentment with "
            "one's assigned role — both men and women have their own spiritual "
            "rewards based on their respective responsibilities. The verse "
            "discourages envy across gender lines, not role-confinement per se; "
            "modern reformists read it as permitting expanded roles where "
            "circumstances have changed."
        ),
        "refutation": (
            "Classical jurisprudence extracted from 4:32 the permanent separation of "
            "gender roles — women should not aspire to men's social prerogatives, "
            "and vice versa. The verse's ban on \"wishing\" what the other sex has "
            "is psychological enforcement of role stratification. Modern expansion "
            "of women's public roles in Muslim-majority societies has required "
            "reading around this verse, which classical jurisprudence cited "
            "consistently against such expansions. The \"contentment\" framing is "
            "retrofitted to make the verse compatible with contemporary gender "
            "flexibility; the classical reading resisted exactly that flexibility."
        ),
    },
    {
        "anchor": "And We send down of the Quran that which is healing and mercy for",
        "response": (
            "Classical theology treats the Quran's healing function as spiritual — "
            "the text cures spiritual ailments (doubt, despair, moral weakness). "
            "The physical-healing applications (<em>ruqya</em>, blessed water) are "
            "supplementary practices developed within the tradition, with modern "
            "apologists emphasizing they should not substitute for medical care."
        ),
        "refutation": (
            "Classical Islamic medicine treated Quranic recitation as genuine "
            "therapeutic intervention, and contemporary Muslim communities "
            "continue to emphasize <em>ruqya</em> and Quran-based spiritual "
            "medicine as substantial modalities. Modern Muslim patients frequently "
            "delay clinical care — especially for mental health conditions "
            "reframed as <em>waswas</em> or jinn-possession — in favor of "
            "spiritual intervention grounded in this verse. The \"supplementary, "
            "not substitute\" caveat is modern reformist framing; the operative "
            "tradition has treated Quran-healing as substantive therapeutic "
            "category."
        ),
    },
    {
        "anchor": "And they followed what the devils had recited during the reign of",
        "response": (
            "Classical tafsir frames Harut and Marut as testing agents sent by Allah "
            "— they announce themselves as temptation (\"we are only a trial\"), "
            "preserving their angelic character while their function serves "
            "pedagogical purpose. The magic they teach is real but its use is "
            "forbidden; the verse warns against sorcery's reality while "
            "acknowledging its existence as divinely-permitted threat."
        ),
        "refutation": (
            "Angels teaching magic — however framed — places the Quran in tension "
            "with its own definition of angels as beings who never disobey "
            "(66:6, 16:50). Either Allah commanded them to teach magic "
            "(divine authorship of sorcery), they disobeyed (contradicting "
            "angelic nature), or they were not angels. The verse's endorsement of "
            "magic's reality preserves pre-Islamic Mesopotamian sorcery "
            "cosmology (the Babylon reference is historically specific) in "
            "Quranic vocabulary. \"Corrective supernatural framework\" would "
            "dismiss the folk belief; Islam's framework confirms it."
        ),
    },
    {
        "anchor": "Then when the Horn is blown with one blast",
        "response": (
            "Classical eschatology treats the trumpet-blast as specific "
            "eschatological event — the final moment when Allah's judgment begins. "
            "The parallels to 1 Thessalonians 4's shofar and Jewish apocalyptic "
            "trumpet reflect common Abrahamic eschatological vocabulary, with "
            "Islam preserving the true meaning in its Quranic form."
        ),
        "refutation": (
            "\"Common Abrahamic vocabulary\" is the apologetic framing for what is "
            "demonstrably borrowed. Jewish apocalyptic literature (Isaiah 27:13, "
            "Zechariah 9:14, 1 Thessalonians 4:16, 1 Corinthians 15:52) all "
            "feature the trumpet-blast motif pre-dating the Quran by centuries. "
            "The Quran is downstream of this tradition. The \"mountains "
            "flattened\" imagery is also standard Near Eastern apocalyptic, "
            "reshaping landscape as divine judgment. A revelation preserving "
            "common vocabulary has participated in the tradition, not "
            "transcended it."
        ),
    },
    {
        "anchor": "And [for] every person We have imposed his fate upon his neck",
        "response": (
            "Classical apologetics treats the deed-book imagery as pedagogical "
            "accommodation — judgment-day accountability rendered in physical "
            "scroll-language 7th-century listeners could grasp. The \"neck-"
            "bound record\" is metaphor for the inescapable nature of one's own "
            "deeds, not a claim about literal physical scrolls."
        ),
        "refutation": (
            "Classical tafsir (Tabari, Ibn Kathir) treated the imagery as referring "
            "to real eschatological events, with specific physical scrolls "
            "produced for each person. The bookkeeping metaphor is inherited from "
            "Jewish apocalyptic literature (Daniel 7:10, Revelation 20:12), where "
            "the divine ledger is ancient-scribe vocabulary. A divine eschatology "
            "whose symbolic apparatus is Late-Antique scribal bookkeeping has "
            "preserved the imagination of the culture that authored it."
        ),
    },
    {
        "anchor": "Who is it that can intercede with Him except by His permission?",
        "response": (
            "Classical theology preserves the permission-based intercession "
            "framework as coherent: Allah remains sovereign; intercession happens "
            "only with His consent. This is not the unfettered priestly mediation "
            "the Quran rejects in Christian theology but a specific permission "
            "granted to certain prophets (especially Muhammad) for eschatological "
            "purposes."
        ),
        "refutation": (
            "The permission-based framework is exactly how Christian priestly "
            "mediation operates — clergy intercede \"with God's permission,\" not "
            "independently. The distinction Islam draws against Christianity "
            "collapses under its own framework: once Muhammad's eschatological "
            "intercession is granted, the rejected category (mediation) has been "
            "restored for Muhammad specifically. The Quran's polemic against "
            "intercession (6:51, 74:48) and its permission for Muhammad's "
            "intercession (2:255, hadith literature) are in structural tension, "
            "which the \"by His permission\" gloss rhetorically covers but does "
            "not resolve."
        ),
    },
    {
        "anchor": "Remain despised therein and do not speak to Me.",
        "response": (
            "Classical eschatology presents hell's rejection as consequence of the "
            "damned's persistent rejection of Allah during life. The \"do not speak\" "
            "command reflects the finality of judgment — the time for repentance "
            "has passed. The mercy-precedes-wrath principle operates in the "
            "pre-judgment period; after judgment, justice governs."
        ),
        "refutation": (
            "Infinite silence-refusal as response to finite earthly wrongdoing is "
            "disproportion. \"Most merciful\" (<em>al-Rahman</em>) is a Quranic "
            "divine attribute specifically emphasised in opening formulas, but "
            "operationally it yields to eternal refusal-to-hear at the point "
            "where mercy would be most needed. A divine ethics that names mercy "
            "as primary and then abandons it permanently at the eschatological "
            "moment has produced the tension the apologetic must manage rather "
            "than resolve."
        ),
    },
    {
        "anchor": "Indeed, those who came with falsehood are a group among you.",
        "response": (
            "Classical apologetics treats the Aisha-slander revelation as corrective "
            "justice: Aisha was innocent, the slander-spreaders were in the wrong, "
            "and Allah's vindication establishes the seriousness of unfounded "
            "accusation. The four-witness rule for <em>qadhf</em> (slander) "
            "derives from this episode as protection for accused women."
        ),
        "refutation": (
            "The pattern — convenient revelation arriving to resolve a prophetic-"
            "household reputation crisis — is repeated across Aisha's slander, "
            "the Zaynab affair, the honey/Mariyah episode, and others. The "
            "Prophet's household reputation is protected by divine intervention "
            "at key moments, producing exactly the \"your Lord hastens to fulfill "
            "your wishes\" pattern Aisha herself noted. A revelation pattern that "
            "systematically defends its messenger's household in real-time "
            "domestic conflicts communicates that the revelation's timing tracks "
            "the messenger's circumstances."
        ),
    },
    {
        "anchor": "But once they are sheltered in marriage, if they should commit ad",
        "response": (
            "Classical apologetics argues the half-punishment provision for slave "
            "women reflects mitigation for their limited agency — they had less "
            "control over their circumstances. The rule is protective, not "
            "degrading. Modern reformists read the verse as prompting "
            "abolitionist reflection: if slave women should be punished less, "
            "the institution creating the category should be questioned."
        ),
        "refutation": (
            "The inconsistency classical jurists noted is telling: stoning cannot "
            "be halved, so the half-punishment rule for slave women implicitly "
            "exempts them from stoning — exposing the framework's internal "
            "incoherence. The \"mitigation\" language accepts slave/free ranking "
            "as foundational; a genuinely egalitarian legal system would not "
            "calibrate punishment by legal status. Modern abolitionist reflection "
            "is reformist work that classical jurisprudence did not perform."
        ),
    },
    {
        "anchor": "Your wives are a place of cultivation for you",
        "response": (
            "Classical apologetics argues the tilth metaphor in its original "
            "Semitic agricultural context emphasized marriage's reproductive and "
            "generational aspect — wives as the source of family continuity, not as "
            "objectified property. The \"however you wish\" phrase addresses "
            "positioning during conception, resolving a specific folk misconception "
            "about sexual positions affecting offspring."
        ),
        "refutation": (
            "The \"tilth\" metaphor in its original context does frame women as "
            "agricultural ground that men cultivate — the agency is with the "
            "farmer, not with the soil. The verse's occasion (correcting a "
            "Jewish folk belief about squinting babies) makes the eternal "
            "metaphor of universal cosmic scripture contingent on village "
            "midwifery gossip. A text whose most objectifying sexual metaphor "
            "originated in a reply to folklore has revealed something about its "
            "compositional context."
        ),
    },
    {
        "anchor": "And to wrap [a portion of] their head covers over their chests",
        "response": (
            "Classical apologetics frames 24:31 as balanced modesty regulation: it "
            "begins with men lowering their gaze (24:30) before addressing women's "
            "attire. The female-specific dress rules were culturally-appropriate "
            "for 7th-century Arabia and their principle (modesty) is enduring "
            "while the specifics adapt to context."
        ),
        "refutation": (
            "The regulatory burden in the combined verses is asymmetric: men are "
            "told to lower gaze (psychological/visual), while women are assigned "
            "comprehensive dress-and-behavior codes. The exception-list "
            "(husbands, male relatives... and \"what your right hand possesses\") "
            "includes owned slaves — meaning a woman must cover before free men "
            "outside family but not before her male slaves. The slave-exception "
            "reveals the framework: modesty is about access and ownership, not "
            "intrinsic dignity."
        ),
    },
    {
        "anchor": "And when you ask [his wives] for something, ask them from behind",
        "response": (
            "Classical apologetics reads 33:53 as specific to the Prophet's "
            "wives, whose unique public-religious role warranted distinct conduct "
            "rules. The verse's \"purity of heart\" framing is psychological: "
            "physical separation preserves the purity both speakers seek, not a "
            "claim about female pollution. Modern apologists stress the verse's "
            "narrow addressee."
        ),
        "refutation": (
            "Classical jurisprudence (across Sunni schools) extended the "
            "<em>hijab</em> principle to all Muslim women as a general framework "
            "for gender-separation in public space. The \"only Muhammad's wives\" "
            "narrowing is modern reformist reading against the classical "
            "extension. The psychological-purity framing ties spiritual state to "
            "physical gender-separation — which becomes the structure underwriting "
            "comprehensive gender-segregation rules in classical law."
        ),
    },
    {
        "anchor": "And [also prohibited to you are all] married women except those",
        "response": (
            "Covered under the parallel entry at Q 4:24: classical apologetics "
            "argues capture in war dissolved the prior marriage, so captives were "
            "not simultaneously married and available. The <em>istibra</em> "
            "waiting period provided procedural protection. The framework was "
            "progressive relative to 7th-century norms."
        ),
        "refutation": (
            "The \"capture dissolves marriage\" claim has no Quranic basis; it is "
            "juristic invention. The verse presupposes the marriage still exists "
            "when it exempts married women for right-hand-possessed status. "
            "<em>Istibra</em> protects lineage clarity, not consent. ISIS's 2014 "
            "Yazidi enslavement cited this verse with classical legal footnoting, "
            "applying the standard reading. A religion whose war-ethics "
            "authorizes sexual access to captured married women has preserved "
            "exactly the structure its apologists now wish to disown."
        ),
    },
    {
        "anchor": "And if he has divorced her [for the third time], then she is not",
        "response": (
            "Classical apologetics frames 2:230 as deterrent against frivolous "
            "triple-divorce: the requirement for the wife to marry and consummate "
            "with another man before reconciliation is designed to make the "
            "triple-talaq effectively irreversible, discouraging hasty "
            "pronouncement. The rule protects women from repeatedly-divorced-and-"
            "reclaimed status."
        ),
        "refutation": (
            "The \"deterrent\" function presupposes the triple-talaq framework that "
            "the Quranic marriage structure generated — modern reforms in Egypt, "
            "India, and other jurisdictions have had to formally abolish instant "
            "triple talaq because the hadith-tradition readily permitted it. The "
            "<em>halala</em> requirement (wife must marry, consummate with, and be "
            "divorced from a third party before reconciliation with the first "
            "husband) has generated a real industry of <em>halala</em> marriages "
            "arranged specifically for the bridge-function, with the third party "
            "sometimes paid to divorce. The rule's consequences include exactly "
            "this exploitation."
        ),
    },
    {
        "anchor": "If [the deceased] has a sister, she will have half of what he lef",
        "response": (
            "Classical apologetics argues the 2:1 male-female inheritance ratio "
            "reflects economic obligations of each sex: men were responsible for "
            "<em>mahr</em> (bridal payment) and family support; women's "
            "inheritance was their own private wealth, protected from family-"
            "support obligations. The ratio is effectively equal when obligations "
            "are factored in."
        ),
        "refutation": (
            "The \"economic obligation balance\" is the standard defense, but it "
            "fails several cases: daughters with no brothers, women with "
            "independent wealth, modern economies where women are financially "
            "autonomous. If the rule were calibrated to obligation, it would "
            "adjust with obligation — but it does not; it is fixed by sex. The "
            "Quran could have pegged the ratio to circumstance rather than "
            "gender; fixing it to gender embedded the 7th-century economic "
            "pattern into eternal divine law."
        ),
    },
    {
        "anchor": "let those whom your right hands possess",
        "response": (
            "Classical apologetics frames 24:58 as privacy regulation for slaves' "
            "own protection: slaves in the household should not enter private "
            "spaces without warning, which establishes a category of privacy "
            "rights the slaves themselves enjoyed. The rule recognises slaves as "
            "moral agents who must respect household boundaries, implying they "
            "have boundaries of their own."
        ),
        "refutation": (
            "The rule structures household life around slaves' <em>presence</em> "
            "inside the master's intimate spaces as the standing condition — "
            "slaves circulate in rooms where masters sleep, change, and have "
            "sexual relations, with the \"knock at three times\" regulation "
            "carving out three specific privacy windows. This normalises "
            "ownership-of-persons-in-domestic-intimacy as the background. "
            "Freedom or absence of slaves from intimate spaces is not the "
            "framework; permissioned intrusion is."
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

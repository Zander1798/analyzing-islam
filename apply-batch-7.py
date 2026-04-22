#!/usr/bin/env python3
"""Batch 7: All 22 Tirmidhi Strong entries."""
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
    # 1 — 73 sects
    {
        "anchor": "The Jews split into 71 sects, the Christians split into 72 sects, and my nation",
        "response": (
            "Apologists argue the hadith is warning, not damning: it urges believers to remain "
            "united in adherence to the Quran and Sunnah, with the \"saved sect\" "
            "(<em>al-firqa al-najiya</em>) identified in parallel hadith as \"those upon what "
            "I and my companions are upon.\" On this reading, the 73-sect arithmetic is "
            "rhetorical rather than precise, and the \"saved sect\" criterion is behavioural "
            "(fidelity to prophetic practice), not denominational — meaning individuals from "
            "multiple communities can qualify."
        ),
        "refutation": (
            "The \"criterion is behavioural\" reading does not prevent every Sunni, Shia, "
            "Sufi, Ahmadiyya, and Salafi community from simultaneously claiming to be that "
            "saved sect. The hadith's structural effect is mutual excommunication: every "
            "Muslim subcommunity reads the other subcommunities as the damned 72. The "
            "\"rhetorical not precise\" defense has to face that the specific numbers have "
            "been canonised by the tradition, and fourteen centuries of intra-Muslim polemic "
            "has used them. A hadith whose primary operational function is to enable "
            "<em>takfir</em> (excommunication) of other Muslims has not preserved unity — it "
            "has institutionalised its opposite."
        ),
    },
    # 2 — 72 virgins
    {
        "anchor": "The martyr has six special favors with Allah",
        "response": (
            "Apologists argue the \"72 virgins\" number is Tirmidhi's specific contribution "
            "and appears in a hadith of <em>hasan</em> grade rather than <em>sahih</em>, so "
            "its authenticity is not guaranteed. Some modern scholars (like Christoph "
            "Luxenberg) argue the Arabic <em>hur</em> originally meant \"white grapes\" rather "
            "than virgins. Mainstream apologetics emphasises that paradise-reward language is "
            "metaphorical across many Quranic passages, designed to move the faithful toward "
            "righteousness rather than to describe literal sexual recompense."
        ),
        "refutation": (
            "The <em>hasan</em> grade is weaker than <em>sahih</em> but still authoritative "
            "in mainstream Sunni jurisprudence, and the 72 number entered Islamic paradise-"
            "theology through exactly this channel. Modern jihadist recruitment materials "
            "cite the number specifically, not as metaphor. The Luxenberg \"white grapes\" "
            "thesis is a fringe philological speculation rejected by both Muslim and non-"
            "Muslim Quranic scholarship. The combined Quran-plus-hadith corpus uses "
            "unmistakably sexual language (large-eyed, well-guarded, maidens of equal age, "
            "unbroken by jinn or human) that no metaphor-defense fits without deeply "
            "rewriting the texts. The gender asymmetry — specific sexual reward for men, "
            "nothing comparable for women — is the fingerprint of a reward system designed "
            "for one sex."
        ),
    },
    # 3 — Lowest paradise kingdom
    {
        "anchor": "The lowest in rank among the people of Paradise will have a kingdom as large",
        "response": (
            "Apologists argue the hadith's geographical-scale language is rhetorical, meant to "
            "convey the incomparable <em>vastness</em> of paradise in terms a 7th-century "
            "listener could imagine. The kingdom imagery is not literal real-estate but the "
            "\"breadth\" of paradise — a sense of expansive freedom that contrasts with "
            "earthly confinement. Modern apologists invoke the Quranic description of "
            "paradise as \"wide as the heavens and earth\" (3:133) to suggest the hadith's "
            "measurements should be read as structural largeness, not literal arithmetic."
        ),
        "refutation": (
            "\"Rhetorical scale\" is the generic defense for every hadith that makes a "
            "falsifiable size claim. If the 2,000-year-travel description is metaphor, then "
            "the specific numbers carry no content and are decoration for emotional effect. "
            "But classical theologians read these measurements literally, and medieval "
            "Islamic cosmology took the paradise-kingdom descriptions seriously as structural "
            "claims. The arithmetic problem is not solved by metaphor: billions of paradise "
            "dwellers each with continent-scale kingdoms exceed the geometric capacity of "
            "any plausible cosmos — the \"heavens and earth\" breadth the Quran names "
            "included. A material-reward paradise imagined in units of aristocratic "
            "sovereignty is paradise shaped by the aspirations of its culture, not by the "
            "spiritual ends it claims to serve."
        ),
    },
    # 4 — Ashura pre-Islamic
    {
        "anchor": "In the pre-Islamic period, the Quraish used to fast on the day of Ashura.",
        "response": (
            "Classical apologetics frames the continuity as purposeful: Islam inherits and "
            "purifies prior monotheistic practices, including those preserved imperfectly "
            "among the pre-Islamic Arabs and Jews. Ashura's pre-Islamic observance traces "
            "back to Noah or Moses (depending on the hadith), which means the Quraysh's "
            "practice preserved a genuine prophetic tradition in diluted form. Islam's "
            "restoration of Ashura is thus return to origin, not pagan borrowing."
        ),
        "refutation": (
            "The \"restoration to origin\" defense is strained by the double attribution: the "
            "hadith corpus gives two different rationales (pre-Islamic Arab practice continued; "
            "Moses's gratitude for deliverance adopted after meeting Medinan Jews) — which "
            "cannot both be the original source. The pattern — pre-Islamic ritual continued "
            "with a new theological label — repeats across Islamic practice (Safa-Marwa "
            "circumambulation, Black Stone veneration, the Ka'ba itself). Each item has a "
            "\"restored from Abraham\" narrative attached. Multiple such narratives applied to "
            "pre-Islamic ritual survivals is the pattern of a religion rationalising "
            "inherited practice, not transcending it."
        ),
    },
    # 5 — Aisha age (Tirmidhi parallel)
    {
        "anchor": "The Messenger of Allah married 'Aishah when she was six years old",
        "response": (
            "The standard apologetic responses for Aisha's age (physical maturity, cultural "
            "norms, revisionist redating) are covered under the Bukhari and Muslim parallel "
            "entries. For this specific Tirmidhi transmission, apologists emphasise that it "
            "appears as a <em>sahih</em> chain of transmission in Tirmidhi, which uses "
            "slightly different methodology than Bukhari/Muslim, reinforcing the "
            "authenticity of the age report through independent isnad."
        ),
        "refutation": (
            "The cross-collection confirmation is in fact the problem for revisionist "
            "redating: Bukhari, Muslim, Abu Dawud, Tirmidhi, and Ibn Majah all preserve the "
            "6/9 age report through independent chains. \"Aisha was older\" apologetics "
            "requires rejecting all five canonical sources — which is not a selective "
            "critique of one weak transmission but a wholesale repudiation of the hadith-"
            "science methodology. If the five most authoritative hadith collections in "
            "Sunni Islam all cannot be trusted on the prophet's own marriage, the entire "
            "canonical apparatus is compromised — which is a higher price than "
            "apologists generally acknowledge paying."
        ),
    },
    # 6 — Grave squeeze
    {
        "anchor": "If anyone could be saved from the grave's squeeze, it would have been Sa'd",
        "response": (
            "Classical theology treats the \"squeeze\" as a post-mortem spiritual experience, "
            "not a physical compression of the body in the grave. The imagery uses "
            "earth-metaphor because the grave is the transitional space between this life "
            "and the next, and the \"squeeze\" represents a purifying encounter that even "
            "the righteous undergo. The hadith's contrast — Sa'd was an exemplary companion "
            "who still experienced the squeeze — emphasises the universality of this "
            "transition, not an earth-physics claim."
        ),
        "refutation": (
            "The \"spiritual not physical\" reading is available but not what the classical "
            "tradition taught. <em>'Adhab al-qabr</em> (torment of the grave) was debated in "
            "substantive physical terms across classical Kalam, with scholars discussing "
            "questions about whether the dead body feels pressure, whether the soul is "
            "reattached, whether angels physically strike the disbeliever. The "
            "spiritualising reading is a modern theological comfort applied retroactively. "
            "More fundamentally, an eschatology that imagines the earth as having moral "
            "agency — physical or spiritual — is an eschatology reading the world animistically, "
            "not as the ordinary causal structure modern cosmology describes."
        ),
    },
    # 7 — Bedouin urinated in mosque
    {
        "anchor": "A Bedouin stood up and urinated in the mosque.",
        "response": (
            "Apologists cite the hadith as evidence of Muhammad's <em>practical wisdom</em> "
            "and gentleness with the ignorant: rather than punish the Bedouin, the Prophet "
            "ordered water poured over the spot and used the moment to teach. The story is "
            "framed as a pedagogical gem about patience with newcomers to Islam, who needed "
            "education rather than harshness. Modern apologists cite it as "
            "the Prophet's model for disproportionate response — kindness where punishment "
            "would be counterproductive."
        ),
        "refutation": (
            "The contrast that makes the hadith revealing is with the other punishments of "
            "the same prophetic biography. Muhammad ordered the Uraniyyin mutilated for "
            "theft and apostasy; he authorised Ma'iz's stoning for voluntary confession of "
            "adultery; he commanded the beheading of the Banu Qurayza's men. Here, a "
            "public desecration of the mosque receives water and a lesson. The difference "
            "is not pedagogy but politics: the Bedouin was politically harmless, while "
            "apostates, adulterers, and treaty-breakers posed structural threats. Punishment "
            "severity tracks threat-to-regime, not crime-against-ethics. A moral code whose "
            "applications vary with the political cost of the offender is a code whose "
            "\"justice\" is strategic."
        ),
    },
    # 8 — Al-Kawthar paradise river
    {
        "anchor": "Al-Kauthar is a river in Paradise, whose banks are of gold",
        "response": (
            "Apologists argue the descriptions of al-Kawthar use earthly luxury imagery "
            "because that is what 7th-century listeners could grasp as signifiers of "
            "abundance — gold, pearls, musk. The actual reality of paradise is "
            "unimaginable by earthly reference; the Quran and hadith provide "
            "<em>pedagogical</em> imagery to orient the believer's longing, not a literal "
            "inventory. Modern apologists cite Quranic statements that no eye has seen or "
            "heart conceived what Allah has prepared for the believers, reinforcing the "
            "metaphorical status of specific descriptions."
        ),
        "refutation": (
            "The \"cultural signifiers\" framing concedes the point: paradise is imagined in "
            "the status-goods of 7th-century Arabian and Byzantine aristocracy — gold, "
            "pearls, musk, silks, tents, reclining cushions, serving youths. That is the "
            "fingerprint of a text written from inside that culture, not above it. A "
            "revelation from the creator of the cosmos could have used aesthetic categories "
            "that transcend 7th-century luxury aspiration; it chose those categories "
            "instead. The \"no eye has seen\" verse is real but co-exists with extensive "
            "specific description — the combination is a rhetorical hedge: grand generality "
            "plus concrete cultural detail, which is exactly how religious imagination "
            "builds a vision of the beyond from the vocabulary of the here."
        ),
    },
    # 9 — Umar head-chop
    {
        "anchor": "Umar said: 'Allow me to chop off the head of this hypocrite.'",
        "response": (
            "Apologists argue the hadith illustrates Muhammad's <em>restraint</em> and "
            "Umar's recognised military zeal in service of the community. The Prophet's "
            "refusal to grant Umar's request is the hadith's moral center: it preserves "
            "lives that Umar's strict interpretation would have taken. The prophet's "
            "restraint is cited as evidence of Islamic moral sophistication — Umar's "
            "proposal was rejected, so the tradition is teaching restraint, not violence."
        ),
        "refutation": (
            "The restraint was preserved for Muhammad; Umar's tendency is preserved without "
            "rebuke. A companion whose recurring default response to dissent is \"let me "
            "behead him\" becomes the second caliph, and mainstream Islamic tradition "
            "celebrates him as a model ruler whose zeal was exemplary. The restraint "
            "Muhammad showed was pragmatic — his stated reason was "
            "\"people would say Muhammad kills his companions\" — not principled objection. "
            "A moral tradition whose canonical memory preserves a leader proposing "
            "summary execution without moral critique has communicated that the proposal "
            "was understandable, even if not adopted. The embedding of such proposals into "
            "caliphal biography as character detail is itself the ethics lesson."
        ),
    },
    # 10 — 40 lashes vs 80
    {
        "anchor": "The Prophet gave forty lashes for drinking. Abu Bakr gave forty. Umar made it ei",
        "response": (
            "Apologists defend Umar's doubling as <em>ijtihad</em> (independent legal "
            "reasoning) operating within prophetic precedent. The underlying principle was "
            "punishment for intoxication; Umar inferred from the Prophet's reasoning that "
            "a stronger penalty was warranted as drinking spread and the community's "
            "deterrent needs increased. Classical jurisprudence preserves this as a "
            "legitimate expansion of hudud by a rightly-guided caliph, not as overthrow of "
            "prophetic rule."
        ),
        "refutation": (
            "<em>Ijtihad</em> can refine rulings on cases not covered by prophetic text; it "
            "cannot double the explicit penalty Muhammad himself applied. The classical "
            "framework treats hudud as divinely fixed — which is why the range of "
            "hudud cases is strictly delimited. If Umar could double hudud by reasoning, "
            "the fixity doctrine is false. If hudud are fixed, Umar's change is an "
            "unauthorised innovation. The tradition preserves both claims "
            "(\"hudud are fixed\" and \"Umar changed the hudud\") without resolution — and "
            "modern Islamic states generally apply Umar's 80-lash rule, not Muhammad's 40. "
            "The prophetic example has been overridden by the caliphal innovation, which "
            "is not what fixed divine law should look like."
        ),
    },
    # 11 — Raising daughters well = paradise
    {
        "anchor": "Whoever raises three daughters, disciplines them, marries them off",
        "response": (
            "Apologists read this hadith as exceptionally pro-female in a 7th-century "
            "context where daughters were often regarded as a burden: the Prophet elevates "
            "raising them well to the level of a paradise-guaranteeing act. The "
            "\"disciplines them, marries them off\" language tracks the father's "
            "responsibilities in that cultural context; it is not assigning the daughter "
            "a secondary role but noting the father's positive duties. Modern apologists "
            "emphasise that the hadith effectively makes female children a spiritual asset "
            "for parents, which was revolutionary at the time."
        ),
        "refutation": (
            "The \"revolutionary for its time\" framing concedes that the ethics is "
            "cultural-historical rather than eternal. The grammar of the hadith is "
            "diagnostic: the daughter's value is the father's paradise-reward. Her own "
            "spiritual biography does not appear as the criterion; his management of her "
            "does. \"Marries them off\" lists as paternal duty the transfer of the daughter "
            "to another household — a disposition, not an empowerment. A hadith that "
            "centres the father's salvation on his daughters' obedient compliance with "
            "marriage arrangement has situated female value instrumentally. Modern "
            "apologetic is right to note the 7th-century context; that is the problem."
        ),
    },
    # 12 — Woman testimony half
    {
        "anchor": "Is not the testimony of a woman half the testimony of a man?",
        "response": (
            "Apologists argue the 2:1 testimony ratio (Quran 2:282) applies to financial "
            "transactions specifically, not all legal testimony, and reflects the practical "
            "reality of 7th-century Arabian commercial life where women's regular "
            "involvement was limited — so their memory of specific transactional details "
            "was less reliable in that context. Modern apologists cite cases where women's "
            "testimony is treated as fully equal (breastfeeding relationships, specific "
            "medical matters only women can witness) as evidence that the 2:1 rule is "
            "domain-specific, not a claim about female cognition."
        ),
        "refutation": (
            "The Tirmidhi hadith's explicit rationale — \"is that not the deficiency of her "
            "intellect?\" — is precisely a claim about female cognition, presented by "
            "Muhammad to a specific audience. Modern apologetic narrowing to financial "
            "transactions is the move of a tradition responding to modern equality norms, "
            "not the reading the text delivers. Classical Islamic law applied the 2:1 ratio "
            "broadly across criminal and civil testimony, and contemporary Shari'a-based "
            "states continue that application. The domain-specific exceptions apologists "
            "cite are just that — exceptions that presuppose the general rule. A scripture "
            "that names female intellectual deficiency as justification for halving "
            "testimony has said something about female cognition; the narrowing is a modern "
            "wish, not the text's content."
        ),
    },
    # 13 — Water from fingers
    {
        "anchor": "The people needed water. The Prophet put his fingers in the water vessel.",
        "response": (
            "Apologists defend the hadith as preserving a genuine miracle of Muhammad's "
            "ministry, attested by multiple chains of transmission. Quran 17:59 (\"We did "
            "not send signs except that the earlier peoples denied them\") is read not as "
            "denying Muhammad any miracles, but as explaining why earlier miracle-based "
            "prophetic missions had failed — Muhammad's signs are preserved in the hadith "
            "corpus, which the Quran references as the \"recollections\" of what the prophet "
            "did. Water multiplication is no harder for Allah than any other recorded "
            "miracle."
        ),
        "refutation": (
            "Quran 17:59 is more pointed than the apologetic allows: it says signs were not "
            "sent because people denied them — implying Muhammad was not sent with signs. "
            "That reading fits with the Quran's broader pattern of framing the text itself "
            "as Muhammad's sole miracle (10:38, 17:88). The hadith corpus's later "
            "accumulation of physical miracles — water from fingers, moon splitting, food "
            "multiplication — tracks the pattern of earlier prophetic traditions (Elisha's "
            "oil, Moses's water, Jesus's loaves). It is exactly what you would predict from "
            "hagiographic development over time: a plain-speaking founder acquires "
            "wonder-working after his death as his community's veneration grows. The "
            "hadith's water-multiplication is not independent corroboration; it is "
            "conventional generic."
        ),
    },
    # 14 — Recite and children become Muslim
    {
        "anchor": "[Reciting specific verses/duas]",
        "response": (
            "Apologists argue the efficacy of <em>duas</em> is probabilistic, not "
            "mechanical — the hadith promises that sincere, specific supplications are "
            "answered in the way that is best for the petitioner, which may include "
            "outcomes different from the literal wording. When the outcome does not "
            "appear, the apologetic view is that Allah substituted a better outcome or "
            "deferred the answer to the hereafter. This is not unfalsifiability; it is the "
            "theological framework of <em>qada wa qadar</em> (divine decree and its "
            "particulars)."
        ),
        "refutation": (
            "The \"substituted better outcome\" framework does have the structure of "
            "unfalsifiability: any observed outcome can be absorbed into \"Allah's best for "
            "you\" regardless of whether it matches the promise. A promise that cannot be "
            "broken is not a promise; it is a template for reassurance. Classical Islamic "
            "culture built whole genres of <em>dua</em> literature around specific verbal "
            "formulas with specific promised outcomes, and when outcomes did not match, "
            "the response was always \"recite more sincerely\" or \"the answer is in the "
            "hereafter.\" This is the rhetorical structure of pure confirmation bias, in "
            "which every outcome is consistent with the hypothesis — the shape of a belief "
            "system that cannot be disconfirmed."
        ),
    },
    # 15 — Muhammad's heart opened
    {
        "anchor": "Two men in white clothes came, split open my chest, and removed a black clot",
        "response": (
            "Classical theology treats the heart-opening episode as preparation for "
            "prophethood — Muhammad's unique purification before receiving revelation. The "
            "\"black clot\" represents the universal human propensity to sin, which every "
            "person carries except those divinely purified. Muhammad's purification does "
            "not make him sinless in later life (Quran 48:2 acknowledges his seeking "
            "forgiveness) but prepares him for the specific role of prophet. The story is "
            "preserved in both Bukhari and Muslim's authentic chains, indicating strong "
            "transmission quality."
        ),
        "refutation": (
            "The purification narrative sits awkwardly beside Quran 48:2's explicit "
            "reference to Muhammad's sins requiring forgiveness. If the heart-surgery "
            "removed his sin-propensity before prophethood, what sins did he later have "
            "requiring forgiveness? The hadith also presupposes that every human child "
            "begins with a physical clot representing Satan's portion — a claim of "
            "cosmological-biological specificity that modern biology does not recognise. "
            "The story's only witness is Muhammad himself, reporting it post-facto about "
            "his own childhood — the same epistemic structure as any unfalsifiable "
            "visionary claim. A prophet-origin narrative authenticating prophecy by "
            "the prophet's own unverifiable testimony has not added evidence; it has "
            "restated the claim."
        ),
    },
    # 16 — Killing dhimmi fragrance
    {
        "anchor": "Whoever kills a protected non-Muslim will not smell the fragrance of Paradise",
        "response": (
            "The hadith is cited by modern apologists as evidence of Islamic protection for "
            "non-Muslim dhimmis: unjust killing of a protected person deprives the killer "
            "of paradise's fragrance for forty years — a severe spiritual consequence that "
            "deters mistreatment. Classical jurisprudence operationalised the protection "
            "through specific legal rules for dhimmis (right to religious practice, "
            "protection from violence, etc.), within the broader framework of the "
            "<em>dhimma</em> contract."
        ),
        "refutation": (
            "\"Unjust killing\" leaves open the broad category of \"just killing\" of non-"
            "Muslims, and classical jurisprudence filled that category with numerous "
            "exceptions: breach of the <em>dhimma</em>, insulting Islam, proselytising to "
            "Muslims, and more. The protection the hadith offers is narrow. The "
            "punishment is also telling: a fragrance-smell deprivation of forty years is "
            "spiritually trivial compared to the eternal hellfire for apostasy or "
            "polytheism. The ethical weighting is the issue: killing a non-Muslim unjustly "
            "costs you scent-of-paradise for forty years; leaving Islam costs you eternity. "
            "Proportion is not a feature the tradition took seriously across the "
            "Muslim/non-Muslim line."
        ),
    },
    # 17 — Mercy precedes wrath
    {
        "anchor": "Allah wrote upon His Throne: 'My mercy precedes my wrath.'",
        "response": (
            "Classical theology reads the hadith as emphasising mercy's primacy in divine "
            "character: Allah's default disposition is compassion, and wrath is the "
            "<em>consequence</em> of persistent human rejection, not a co-equal attribute. "
            "The hadith's structure (mercy precedes wrath) preserves the hierarchy of "
            "attributes even though both are real. Paradise is the natural destination for "
            "those who align with mercy; hell is the consequential destination for those "
            "who persistently reject it. Infinity of consequence (eternal hell) reflects "
            "the seriousness of the rejection, not a defeat of mercy."
        ),
        "refutation": (
            "Quantitative priority is meaningless against infinite consequence. \"Mercy "
            "precedes wrath\" might be theologically true in some abstract ordering, but "
            "the operational reality is that most of humanity has either never heard the "
            "Muhammad-specific message, or has encountered it and not converted for "
            "reasons that include honest intellectual disagreement — and classical Islamic "
            "theology places these people in hell forever. An \"infinite wrath\" "
            "co-existing with \"mercy precedes\" requires the \"precedes\" to be rhetorical, "
            "not operational. A mercy whose practical reach is fundamentally compromised "
            "by eternal punishment for unchosen cultural circumstances is a mercy whose "
            "self-description does not match its consequences."
        ),
    },
    # 18 — Annual campaign
    {
        "anchor": "Classical fiqh (Shafi'i, Hanbali) derived from Tirmidhi's jihad chapters:",
        "response": (
            "Apologists distinguish classical juristic rulings on annual campaigns "
            "(<em>ghazwa</em>) from the prophetic practice and Quranic text. The "
            "\"imam should campaign annually\" rule derives from the political-strategic "
            "thinking of specific classical jurists in specific imperial contexts, not from "
            "a direct hadith or verse. Modern Muslim-majority polities have long abandoned "
            "the rule as anachronistic. The classical juristic framework operated within "
            "the specific geopolitical reality of the early caliphate and does not bind "
            "modern practice."
        ),
        "refutation": (
            "The classical jurists did not invent the annual-campaign rule from nothing — "
            "they derived it from the cadence of Muhammad's own military practice and the "
            "broader Quranic legal framework that imagined perpetual engagement with "
            "non-Muslim territory (<em>Dar al-Harb</em>). The modern \"abandoned as "
            "anachronistic\" framing is a de facto reform that requires reading classical "
            "law against its own grain. A political theology that scheduled military "
            "activity as a religious obligation did not merely permit violence; it "
            "integrated it into the religious calendar. That modern Muslims do not do this "
            "is a welcome departure, but the departure does not rehabilitate the "
            "classical jurisprudence it departs from."
        ),
    },
    # 19 — Kill both doing act of Lut (Tirmidhi variant)
    {
        "anchor": "Whoever you find doing the act of the people of Lut — kill the one doing",
        "response": (
            "Apologists argue the hadith's <em>hasan</em> (rather than <em>sahih</em>) "
            "grading permits some critical distance, and classical jurisprudence actually "
            "varied on the penalty — some schools (Hanafi) prescribed imprisonment or "
            "<em>ta'zir</em> (discretionary punishment), not death, while others required "
            "the near-impossible four-witness evidentiary bar that makes conviction "
            "practically unachievable. The Quran itself does not supply a specific "
            "criminal penalty, which some modern scholars argue is evidence the tradition "
            "never intended capital punishment."
        ),
        "refutation": (
            "The schools did vary on exact penalty but the majority — Maliki, Shafi'i, "
            "Hanbali, and later Hanafi positions — codified death as the penalty, which is "
            "why contemporary Muslim-majority states applying classical jurisprudence "
            "(Iran, Saudi Arabia, Afghanistan, Brunei) still execute for same-sex acts. The "
            "hadith's function was to supply the death penalty the Quran does not supply, "
            "and whatever the chain grade, it has served that function for 1,400 years. "
            "The \"Quran is silent\" observation is accurate but is a problem rather than a "
            "defense: it means the scriptural basis for capital punishment on consensual "
            "private adult intimacy rests on a hadith of less than maximum authority — and "
            "that is the warrant on which people are killed today."
        ),
    },
    # 20 — Slave marriage without permission
    {
        "anchor": "Any slave who marries without his master's permission, his marriage is invalid",
        "response": (
            "Classical apologetics frames the permission-requirement as <em>protection</em> "
            "of both slave and master: slaves had limited capacity to support a household "
            "independently, so marriage without the master's economic guarantee could "
            "leave both spouses and any children in dire condition. The master's consent "
            "functioned as the slave's guardian (<em>wali</em>) in the same way fathers "
            "served as guardians for free women. The \"fornicator\" language is rhetorical "
            "emphasis on the invalidity of the unauthorised union, not a literal criminal "
            "charge."
        ),
        "refutation": (
            "The \"guardian as protection\" analogy is flawed: fathers (as <em>awliya'</em> "
            "for their daughters) were presumed to act in the daughter's interests; "
            "masters controlling slaves' marriages were presumed to act in the master's "
            "economic interests. The hadith's \"fornicator\" label is legally consequential "
            "— an invalid marriage produces what the law calls <em>zina</em> (fornication), "
            "with real penal consequences in classical Islamic jurisprudence. The "
            "institution the hadith regulates is ownership of human beings whose sexual "
            "and marital lives were the master's property to control. A religion whose "
            "marriage code starts with the master's permission has rendered the slave's "
            "relationship with their beloved a privilege the master can withhold — and "
            "criminalised their love if the withholding is defied."
        ),
    },
    # 21 — Jizya permanence
    {
        "anchor": "Two Qiblahs in one land are of no benefit",
        "response": (
            "Apologists argue the jizya framework offered protected status "
            "(<em>dhimma</em>) under specific conditions — the taxed non-Muslim community "
            "retained religious practice, property, and judicial autonomy in exchange for "
            "the tax. Historical reality across Muslim-majority societies varied: periods "
            "of genuine coexistence (Al-Andalus, Abbasid Baghdad) alternated with periods "
            "of persecution, but the legal framework itself was more accommodating than "
            "the pre-modern alternatives (Byzantine restrictions on Jews, European "
            "expulsions). The conversion incentive was no more coercive than many "
            "comparable arrangements in the period."
        ),
        "refutation": (
            "\"More accommodating than comparable arrangements\" is historical relativism, "
            "not ethics. A system that taxes religious identity — with exit only through "
            "conversion — is a system whose \"freedom of worship\" is conditional on "
            "fiscal submission. The hadith's prohibition on preaching or practicing "
            "non-Muslim religion openly adds public-space exclusion to the fiscal "
            "pressure. The dhimmi framework embedded religious second-class status into "
            "eternal law, which is why its application has never produced "
            "full equality even in the better periods. \"Freedom only in private, and "
            "charged admission even then\" is an accurate description of what the "
            "framework actually is, and comparisons to Byzantine law do not rehabilitate "
            "its structure."
        ),
    },
    # 22 — Faces blackened/whitened
    {
        "anchor": "On the Day [some] faces will turn white and [some] faces will turn black.",
        "response": (
            "Classical apologetics emphasises the colour imagery as purely spiritual — "
            "\"white\" signifying purity and \"black\" signifying moral stain, consistent "
            "with symbolic usages in many cultures. The language does not refer to skin "
            "tone or racial category; it is a moral-spiritual metaphor. Apologists note "
            "that the Quran explicitly rejects racial hierarchy (49:13) and that early "
            "Islamic history included prominent Black figures (Bilal, Mahmud Khan, "
            "countless scholars) with full community status."
        ),
        "refutation": (
            "\"Spiritual metaphor only\" is the standard defense, but the metaphor's choice "
            "is what requires accounting. Salvation is white; damnation is black — in a "
            "region and period where the colour imagery would inevitably carry some racial "
            "association. Arab supremacist polemic across Islamic history has cited this "
            "and parallel verses in anti-Black rhetoric, treating the spiritual metaphor "
            "as extending to the literal. A divine author writing an eternal scripture "
            "would presumably anticipate how colour metaphors for moral states would be "
            "read across cultures and eras, and would either avoid them or gloss them "
            "carefully. The Quran does neither. The \"prominent Black figures\" "
            "counter-examples are real but do not remove the scriptural image's own "
            "colour-coding."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/tirmidhi.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

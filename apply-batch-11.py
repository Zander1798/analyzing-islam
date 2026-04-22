#!/usr/bin/env python3
"""Batch 11: First 40 Bukhari Strong entries."""
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
        "anchor": "If a house fly falls in the drink of anyone of you",
        "response": (
            "Apologists cite studies on bacteriophages attached to fly wings as potential "
            "retrofit for the hadith: modern research has identified virus-like agents on "
            "insect exteriors, and some apologetic writers interpret \"disease on one wing, "
            "cure on the other\" as anticipating this antimicrobial property. The hadith is "
            "reframed as pre-scientific microbiology communicated in 7th-century vocabulary."
        ),
        "refutation": (
            "The bacteriophage retrofit is not what the hadith says. It says: <em>dip the "
            "fly in, because one wing has disease and the other has cure</em> — a specific "
            "treatment protocol whose medical content modern biology does not support. "
            "Flies carry dozens of pathogens (typhoid, cholera, dysentery, E. coli); "
            "submerging one into a drink spreads those pathogens through the liquid, not "
            "neutralises them. No classical commentator extracted the bacteriophage reading "
            "before 20th-century microbiology made it possible to retrofit. The pattern of "
            "\"scientific miracle after the science settles\" is the signature of "
            "compatibility reasoning, not prediction."
        ),
    },
    {
        "anchor": "Some people of 'Ukl or 'Uraina tribe came to Medina",
        "response": (
            "Apologists argue the camel-urine prescription was situational — a specific "
            "therapeutic recommendation using what was available in the desert, not a "
            "standing medical endorsement. The subsequent mutilation of the 'Uraynans is "
            "framed as lawful punishment for their murder of the herdsmen and theft of the "
            "camels after their treatment, not arbitrary cruelty. The hadith preserves a "
            "sequence of justice: hospitality, betrayal, trial, penalty."
        ),
        "refutation": (
            "The therapeutic framing treats Muhammad as a 7th-century folk physician giving "
            "culturally-appropriate advice — fine as a historical observation, fatal as a "
            "claim about divine medical authority. WHO has specifically warned against "
            "camel-urine consumption due to MERS-CoV transmission. The punishment is "
            "separate and independently troubling: mutilating hands and feet, leaving the "
            "men to die of thirst in the sun, was ruled excessive even by some classical "
            "jurists who added procedural limits. \"Justice sequence\" does not rehabilitate "
            "medical advice that harms or punishment that tortures."
        ),
    },
    {
        "anchor": "A person was mentioned before the Prophet (pbuh) and he was told that he ha",
        "response": (
            "Classical apologetics treats the \"Satan urinated in his ear\" language as "
            "idiomatic rebuke for oversleeping and missing dawn prayer — rhetorical "
            "intensification, not anatomical claim. Modern apologists emphasise the hadith's "
            "pedagogical point: prayer-punctuality matters enough that the tradition uses "
            "vivid imagery to drive it home. The anatomical reading is ruled out in "
            "sophisticated theological discourse."
        ),
        "refutation": (
            "Classical commentators (Ibn Hajar, al-Nawawi) debated whether Satan's urine "
            "is physical or symbolic, which means the plain reading was physical enough to "
            "require substantive theological argument. Cross-collection <em>sahih</em> "
            "attestation in Bukhari, Abu Dawud, and Ibn Majah establishes the claim as "
            "authoritative teaching, not folk aside. A tradition in which Satan has a "
            "urinary tract and targets the ears of the negligent has preserved folk "
            "demonology at the highest authority level — the \"idiomatic rhetoric\" "
            "framing is modern comfort, not the classical reading."
        ),
    },
    {
        "anchor": "The sun and the moon do not eclipse because of someone's death.",
        "response": (
            "Apologists celebrate the eclipse hadith as evidence of Muhammad's anti-"
            "superstition: he refuses to attribute celestial events to human affairs, "
            "directing people instead to prayer and remembrance. The separate \"sun under "
            "the Throne\" hadith is cast as metaphorical description of divine "
            "sovereignty over cosmic bodies, not a physical claim about the sun's "
            "trajectory."
        ),
        "refutation": (
            "The two hadiths are in structural tension: one treats the sun as a "
            "regular astronomical body following natural law (anti-superstition), the "
            "other treats it as a personal agent that moves to prostrate beneath Allah's "
            "throne each night. The metaphorical reading of the latter is retrofitted — "
            "classical commentators (al-Nawawi, Ibn Hajar) read the sun's prostration "
            "literally, as a physical motion. The \"progress\" the eclipse hadith "
            "represents is real but partial, and the tradition did not complete the "
            "correction — both pictures are preserved as authoritative, which is "
            "exactly the combination a human author reworking inherited folk "
            "cosmology would produce."
        ),
    },
    {
        "anchor": "The Prophet used to visit all his wives in a round",
        "response": (
            "Classical apologetics frames the \"strength of thirty men\" report as "
            "expression of the Prophet's divine-blessed vitality — a miraculous "
            "capacity given him specifically for his multi-wife responsibilities. The "
            "companions preserved the detail affectionately, as evidence of "
            "prophetic excellence rather than as something shameful. Modern "
            "apologists situate the report within the 7th-century context where "
            "sexual capacity was a sign of health and blessing."
        ),
        "refutation": (
            "The \"affection of companions\" does not address what the hadith "
            "communicates: sexual performance as prophetic attribute. A religion whose "
            "founder's most-famous companion preserved a report of his sexual rounds "
            "as praise has embedded the category into its devotional literature. The "
            "\"divinely-blessed vitality\" framing is exactly the apologetic frame — "
            "but it treats as theologically load-bearing a claim that would be "
            "embarrassing about any other religious figure. The asymmetry of "
            "embarrassment tracks exactly whose reputation is being defended."
        ),
    },
    {
        "anchor": "Once the Prophet was bewitched so that he began to imagine",
        "response": (
            "Classical theology treats the bewitchment as real supernatural attack "
            "that affected Muhammad's mundane perception but not his prophetic "
            "function — no revelation from that period was corrupted. Surah al-Falaq "
            "and al-Nas were revealed specifically as protective response, "
            "demonstrating Allah's vigilance. The episode is framed as Muhammad's "
            "humanity in the face of an evil attempt that ultimately failed."
        ),
        "refutation": (
            "The \"worldly but not prophetic\" distinction is not in the hadith; it is "
            "a modern theological patch. If a sorcerer could plant false memories in "
            "Muhammad for months, the claim that no revelation was tainted cannot be "
            "verified — it is stipulated by the same tradition that documents the "
            "vulnerability. Quran 5:67's promise that Allah will \"protect you from "
            "the people\" is directly undermined. The compartmentalisation defense "
            "requires a precise cognitive/prophetic distinction the 7th-century text "
            "does not supply."
        ),
    },
    {
        "anchor": "I have been sent with the shortest expressions bearing",
        "response": (
            "Classical apologetics argues that \"victory with terror\" (<em>ru'b</em>) "
            "refers to divinely-instilled dread in the hearts of enemies before battle — "
            "psychological advantage granted by Allah, not a policy of deliberate "
            "terrorism against civilians. The terror is in the enemy's heart, not "
            "Muslim tactic. Modern apologists contrast this with contemporary "
            "terrorism, which deliberately targets non-combatants — a distinction "
            "classical Islamic law preserved."
        ),
        "refutation": (
            "\"Divine dread\" or tactical, the category the Prophet's biography "
            "credits is <em>terror</em> as source of victory — the Arabic word is "
            "<em>ru'b</em>, whose meaning includes both fear and the instruments of "
            "producing it. Classical Islamic military doctrine (al-Mawardi, al-"
            "Shaybani) developed the verse into active principles of projecting "
            "fear, including exemplary executions and enemy-facing displays. The "
            "modern jihadist citation of this hadith is not misreading; it is "
            "application of a tradition the classical jurisprudence systematically "
            "developed."
        ),
    },
    {
        "anchor": "When the tribe of Bani Quraiza was ready to accept Sad's judgment",
        "response": (
            "The standard apologetic frames the Qurayza execution as Sa'd ibn Mu'adh's "
            "ruling applying the tribe's own Torah law (Deuteronomy 20:13-14) to a "
            "community that had breached its treaty during the Battle of the Trench "
            "— treason, not mere religious difference. Muhammad's endorsement of the "
            "judgment (\"Allah's judgment\") is framed as recognition that the "
            "sentence was correct under the tribe's legal tradition, not an "
            "expansion of Islamic law."
        ),
        "refutation": (
            "The \"their own law\" framing is questionable history (the Deuteronomic "
            "rule applied to besieged cities that refused peace, not surrendered "
            "internal allies) and shifts responsibility to a judge hand-picked by "
            "Muhammad for his known severity. The Quranic endorsement (33:26-27) "
            "treats the outcome as divine provision, crediting Allah with the "
            "killing. \"Allah's judgment\" is Muhammad's own endorsement, making the "
            "prophetic authorisation explicit. A day-long execution of hundreds of "
            "surrendered prisoners by the Prophet's community, theologically "
            "credited, is not improved by rewriting the legal framework that "
            "delivered it."
        ),
    },
    {
        "anchor": "'Ali replied, 'No, except Allah's Book or the power of understanding",
        "response": (
            "Classical apologetics narrows the hadith to public apostasy combined with "
            "armed rebellion, not private belief change. Modern reformists cite Quran "
            "2:256's principle against compulsion and argue the death penalty reflects "
            "specific 7th-century political circumstances rather than eternal rule. "
            "Several Muslim-majority states have removed apostasy from criminal law."
        ),
        "refutation": (
            "The classical consensus treated apostasy itself as capital without "
            "requiring additional hostility. Six canonical collections preserve the "
            "command, which makes the \"fringe hadith\" dismissal impossible. "
            "Current enforcement in Saudi Arabia, Iran, Mauritania applies to private "
            "belief change. The 2:256 tension is real; the classical solution was to "
            "abrogate 2:256 — which modern apologists quietly abandon while still "
            "citing it as evidence of tolerance. \"No compulsion\" and \"death for "
            "leaving\" cannot coherently both operate."
        ),
    },
    {
        "anchor": "In very hot weather delay the Zuhr prayer till it becomes",
        "response": (
            "Classical apologetics treats \"hell's breath\" as poetic theological "
            "imagery — associating discomfort with eschatological reality to "
            "encourage spiritual awareness. The practical instruction (delay Zuhr in "
            "summer) is sound advice regardless of the metaphysical framing. Modern "
            "apologists argue the hadith's rhetorical register is pedagogical, not "
            "cosmological."
        ),
        "refutation": (
            "\"Poetic imagery\" is the general apologetic defense for every hadith "
            "making a falsifiable physical claim. Classical commentators read the "
            "hell's-breath attribution literally as causal cosmology, and the "
            "tradition preserves it as authoritative teaching. Seasonal temperature "
            "variation is caused by Earth's axial tilt, not by hell's respiratory "
            "cycle. The \"pedagogical\" framing works for a parable; it does not "
            "explain a claimed-factual report about why summers are hot, preserved "
            "in the most authoritative Sunni collection."
        ),
    },
    {
        "anchor": "The Hour will not be established until the son of Mary",
        "response": (
            "Classical eschatology treats Jesus's return as restoration — the true "
            "Islamic Jesus correcting Christian distortions (crucifixion-belief, "
            "cross-veneration, trinitarianism) and leading humanity to the "
            "monotheism he originally taught. The symbols he destroys (cross, swine) "
            "represent the deviations Christians added; his destruction of them is "
            "theological rectification."
        ),
        "refutation": (
            "\"Restoration\" means the Christian messiah returns to dismantle "
            "Christianity's symbols, abolish the <em>dhimmi</em> tax (forced "
            "conversion or war), and establish Islamic universalism. That is "
            "eschatological supersessionism, not reconciliation. A prophecy in "
            "which Jesus destroys the symbols of his own tradition and collapses "
            "alternative religious options for non-Muslims has absorbed "
            "Christianity only to annul it. The \"rectification\" framing is "
            "Islamic self-description; from any other vantage it is the "
            "eschatological elimination of a rival faith."
        ),
    },
    {
        "anchor": "Shall I not tell you about the Dajjal a story of which",
        "response": (
            "Classical apologetics treats the Dajjal as genuine prophetic warning "
            "about a future deceiver whose supernatural powers will test the faith "
            "of believers at the end times. The distinctive physical features (one-"
            "eyed, the letter k-f-r written on his forehead) are given as "
            "recognition criteria. The parallels to Zoroastrian and Jewish "
            "apocalyptic figures reflect common human apprehension of cosmic "
            "deception rather than literary borrowing."
        ),
        "refutation": (
            "The \"common apprehension\" framing grants theological legitimacy to "
            "Zoroastrian Pish-Dâdak and Jewish apocalyptic anti-messiahs as "
            "preserving genuine cosmic information — at which point the "
            "distinctiveness of Islamic eschatology dissolves. The Dajjal's "
            "features are culturally specific to the Near Eastern apocalyptic "
            "imagination of the 3rd–7th centuries; the parallels to the Syriac "
            "Alexander Legend, Zoroastrian end-time figures, and Jewish Merkabah "
            "anti-messiah figures are direct. A religion whose end-time antagonist "
            "is an amalgam of surrounding traditions' monsters has preserved its "
            "eschatology in their vocabulary."
        ),
    },
    {
        "anchor": "If a husband calls his wife to his bed (i.e. to have",
        "response": (
            "Classical apologetics reads the hadith as addressing arbitrary refusal "
            "— the angelic curse applies only when the wife's refusal lacks "
            "legitimate reason (illness, menstruation, pain). Modern apologists "
            "situate the hadith within a broader marital ethic of mutual kindness "
            "(<em>mu'asharat bi'l-ma'ruf</em>) that qualifies the prescription to "
            "specific abusive-refusal cases."
        ),
        "refutation": (
            "The \"legitimate reasons\" qualification is juristically elaborated; the "
            "hadith's plain text does not include it. The curse falls on the wife "
            "whose refusal causes the husband to sleep angry, with the standard for "
            "legitimacy being the husband's mood. Classical jurisprudence extracted "
            "from this hadith the doctrine of <em>tamkeen</em> (sexual access as "
            "enforceable husbandly right), which in several classical formulations "
            "effectively removes wife's consent from the marriage relation. A "
            "heavens whose angels curse a wife for saying no has sanctified "
            "marital coercion."
        ),
    },
    {
        "anchor": "The Prophet forbade laughing at a person who passes wind",
        "response": (
            "The apologetic reading frames the hadith as a <em>restriction</em> "
            "on wife-beating: the camel analogy is a rhetorical intensifier pointing "
            "toward the incongruity of beating a wife you then sleep with. The "
            "deeper principle being gestured at is that marital violence is "
            "inappropriate, with the ironic structure of the remark doing the "
            "moral work."
        ),
        "refutation": (
            "The hadith does not say \"don't beat your wife\"; it says \"don't "
            "beat your wife <em>like a stallion camel</em>\" — don't use the "
            "specific severe beating reserved for difficult animals. The structure "
            "preserves wife-beating as category while adjusting its intensity. The "
            "additional rhetorical weight (\"and then sleep with her the same "
            "night\") draws attention to the awkward combination of violence and "
            "intimacy, but does not prohibit the violence itself. The apologetic "
            "reads the hadith as making a point it does not make."
        ),
    },
    {
        "anchor": "The angel of death was sent to Moses and when he went to him",
        "response": (
            "Classical theology reads the hadith as pedagogical narrative about "
            "prophetic reluctance to die — Moses's resistance is framed as moral "
            "teaching about the preciousness of life, with the angel's eye "
            "restoration (by Allah) demonstrating divine sovereignty over both "
            "prophet and angel. The physical details are not central; the moral "
            "lesson is."
        ),
        "refutation": (
            "The physical details are what the hadith preserves: a prophet of "
            "Allah slapping an angel and gouging out his eye, requiring divine "
            "restoration. This is a specific story with specific physical content "
            "that classical commentators debated as literal — including whether "
            "angels are susceptible to physical injury (theologically awkward) "
            "and how Allah restored the angel (requiring supplementary miracle). "
            "\"Pedagogical narrative\" is retrofit; the tradition preserved the "
            "story because its 7th-century audience found it meaningful, and its "
            "implications (prophets assaulting divinely-commanded angels) are "
            "more difficult than the lesson they support."
        ),
    },
    {
        "anchor": "No Muslim should be killed in retaliation for killing a disbeliever",
        "response": (
            "Classical apologetics argues the rule reflects the specific political "
            "context of the early Islamic state — Muslim life under the pact had "
            "higher political value because Muslims were citizens of the ummah "
            "while non-Muslims held protected-foreigner status. The rule is "
            "operational, not a statement about ultimate human dignity. Modern "
            "apologists emphasise that <em>qisas</em> (equal retribution) applies "
            "to all Muslim-on-Muslim killing."
        ),
        "refutation": (
            "The \"operational not ultimate\" framing describes what the rule does "
            "without defending it: a legal system that treats the killing of a "
            "non-Muslim as a lesser offense than the killing of a Muslim has "
            "structurally devalued non-Muslim life. Classical <em>diyya</em> "
            "(blood-money) valuations followed the same logic — Jewish/Christian "
            "lives were worth half a Muslim's in Shafi'i/Hanbali schools; Zoroastrian "
            "lives worth even less. These schedules are real legal history, not "
            "modern slander. A religion whose founding legal framework tiered "
            "blood-money by faith has embedded religious hierarchy into the "
            "criminal-law definition of human worth."
        ),
    },
    {
        "anchor": "You (true Muslims) are the best of peoples ever raised up for m",
        "response": (
            "Classical apologetics reads \"chains\" as forceful guidance toward "
            "moral truth — the <em>tarbiyah</em> (educational raising-up) of "
            "humanity to monotheism and righteousness. The image is not literal "
            "slave-chains but theological: the Muslim community's role is to "
            "bring humanity from disbelief to faith, with \"chains\" as metaphor "
            "for firm instruction."
        ),
        "refutation": (
            "The \"firm instruction\" reading is retrofit — classical tafsir "
            "(Tabari, Ibn Kathir) read the image literally as captives brought "
            "toward conversion. The combination of \"best of peoples\" with the "
            "chains-until-conversion motif is the theological root of the "
            "historical practice where converted war-captives were freed or "
            "integrated while non-converting captives remained enslaved. The "
            "framing of Muslim superiority as the mission of bringing others in "
            "chains is not incidental rhetoric; it is the exegetical logic by "
            "which conquest-plus-conversion became theologically meritorious."
        ),
    },
    {
        "anchor": "Listen and obey (your chief) even if an Ethiopian whose",
        "response": (
            "Apologists frame the hadith as anti-racist: the Prophet is affirming "
            "that obedience to legitimate leadership transcends ethnicity, and "
            "that even a Black leader (outside the Arab norm of the time) must "
            "be obeyed. The \"head like a raisin\" phrase is cultural-descriptive "
            "for tightly-coiled hair, not denigrating. Black figures in early "
            "Islam (Bilal, Mahmud Khan) held prominent positions, supporting "
            "this reading."
        ),
        "refutation": (
            "The rhetorical structure is diagnostic: the sentence asks listeners "
            "to obey <em>even if</em> the leader is Ethiopian — which presupposes "
            "that an Ethiopian leader would be startling or undesirable. A "
            "genuinely non-ethnic framing would say \"obey your leader whoever "
            "he is\" without invoking the Black leader as the edge case. The "
            "\"head like a raisin\" phrase is physical description used in a "
            "deprecatory context, whatever its literal meaning. The presence of "
            "Black figures in early Islam is real, and is consistent with "
            "Arab-Islamic societies that recognised Black individuals while "
            "retaining hierarchical race-attitudes. The hadith's framing tells us "
            "about the latter."
        ),
    },
    {
        "anchor": "And whoever sees me in a dream then surely he has see",
        "response": (
            "Classical theology treats prophetic dreams as authentic — Muhammad's "
            "form cannot be impersonated by Satan in dream-vision, which provides "
            "a legitimate (if rare) channel of spiritual experience for believers. "
            "The hadith is not an invitation to build doctrine on dreams but a "
            "reassurance that genuine prophetic visitations, when they occur, can "
            "be trusted. Classical scholars (al-Nawawi) developed strict criteria "
            "for distinguishing authentic prophetic dreams from other experience."
        ),
        "refutation": (
            "The \"strict criteria\" are precisely what the tradition has been "
            "unable to establish, which is why 1,400 years of dream-based "
            "religious claims have produced competing authorities: Sufi saints "
            "claiming prophetic confirmation of their teachings, Mahdi-claimants "
            "citing dream-endorsements, reformers dreaming justification for "
            "their programs. If dreams of Muhammad are genuinely authentic, "
            "the tradition has no mechanism to adjudicate between conflicting "
            "dream-reports — which means the claim functions as authority-"
            "inflation for whoever reports the dream. The hadith's rule "
            "creates exactly the religious-authority structure it pretends to "
            "prevent."
        ),
    },
    {
        "anchor": "When will the Hour be established",
        "response": (
            "Classical apologetics offers two interpretations of \"slave woman "
            "gives birth to her master\": (1) the slave's daughter, upon "
            "emancipation, becomes free and inherits authority over her mother "
            "— demonstrating social upheaval; (2) the \"master\" is the slave's "
            "biological father (through concubinage), and the son's status is "
            "inverted by inheritance rules. Both readings treat the phrase as "
            "apocalyptic imagery signaling the world's disorder, not an "
            "endorsement of slavery."
        ),
        "refutation": (
            "Both readings require slavery as background framework to be "
            "intelligible — the apocalyptic force of the phrase depends on "
            "slavery being the normal condition against which the disruption "
            "is measured. A sign of the end times that only works if "
            "institutional slavery is the baseline is a sign that has "
            "preserved the institution inside its eschatological imagination. "
            "If Islam genuinely intended abolition, its end-times vocabulary "
            "should not require slavery as the normal order being disrupted."
        ),
    },
    {
        "anchor": "'Umar came near the Black Stone and kissed it",
        "response": (
            "Classical apologetics treats the Black Stone ritual as continuity "
            "with Abrahamic monotheism — the Stone was a marker set by Abraham "
            "and Ishmael when they built the Ka'ba, and its veneration is "
            "obedience to prophetic tradition, not stone-worship. Umar's "
            "acknowledgment that the stone itself has no power is evidence of "
            "the ritual's non-idolatrous character: it is followed because of "
            "prophetic precedent, not because of the stone's intrinsic power."
        ),
        "refutation": (
            "Umar's acknowledgment is exactly the admission that makes the "
            "ritual awkward: he explicitly grants that he is performing a "
            "stone-veneration act that would be pagan in any other context, "
            "and defends it only by appeal to Muhammad's practice. That is "
            "the structural definition of a pagan ritual preserved under "
            "monotheist framing. The \"Abrahamic origin\" claim is an "
            "intra-Islamic assertion without independent archaeological or "
            "historical support; the Black Stone was venerated by pre-"
            "Islamic Arabian polytheists at the Ka'ba long before Islam, "
            "and Islam retained the practice while substituting theology."
        ),
    },
    {
        "anchor": "Al-Buraq, a white animal, smaller than a mule and bigger than a donkey",
        "response": (
            "Classical theology treats the Isra and Mi'raj as genuine miraculous "
            "journey — a one-time supernatural event whose physical impossibilities "
            "are the point (if it were physically possible, it would not be a "
            "miracle). The Buraq's specific characteristics, the seven heavens, the "
            "prophetic meetings, and the negotiations over daily prayer count are "
            "all preserved as authentic prophetic experience."
        ),
        "refutation": (
            "The \"miraculous therefore impossible is allowed\" defense explains "
            "everything, which means it discriminates nothing. A supernatural "
            "journey whose form is identical to Zoroastrian Arda Viraf (9th-"
            "century documentation of pre-Islamic traditions), Jewish Merkabah "
            "mysticism, and Christian apocalyptic ascension narratives has "
            "preserved the apocalyptic ascent genre of the Near East. The "
            "\"seven heavens\" architecture is Mesopotamian cosmology, not "
            "physics. The Buraq is structurally identical to earlier "
            "divine-mount traditions. A miraculous journey that looks exactly "
            "like the tradition it claims to transcend has participated in the "
            "tradition rather than transcended it."
        ),
    },
    {
        "anchor": "Healing is in three things: A gulp of honey, cupping",
        "response": (
            "Classical apologetics argues the hadith identifies three specific "
            "remedial categories relevant to the Arabian context, not a universal "
            "medical inventory. Honey (nutrition, antibacterial), cupping (blood "
            "regulation, widely practiced historically), and cautery (infection "
            "control by heat) were all reasonable 7th-century treatments. Modern "
            "apologists defend honey's antimicrobial properties as demonstrable, "
            "giving the hadith partial vindication."
        ),
        "refutation": (
            "\"Healing is in three things\" is not \"three useful things are "
            "among the many healings\"; it is a universal framing that excludes "
            "everything else. The list omits surgery, antibiotics, vaccines, "
            "antiseptics, and the entire modern medical repertoire. Branding "
            "with fire as general therapy is both ineffective and harmful for "
            "most conditions; cupping has limited evidence-based indications "
            "despite widespread use. A prophetic medical claim of universal "
            "scope ('healing is in these three') from a divinely-informed "
            "source should not exclude modern medicine wholesale. The "
            "apologetic that limits 'three things' to the 7th-century context "
            "concedes that the hadith is historically contingent."
        ),
    },
    {
        "anchor": "The dead person is tortured by the crying of his relatives.",
        "response": (
            "Aisha's own objection (preserved in the canon) is cited by apologists "
            "as evidence of the tradition's honest self-correction: the hadith "
            "troubled early Muslims, and Aisha raised the obvious conflict with "
            "Quran 6:164 (\"no bearer of burdens bears another's burden\"). "
            "Classical scholars harmonised by restricting the hadith's scope to "
            "the deceased who explicitly wished for lamentation while alive, or "
            "who encouraged it."
        ),
        "refutation": (
            "Aisha's objection is preserved — which is a point for transmission "
            "honesty, but it establishes that a canonical hadith contradicts the "
            "Quran. The \"prior wish\" harmonisation is juristic patching not in "
            "the hadith's text. A tradition whose canonical material requires "
            "harmonisation with its own scripture by the Prophet's wife has "
            "conceded that its authentic materials are not all equally reliable "
            "— but the canonical framework treats them as if they are. The "
            "community's preservation of both hadith and counter-hadith is "
            "symptomatic of the cumulative nature of the source material, not "
            "evidence of sophistication."
        ),
    },
    {
        "anchor": "everyone will have two wives from the houris",
        "response": (
            "Classical apologetics treats the paradise descriptions as vivid "
            "symbolism for the unimaginable joys awaiting believers — the "
            "\"transparent flesh\" is metaphor for purity and beauty beyond "
            "earthly categories, not a literal anatomical claim. The houris "
            "function as theological imagery for divine abundance, with the "
            "Quranic caveat that what paradise offers \"no eye has seen\" "
            "indicating the descriptions are pedagogical, not reportorial."
        ),
        "refutation": (
            "The symbolism reading cannot be sustained across the combined "
            "Quranic and hadith corpus: hadith literature gives extensive "
            "specific physical descriptions (Tirmidhi 1663, Bukhari 3327) that "
            "make no sense as allegory. Classical tafsir read the passages "
            "literally. The gender asymmetry is stark — specific sexual reward "
            "for men, with paradise for women described primarily as reunion "
            "with their earthly husbands. The \"transparent flesh\" aesthetic "
            "is the imagination of pre-modern Arab culture picturing perfect "
            "femininity; it tells us about the culture that produced the "
            "image, not about the cosmos."
        ),
    },
    {
        "anchor": "The Prophet was asked about the offspring of the pagans",
        "response": (
            "Classical apologetics argues the hadith addresses accidental "
            "civilian casualties in unavoidable night-raids, not deliberate "
            "killing of non-combatants. The ruling places civilian deaths "
            "in the category of battle-contingency rather than authorized "
            "target. Modern apologetic readings cite Muhammad's later "
            "prohibitions on killing women and children in specific contexts "
            "as evidence of progressive refinement toward civilian protection."
        ),
        "refutation": (
            "The hadith's phrase — civilians \"from them\" (the enemy "
            "group) — is an ownership category, not a protection. Classifying "
            "women and children of enemy groups as belonging-to-them is "
            "exactly how collective guilt attaches in pre-modern warfare, and "
            "the ruling operationally permits their deaths during operations. "
            "Later prohibitions do exist but did not consistently govern "
            "classical military jurisprudence, which permitted civilian "
            "casualties under various conditions. The hadith is the textual "
            "warrant for that permissiveness."
        ),
    },
    {
        "anchor": "Then he will be hit with an iron hammer between his two ears",
        "response": (
            "Classical theology treats grave-torture as real eschatological "
            "reality operating in a dimension between death and resurrection "
            "— the body is <em>not</em> present in the grave in the normal "
            "physical sense; rather, the soul experiences the punishment "
            "described in physical vocabulary because human language has no "
            "other register. The iron hammer is symbolic of specific "
            "spiritual consequence, not a physical implement."
        ),
        "refutation": (
            "If the body is not present and the hammer is symbolic, the "
            "vivid physical detail the hadith preserves (iron hammer "
            "between the ears, supernatural scream audible to specified "
            "species) is rhetorical horror, not spiritual teaching. The "
            "\"symbolic\" reading is the modern theological retreat from "
            "the classical tradition's literal acceptance of grave-torture "
            "physics. Classical commentators (al-Tirmidhi, Ibn Hajar) "
            "debated whether the body is reconstituted for the punishment — "
            "which only makes sense if they took the hammer literally. The "
            "tradition preserved the specific physical details because its "
            "audience found them theologically meaningful, and the "
            "spiritualising retreat is retrofitting, not classical "
            "doctrine."
        ),
    },
    {
        "anchor": "Noah will reply: 'Today my Lord has become so angry",
        "response": (
            "Classical eschatology reads the intercession hadith as "
            "establishing Muhammad's unique role on the Day of Judgment — "
            "other prophets are framed as too humble or conscious of their "
            "own shortfalls to intercede, leaving the intercessory function "
            "to Muhammad alone. This is prophetic hierarchy within the "
            "overall framework of Allah's ultimate mercy, not a claim that "
            "other prophets are sinful or unable. The hadith's function is "
            "to establish Muhammad's distinctive eschatological role."
        ),
        "refutation": (
            "The structure depicts previous prophets citing specific sins "
            "(Noah's prayer, Abraham's lies, Moses's killing, Jesus's "
            "disclaiming divinity) as reasons they cannot intercede — which "
            "makes each previous prophet a limited case, with Muhammad the "
            "unique full intercessor. That restoration of the intercessory "
            "function is exactly the priest-mediator role Islam elsewhere "
            "denies. The hadith establishes for Muhammad what the Quran "
            "elsewhere rejects about Christian ecclesiology. The "
            "\"prophetic hierarchy\" framing is a theological structure "
            "that substitutes one mediator for another, not the "
            "abolition of mediation Islam claims."
        ),
    },
    {
        "anchor": "This Quran has been revealed to be recited in seven different",
        "response": (
            "Classical tradition holds that the seven <em>ahruf</em> were "
            "divinely-sanctioned dialect variations accommodating the "
            "linguistic diversity of Arabian tribes. Uthman's standardisation "
            "preserved the core consonantal skeleton while permitting the "
            "canonical <em>qira'at</em> (recitation modes) as legitimate "
            "variations. Modern apologists argue this is evidence of "
            "Quranic flexibility and preservation within diversity, not "
            "textual failure."
        ),
        "refutation": (
            "Seven divinely-sanctioned variants directly undermine the "
            "\"one Quran\" claim. If original revelation had seven forms, "
            "the text Uthman standardised was already a choice among "
            "possible forms — meaning the current text is not the full "
            "revealed material, just one canonical slice. Uthman's "
            "burning of competing codices (including those of respected "
            "companions like Ibn Masud and Ubayy ibn Ka'b) is how textual "
            "uniformity was produced. The claim of pristine preservation "
            "and the practice of producing uniformity through fire cannot "
            "both be honest descriptions of the same history."
        ),
    },
    {
        "anchor": "Allah enjoined fifty prayers on my followers",
        "response": (
            "Classical theology reads the fifty-prayers narrative as "
            "pedagogical demonstration of divine mercy: Allah's initial "
            "prescription was pedagogical (showing the community what "
            "could theoretically be required), with the reduction to five "
            "demonstrating Allah's consideration for human capacity. "
            "Moses's role is not correction of Allah but participation in "
            "the lesson about mercy being built into the revelation."
        ),
        "refutation": (
            "The \"pedagogical\" framing requires Allah to have prescribed "
            "something He intended to revoke, which either makes the "
            "original prescription fraudulent (Allah prescribing what He "
            "did not really want) or makes the reduction contingent on "
            "Moses's advice (Moses knowing what Allah did not). The "
            "hadith's plain structure has Moses repeatedly urging Muhammad "
            "to go back and ask for reductions, with Allah agreeing — a "
            "negotiation sequence. A divine prescription that is "
            "adjusted downward through mortal advocacy is not divine "
            "prescription in the sense Islamic theology elsewhere "
            "requires; it is committee legislation with supernatural "
            "vocabulary."
        ),
    },
    {
        "anchor": "Allah's Apostle ordered that the dogs should be killed.",
        "response": (
            "Classical apologetics situates the dog-culling in specific "
            "public-health circumstances — rabies outbreak in Medina, "
            "dogs carrying parasites and disease. The subsequent relaxation "
            "(only black dogs, or only rabid dogs) represents prophetic "
            "reasoning about proportionate response. Modern apologists "
            "emphasise Muhammad's general kindness to animals and frame the "
            "dog-episode as contextual emergency, not a standing animal-"
            "killing precedent."
        ),
        "refutation": (
            "The rationalising of a mass animal-culling on religious grounds "
            "is the apologetic task — but the underlying precedent is "
            "prophetic authorisation of killing a category of animal for "
            "being the wrong species. The later qualifications (only "
            "black dogs, specifically rabid dogs) are adjustments to the "
            "rule, not repudiation of the original order. Classical "
            "jurisprudence preserves both the original command and the "
            "modifications, which leaves the dog-culling authority "
            "permanently available to communities that wish to revive "
            "it. A religion whose founder ordered mass species-killing and "
            "then partially rescinded has established the institution of "
            "religious animal-culling, regardless of contemporary "
            "moderation."
        ),
    },
    {
        "anchor": "From among the portents of the Hour are: Religious knowl",
        "response": (
            "Classical eschatology reads the 50:1 ratio as symbolic — \"many "
            "women, few men\" signaling the end-times disruption of normal "
            "balance, with the specific number being apocalyptic rhetoric "
            "rather than statistical claim. Possible real-world "
            "instantiations (war casualties producing female surplus, "
            "differential mortality rates) are cited as compatible with "
            "the prophecy's structural observation without requiring the "
            "precise ratio."
        ),
        "refutation": (
            "\"Symbolic apocalyptic rhetoric\" is the general defense "
            "against every specific prediction; if it defuses anything, "
            "it means nothing. The hadith frames female-surplus as a "
            "negative cosmic sign — which presupposes that balanced sex "
            "ratios are the natural order and female predominance is "
            "<em>disorder</em>. That presupposition tells us something "
            "about the tradition's view of women: their excess is a sign "
            "of things going wrong, not of anything else. A religion "
            "whose end-time prophecy treats abundant women as "
            "civilisational alarm has embedded into eschatology exactly "
            "the gender-anxiety its culture carried."
        ),
    },
    {
        "anchor": "Bukhari: no clear hadith prescribing a specific punishment",
        "response": (
            "Classical apologetics argues Bukhari's silence on specific "
            "same-sex punishment is methodological: the compiler applied "
            "stricter authenticity criteria and did not include the "
            "\"kill the doer and one done to\" hadith under his stricter "
            "standards. Other collections (Tirmidhi, Abu Dawud, Ibn Majah) "
            "preserve the punishment hadith. The absence from Bukhari does "
            "not invalidate the punishment; it reflects selection criteria."
        ),
        "refutation": (
            "The apologetic explanation concedes the problem: the most "
            "authoritative Sunni collection did not preserve the hadith "
            "that subsequent Sunni jurisprudence used to establish "
            "capital punishment for same-sex acts. That silence is "
            "telling — if the hadith were well-attested, Bukhari's strict "
            "criteria should have accepted it. Classical Sunni law built "
            "the death penalty on materials that Islam's most "
            "authoritative collection declined to include, which "
            "undermines the \"divine law\" framing of that penalty. "
            "Bukhari's silence is evidence against the sahih-status of "
            "the punishment tradition, even if other collections include "
            "it."
        ),
    },
    {
        "anchor": "If a slave-girl (Ama) commits illegal sexual intercourse",
        "response": (
            "Classical apologetics notes the hadith's context: slave-girls "
            "who repeatedly committed offenses beyond their owner's "
            "control were disposed of by sale, not executed — a graduated "
            "response compared to free-person penalties. The \"sell her "
            "for a hair rope\" hyperbolic phrasing emphasises disposal, "
            "not economic valuation; classical jurisprudence placed "
            "minimum sale prices on slaves to prevent trivialisation."
        ),
        "refutation": (
            "\"Graduated response\" is the apologetic frame for the "
            "systematic treatment of the enslaved person as economically "
            "disposable — which is the problem the hadith preserves. "
            "The \"hair rope\" phrasing communicates, not hides, the "
            "category: this human being's value has collapsed to "
            "whatever residual economic use a new owner might extract. "
            "A religion whose prophetic precedent for dealing with a "
            "repeat-offending slave is systematic resale at whatever "
            "price the market will bear has preserved the "
            "commodification of enslaved persons as ethically "
            "workable, regardless of how classical law later elaborated "
            "minimum-price protections."
        ),
    },
    {
        "anchor": "A bedouin came to the Prophet and said, 'O Allah's Apostle! My son was a",
        "response": (
            "Classical apologetics treats the Unais narrative as example "
            "of Islamic procedural justice: the young man was punished "
            "for his offense (100 lashes, one-year exile) and the woman "
            "confessed — her execution was consequent to her own "
            "confession, not summary judgment. The different penalties "
            "track the legal distinction between unmarried (lashing) and "
            "married (stoning) fornication, applied correctly to each "
            "person's status."
        ),
        "refutation": (
            "\"Applied correctly\" assumes the framework is just; the "
            "framework is the issue. A legal system that assigns the "
            "married woman stoning and the unmarried male lashing — for "
            "what is the same act of consensual sex — has gendered the "
            "punishment. The stoning rests on a hadith-supplied rule "
            "not present in the Quran's current text, which means the "
            "most severe penalty depends on the <em>naskh al-tilawa</em> "
            "doctrine. And Unais was sent to adjudicate by himself, "
            "without witnesses or trial — the Quranic four-witness "
            "requirement (24:4) was bypassed because the woman confessed. "
            "The procedure is permissive of exactly the abuses that "
            "formal witness-requirements are supposed to prevent."
        ),
    },
    {
        "anchor": "I used to play with the dolls in the presence of the Prophet",
        "response": (
            "Standard apologetic responses to Aisha's age (physical "
            "maturity, cultural norms, revisionist redating) are covered "
            "across the other canonical collections. For this specific "
            "Bukhari preservation, apologists note the candid detail as "
            "evidence of the tradition's honesty — it preserves the "
            "incongruity rather than sanitising it. The doll-play is "
            "cited as evidence Muhammad was gentle with his young wife, "
            "permitting normal childhood activities."
        ),
        "refutation": (
            "Candour preserves the problem, not the solution. The "
            "translator's own footnote confirms Aisha was a "
            "\"little girl, not yet reached the age of puberty\" — a "
            "gloss on Bukhari's own text. A religion whose founder's "
            "wife is documented as <em>simultaneously</em> old enough for "
            "consummation and young enough for dolls has documented its "
            "own ethical disjunction. Apologetic moves must choose: "
            "accept the consummation age and reject the dolls as "
            "historical (requires rejecting canonical hadith), or accept "
            "the dolls and address the consummation-at-nine (requires "
            "accepting what the text says about her age). The tradition "
            "preserves both without discomfort, which is itself the "
            "ethical information."
        ),
    },
    {
        "anchor": "Allah's Apostle used to kiss some of his wives while he was fasting",
        "response": (
            "Classical apologetics frames the hadith as establishing that "
            "affectionate contact during fasting is permitted for those "
            "who can control themselves, with Muhammad's example "
            "demonstrating the principle. The tradition does not privilege "
            "the Prophet as the only one permitted; rather, it shows the "
            "rule's actual scope (self-control is the criterion) and "
            "notes that ordinary believers often lack this control, "
            "which is why a more cautious practice is recommended for "
            "them."
        ),
        "refutation": (
            "The hadith's narrator frames Muhammad's self-control as "
            "distinctive — \"he had the best control of his passion\" — "
            "which positions him as the exception. The pattern is "
            "structural: the Prophet is permitted what ordinary "
            "believers must avoid, with the rule framed as scaling by "
            "personal capacity. Combined with other privilege-hadiths "
            "(extended marriage allowances, specific intercession rights, "
            "special shares of war booty), the picture is of a leader "
            "whose personal freedoms exceed community norms on religious "
            "grounds. \"Moral authority derived from exceptional "
            "self-control\" is the category that has produced the "
            "charismatic-leader exemptions every religious tradition has "
            "had to reckon with."
        ),
    },
    {
        "anchor": "Uthman ordered that Al-Walid be flogged forty lashes",
        "response": (
            "Classical apologetics frames the Al-Walid episode as evidence "
            "of Islamic legal equality: even a high-ranking official "
            "(governor of Kufa) was flogged for drinking, demonstrating "
            "that Islamic law applied to all regardless of status. "
            "Modern apologists cite this as model of accountability "
            "unusual in pre-modern legal systems, where rank typically "
            "granted immunity."
        ),
        "refutation": (
            "\"Equality\" in application is real for this case — but the "
            "content is the problem: flogging as criminal penalty for "
            "alcohol consumption (40 or 80 lashes, with the larger "
            "number Umar's addition). The application-equality does not "
            "rehabilitate the penalty as ethically sound. Flogging has "
            "been abolished in most jurisdictions as cruel and "
            "disproportionate, yet Saudi Arabia, Iran, parts of Pakistan "
            "and Nigeria continue to apply hadd punishments derived "
            "from precisely this hadith. The \"accountability\" model "
            "preserves the punishment while extending it more evenly — "
            "which is a mixed achievement if the underlying penalty is "
            "itself problematic."
        ),
    },
    {
        "anchor": "Abdullah bin Umar divorced his wife during her menses.",
        "response": (
            "Classical apologetics argues the hadith establishes "
            "protective procedural rules for divorce: the menses timing "
            "affects the waiting period (<em>iddah</em>) calculation, so "
            "the Prophet's correction is technical rather than "
            "substantive. The divorce remains valid; it simply must be "
            "delayed to a menstrually-appropriate moment. The rule "
            "structure is pragmatic household-law for a pre-modern "
            "community, not a statement about the validity of women's "
            "legal standing."
        ),
        "refutation": (
            "\"Technical not substantive\" describes the juristic "
            "content; what remains is that divorce timing is coordinated "
            "with female biology in a way the framework presumes the "
            "man's unilateral action will drive. The wife's reproductive "
            "cycle is the scheduling mechanism for a decision she does "
            "not make. A divorce-law structure in which the husband's "
            "pronouncement is valid but its timing is calibrated to the "
            "wife's menses has placed the woman in the role of passive "
            "biological datum in a legal process she does not control. "
            "That structure is what fourteen centuries of asymmetric "
            "divorce practice has reflected, and the \"technical rule\" "
            "framing does not alter it."
        ),
    },
    {
        "anchor": "You (i.e. Muslims) will fight with the Jews till som",
        "response": (
            "Classical eschatology treats the hadith as specifically "
            "describing eschatological events at the end of time — the "
            "final battle with followers of the <em>Dajjal</em>, who per "
            "other hadith will include 70,000 Jews of Isfahan. The "
            "\"Jews\" of the final battle are eschatologically specific, "
            "not the Jewish community as such. Modern apologists argue "
            "the hadith does not license present-day violence; it "
            "describes a supernatural-eschatological conclusion."
        ),
        "refutation": (
            "The \"future eschatological only\" framing cannot insulate "
            "the text from its present-day use. Hamas's founding "
            "charter (1988, Article 7) cites this hadith explicitly as a "
            "present-operative theological warrant. Israeli hard-right "
            "activists plant or refuse Gharqad trees based on the "
            "prophecy. The hadith is active in modern violence, not "
            "quarantined to a distant future. A scripture-status "
            "tradition that scripts one specific ethnoreligious "
            "community into the Antichrist's army — and commands their "
            "elimination — has pre-justified genocide regardless of when "
            "the \"fulfillment\" is imagined. \"Specific eschatological "
            "enemies\" is exactly the rhetoric that makes the category "
            "transferable to any contemporary rival."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/bukhari.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

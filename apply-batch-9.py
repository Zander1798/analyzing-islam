#!/usr/bin/env python3
"""Batch 9: All 35 Nasa'i Strong entries."""
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
        "anchor": "The Messenger ordered them to go to the camels and drink their urine",
        "response": (
            "Apologists argue the hadith records a specific <em>therapeutic</em> prescription "
            "for a group of men suffering from a particular Medinan illness — an ad hoc "
            "treatment using what was available in the 7th-century Arabian environment, not "
            "a standing medical endorsement of urine-drinking. Some modern apologists further "
            "cite studies on camel urine's alkaline composition as potentially bactericidal, "
            "framing the hadith as unwittingly pointing at a pharmacological property."
        ),
        "refutation": (
            "The \"specific therapeutic\" framing does not address the text's presentation of "
            "the Prophet as the prescriber. A divinely-informed prophet prescribing medical "
            "treatment should not be administering a remedy whose active effect is either "
            "nonexistent or drastically outweighed by its pathogen load — camel urine has "
            "been specifically implicated by the WHO as a vector for MERS-CoV transmission. "
            "The \"modern studies on alkalinity\" is retrofit: the hadith makes a concrete "
            "medical recommendation that modern epidemiology has specifically warned against. "
            "A revelation that would not need to be subsequently overruled by public-health "
            "institutions is precisely what a scripture-status medical claim should produce."
        ),
    },
    {
        "anchor": "The unmarried fornicator — 100 lashes and one year of exile.",
        "response": (
            "Classical jurisprudence distinguishes the Quranic 100-lashes for the unmarried "
            "from the hadith-supplied one-year exile and from the stoning-for-adulterer. "
            "Apologists argue the punishments follow a graduated structure addressing "
            "different social harms, and that the evidentiary bar (four eyewitnesses to "
            "actual penetration) was so high that actual enforcement was rare. The exile "
            "component is framed as protective removal from a community where the offense "
            "occurred, not as additional cruelty."
        ),
        "refutation": (
            "The \"rare in practice\" defense is not a defense of the rule as eternal law. A "
            "penal code combining 100 lashes with one year of exile for consensual sex — "
            "continuously operative in several Muslim-majority jurisdictions today — is a "
            "penal code whose content is at issue, not its frequency of enforcement. The "
            "graduated structure's final rung (stoning for the married adulterer) is not "
            "even in the Quran's extant text, which means the corpus-level punishment "
            "regime requires hadith to exist at all — undermining the Quran's "
            "self-description as complete."
        ),
    },
    {
        "anchor": "We captured some women and wanted to practice coitus interruptus",
        "response": (
            "The standard response frames the hadith as part of a gradual regulatory "
            "trajectory: Islam inherited 7th-century concubinage and slavery practices and "
            "progressively tightened their conditions, with eventual abolition the implied "
            "endpoint. The specific Q&A about <em>'azl</em> reflects the community's concern "
            "with property-value economics (future resale) rather than a moral endorsement "
            "of the underlying sexual access."
        ),
        "refutation": (
            "The \"gradual trajectory toward abolition\" is a 20th-century reading that "
            "fourteen centuries of classical Islamic jurisprudence did not deliver. The "
            "hadith presents the Prophet's response to companions who asked about coitus "
            "interruptus with captive women — a question whose premise (sex with captives "
            "is permitted) was accepted without objection. ISIS cited this and parallel "
            "hadiths with explicit classical-legal footnoting when it enslaved Yazidi women "
            "in 2014. A religion that regulates the <em>timing</em> of sexual contact with "
            "captives has accepted the underlying transaction and moved on to adjust its "
            "technical parameters."
        ),
    },
    {
        "anchor": "Is not the testimony of a woman half the testimony of a man?",
        "response": (
            "Modern apologists argue the 2:1 ratio applies narrowly to financial "
            "transactions (Quran 2:282), reflecting practical reality in 7th-century "
            "commerce where women's typical involvement in such affairs was limited. The "
            "\"deficient intellect\" language in the Nasa'i hadith is often rendered by "
            "apologists as a specific observation about memory for transactional details in "
            "that context, not a claim about female cognition in general. Cases where "
            "women's testimony is treated as fully equal (breastfeeding, medical) are cited "
            "to show the ratio is domain-specific."
        ),
        "refutation": (
            "The hadith's explicit rationale — \"is that not the deficiency of her "
            "intellect?\" — is a claim about female cognition, delivered by the Prophet "
            "himself, not a narrow commercial observation. Classical Islamic law applied "
            "the 2:1 ratio broadly across criminal and civil testimony, and modern "
            "Shari'a-based states continue that application. The domain-specific exceptions "
            "apologists cite presuppose the general rule. A scripture that frames female "
            "intellectual deficiency as justification for halving testimony has said "
            "something about female cognition; the narrowing is a modern wish, not the "
            "text's content."
        ),
    },
    {
        "anchor": "Khalid is a sword among the swords of Allah",
        "response": (
            "Apologists emphasise Khalid's military skill as a legitimate service to the "
            "Muslim community, with the honorific recognising his role in defending the "
            "early Islamic state. The Banu Jadhima episode (where Khalid killed people who "
            "had declared \"we believed\") was rebuked by Muhammad, and Khalid's "
            "reputation was built on subsequent campaigns where he was regarded as an "
            "effective commander. Modern apologists frame the title as a statement about "
            "his military excellence, not an endorsement of every action."
        ),
        "refutation": (
            "The Banu Jadhima rebuke is real — but it did not result in loss of status, "
            "loss of command, or the removal of the honorific. Muhammad's stated response "
            "was \"I declare myself innocent of what Khalid did,\" but Khalid remained in "
            "command and the \"Sword of Allah\" title continued. The structural fact is "
            "that a general whose early career included massacre of professing converts "
            "retained prophetic endorsement. A religion that hands its deity's name to "
            "the weapon of a leader whose excesses it has privately disavowed has "
            "sacralised the instrument while keeping its distance from the hand — a "
            "position that has aged poorly across fourteen centuries of citations."
        ),
    },
    {
        "anchor": "Magic was worked on the Messenger of Allah until he used to imagine",
        "response": (
            "Classical theology treats the bewitchment as a genuine supernatural attack "
            "that affected Muhammad's worldly perception but not his prophetic function — "
            "Allah's protection of revelation (Quran 15:9, 5:67) is preserved because the "
            "bewitchment did not corrupt any revealed verses, only Muhammad's mundane "
            "memory. Surah al-Falaq and al-Nas (Quran 113–114) were revealed specifically "
            "as protective formulas against such magic, resolving the crisis through "
            "divine response."
        ),
        "refutation": (
            "The apologetic requires a clean line between Muhammad's \"worldly "
            "perception\" and his \"prophetic reception\" that the hadith does not draw. "
            "If a Jewish sorcerer could falsely plant memories for months without "
            "divine protection preventing it, the claim that no revelation during that "
            "period was tainted cannot be verified — it is a stipulation. The Quran's "
            "promise (5:67) that Allah will protect Muhammad from disbelievers is "
            "directly undermined by his multi-month bewitchment. The attempt to rescue "
            "the claim by compartmentalising \"cognitive\" from \"prophetic\" functions "
            "is a modern psychological frame the 7th-century text does not supply."
        ),
    },
    {
        "anchor": "They (the jinn) are the delegation of the jinn of Nasibin",
        "response": (
            "Classical Islamic theology accepts the existence of jinn as a distinct "
            "creation described in the Quran (Surah al-Jinn). The hadith's specific "
            "nutritional detail — jinn eat bones and dung — is read as protection for "
            "ritual hygiene: Muslims should not use these materials for cleansing because "
            "they are already assigned as food for another order of beings. The rule "
            "coordinates human ritual space with the broader theological framework of "
            "multiple intelligent creations."
        ),
        "refutation": (
            "The biological specificity — what jinn eat, how they arrive as \"delegations,\" "
            "which materials belong to them — is exactly the level of detail that "
            "differentiates revealed information from folk mythology, and the hadith "
            "falls on the folk-mythology side. Toilet etiquette coordinated with the "
            "dietary preferences of supernatural creatures is indistinguishable from "
            "the pre-Islamic nocturnal-demon frameworks Islam's <em>anti-jahiliyya</em> "
            "rhetoric claims to abolish. The rebadging (\"jinn\" instead of \"demons\") "
            "does not redeem the underlying cosmology."
        ),
    },
    {
        "anchor": "None of you should hold his private part with his right hand while urinating.",
        "response": (
            "Apologists argue the hygiene-differentiation reflects genuine sanitary "
            "thinking: the right hand was used for eating and greeting in 7th-century "
            "Arabian culture, so restricting private-part handling to the left hand "
            "minimised contamination in an era without running water or soap. The rule "
            "is thus a culturally-appropriate hygiene protocol, not arbitrary ritual."
        ),
        "refutation": (
            "The hygiene framing is partial at best and does not scale to the full "
            "right-hand/left-hand code that classical Islamic manners extract from "
            "similar hadith — which regulate food, greeting, entering mosques, and much "
            "more. The cumulative effect is an elaborate handedness ritual with "
            "theological weight, not a narrow sanitary rule. And left-handed Muslims "
            "must learn the mirror logic for every activity, which is exactly the "
            "pattern of cultural-ritual coding rather than functional hygiene. Divine "
            "revelation that distinguishes which hand may touch genitals during "
            "urination has described 7th-century Arabian etiquette and called it sacred."
        ),
    },
    {
        "anchor": "The Prophet forbade eating the flesh of domestic donkeys on the day of Khaybar.",
        "response": (
            "Apologists argue the hadith does not contradict the Quran but supplements it: "
            "Quran 5:3 gives a general prohibited-meat list, and the prophetic tradition "
            "clarifies specific additional items not enumerated in the general rule. This "
            "is how <em>sunnah</em> functions throughout Islamic law — providing detail "
            "the Quran frames in general terms. The donkey prohibition was specifically "
            "occasioned by wartime food-scarcity concerns at Khaybar, not a permanent "
            "dietary rule."
        ),
        "refutation": (
            "The \"supplementation\" model has a structural problem: if the Quran is "
            "complete and clear (as 6:38, 16:89 claim), it should not need hadith to "
            "add forbidden foods not listed in its dietary rule. \"Hadith supplements "
            "Quran\" is the apologetic move that explains <em>every</em> addition the "
            "tradition has made — but the net effect is that Islamic dietary law is "
            "established by the hadith corpus, not the Quran alone. The "
            "\"specifically Khaybar\" framing contradicts the classical and continuing "
            "jurisprudence, which treats donkey-meat as permanently forbidden regardless "
            "of circumstance."
        ),
    },
    {
        "anchor": "The spoils of war are divided into five parts",
        "response": (
            "Classical apologetics argues the prophetic fifth (<em>khums</em>) was not "
            "personal enrichment but funded the Muslim state's charitable and religious "
            "obligations — support for orphans, the poor, travellers, and the Prophet's "
            "household as public figures. The rule is analogous to state revenue systems "
            "that allocate public funds for public purposes. The Prophet himself lived "
            "simply and the <em>khums</em> funded his public role, not personal luxury."
        ),
        "refutation": (
            "The \"public purposes\" framing does not dissolve the structural issue: a "
            "religious leader's income is tied directly to the volume of war-plunder "
            "generated, which creates a financial incentive favourable to continued "
            "military expansion. The same fifth share included captured human beings — "
            "women distributed as concubines to the Prophet and his close associates. "
            "\"Living simply\" and \"funding public functions\" are compatible with the "
            "institutional fact that prophetic authority was paid on war's productivity. "
            "A system that fuses prophecy with procurement has a design problem the "
            "charitable-use framing cannot repair."
        ),
    },
    {
        "anchor": "Avoid the seven destructive sins",
        "response": (
            "Classical apologetics reads the inclusion of battle-desertion among the seven "
            "great sins as reflecting the existential stakes of early Islam — the young "
            "community could not survive mass desertion in the formative battles, and the "
            "moral weight of the rule matched the strategic necessity. Modern apologists "
            "argue the rule was contextual to early warfare under Muhammad's command, not "
            "a standing principle for all Muslim armed forces in all eras."
        ),
        "refutation": (
            "The \"contextual to early Islam\" framing is a modern narrowing; classical "
            "jurisprudence treated the ranking as permanent moral theology. Equating "
            "battle-desertion with idolatry and murder inverts the moral weight that "
            "systems taking human life seriously typically assign: soldiers who choose "
            "survival over suicidal attack are morally indistinguishable (on this "
            "ranking) from those who worship other gods or kill innocents. That is "
            "exactly the moral arrangement a religion committed to holy war produces, "
            "and it is the one this hadith preserves."
        ),
    },
    {
        "anchor": "Whoever slaps his slave without cause — his expiation is to set him free.",
        "response": (
            "Classical apologetics frames the rule as part of Islam's broader pro-"
            "manumission framework: wrongful treatment of a slave obligates the owner to "
            "free the slave as expiation, creating a built-in incentive toward emancipation "
            "and against abuse. The rule treats the slave's dignity as substantial enough "
            "that its violation requires the most serious compensation — freedom itself."
        ),
        "refutation": (
            "The inverse reading is diagnostic: the \"expiation\" is <em>freeing</em> the "
            "slave, which presupposes that ownership is the baseline and manumission is "
            "the penalty. An assault in an ordinary legal framework punishes the "
            "assailant; here, the \"punishment\" is the loss of the assaulted person as "
            "property. There is no punishment of the master beyond the loss of the asset. "
            "A legal system that makes \"let him go\" the remedy for striking a slave has "
            "treated bondage as the normal condition and freedom as the cost — the "
            "opposite of the framing modern apologetics wants to extract."
        ),
    },
    {
        "anchor": "The Prophet deferred her until she gave birth, then until she weaned the child",
        "response": (
            "The Ghamidiyya case is treated by apologists as evidence of Islamic legal "
            "rigor: Muhammad repeatedly deferred the sentence until the woman had given "
            "birth and weaned her child, demonstrating concern for the infant's welfare "
            "and multiple opportunities for the accused to withdraw her confession. The "
            "stoning was ultimately at her own persistent request, with the Prophet "
            "reportedly praising her sincere repentance after her death."
        ),
        "refutation": (
            "The procedural delay makes the execution premeditated, not mitigated. A "
            "system that waits two years while caring for the infant of a pregnant "
            "confessor before executing her has demonstrated methodical follow-through, "
            "not clemency. The moral profile of the outcome — a weaned toddler left "
            "motherless by the community's formal procedure — is not improved by the "
            "care taken along the way. And the Prophet's post-death praise is exactly the "
            "theological framing that makes the execution coherent within the system: "
            "death for sexual transgression is spiritually beneficial for the "
            "executed. That frame is the problem."
        ),
    },
    {
        "anchor": "The verse 'your wives are a tilth' was revealed after Jewish superstition",
        "response": (
            "Apologists argue the occasion-of-revelation context does not reduce the "
            "verse's permanent status: the Quran's counter-move against a specific "
            "superstition (about squint-eyed babies from particular sexual positions) "
            "yields a general principle about marital sexual permissibility that "
            "transcends the occasion. The \"tilth\" metaphor is standard Near-Eastern "
            "agricultural imagery for fecundity, not a statement of female inferiority."
        ),
        "refutation": (
            "If the verse's occasion was correcting village folklore about conception "
            "positions, then its origin as scripture-level response to local gossip is "
            "diagnostic of how the eternal was authored — with one eye on midwifery "
            "hearsay. The \"tilth\" metaphor is indeed standard Near-Eastern imagery — "
            "and it consistently frames women as the passive ground that men cultivate, "
            "with agency assigned to the male farmer. A universal divine scripture "
            "could have avoided the imagery or flagged it as provisional; 2:223 does "
            "neither. The combination — folkloric occasion plus agrarian-subordination "
            "metaphor — is the signature of a text written from inside its culture, not "
            "from above it."
        ),
    },
    {
        "anchor": "A virgin is consulted about her marriage — her silence is her consent.",
        "response": (
            "Apologists argue the rule is a practical accommodation to 7th-century cultural "
            "reality: virgins in the period were culturally expected to be shy and often "
            "reluctant to verbally agree to a marriage in front of male guardians. The "
            "\"silence\" provision protects the virgin's consent from being invalidated by "
            "the cultural pressure to demur verbally. Classical jurisprudence requires the "
            "guardian to ensure the marriage is in her interest and permits her to object "
            "if the proposal is genuinely unwanted."
        ),
        "refutation": (
            "The \"protects her consent\" framing inverts the actual legal mechanism: the "
            "rule defaults to agreement, placing the burden on the silent girl to object "
            "against family pressure. A frightened, intimidated, or uncomprehending girl "
            "(the rule explicitly applies to prepubescent cases) has no structural means "
            "to refuse — her silence is captured as consent regardless of its actual "
            "content. Classical jurisprudence on paternal marriage authority (<em>jabr</em>) "
            "permitted fathers to marry off daughters who had not yet reached puberty "
            "without any consent process at all, making the \"silence = consent\" rule "
            "operative primarily where objection was already psychologically blocked. A "
            "consent architecture that counts silence as agreement has written the exit "
            "condition out of the contract."
        ),
    },
    {
        "anchor": "The Prophet cursed men who imitate women and women who imitate men",
        "response": (
            "Classical apologetics frames the curse as directed at <em>deliberate "
            "gender-performance crossing</em>, not innate disposition. The specific Arabic "
            "terminology (<em>mukhannathun</em>) referred to men who adopted female "
            "mannerisms for social access to women's quarters, with the exile responding "
            "to a specific privacy-violation incident. Modern apologists distinguish "
            "between this narrow behavioural rule and broader anti-trans animus."
        ),
        "refutation": (
            "The \"deliberate performance\" framing does not capture the hadith's scope: "
            "the exile applied to multiple named individuals based on presentation, and "
            "classical jurisprudence built an enduring category restricting "
            "<em>mukhannathun</em>'s public participation — a category that extended well "
            "beyond privacy-violation concerns. Contemporary state-level enforcement "
            "against gender-nonconforming people in multiple Muslim-majority jurisdictions "
            "cites this and parallel hadiths as prophetic precedent. A religion whose "
            "founder cursed men for walking with a certain gait has aimed its disapproval "
            "at the shape of personality, and the \"only deliberate\" narrowing cannot be "
            "extracted from the text."
        ),
    },
    {
        "anchor": "I was shown hellfire, and I saw that most of its inhabitants are women.",
        "response": (
            "Classical theology reads the hadith as a prophetic warning specifically about "
            "behaviors the Prophet observed as common among women of his community — "
            "ingratitude toward husbands and excessive cursing. The hadith's reasons given "
            "are cited as the correctable fault, not a claim about female spiritual "
            "capacity. Modern apologists note that the hadith should be read alongside "
            "the Quran's affirmation of spiritual equality (33:35), meaning women are "
            "<em>capable</em> of equal reward, just <em>observed</em> to fall short more "
            "often in the Prophet's community."
        ),
        "refutation": (
            "The observation-not-essence defense is weak. If hell's population is "
            "disproportionately female across all Muslim generations (not just the "
            "Prophet's community), the claim is about women as a category, not a local "
            "observation. If the demographic is local to Muhammad's time, the hadith is "
            "dated and should not function as eternal theology. The cited \"reasons\" "
            "— ingratitude, cursing — are mundane social behaviors whose gendered "
            "distribution (if any) is contingent on the roles available. A religion whose "
            "prophet reports a gendered hell-majority and assigns the cause to "
            "stereotyped feminine faults has articulated something about its view of "
            "half its adherents that spiritual-equality verses do not neutralise."
        ),
    },
    {
        "anchor": "The Prophet took Safiyyah at Khaybar after the killing of her husband",
        "response": (
            "Apologists argue Safiyyah's subsequent status as an honoured wife "
            "(<em>Umm al-Mu'minin</em>) and her reported affection for Muhammad reframes "
            "the consummation context: she converted, was elevated to royal marriage rather "
            "than concubinage, and lived as a respected member of the Prophet's household. "
            "The alliance-marriage interpretation places the relationship in the category "
            "of political marriage common in the period, not sexual conquest."
        ),
        "refutation": (
            "Her outcome does not rewrite the circumstances of the wedding night, and the "
            "circumstances are what the hadith preserves. Safiyyah's father was killed at "
            "Khaybar days before; her husband (Kinana) had been tortured to reveal hidden "
            "treasure and killed; her people were in the process of being enslaved or "
            "executed. The consummation on the same journey — with the <em>istibra</em> "
            "waiting period reportedly waived — occurred while her mourning was acute. "
            "\"Royal marriage\" as a framing does not recover ordinary consent from that "
            "timeline. A prophet whose wedding night followed the killing of his wife's "
            "father and husband has defined love on terms a modern ethical framework "
            "cannot rehabilitate."
        ),
    },
    {
        "anchor": "Aisha played with a horse that had two wings made of cloth",
        "response": (
            "Apologists frame the hadith as evidence of Muhammad's kindness and the "
            "household's gentle character — he did not strictly apply the picture-making "
            "prohibition to his young wife's toys. The Prophet's laughter is cited as "
            "warm marital affection. The doll-playing is read as demonstrating normal "
            "childhood activities continuing alongside the marriage, showing that Aisha "
            "was treated with care."
        ),
        "refutation": (
            "The \"kindness and warmth\" framing cannot absorb the underlying "
            "incongruity: a wife old enough for sexual consummation, still playing with "
            "toy horses. The preservation is candid — the tradition did not censor the "
            "detail — but the candour is exactly what makes apologetic rescues "
            "impossible. Defenders who argue Aisha was older (the \"she was really 19\" "
            "revisionism) cannot accept the toys as historical. Defenders who accept the "
            "toys must grant her developmental age. The tradition preserves both "
            "simultaneously, which is the real difficulty: a marriage that includes "
            "consummation and toy horses is a marriage whose ethical profile the "
            "tradition itself has documented."
        ),
    },
    {
        "anchor": "Nasai preserves the same social-humiliation hadith",
        "response": (
            "Classical apologetics contextualises the narrow-street rule within the "
            "broader framework of <em>dhimma</em> protocol: non-Muslim dhimmis were "
            "protected under specific legal terms that included behavioral markers of their "
            "secondary status. The apologetic position holds that protection — not "
            "degradation — was the goal, with the narrow-street and initial-greeting rules "
            "being symbolic reminders of the political hierarchy, not substantive "
            "discrimination. Modern Muslim-majority states have long abandoned these "
            "provisions."
        ),
        "refutation": (
            "\"Symbolic reminders\" is apologetic terminology for systematic public "
            "humiliation. A religion that legislates which side of the road the Other "
            "must walk on, who greets whom first, and how interfaith interactions signal "
            "rank has not created a framework of toleration; it has created a framework "
            "of ranked subordination. Modern abandonment is a welcome departure, but "
            "departure from classical law is not a rehabilitation of it. The \"protection "
            "not degradation\" framing was the classical legal self-description — and "
            "classical Muslim societies regularly enforced practices that the modern "
            "framing explicitly denies, with citations to these exact hadiths."
        ),
    },
    {
        "anchor": "May Allah curse the Jews and Christians, for they took the graves",
        "response": (
            "Apologists frame the hadith as a warning against a <em>practice</em> "
            "(grave-veneration) rather than a curse on the communities as such. "
            "Muhammad's rebuke is directed at those who imitate the practice, including "
            "Muslims — Salafi reformist tradition explicitly cites this hadith to "
            "criticise Sufi shrine veneration in Muslim contexts. The deathbed weight is "
            "real but the content is behavioural ethics, not collective damnation."
        ),
        "refutation": (
            "\"Curse\" in Islamic theological vocabulary has specific weight — it means "
            "more than \"warning against a practice.\" Classical commentators (Ibn "
            "Taymiyyah, al-Nawawi) treated the deathbed utterance as a statement about the "
            "communities' spiritual fate, not only a procedural rebuke. The selective "
            "application is telling: the \"don't do what they did\" warning applies to "
            "Jewish and Christian practice, but Muslim practice at Muhammad's tomb in "
            "Medina is itself the largest pilgrimage-to-a-grave in Islam, conducted "
            "daily by millions without the same curse attaching. The rule is applied "
            "outward but not inward, which reveals it as polemical rather than principled."
        ),
    },
    {
        "anchor": "The Dajjal will be followed by seventy thousand Jews of Isfahan",
        "response": (
            "Classical apologetics reads the hadith as eschatological prediction about "
            "specific enemies of the eschatological moment — not a standing indictment of "
            "Jewish communities. The <em>Dajjal</em> is supernatural; his followers at "
            "that specific moment are described geographically and sartorially as a way "
            "of identifying them. Modern apologists argue \"70,000\" is idiomatic for a "
            "large number and should not be read as an ethnic roll-call."
        ),
        "refutation": (
            "The \"eschatological only\" framing does not insulate the text from its "
            "operational use. Contemporary antisemitic Muslim rhetoric — including "
            "political and religious discourse — cites this hadith as a statement about "
            "Jewish eschatological alignment with evil. A scripture-status tradition that "
            "assigns an entire ethno-religious community to the role of antichrist's "
            "foot-soldiers is not neutralised by saying the battle is future. The moral "
            "category is established now, and the prophecy operates as pre-justification "
            "for enmity regardless of when its \"fulfillment\" is imagined."
        ),
    },
    {
        "anchor": "Whoever changes his religion, then kill him.",
        "response": (
            "The standard apologetic narrows the hadith to public political apostasy "
            "combined with hostility to the Muslim state — not private belief change. "
            "Modern reformist scholars argue the Quran's 2:256 (\"no compulsion in "
            "religion\") takes priority, and that the classical application was specific "
            "to 7th-century political conditions rather than an eternal rule. Several "
            "Muslim-majority states have formally removed apostasy from criminal law in "
            "recent decades."
        ),
        "refutation": (
            "The classical consensus across all four Sunni schools and Jaʿfari Shia law "
            "treated apostasy itself as capital, without the \"added hostility\" "
            "requirement apologists now specify. Six canonical hadith collections "
            "preserve the command — the \"fringe hadith\" dismissal is categorically "
            "impossible given its cross-collection attestation. Contemporary "
            "enforcement in several Muslim-majority jurisdictions continues to apply "
            "the rule to private belief change. The tension with 2:256 is real, and the "
            "classical resolution was to abrogate 2:256 — which modern apologists "
            "quietly abandon while still citing 2:256 as evidence of tolerance."
        ),
    },
    {
        "anchor": "They are the dogs of Hellfire.",
        "response": (
            "Classical apologetics restricts the hadith to the historical Khawarij — an "
            "early sect that practiced <em>takfir</em> against other Muslims and "
            "legitimised killing them. The harsh language reflects the specific "
            "existential threat they posed to the early community, not a template for "
            "future use. Modern apologists use the hadith against contemporary extremist "
            "groups (ISIS, al-Qaeda), describing them as \"neo-Khawarij\" — a positive "
            "application of the tradition against violent extremism."
        ),
        "refutation": (
            "The apologetic reading is accurate about the original target, but that does "
            "not remove the template-setting function. By prophetically pre-damning a "
            "specific theological faction, the tradition established the principle of "
            "scriptural excommunication — a tool used against every reform and dissenting "
            "movement in subsequent Islamic history (Mutazilites, Ismailis, Ahmadis, "
            "inter-sectarian polemic). The \"dogs of hellfire\" framing dehumanises "
            "dissenters rather than refutes their arguments. A prophetic precedent of "
            "theological sub-humanisation is what makes mutual <em>takfir</em> "
            "structurally available — and the structure has outlasted any original "
            "target."
        ),
    },
    {
        "anchor": "Jesus will descend and break the cross, kill the swine, and abolish the jizya",
        "response": (
            "Classical eschatology treats the hadith as predicting Jesus's return as the "
            "final Islamic redeemer — correcting the Christian community back to "
            "monotheism by rejecting crucifixion-theology (breaking the cross) and "
            "abolishing the secondary-status <em>jizya</em> arrangement because "
            "Christians will then convert. Apologists frame this not as Christian "
            "extermination but as theological rectification; Jesus, as a Muslim prophet in "
            "the Islamic tradition, aligns what his earthly mission was allegedly "
            "distorted into."
        ),
        "refutation": (
            "\"Abolishing jizya\" means conversion or death — the non-Muslim alternative "
            "ends when Christians cannot opt out of the converted-or-fight binary. The "
            "return of the Christian messiah as an anti-Christian warrior against the "
            "symbols of his own tradition (the cross, swine) is a pointed theological "
            "reversal rather than reconciliation. A prophecy in which Jesus destroys his "
            "followers' symbols, criminalises their choices, and collapses their legal-"
            "religious autonomy has absorbed Christianity only to annul it. The "
            "\"rectification\" framing is Islamic self-description; from any other "
            "vantage, it is eschatological supersessionism with teeth."
        ),
    },
    {
        "anchor": "Allah does not accept prayer without purification nor charity from unlawful",
        "response": (
            "Classical apologetics argues the rule protects the integrity of religious "
            "merit: charity from stolen wealth cannot generate spiritual reward because "
            "the act is built on prior injustice. The orphan still gets fed (the material "
            "benefit is real); the spiritual accounting simply does not credit the "
            "charitable giver because their moral standing was corrupt. This is not "
            "prioritising bookkeeping over welfare; it is preserving the meaning of moral "
            "choice."
        ),
        "refutation": (
            "The apologetic concedes the asymmetry: the orphan's benefit is acknowledged "
            "but discounted. A moral framework that centers the auditor's trail — "
            "ensuring the giver is not improperly credited — over the orphan's meal has "
            "priced accounting above relief. A consequentialist ethics (the orphan ate) "
            "and a deontological ethics (the giver lacked standing) are both defensible "
            "frameworks, but a system that chooses to emphasise the giver's accounting "
            "over the beneficiary's welfare has chosen its moral register. \"Merit "
            "accrual\" is the framing that permits the rule to hold; it is not a "
            "justification that lands if you center the orphan."
        ),
    },
    {
        "anchor": "There was revealed 'ten clear sucklings'; then it was abrogated by 'five.'",
        "response": (
            "The classical concept of <em>naskh al-tilawa</em> (abrogation of wording) "
            "holds that some verses were deliberately removed from the Quran's final form "
            "while their rulings remained or were replaced — a divine editorial process, "
            "not a textual failure. The tradition explicitly preserves these reports "
            "because the resulting jurisprudence depends on knowing the earlier rule. The "
            "existence of the category itself is evidence of the Quran's careful "
            "redaction, not its incompleteness."
        ),
        "refutation": (
            "<em>Naskh al-tilawa</em> is the apologetic rescue that concedes the substantive "
            "point: verses were recited as Quran, then removed from the final text. "
            "Aisha's narration that the passages were still being recited when Muhammad "
            "died — and the implication that they were then redacted post-mortem — is "
            "doctrinally costly. It undermines 15:9 (\"We have revealed the reminder and "
            "We are its guardian\") by exposing the Quran as a humanly edited text. The "
            "\"divine editorial\" framing requires Allah to have composed verses, revealed "
            "them for recitation, then removed them from the canonical form — a process "
            "whose function (presumably to secure the law) could have been achieved "
            "without requiring the community to live with a text missing revealed "
            "content."
        ),
    },
    {
        "anchor": "Allah decreed the measures of all things fifty thousand years before",
        "response": (
            "Classical theology uses the hadith to establish divine foreknowledge and "
            "pre-determination without reducing human moral agency — the Ash'arite "
            "<em>khalq</em>/<em>kasb</em> distinction holds that Allah creates the act "
            "while the human \"acquires\" responsibility, resolving the paradox between "
            "foreknowledge and freedom. \"50,000 years before creation\" is not a "
            "temporal claim about normal time but a theological assertion about the "
            "eternity of divine knowledge."
        ),
        "refutation": (
            "The <em>khalq</em>/<em>kasb</em> distinction is the scholastic scaffolding "
            "invented centuries after the Quran to manage exactly this contradiction — "
            "and its opacity is notorious even within Islamic theology. If fates are "
            "written before creation and Allah creates the acts, human agents are not "
            "making choices; they are executing a script whose content they did not "
            "author. Pairing this picture with eternal hellfire for \"wrong choices\" "
            "is precisely what makes the moral theodicy incoherent. The \"50,000 years "
            "before creation\" phrase is also self-contradictory — \"years\" is a "
            "temporal unit, but time begins with creation. A religion whose predestination "
            "claim requires time before time has told us what kind of statement it is "
            "making — mythology rather than metaphysics."
        ),
    },
    {
        "anchor": "This Quran has been revealed in seven ahruf.",
        "response": (
            "Classical tradition holds that the seven <em>ahruf</em> were divinely-sanctioned "
            "variant readings accommodating the dialectal diversity of Arabic tribes in "
            "Muhammad's time. Uthman's standardisation preserved the core text and "
            "unified the community, while permitting the ten canonical <em>qira'at</em> "
            "(recitation modes) as legitimate variations within the unified consonantal "
            "skeleton. Modern apologists argue this shows the Quran's adaptability, not a "
            "preservation failure."
        ),
        "refutation": (
            "The existence of seven divinely-sanctioned variants directly undermines the "
            "\"one preserved Quran\" claim. If the original revelation had seven forms, "
            "the \"Quran\" that Uthman standardised was already a choice among possible "
            "forms — meaning the current text is not the full revealed material, just one "
            "canonical slice. Uthman's burning campaign destroyed competing codices "
            "(including those of respected companions like Ibn Masud and Ubayy ibn Ka'b), "
            "which is how textual uniformity was produced. The claim of pristine "
            "preservation and the practice of producing uniformity through fire cannot "
            "both be honest descriptions of the same history."
        ),
    },
    {
        "anchor": "The first thing Allah created was the Pen",
        "response": (
            "Classical theology treats the Pen as symbolic of divine ordaining — the first "
            "creation is the instrument of decree, which writes the measurements of all "
            "things in the Preserved Tablet. The parallels to other Near Eastern "
            "scribal-creation motifs (Thoth, Nabu) are cited by apologists as evidence "
            "that ancient cultures perceived a common reality that Islam clarified and "
            "preserved in its pure form. Scribal imagery is metaphorical for divine "
            "decree, not literal stationery."
        ),
        "refutation": (
            "The \"common perception preserved in pure form\" defense grants legitimacy to "
            "Egyptian, Mesopotamian, and other ancient mythologies as sources of "
            "theological truth — at which point Islam's distinctiveness dissolves into a "
            "continuity with the pre-existing religious imagination of the region. The "
            "more honest account is simpler: the scribal-creation motif is widespread "
            "because ancient scribal cultures imagined the cosmos in the terms of their "
            "own profession, and Islam inherited one such framing along with the rest of "
            "its Near Eastern context. A creation whose first moment involves stationery "
            "has told us about the imagination that authored the account — the imagination "
            "of a scribe."
        ),
    },
    {
        "anchor": "Whoever wrongfully takes a span of land — a chain of seven earths",
        "response": (
            "Apologists read the \"seven earths\" as referring to layered physical "
            "strata — crust, mantle, outer core, inner core, and so on — retroactively "
            "fitting the hadith to modern geology. Alternative interpretations frame the "
            "\"seven earths\" as parallel inhabited worlds or as theological imagery for "
            "the severity of the land-theft punishment, not literal geological strata."
        ),
        "refutation": (
            "The \"tectonic plates\" reading is a classic <em>i'jaz 'ilmi</em> retrofit — "
            "the seven-earth cosmology is a direct parallel to the Mesopotamian "
            "<em>Kur</em> cosmology of layered underworlds, which was widespread in the "
            "Near East for millennia before Islam. The modern plate-tectonics framing "
            "requires reading the hadith as having anticipated specific scientific "
            "findings, with no classical commentator having extracted the reading before "
            "20th-century geology made it available. The alternative \"parallel worlds\" "
            "reading has no text-internal support. The simplest account is that the "
            "hadith preserves the inherited Mesopotamian cosmology, relabeled."
        ),
    },
    {
        "anchor": "Classical commentary on the Safa/Marwa run, Black Stone kiss, and circumambulati",
        "response": (
            "Classical apologetics argues the pre-Islamic rituals at Mecca were originally "
            "Abrahamic — established by Abraham and Ishmael when they built the Ka'ba — "
            "and only <em>superficially</em> corrupted by pagan practice afterward. Islam "
            "restored the rituals to their original monotheistic meaning, which is why the "
            "tradition preserves them under new theological framing. The continuity is "
            "not pagan survival; it is prophetic restoration."
        ),
        "refutation": (
            "The \"originally Abrahamic\" narrative has no independent historical or "
            "archaeological support — it is an intra-Islamic claim asserted about its own "
            "rituals. The documented pre-Islamic Arabian religious practice at Mecca "
            "included the Safa-Marwa run, the Black Stone veneration, and the Ka'ba "
            "circumambulation, all performed by polytheists worshipping multiple deities. "
            "The rebadging under Islam retained the practice and replaced the theology. "
            "The same pattern — inherited ritual with substituted meaning — is exactly "
            "what Islam elsewhere criticises in other religions as corruption. Applying "
            "the critique outward but not inward is the standard move; it does not "
            "rehabilitate the underlying practice."
        ),
    },
    {
        "anchor": "The moon was split into two halves during the time of Allah's Messenger.",
        "response": (
            "Classical tradition holds that the moon-splitting was a miracle performed in "
            "response to Meccan demands for a sign — genuinely witnessed by Muhammad's "
            "contemporaries and preserved across multiple <em>sahih</em> chains. The "
            "absence of Chinese or Byzantine astronomical records is explained by "
            "localised miraculous manifestation, by the event's brevity, or by gaps in "
            "surviving records. Modern apologists point to lunar geological features "
            "(the Ariadaeus rille) as possible physical residue."
        ),
        "refutation": (
            "\"Localised miracle\" does not match the verse's language — \"the moon has "
            "split\" is a cosmological claim, not a perspectival one. A genuine "
            "splitting would have been recorded by Chinese astronomers (who maintained "
            "meticulous lunar observation in the 7th century), by Indian observers, by "
            "Byzantine chroniclers, and by any ordinary observer who looked up. Their "
            "total silence is diagnostic. The \"rille\" claim is a modern misreading of "
            "geological features formed billions of years before Islam. A miracle whose "
            "only evidence is the testimony of the community that already believed is "
            "indistinguishable from a claim."
        ),
    },
    {
        "anchor": "Your fire is one-seventieth of the heat of hellfire.",
        "response": (
            "Classical theology reads the hadith as rhetorical emphasis on the "
            "unimaginable intensity of hellfire, not a specific thermodynamic "
            "measurement. The \"seventy times\" idiom is commonly used in Semitic "
            "languages for \"very many\" rather than precise arithmetic. The hadith's "
            "function is pedagogical — impressing on believers the seriousness of "
            "eschatological consequence in terms 7th-century listeners could grasp, not "
            "making a physical claim."
        ),
        "refutation": (
            "\"Rhetorical emphasis\" is the general apologetic defense for every hadith "
            "that makes a falsifiable physical claim, and if it defuses anything it "
            "explains nothing. The tradition also gives many specific numerical claims "
            "about the dimensions, duration, and physical features of hell — a "
            "70-year-falling rock, 60-cubit body measurements, specific temperature "
            "ratios — and the cumulative effect is an eschatology with measurable "
            "specificity, not general warning. The escalation pattern (ever-larger "
            "numbers, ever-more-vivid torments) has the shape of rhetorical competition "
            "rather than moral reflection. A religion that multiplies the temperature of "
            "hell when challenged has substituted bigger threats for better arguments."
        ),
    },
    {
        "anchor": "Gog and Magog will be released. They will pass by Lake Tiberias and drink it dry",
        "response": (
            "Classical apologetics treats the Gog-Magog prophecy as continuing the "
            "biblical tradition (Ezekiel 38–39, Revelation 20:7–10) with Muhammad "
            "providing additional detail. The thematic continuity across Abrahamic "
            "traditions is read as confirmation of common apocalyptic truth rather than "
            "mere literary borrowing. Lake Tiberias is cited as a specific geographic "
            "marker giving the prophecy identifiable fulfillment criteria."
        ),
        "refutation": (
            "\"Common apocalyptic truth\" is available as framing but does not distinguish "
            "Quranic eschatology from the Jewish-Christian apocalyptic literary tradition "
            "from which it demonstrably borrows. The Gog-Magog mythology is preserved in "
            "Jewish scripture centuries before Islam; the Quran's version is downstream. "
            "The specific \"drinking Lake Tiberias dry\" detail is pictorial apocalyptic "
            "imagery, not a geological claim — and is not falsifiable in any operational "
            "sense because the lake could be restored after the event. No archaeological "
            "trace of the Dhul-Qarnayn wall has been located despite extensive "
            "exploration, which is the expected finding for a borrowed mythology rather "
            "than historical event."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/nasai.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

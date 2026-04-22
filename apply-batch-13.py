#!/usr/bin/env python3
"""Batch 13: Quran Moderate entries 1-40."""
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
        "anchor": "gardens [in Paradise] beneath which rivers flow. Whenever they are",
        "response": (
            "Classical theology reads paradise descriptions as accommodations to human "
            "imagination — 7th-century Arabian listeners needed tangible images, and the "
            "Quran uses gardens, rivers, and companionship as pedagogical vocabulary. "
            "Quran 32:17 itself says \"no soul knows what comfort has been prepared "
            "for them,\" suggesting the concrete descriptions are provisional symbols "
            "for a reality beyond earthly categories."
        ),
        "refutation": (
            "The symbolic reading cannot be sustained across Quran and hadith: "
            "specific sexual-reward details (maidens of equal age, unbroken by jinn or "
            "humans, 72 virgins per martyr) make no sense as mere metaphor and are "
            "consistently read literally by classical tafsir. The gender asymmetry is "
            "diagnostic — men receive specific sexual inventory; women receive reunion "
            "with earthly husbands. A pedagogical symbol-system that rewards only one "
            "sex specifically has revealed the imagination of the culture that "
            "produced it."
        ),
    },
    {
        "anchor": "Strike him [i.e., the slain man] with part of it [the sla",
        "response": (
            "Classical apologetics treats the cow narrative as divine teaching of the "
            "Israelites' obedience and the power of Allah to revive the dead — a "
            "miracle story confirming prophetic authority. The variations from the "
            "biblical red-heifer ritual are framed as Quran preserving genuine prophetic "
            "tradition that Jewish scripture distorted; the differences are not errors "
            "but corrections."
        ),
        "refutation": (
            "The story is a conflation of two separate Torah ceremonies (Numbers 19's "
            "red heifer purification ritual and Deuteronomy 21's unsolved-murder broken-"
            "neck rite), neither of which involves reviving the dead. The Quran's "
            "version transforms legal ritual into miracle narrative. That transformation "
            "is what happens when stories cross oral transmission between communities — "
            "original legal specifics become colorful miracle-lore. It is the signature "
            "of folk retelling, not divine correction."
        ),
    },
    {
        "anchor": "And We gave Jesus, the son of Mary, clear proofs and supported him wit",
        "response": (
            "Classical apologetics argues Quran's \"Holy Spirit = Gabriel\" identification "
            "corrects an error in Christian Trinitarian theology. The Quran confirms what "
            "the original scriptures taught (Jesus supported by a messenger-angel) and "
            "rejects the post-biblical deification of that messenger into a third person "
            "of a divine Trinity."
        ),
        "refutation": (
            "The identification requires rejecting all known Jewish and Christian "
            "literature — where the Holy Spirit (<em>ruach ha-kodesh</em>, <em>"
            "pneuma hagion</em>) is consistently described as Allah's own spirit or "
            "presence, never as an angel. \"Gabriel\" is named repeatedly in the Bible "
            "as a messenger angel <em>distinct</em> from the Spirit. A divine author "
            "correcting the Christian and Jewish traditions He claims to confirm should "
            "not make identification changes the source texts flatly contradict."
        ),
    },
    {
        "anchor": "And they followed [instead] what the devils had recited during the rei",
        "response": (
            "Classical tafsir frames Harut and Marut as testing agents sent by Allah to "
            "expose human susceptibility to magic — they announce themselves as "
            "temptation (\"we are only a trial, so do not disbelieve\"), preserving their "
            "character as angels while their function serves a divine pedagogical "
            "purpose. The passage is theodicy in narrative form, not endorsement of "
            "angelic disobedience."
        ),
        "refutation": (
            "Angels teaching magic — however framed — places the Quran in tension with "
            "its own repeated definition of angels as perfectly obedient beings who do "
            "only what Allah commands (66:6, 16:50). Either Allah commanded them to "
            "teach magic (placing divine agency behind the spread of sorcery that the "
            "same Quran condemns), or they disobeyed (contradicting angelic nature), or "
            "they were not angels (contradicting the passage). Classical commentators "
            "recognised the problem and produced competing interpretations, none of which "
            "fully resolve the tension the text creates."
        ),
    },
    {
        "anchor": "Prescribed for you is legal retribution for those murdered — the free",
        "response": (
            "Classical apologetics argues the verse establishes <em>qisas</em> within "
            "the social categories already existing in 7th-century Arabia, while "
            "simultaneously introducing restraint (only equivalent retribution, not "
            "unlimited blood-feud vengeance). The graduated structure is reform relative "
            "to pre-Islamic Arab practice, not endorsement of the ranking system. "
            "Modern reformist jurisprudence increasingly applies equal <em>qisas</em> "
            "across status categories."
        ),
        "refutation": (
            "\"Reform relative to pre-Islamic practice\" concedes the ethics are "
            "historical-cultural, not eternal. The verse explicitly tiers human lives "
            "by sex and legal status (free/slave), encoding that tiering into divine "
            "law. Modern equalising reform requires reading the tradition against its "
            "classical grain. A legal framework whose foundational <em>qisas</em> "
            "categories rank humans by status has embedded hierarchy into the "
            "definition of justice — and the classical jurisprudence applied the "
            "tiered schedule for fourteen centuries."
        ),
    },
    {
        "anchor": "Or [consider such an example] as the one who passed by a township whic",
        "response": (
            "Classical tafsir treats the 100-year preservation of food as a miraculous "
            "sign demonstrating Allah's power over decay — the preserved food and "
            "reviving donkey are specific divine suspensions of natural law for "
            "pedagogical purpose. The text does not claim food is normally preservable; "
            "it claims Allah miraculously preserved it for this specific teaching."
        ),
        "refutation": (
            "The apologetic \"miracle\" framing is available but creates a pattern "
            "problem: whenever a Quranic story contains physical impossibility, "
            "\"miracle\" is invoked without text-internal support for the miracle's "
            "scope. The food-preservation detail is incidental to the story's alleged "
            "theological point (divine power over time), which could be demonstrated "
            "without specific impossible physical claims. The detail's presence — and "
            "its similarity to legendary elements in earlier Jewish and Christian "
            "apocrypha (e.g., the Legend of Abimelech) — is the signature of folk "
            "narrative, not independent revelation."
        ),
    },
    {
        "anchor": "Take four birds and commit them to yourself. Then put on each hill a p",
        "response": (
            "Classical tafsir frames this as Abraham's request for experiential "
            "knowledge of resurrection — Allah teaches by demonstration. The bird "
            "story's absence from the Bible is not an error; it preserves a genuine "
            "prophetic tradition Jewish scripture omitted or lost. Elements resembling "
            "Genesis 15 (Abraham's covenant sacrifice) are coincidental or reflect "
            "common Near Eastern symbolic vocabulary."
        ),
        "refutation": (
            "The similarity to Genesis 15 is structural (cut birds, divine "
            "intervention, revelation about the future) and too specific to be "
            "coincidental. The Quranic version transforms legal-covenantal ritual "
            "(cutting animals to seal an oath between parties who pass through the "
            "pieces) into a resurrection-demonstration. That transformation is "
            "typical of oral-tradition repurposing. A revelation preserving "
            "\"genuine lost tradition\" should not also include narrative edits that "
            "mirror how folk retelling reshapes stories."
        ),
    },
    {
        "anchor": "Indeed, the example of Jesus to Allah is like that of Adam.",
        "response": (
            "Classical apologetics argues the Quran is refuting a specific Christian "
            "argument: if Jesus's divinity were inferred from his virgin birth, Adam "
            "(created without either parent) would have a stronger claim. The Quran "
            "exposes this logical weakness in popular Christian devotion without "
            "addressing the formal theological arguments of sophisticated Christology."
        ),
        "refutation": (
            "The \"popular devotion\" framing concedes the Quran is addressing a "
            "straw-man Christology rather than the actual claim: Christian theology "
            "locates Jesus's divinity in his preexistent relationship to the Father "
            "and his resurrection, not primarily in the mechanics of his birth. The "
            "Quran's Adam-parallel is a category error — it refutes a claim "
            "Christians do not actually make. A divine author correcting Christian "
            "theology should be addressing the theology Christians confess, not its "
            "most easily-refutable misrepresentation."
        ),
    },
    {
        "anchor": "Abraham was neither a Jew nor a Christian, but he was one inclining to",
        "response": (
            "Classical apologetics argues Abraham's pre-Judaism status as <em>hanif</em> "
            "(pure monotheist) means his religion was proto-Islamic monotheism before "
            "either Judaism or Christianity formed. The Quran's \"Abraham was a Muslim\" "
            "is correct in the linguistic sense of \"one who submits\"; Islam is the "
            "restoration of the original Abrahamic religion, not a new religion "
            "displacing it."
        ),
        "refutation": (
            "The retroactive labeling is theological self-positioning, not historical "
            "description. Abraham in the Hebrew Bible is presented as covenant-maker "
            "with YHWH through specific ritual and genealogical structures (circumcision, "
            "land promise, Isaac-lineage) that are continuous with Judaism, not "
            "abstracted from it. Claiming Abraham for Islam while defining \"Muslim\" "
            "generically enough to include him (and Moses, and the other Hebrew "
            "patriarchs) deprives the term of specific content and makes the claim "
            "linguistically trivial rather than historically informative."
        ),
    },
    {
        "anchor": "You are the best nation produced for mankind.",
        "response": (
            "Classical apologetics frames \"best nation\" as aspirational description "
            "of the community's moral potential when it enjoins good and forbids evil "
            "— the \"best\" status is <em>conditional</em> on fulfilling those "
            "criteria, not an ontological claim. Muslims who fail these duties forfeit "
            "the title; the verse is therefore a charge to virtue, not supremacism."
        ),
        "refutation": (
            "The conditional framing is available but has not been the operative "
            "reading: classical tafsir and popular Muslim discourse have applied \"best "
            "nation\" categorically, with enjoining good and forbidding evil treated "
            "as the community's corporate mission rather than as condition for status. "
            "The contrast with New Testament descriptions of the church (received grace, "
            "not superiority) is stark. A scripture that names one religious community "
            "as \"best of peoples\" has embedded supremacist framing regardless of the "
            "conditional apologetic."
        ),
    },
    {
        "anchor": "We will cast terror into the hearts of those who disbelieve for what t",
        "response": (
            "Classical apologetics argues \"terror\" (<em>ru'b</em>) refers to divinely-"
            "instilled dread in enemy hearts — psychological advantage granted by Allah "
            "before battle, not a tactic Muslims deliberately employ against civilians. "
            "The terror is a gift Allah gives the believers, not an instrument Muslims "
            "wield. Modern apologists contrast this with contemporary terrorism's "
            "deliberate civilian-targeting."
        ),
        "refutation": (
            "Classical Islamic military doctrine (al-Shaybani, al-Mawardi) developed "
            "\"terror\" into active operational principles — exemplary executions, "
            "enemy-facing displays, psychological warfare — that go beyond passive "
            "divine gift. The Arabic <em>ru'b</em> and <em>irhab</em> (modern Arabic "
            "for terrorism) share the same linguistic root, and modern jihadist "
            "citation of these verses is not misreading; it is application of the "
            "tradition classical jurisprudence systematically elaborated."
        ),
    },
    {
        "anchor": "And do not say about those who are killed in the way of Allah, 'They a",
        "response": (
            "Classical theology treats the martyr's continued-life claim as "
            "eschatological reality: the righteous slain experience paradise "
            "continuously from death onward, without the intermediate state of "
            "grave-waiting that applies to ordinary believers. The psychological "
            "effect on combatants is incidental; the theological content is about "
            "Allah's special honor for those killed in righteous cause."
        ),
        "refutation": (
            "The incentive structure is exactly what the doctrine produces: a religious "
            "tradition offering continuous-paradise-from-moment-of-death as reward for "
            "dying in battle has designed the exact psychological framework for "
            "religiously-motivated violent self-sacrifice. Modern extremist "
            "recruitment cites these verses verbatim, not as distortion but as "
            "accurate application. Whatever the theological content, the operational "
            "effect has been the normalisation of martyrdom as religious goal — which "
            "is the problem responsible religious ethics needs to address, not "
            "relabel."
        ),
    },
    {
        "anchor": "It is He who has sent down to you the Book; in it are verses precise",
        "response": (
            "Classical theology reads the \"precise\" vs \"ambiguous\" distinction as "
            "evidence of divine wisdom: some verses are legally clear and form the "
            "<em>muhkam</em> core; others (the <em>mutashabih</em>) require "
            "interpretive work and invite scholarly engagement. The ambiguity is "
            "pedagogical, not contradictory, and motivates the tafsir tradition's "
            "ongoing reflection."
        ),
        "refutation": (
            "The Quran elsewhere claims to be \"clear\" (5:15), \"easy\" (54:17), and "
            "\"an explanation for everything\" (16:89) — but 3:7 concedes some verses "
            "cannot be understood by anyone except Allah. The two claims cannot both "
            "be comprehensively true. The \"clear+ambiguous in balance\" reading "
            "requires treating the clarity verses as rhetorical hyperbole. That is the "
            "apologetic patch the tradition's own divisions reveal: clarity for "
            "external-facing claims, ambiguity when theological or legal problems "
            "surface."
        ),
    },
    {
        "anchor": "Then do they not reflect upon the Quran? If it had been from [any] oth",
        "response": (
            "Classical apologetics argues the verse does not promise zero surface "
            "contradictions — it promises that <em>apparent</em> contradictions can all "
            "be resolved through proper interpretation, abrogation theory, context, and "
            "tafsir. The challenge is to the discerning reader to work through the "
            "resolutions, which classical scholars have done in massive commentary "
            "literature."
        ),
        "refutation": (
            "\"Many apparent contradictions that can all be resolved with sufficient "
            "interpretive work\" is structurally indistinguishable from \"contains "
            "contradictions.\" 4:82 promises the absence of <em>ikhtilaf</em> "
            "(discrepancy) — a claim the text fails in areas apologetics must "
            "manage: no-compulsion vs fight-until-religion-is-for-Allah, kind-to-"
            "parents vs disown-unbeliever-parents, equal-justice-for-wives vs "
            "you-cannot-be-equal-between-wives. A book whose self-stated test is "
            "\"no discrepancy\" requires unfalsifiable interpretive rescue to pass its "
            "own test."
        ),
    },
    {
        "anchor": "This day I have perfected for you your religion and completed",
        "response": (
            "Classical apologetics addresses the post-5:3 revelation problem through "
            "two approaches: (1) 5:3 refers specifically to the completion of the "
            "<em>rituals</em> of Hajj, not the entire religious legislation; (2) "
            "chronological ordering of Quranic revelation is uncertain, and some verses "
            "traditionally dated later may actually precede 5:3. On either reading, "
            "the \"perfected\" claim does not contradict subsequent revelation."
        ),
        "refutation": (
            "The \"just Hajj rituals\" reading is a narrowing not in the verse's text. "
            "\"I have perfected your religion and completed My favor\" is categorical. "
            "Classical tradition accepts multiple verses as revealed after 5:3 — 2:281 "
            "(often called the \"last verse\"), 4:176, and others. If the religion was "
            "\"perfected\" at 5:3, subsequent revelation is either superfluous or the "
            "religion was not yet perfected. The chronology-uncertainty defense is "
            "itself diagnostic: a scripture whose completion-claim cannot be "
            "reconciled with its composition history without reshuffling the order is "
            "a scripture with a design issue."
        ),
    },
    {
        "anchor": "And know that anything you obtain of war booty — then indeed, for Alla",
        "response": (
            "Classical apologetics frames Muhammad's 20% share (<em>khumus</em>) as "
            "public-purpose funding — supporting orphans, the poor, travellers, the "
            "Prophet's household in its public representative capacity, and the needs "
            "of the <em>umma</em>. The Prophet's simple personal lifestyle is cited as "
            "evidence that the <em>khumus</em> did not personally enrich him; he "
            "administered it for community welfare."
        ),
        "refutation": (
            "Structural dependency of prophetic authority on war-plunder volume is "
            "the problem, not whether individual instances produced personal luxury. "
            "A religious leader whose revenue scales with successful military "
            "operations has an institutional incentive favouring continued war-"
            "making. The \"public purposes including the Prophet's household\" "
            "framing concedes that material flow from raid to prophetic authority "
            "was direct and systematic. A prophecy whose financial model fuses with "
            "procurement has a design problem modest personal living does not "
            "repair."
        ),
    },
    {
        "anchor": "Indeed, Allah has purchased from the believers their lives and their p",
        "response": (
            "Classical theology reads 9:111 as eschatological promise: believers who "
            "sincerely commit their lives to divine purposes receive paradise in "
            "return. The language of commerce is metaphor for the deeper reality of "
            "divine promise backed by all Allah's trustworthiness. The verse is "
            "motivational theology, not literal transaction economics."
        ),
        "refutation": (
            "Whether literal or metaphorical, the verse frames religious commitment as "
            "transaction — specifically, one in which life is exchangeable for "
            "paradise. That framing has been cited in every major jihadist recruitment "
            "tradition from medieval to modern, because the transactional structure "
            "is the text's plain content. A religion that uses marketplace vocabulary "
            "for its martyrdom doctrine has designed an incentive structure whose "
            "operational consequences are exactly what the vocabulary predicts."
        ),
    },
    {
        "anchor": "But indeed, We have tried your people after you [depart",
        "response": (
            "Classical apologetics treats \"al-Samiri\" as a tribal name or descriptor "
            "— perhaps an Israelite tribe or a specific individual named for his "
            "region — not necessarily connected to the later Samaritan community. "
            "The linguistic similarity is coincidental or reflects a shared root that "
            "predated the post-exile Samaritan emergence."
        ),
        "refutation": (
            "\"Al-Samiri\" (<em>al-Samiriyy</em>) in Arabic most naturally means "
            "\"the Samaritan\" — a designation for a member of the Samaritan community. "
            "The Samaritans as a distinct ethnic-religious community emerged after the "
            "Assyrian conquest of the northern Israelite kingdom (722 BCE), centuries "
            "<em>after</em> Moses. The Quran's use of the term in a Mosaic context is "
            "an anachronism. The \"coincidental name\" defense requires stipulating a "
            "pre-Samaritan Arabic usage for which there is no independent attestation."
        ),
    },
    {
        "anchor": "And those who accuse chaste women and then do not produce four witness",
        "response": (
            "Classical apologetics argues the four-witness rule protects accused women "
            "from defamation, not shields rapists — and that rape prosecution operates "
            "under <em>ghasb</em> (coercion) rather than <em>zina</em> rules, with "
            "different evidentiary standards. Modern reformist scholars emphasise that "
            "rape victims have never been required to produce four witnesses of the "
            "assault itself; that application is modern misuse."
        ),
        "refutation": (
            "Pakistan's Hudood Ordinance (1979-2006), northern Nigeria's current "
            "Sharia implementation, and parts of Sudan's criminal code have all "
            "applied the four-witness standard in rape cases, with rape victims "
            "charged with <em>zina</em> based on pregnancy evidence when they could "
            "not meet the witness bar. \"Modern misuse\" frames systematic "
            "application across multiple jurisdictions as aberration, but the "
            "classical jurisprudence left ample room for this reading. If the "
            "Quranic rule were clearly protective, these misapplications should not "
            "have textual warrant — but they do."
        ),
    },
    {
        "anchor": "Or have you thought that the companions of the cave and the inscriptio",
        "response": (
            "Classical apologetics argues the Seven Sleepers narrative preserves a "
            "historical event that both Christian and Islamic traditions record, "
            "reflecting genuine divine providence for righteous persons in persecution. "
            "The Christian apocryphal version is a parallel preservation, not the "
            "source. Details of the Quranic account (the youths' prayer, the dog, the "
            "precise year-count) are distinct enough to suggest independent witness."
        ),
        "refutation": (
            "The Seven Sleepers story is documented in Syriac Christian literature "
            "(Jacob of Serugh, d. 521 CE) more than a century before the Quran's "
            "revelation, and was widely circulated in Near Eastern Christianity. The "
            "Quranic version's details (sleeping in a cave, miraculous preservation, "
            "waking with anachronistic coinage) track the Christian legend closely. "
            "\"Independent witness\" requires evidence the Quran did not access the "
            "circulating Syriac tradition — evidence that does not exist. The "
            "\"parallel preservation\" framing is the shape of tradition-borrowing, "
            "not divine corroboration."
        ),
    },
    {
        "anchor": "So they set out, until when they met a boy, he killed him.",
        "response": (
            "Classical theology reads the Khidr narrative as establishing the reality "
            "of hidden divine knowledge (<em>'ilm al-ghaib</em>) — Khidr acts on "
            "information Moses does not have access to, demonstrating that apparent "
            "moral violations can serve deeper divine purposes. The verse teaches "
            "epistemic humility about the limits of human moral judgment when divine "
            "foreknowledge is involved."
        ),
        "refutation": (
            "The theological lesson undermines the moral framework Islam elsewhere "
            "insists on: if divine foreknowledge justifies preemptive killing of "
            "someone who has not yet sinned, the Quran's judicial and ethical "
            "verses (which require actual offense before punishment) are "
            "compromised. Classical commentators struggled with this precisely "
            "because it concedes that divine purposes can license acts that look "
            "like injustice. \"Hidden divine knowledge\" is unfalsifiable by "
            "construction — any act can be defended as serving purposes only God "
            "knows. That is exactly the epistemic move that religious violence has "
            "used for fourteen centuries."
        ),
    },
    {
        "anchor": "So have you considered al-Lat and al-Uzza?",
        "response": (
            "Classical apologetics contests the historicity of the Satanic Verses "
            "incident: the earliest biographical sources (al-Waqidi, Ibn Ishaq, al-"
            "Tabari) preserve it, but Ibn Hazm and later defenders argued the "
            "account is unreliable or misattributed. On this view, 22:52 addresses "
            "a general danger (Satan's interference with prophetic messaging) "
            "without specifically conceding the al-Lat/al-Uzza episode happened."
        ),
        "refutation": (
            "The narrative is preserved in the earliest layer of Islamic historical "
            "literature — Ibn Ishaq's biography (8th century, within the lifetime "
            "of people who knew eyewitnesses' children), al-Tabari's tafsir, and "
            "al-Waqidi's <em>Maghazi</em>. Rejecting these sources wholesale damages "
            "the historical foundation on which most Islamic biography rests. "
            "\"Unreliable\" selectively applied to embarrassing material while the "
            "same sources are cited elsewhere is the classic apologetic double-"
            "standard. The verse 22:52 exists in the canonical Quran precisely "
            "because it was revealed in response to exactly the incident the "
            "apologetic denies."
        ),
    },
    {
        "anchor": "Over it are nineteen [angels].",
        "response": (
            "Classical tafsir treats the \"19 angels\" as eschatological-theological "
            "claim about hell's administration, not a numerological prophecy. Rashad "
            "Khalifa's code was eventually rejected by mainstream Islamic scholarship "
            "(he was declared apostate by multiple authorities before his "
            "assassination). The verse operates within classical eschatology, not "
            "within Khalifa's system."
        ),
        "refutation": (
            "The mainstream rejection of Khalifa's code came only after his specific "
            "numerical predictions failed and his methodology was exposed as "
            "selective. For decades his code was embraced by many modern apologists "
            "specifically because it seemed to offer scientific-miracle evidence for "
            "the Quran. The eventual rejection was not based on the verse's "
            "original meaning (mainstream classical tafsir also found the 19 "
            "specification odd), but on Khalifa's specific misuse. A verse whose "
            "numerical specificity can be so readily weaponised for spurious "
            "\"miracles\" — and was — is a verse whose function the mainstream has "
            "had to disavow retrospectively."
        ),
    },
    {
        "anchor": "And to Solomon were gathered his soldiers of the jinn and men and bird",
        "response": (
            "Classical apologetics argues the Quranic Solomon preserves features of the "
            "historical Solomon the Biblical account attenuated — including genuine "
            "divine-power demonstrations over the natural world. Jewish apocryphal "
            "literature (Testament of Solomon, 1st–3rd century CE) contains similar "
            "jinn-controlling stories, suggesting a genuine oral tradition the "
            "canonical Bible omitted."
        ),
        "refutation": (
            "The Testament of Solomon is precisely the kind of apocryphal literature "
            "Islam elsewhere rejects as post-biblical embellishment — but the Quran "
            "preserves material continuous with it. The jinn-controlling, animal-"
            "speaking, wind-riding Solomon is Near Eastern legendary Solomon, not "
            "biblical Solomon. The Quran's Solomon is the Solomon of the "
            "late-antique Jewish-apocryphal imagination, not the Solomon of "
            "1 Kings. That tells us which sources were actually circulating in "
            "7th-century Arabia and being absorbed into the new scripture."
        ),
    },
    {
        "anchor": "Created man from a clinging substance [alaqah]",
        "response": (
            "Classical apologetics argues <em>'alaqah</em> refers to embryological "
            "stages modern medicine has confirmed — the zygote does attach to the "
            "uterine wall, and the term can mean \"clinging substance\" as well as "
            "\"blood clot.\" Modern apologetic literature (Bucaille, Naik) cites "
            "the term as scientific miracle predating modern embryology."
        ),
        "refutation": (
            "<em>'alaqah</em> in classical Arabic and in all traditional tafsir means "
            "\"leech\" or \"clinging blood clot\" — the retrofitted \"clinging "
            "substance\" gloss is modern apologetic work. The Quranic embryology "
            "(drop → clot → lump of flesh → bones clothed with flesh) matches almost "
            "exactly with Galen's 2nd-century medical model, which was the standard "
            "in the Roman-Arab world for centuries before Muhammad. \"Scientific "
            "miracle\" reading requires the Quran to have anticipated modern "
            "embryology; the text simply reproduces already-available Greek "
            "physiology."
        ),
    },
    {
        "anchor": "Pharaoh said, 'O Haman, build for me a tower that I might reach the wa",
        "response": (
            "Apologists argue \"Haman\" may be a title rather than a name — an "
            "Egyptian official's role — or may refer to a differently-named Egyptian "
            "figure whose name coincidentally matches Esther's Persian Haman. Modern "
            "apologetic literature cites possible Egyptian etymology for an official "
            "title resembling \"Hamnan.\""
        ),
        "refutation": (
            "Egyptian records preserve detailed court structures with specific "
            "official titles — none match \"Haman.\" Haman in Persian-Jewish "
            "literature is the villain of Esther, set in the Achaemenid court "
            "centuries after Exodus. The \"title not name\" and \"coincidental Egyptian "
            "Haman\" defenses are unattested stipulations. The Quran's narrative "
            "combines an Exodus-era Pharaoh with a Persian-era name and a "
            "Mesopotamian-style ziggurat — the three elements together are the "
            "fingerprint of a composite narrative drawing from multiple circulating "
            "traditions, not from independent divine knowledge."
        ),
    },
    {
        "anchor": "And We took the Children of Israel across the sea, and Pharaoh",
        "response": (
            "Classical apologetics argues the Quran's distinction between Pharaoh's "
            "body (preserved as a sign) and his drowning is genuine, and some modern "
            "apologists cite Ramesses II's preserved mummy as fulfillment. The "
            "details are compatible: Pharaoh drowned, but his body was later recovered "
            "and preserved — exactly what the Quran indicates."
        ),
        "refutation": (
            "The Pharaoh-mummy apologetic is weak historical reasoning. Ramesses II's "
            "body was preserved through standard Egyptian mummification after death, "
            "not as divine sign. The verse 10:92 says \"We will preserve your body, "
            "that you may be a sign\" — as if uniquely preserved, distinct from all "
            "other Egyptian Pharaohs. But every major Pharaoh was mummified; "
            "Ramesses's preservation is not exceptional. The retrofitting of a "
            "standard Egyptian funerary practice as Quranic miracle is the shape of "
            "retroactive reading, not genuine prediction."
        ),
    },
    {
        "anchor": "And the sun runs [on course] toward its stopping point.",
        "response": (
            "Modern apologetic readings interpret the sun's \"running to a resting "
            "place\" as referring to the sun's actual galactic motion — the Solar "
            "System orbits the galactic center over roughly 230 million years. The "
            "verse is read as anticipating heliocentric and galactic astronomy "
            "discoveries made in the 20th century."
        ),
        "refutation": (
            "The galactic-motion reading is pure retrofit. Classical tafsir read "
            "the \"run\" language in the context of geocentric cosmology — the sun's "
            "apparent daily motion across the sky as literal traversal. The "
            "\"resting place\" was interpreted as the sun's nightly retreat (other "
            "hadith describe this as under Allah's throne). Modern apologists read "
            "modern astronomy back into the verse; the classical readers could not, "
            "because they didn't have the galactic framework available. This is the "
            "standard i'jaz 'ilmi pattern: compatibility reasoning after the "
            "science settles, not prediction before."
        ),
    },
    {
        "anchor": "[This is] a Book whose verses are perfected and then presented in deta",
        "response": (
            "Classical apologetics frames the tafsir tradition as <em>application</em> "
            "of clarity, not contradiction of it. The Quran is clear in its core "
            "monotheistic message and moral framework; commentary develops the "
            "implications for specific legal, historical, and contextual "
            "applications. The commentary tradition is fulfillment of the text's "
            "invitation to reflection, not evidence against its clarity."
        ),
        "refutation": (
            "Fourteen centuries of tafsir that routinely disagree with each other on "
            "core theological and legal matters — including whether a verse is "
            "abrogated, how a command applies, what the text even means — is "
            "not \"application of clarity.\" The classical commentaries (Tabari, "
            "Qurtubi, Ibn Kathir, Razi, Zamakhshari, Tabarsi) preserve substantive "
            "disagreements on fundamental interpretive questions. A text genuinely "
            "clear enough to need no interpretation would not have produced "
            "thousands of volumes of scholarly dispute about what it means. The "
            "\"clear but requires elaboration\" defense is the apologetic patch that "
            "concedes exactly the problem."
        ),
    },
    {
        "anchor": "Until, when Our command came and the oven overflowed",
        "response": (
            "Classical tafsir offers varying interpretations of the \"oven\" "
            "(<em>tannur</em>) — some commentators read it as a geographic feature "
            "(a specific location in Iraq or the Levant), others as figurative "
            "imagery for the flood's onset, others as the point where water first "
            "appeared. The variety reflects interpretive richness, not confusion."
        ),
        "refutation": (
            "The \"variety of interpretations\" is exactly the evidence of the "
            "text's specificity problem: if the passage had a clear referent, "
            "classical commentators would not need multiple hypotheses. The verse "
            "reads as preserving a folk-narrative element whose original meaning "
            "was already unclear by the time the tradition encountered it. "
            "Pre-Islamic Mesopotamian flood traditions (Gilgamesh) feature "
            "different specifics; the Quran's version contains a unique detail "
            "(tannur) that does not appear in the biblical or Mesopotamian "
            "accounts and whose meaning the tradition itself has not resolved."
        ),
    },
    {
        "anchor": "Indeed, it is We who sent down the Quran, and indeed, We will be its g",
        "response": (
            "Classical apologetics reconciles the preservation-promise with Uthmanic "
            "standardisation by distinguishing revelation (which was preserved "
            "through memorisation and divine protection) from codex production "
            "(which required human standardisation to prevent dialectical drift "
            "from creating diverging texts). The burning of variant codices is "
            "framed as necessary community-unity action, not preservation failure."
        ),
        "refutation": (
            "\"Preservation\" that requires human intervention through burning is not "
            "the preservation the verse promises. If Allah guards the Quran, human "
            "fire was unnecessary — the promise is falsified precisely by the "
            "need to destroy alternatives. The companions whose codices were "
            "destroyed (Ibn Mas'ud, Ubayy ibn Ka'b) were among the Prophet's most "
            "trusted Quran-teachers, and their versions had significant textual "
            "differences. A preservation mechanism that required destroying the "
            "alternatives is not divine preservation; it is editorial standardisation "
            "with theological cover."
        ),
    },
    {
        "anchor": "Arise the night, except for a little — half of it",
        "response": (
            "Classical theology treats the staged reduction of night-prayer obligation "
            "as pedagogical accommodation — initial rigor followed by Allah's "
            "merciful adjustment as the community's capacity became clear. The "
            "scaling reflects divine kindness, not divine ignorance. The pattern "
            "matches the 50-to-5 prayer reduction; Allah calibrates obligation to "
            "human capacity through revealed accommodation."
        ),
        "refutation": (
            "\"Allah knew there would be among you those who are ill\" (73:20's "
            "phrasing) places the knowledge-acquisition after the initial command. "
            "Either Allah knew from the start (in which case the stricter original "
            "was unnecessarily burdensome, imposed only to be withdrawn — the "
            "initial prescription was performative) or Allah learned (contradicting "
            "the tradition's omniscience claim). The pedagogical framing is "
            "apologetic retrofit. An omniscient lawgiver should calibrate to the "
            "final level at the first step; adjustment implies imperfect knowledge "
            "of the population being legislated for."
        ),
    },
    {
        "anchor": "When you [wish to] privately consult the Messenger, present before you",
        "response": (
            "Classical tafsir treats 58:12-13 as a brief pedagogical regulation: the "
            "charity-before-consultation rule tested sincerity of those seeking "
            "private audience with Muhammad, exposing the hypocrites who balked at "
            "the small cost. After the test fulfilled its purpose — identifying who "
            "was serious — the rule was relaxed, which is consistent with "
            "<em>naskh</em> theology of progressive divine dispensation."
        ),
        "refutation": (
            "A divine command abrogated after one person complied — and the "
            "relaxation arriving in the very next verse — is not progressive "
            "dispensation; it is admission that the rule failed its intended "
            "purpose. If the test was genuinely informative, it would have been "
            "maintained long enough to produce information. The structure — rule "
            "given, rule abrogated within verses because no one obeyed — reads "
            "exactly like pragmatic adjustment of a legal proposal that didn't "
            "take hold, which is what human legislation looks like when its "
            "sponsor recognises a miscalculation."
        ),
    },
    {
        "anchor": "do not take the Jews and the Christians as allies",
        "response": (
            "Classical apologetics narrows <em>awliya'</em> to military-political "
            "alliance rather than friendship: 5:51 prohibits formal alliance with "
            "hostile Jewish and Christian powers in wartime context, not personal "
            "relationships with individual Jews and Christians. Modern reformists "
            "(Ramadan, Qadhi) cite classical exceptions permitting peaceful "
            "coexistence and interfaith friendship."
        ),
        "refutation": (
            "<em>Awliya'</em> in classical Arabic has a broad range covering "
            "alliance, friendship, protection, trust — not only military alliance. "
            "Classical tafsir (Tabari, Ibn Kathir) read the prohibition broadly, "
            "and modern conservative Muslim discourse continues to apply it to "
            "personal interfaith friendship. The narrow-military reading is the "
            "modern apologetic move that reformists use to make Islam compatible "
            "with pluralistic societies — a welcome reform that requires reading "
            "against the classical grain. A religion whose founding scripture "
            "prohibits (even narrowly) religious-category alliance has embedded "
            "identity politics into its ethical framework."
        ),
    },
    {
        "anchor": "Muhammad is the Messenger of Allah; and those with him are severe agai",
        "response": (
            "Classical apologetics frames \"severe against disbelievers\" as "
            "situational description of wartime conduct — Muslims in active "
            "military confrontation with hostile polytheist powers, not a standing "
            "ethical principle. The paired clause (\"merciful among themselves\") "
            "is the positive internal norm; the \"severity\" is tactical "
            "necessity, not virtue. Modern apologists distinguish this from "
            "contemporary extremist applications."
        ),
        "refutation": (
            "The verse embeds the severity-toward-outsiders / mercy-toward-insiders "
            "pattern into the description of Muhammad's followers as a standing "
            "feature of their identity, not a temporary tactical posture. Modern "
            "radical groups cite this verse verbatim as mission statement, "
            "accurately quoting what the text says. The \"situational, wartime only\" "
            "reading is modern apologetic retrofit; classical tafsir did not "
            "restrict the ethic to specific campaigns. A scripture that defines "
            "believers by their severity toward outsiders has articulated exactly "
            "the in-group ethics the modern application reflects."
        ),
    },
    {
        "anchor": "O Prophet, fight against the disbelievers and the hypocrites",
        "response": (
            "Classical apologetics distinguishes between fighting external "
            "disbelievers (military confrontation with hostile powers) and dealing "
            "with internal hypocrites (social-ethical pressure, not armed "
            "violence). The word \"fight\" (<em>jahid</em>) against hypocrites is "
            "understood as <em>jihad</em> in the broader sense (striving, "
            "rebuking, arguing), not combat. Most classical jurists did not "
            "authorise killing hypocrites in the way they authorised fighting "
            "disbelievers."
        ),
        "refutation": (
            "The <em>jihad</em>-as-broader-striving reading is available but has "
            "not constrained classical applications. The \"hypocrite\" category "
            "is structurally unfalsifiable — internal states of belief cannot be "
            "externally verified, which means anyone a community wishes to "
            "exclude can be labeled <em>munafiq</em>. Modern sectarian killings "
            "within Muslim-majority societies (Shia vs Sunni, Ahmadi persecution, "
            "moderate vs extremist) consistently deploy the hypocrite category "
            "to justify violence against fellow Muslims. A scripture that "
            "authorises \"fighting\" against an unverifiable-by-design internal "
            "category has given sectarian violence structural cover."
        ),
    },
    {
        "anchor": "do not take My enemies and your enemies as allies — extending af",
        "response": (
            "Classical apologetics reads 60:1 in specific historical context: the "
            "Meccan migration era, when some Muslims in Medina had family members "
            "still among the hostile Meccans. The verse addresses active wartime "
            "alliance, not ordinary family affection. Quran 60:7-8 explicitly "
            "permits kindness to non-Muslims who have not fought the community — "
            "which apologists cite as the broader principle."
        ),
        "refutation": (
            "60:7-8 is cited as mitigation — but 60:1's text extends the "
            "prohibition to \"affection\" (<em>mawadda</em>), which is a broader "
            "category than military alliance. The verse regulates emotional-"
            "relational orientation, not just political association. "
            "Reconciling 60:1 with 60:7-8 requires classifying most non-Muslim-"
            "Muslim affection as okay while specific types are prohibited — a "
            "distinction the tradition has drawn inconsistently across fourteen "
            "centuries. The \"specific historical context\" narrowing is modern "
            "reformist work that the classical tradition did not systematically "
            "apply."
        ),
    },
    {
        "anchor": "O Jesus, Son of Mary, did you say to the people, 'Take me and my mothe",
        "response": (
            "Apologists argue 5:116 may address Collyridian-style sects or "
            "functional-veneration practices rather than misidentifying the Trinity. "
            "The \"take me and my mother as deities\" phrasing could be addressing "
            "popular devotional practice that effectively treated Mary as divine, "
            "regardless of official Christological doctrine."
        ),
        "refutation": (
            "The Collyridian hypothesis rests on a sect attested only in Epiphanius's "
            "<em>Panarion</em> and never evidenced as widespread. Orthodox "
            "Christianity — Catholic, Protestant, Eastern Orthodox, Oriental — has "
            "never defined the Trinity as Father/Mary/Jesus. If the Quran is "
            "addressing \"functional\" rather than official theology, the text "
            "should say so; instead it presents the mis-identification as the "
            "target doctrine. A divine author correcting Christian theology "
            "should be engaging the Christianity Christians actually confess."
        ),
    },
    {
        "anchor": "I am the messenger of Allah to you... bringing good tidin",
        "response": (
            "Classical apologetics argues the \"Ahmad\" prophecy finds its Christian "
            "parallel in John 14:16's \"Paraclete\" (<em>Parakletos</em>). Some "
            "apologists propose that <em>Parakletos</em> (\"comforter\") is a "
            "mistranscription of <em>Periklytos</em> (\"praised,\" analogous to "
            "Arabic <em>Ahmad</em>). On this reading, early Christian manuscript "
            "corruption obscured the original prophecy of Muhammad."
        ),
        "refutation": (
            "No Greek manuscript evidence supports <em>Periklytos</em> in any early "
            "copy of John 14. Every surviving early Greek manuscript reads "
            "<em>Parakletos</em>, and the early church fathers consistently "
            "identified the Paraclete as the Holy Spirit (already sent at "
            "Pentecost per Acts 2). The \"mistranscription\" theory requires a "
            "textual corruption so ancient and comprehensive that no pre-"
            "corruption manuscript survives anywhere in the Christian world — a "
            "claim with no independent evidence. A prophetic prediction whose "
            "textual support requires a conjectured mis-spelling unattested in "
            "any manuscript is not prediction; it is retroactive construction."
        ),
    },
    {
        "anchor": "How can I have a boy while no man has touched me?",
        "response": (
            "Classical apologetics argues the Quran's Mary narrative focuses on "
            "specific theological truths (virgin birth, Jesus's prophetic status, "
            "Allah's creative power) and omits Joseph as extraneous to those "
            "purposes. The \"sister of Aaron\" phrase is idiomatic descent-language "
            "in Semitic usage, not literal sister-of-Moses claim. Omission is "
            "theological focus, not historical error."
        ),
        "refutation": (
            "The Quran's Mary narrative contains Aaron as her \"brother\" (19:28), "
            "Imran as her father (3:35 — the Arabic form of Amram, the biblical "
            "father of Moses and the original Miriam), and a birth-under-palm-tree "
            "scene paralleling the apocryphal <em>Pseudo-Matthew</em>. The "
            "cluster of three separate issues (Joseph absent, Mary's lineage "
            "confused with Miriam's, apocryphal birth-narrative) is not "
            "theological focus; it is evidence that the author was working from "
            "oral traditions that had merged the two Marys. A divine narrator "
            "of Jesus's mother's life would not repeatedly attribute to her the "
            "lineage of a woman who lived 1,300 years earlier."
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

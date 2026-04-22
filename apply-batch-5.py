#!/usr/bin/env python3
"""Batch 5: Muslim Strong entries 1-18."""
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
    # 1 — Tent pole, fetus compensation
    {
        "anchor": "A woman struck her co-wife with a tent-pole and she was pregnant and she killed",
        "response": (
            "The classical apologetic frames the hadith as evidence of Islam's sophisticated "
            "fetal-compensation jurisprudence: by assigning a specific monetary value "
            "(<em>ghurra</em>, one slave) to the lost fetus, the law protected pregnant women "
            "from violence by pricing the harm, while also distinguishing the fetus from a "
            "fully-legal person (thus a lesser compensation than full blood-money). Modern "
            "apologists emphasize the verdict as progressive for its time — most 7th-century "
            "legal systems assigned no value to the fetus at all."
        ),
        "refutation": (
            "\"Progressive for its time\" is not a defense of a law that is then treated as "
            "eternal. A divine legal code for all humanity should not embed the 7th-century "
            "practice of using slaves as currency units. The framing also sidesteps the "
            "hadith's implicit endorsement of the household structure that produced the "
            "violence — polygamy putting two women in competition for the same husband, ending "
            "in a lethal blow. The law responds with pricing, not reform; the structural cause "
            "is untouched. Pricing a fetus as \"one slave\" requires the institution of slavery "
            "to give the measurement meaning, which makes slavery structurally load-bearing in "
            "eternal divine law."
        ),
    },
    # 2 — Fugitive slave = disbeliever
    {
        "anchor": "When a slave flees from his master he becomes an unbeliever till he returns",
        "response": (
            "Apologists argue the hadith is hyperbolic rhetorical language emphasising the "
            "seriousness of breaking a social bond — analogous to expressions like \"he who "
            "disobeys the imam has disobeyed me.\" Classical jurisprudence did not literally "
            "treat every fugitive slave as an apostate subject to the death penalty; the hadith "
            "was read as a stern moral rebuke, not a legal ruling. Modern apologists further "
            "emphasise that the Quran encourages manumission (<em>fakk raqabah</em>) as a "
            "virtuous act, so the \"runaway\" context is narrower than it appears."
        ),
        "refutation": (
            "\"Hyperbolic\" is the catch-all apologetic defense for any hadith whose plain "
            "meaning is uncomfortable — and if it defuses anything, it means nothing. "
            "Classical jurists did not uniformly treat the hadith as hyperbole: the "
            "Hanafi and Maliki manuals discussed the fugitive-slave's theological status as a "
            "live legal question, including the possibility of execution where the slave "
            "simultaneously fled Islam. The deeper problem is structural: a religion that "
            "describes the slave's attempt at freedom as equivalent to leaving the faith has "
            "absolutized ownership. The Quran's manumission verses are real but orthogonal — "
            "they encourage freeing slaves voluntarily, not recognising their self-emancipation."
        ),
    },
    # 3 — Empty grave for Jesus
    {
        "anchor": "[Classical tradition, transmitted through hadith commentaries:]",
        "response": (
            "Classical apologists read the \"empty grave\" tradition as eschatological symbolism "
            "of Jesus's expected return, not a literal architectural reservation. The tradition "
            "emphasizes Jesus's mortality and eventual burial alongside Muhammad as theological "
            "assertion of his human (non-divine) status — correcting Christian claims of "
            "ascension and bodily resurrection. Modern apologists note the tradition is "
            "reported in varying and sometimes contradictory forms, suggesting it circulated as "
            "devotional imagery rather than as architectural specification."
        ),
        "refutation": (
            "The \"symbolic\" framing does not rescue the claim, because the tradition is "
            "specifically physical: a grave is reserved in Medina. The claim is checkable, and "
            "Muhammad's tomb complex in Medina has been photographed, measured, and described "
            "for centuries by pilgrims and scholars without any pre-reserved empty grave being "
            "documented. Classical tafsir (Tabari, Ibn Kathir, al-Qurtubi) treated the "
            "tradition as asserting a real physical fact. If the tradition was meant "
            "symbolically, the specific physical claim should have been disowned when the "
            "reserved grave could not be located; instead, the tradition persists without "
            "physical evidence, which is the shape of a claim that has quietly become "
            "unfalsifiable."
        ),
    },
    # 4 — Cursed Jews and Christians for tomb-worship
    {
        "anchor": "Allah cursed the Jews and the Christians because they took the graves of their p",
        "response": (
            "Apologists argue the hadith forbids worship <em>at</em> graves, not visitation or "
            "respectful remembrance. Classical scholars (Ibn Taymiyyah, Abd al-Wahhab) drew a "
            "distinction between permissible visitation (<em>ziyarat al-qubur</em>) and "
            "prohibited supplication directed to the dead. Salafi reform movements have "
            "explicitly applied this hadith to Muslim practice, criticising tomb-shrines as "
            "un-Islamic. The practice at Muhammad's tomb in Medina is carefully regulated to "
            "forbid direct prayer to him — visitors send <em>salawat</em> to him as they would "
            "anywhere."
        ),
        "refutation": (
            "The reformist distinction (visitation OK, veneration not) is real but has been "
            "systematically violated across Islamic history. Muhammad's tomb is a pilgrimage "
            "destination, with a specific liturgy of visitation, specific prayers recited in "
            "its presence, and specific spiritual benefits ascribed to proximity. That is "
            "\"taking the grave as a place of worship\" under any reasonable reading of the "
            "hadith. Sufi shrine-complexes across the Muslim world — Mawlana in Konya, "
            "Data Ganj Bakhsh in Lahore, Sidi Abu al-Hassan in Cairo — are explicitly "
            "worship-sites. The hadith's prohibition applied to others but not to the "
            "community's own practice is exactly the asymmetry that makes the polemic against "
            "Jews and Christians rhetorically useful and ethically empty."
        ),
    },
    # 5 — Gharqad tree / Jews at end times
    {
        "anchor": "The last hour would not come until the Muslims fight against the Jews",
        "response": (
            "Classical apologetic readings frame the hadith as an eschatological prophecy about "
            "a final battle with <em>specific</em> enemies of the eschatological moment — not "
            "a standing command for Muslims to seek out and kill Jews in general. The hadith "
            "describes what will happen at the end, not what should be done now. Modern "
            "apologists emphasise that the \"Jews\" of the final battle are identified in the "
            "tradition with followers of the Dajjal specifically, a supernatural antichrist "
            "figure — not with Jewish communities as a whole."
        ),
        "refutation": (
            "The \"specific eschatological enemies\" framing is interpretively available but "
            "has not been how the hadith has historically functioned. Hamas's founding charter "
            "(1988, Article 7) cites this hadith directly and explicitly as a mandate for "
            "Muslims to kill Jews. Israeli far-right groups plant Gharqad trees specifically to "
            "\"expose\" Jewish hideouts from the hadith's prophecy. The tradition is active in "
            "modern violence, not quarantined to a distant eschatological moment. A scripture-"
            "status text that functions as prophetic warrant for genocide in the 21st century "
            "is not neutralized by claiming its application was meant to be restricted to the "
            "end of time. The eschatology is operational now — which is exactly the problem."
        ),
    },
    # 6 — Black stone whiter than milk
    {
        "anchor": "The Black Stone descended from paradise and it was more intensely white than mil",
        "response": (
            "The classical reading treats the hadith as theological symbolism: the stone's "
            "visual darkening by \"human sins\" is a vivid image for the cumulative weight of "
            "moral failure across human history, not a geological claim. Apologists argue "
            "similar metaphors appear across religious traditions (defilement imagery, "
            "purity-and-stain language) and are understood by mature readers as symbolic. The "
            "stone's pre-Islamic veneration at the Ka'ba is re-framed through this hadith as "
            "continuous with Abrahamic monotheism rather than as pagan survival."
        ),
        "refutation": (
            "The \"symbolic\" reading is retrofitted. Classical tafsir and hadith commentary "
            "(al-Nawawi, Ibn Hajar) treated the white-to-black transition as a literal "
            "physical event, with the Stone described as having been \"received from "
            "paradise\" and progressively blackened by the contact of sinners. Sin is not a "
            "causal agent that alters the albedo of rock, and no geochemical process explains "
            "the claim. The stone-descent-from-paradise motif is continuous with Semitic "
            "<em>baetyl</em> (sacred stone) traditions stretching back millennia — the Black "
            "Stone's veneration is a pre-Islamic Arabian religious practice that Islam "
            "inherited rather than abolished. The hadith's mythology is pre-Islamic "
            "paganism refitted with a theological frame."
        ),
    },
    # 7 — Rock falling 70 years
    {
        "anchor": "A rock thrown from the brink of Hell would continue falling for seventy years",
        "response": (
            "The apologetic reading treats the hadith as theological hyperbole — emphasizing "
            "the horrifying depth of hell in language that 7th-century listeners could grasp, "
            "not asserting a precise measurement in meters. Modern apologists add that "
            "\"seventy\" in Semitic idiom frequently means \"a very large number\" rather than "
            "a precise count (compare \"seventy times seven\" in Matthew 18:22). The hadith is "
            "doing rhetorical work, not physics."
        ),
        "refutation": (
            "\"Rhetorical hyperbole\" is the general escape for any hadith that makes a "
            "falsifiable physical claim. If every specific number in the hadith corpus is "
            "open to this treatment, the corpus loses all determinate content. Classical "
            "theologians read the hadith as a real measurement; the falling-time claim was "
            "used in serious medieval cosmological thinking about hell's structure. The "
            "hadith is also at odds with other canonical traditions that locate hell inside "
            "the earth or beneath the \"seventh earth\" — a 700-million-kilometer pit does not "
            "fit inside any traditional cosmological diagram. The multiple, contradictory "
            "spatial claims about hell across the hadith canon are better explained as "
            "accumulated folk mythology than as components of a coherent revelation."
        ),
    },
    # 8 — Wailing punishment
    {
        "anchor": "He who is wailed over is punished because of the wailing for him",
        "response": (
            "The apologetic harmonisation follows Aisha's own recorded objection: the hadith "
            "is either misattributed, or contextually limited to those who wished during life "
            "that their community would wail over their death (and so are punished for that "
            "prior intention, not for others' actions at their funeral). Classical scholars "
            "(al-Nawawi, Ibn Hajar) documented the tension with Quran 6:164 and offered "
            "varying reconciliations. Modern apologists note the hadith is evidence of "
            "internal self-correction: the tradition preserves both the problematic hadith and "
            "Aisha's rebuttal of it."
        ),
        "refutation": (
            "Aisha's rebuttal is indeed preserved, which is a point in favour of the "
            "tradition's internal honesty — but her rebuttal is itself evidence that a "
            "canonical hadith contradicts the Quran. That contradiction should not exist in "
            "the first place if the hadith corpus is reliable guidance. The \"contextual "
            "intention\" reading is a patch generated by commentators to reconcile the "
            "contradiction; it is not in the hadith itself. The deeper problem is that a "
            "corpus which regularly requires this kind of harmonisation has conceded that its "
            "materials are not all equally authentic — but the canonical framework treats them "
            "as if they are. The community's preservation of both hadith and counter-hadith is "
            "not a feature; it is a symptom."
        ),
    },
    # 9 — Ethiopians with spears
    {
        "anchor": "The Ethiopians were playing with their spears in the mosque on the day of 'Id",
        "response": (
            "The apologetic reading treats the hadith as a window into Muhammad's recreational "
            "inclusiveness — he permitted the Ethiopian delegation's cultural expression in "
            "the mosque, even shielded his wife's view of it, demonstrating his openness to "
            "non-Arab cultures. Modern apologists emphasise this as an anti-racist moment: "
            "Muhammad welcomed Black cultural performance rather than excluding it, a "
            "corrective to later Islamic (and global) racism. The hadith is framed as evidence "
            "of Muhammad's character, not a problem."
        ),
        "refutation": (
            "The \"inclusive\" framing does not address the actual ethnographic dynamic: the "
            "Arab Prophet and his child-wife watching Black performers as entertainment. The "
            "performers are the spectacle; the Arab pair are the audience. The inclusion is "
            "real, but so is the asymmetry — Ethiopians are welcome to perform, not to sit as "
            "co-audience. Aisha's age at the event (still short enough to rest her chin on "
            "Muhammad's shoulder) is preserved without editorial discomfort, confirming the "
            "timing problem of her marriage. The hadith is valuable less for what it says about "
            "inter-cultural relations than for what it shows about how an intimately "
            "documented private scene became scripture for 1.8 billion people — along with "
            "all of its 7th-century cultural assumptions."
        ),
    },
    # 10 — Child resembles whichever parent's water predominates
    {
        "anchor": "The water of the man is thick and white, and the water of the woman is thin",
        "response": (
            "Apologists argue the hadith describes observed phenomena of 7th-century "
            "reproductive biology in pre-scientific terms — not a claim about genetics. The "
            "\"predominance\" language tracks visible dominance of inherited traits (hair "
            "color, facial features, skin tone), not a claim about sex determination per se. "
            "Modern apologists further argue the hadith's distinction between male and female "
            "reproductive contributions anticipates the idea — novel in its era — that both "
            "parents contribute to the fetus, rather than the then-popular \"seed in soil\" "
            "Aristotelian model where only the male contributed active material."
        ),
        "refutation": (
            "The \"anticipates both parents contribute\" defense is retrofitted: Aristotelian "
            "seed-soil theory was not universal in 7th-century Arabia, and the idea that both "
            "parents contribute physical material was already present in Galenic medicine, "
            "which circulated in the Near East. The hadith's specific claim — that "
            "predominance of one fluid over the other determines the child's likeness — is "
            "false to genetics, where chromosomal contribution is fixed rather than "
            "quantitative-predominance. The \"pre-scientific observation\" framing concedes "
            "that the hadith is reporting ancient folk biology, not revelation. A divine "
            "source speaking about reproduction should not be reproducing pre-Galenic mistakes."
        ),
    },
    # 11 — Banu Mustaliq / withdrawal
    {
        "anchor": "We took captives of the Arabs and we desired women",
        "response": (
            "Classical apologetics frames the hadith as evidence of the Quranic ethical "
            "trajectory even in wartime: Muhammad's companions ask about contraception "
            "(<em>'azl</em>) during concubinage because they wanted to avoid children with "
            "captives, and Muhammad's response — leaving the decision to them — is framed as "
            "granting moral autonomy within a difficult situation. Modern apologists emphasise "
            "that the Quran's long trajectory toward abolition begins with such regulation: "
            "the alternative in the 7th-century Near East was unregulated exploitation with "
            "no theological framework at all."
        ),
        "refutation": (
            "The \"regulation-not-endorsement\" frame is standard but strained: the hadith "
            "records Muhammad's companions asking a detailed Q&A about contraceptive methods "
            "during the sexual use of captured women whose husbands were alive elsewhere. "
            "The moral content is the permission of the act; the method is a technical "
            "footnote. A divine prophet asked this question could have answered with "
            "prohibition; instead the response is <em>'azl</em> is permitted either way. The "
            "\"trajectory toward abolition\" is apologetic retroactive reading — Islam "
            "regulated concubinage without ever abolishing it, and classical jurisprudence "
            "treated the practice as permanent divine permission. The hadith is a snapshot of "
            "the ethics it pretends to transcend."
        ),
    },
    # 12 — Hijrah doesn't cease
    {
        "anchor": "Hijrah will not come to an end until repentance ceases",
        "response": (
            "Apologists argue the hadith describes an ongoing spiritual-emotional orientation "
            "— Muslims must always be ready to migrate (physically or spiritually) from "
            "environments hostile to faith — not a standing command to emigrate from all "
            "non-Muslim societies. Many Muslim scholars (including Yusuf al-Qaradawi) have "
            "explicitly ruled that Muslims can legitimately reside in non-Muslim countries and "
            "participate as citizens, consistent with the hadith's spiritual meaning. The "
            "extremist reading (ISIS, al-Qaeda) is a misappropriation, not a continuation of "
            "mainstream interpretation."
        ),
        "refutation": (
            "The spiritual-orientation reading is possible but has to contend with the hadith's "
            "explicit linkage of hijrah (a physical migration act) to the acceptance of "
            "repentance — a specific eschatological tether that extremist groups read as "
            "directive. The fact that mainstream scholars have had to explicitly counteract "
            "the separatist reading reveals that the text's default sense supports it. "
            "\"Hijrah\" is a specific legal-theological category in Islamic law, not an "
            "abstract metaphor; extending it metaphorically to cover \"spiritual migration\" is "
            "a legitimate pious interpretation but not textually obvious. A hadith that "
            "requires 1,400 years of consistent scholarly rebuttal to prevent its separatist "
            "reading is a text whose structure creates the problem the scholars must solve."
        ),
    },
    # 13 — Ghamidiyya stoned while child watched
    {
        "anchor": "He sent her away until she had given birth, returned to nurse the child",
        "response": (
            "Classical apologetics emphasises the hadith as a story of prophetic mercy within a "
            "structure of divine law. Muhammad repeatedly sent the Ghamidiyya woman away, "
            "giving her opportunities to recant or escape sentence. The two-year nursing "
            "period demonstrates the law's concern for the child's welfare. The stoning was "
            "requested by the woman herself as atonement; the Prophet's reluctance is "
            "preserved in the hadith. The story is read as evidence of Islamic law's "
            "proceduralism, not its brutality."
        ),
        "refutation": (
            "The \"reluctance\" and \"procedural delay\" defenses do not rescue the outcome: a "
            "woman was stoned to death while her weaned child watched. Procedural due-process "
            "before an execution does not change the moral status of the execution. The "
            "hadith's own tender detail — the child with bread in hand — is preserved as "
            "pastoral memory, which tells us the community that preserved the story saw no "
            "moral problem in the scene. A legal system whose most touching episode is a "
            "toddler watching his mother killed for consensual sex has a moral register that "
            "cannot be defended by appealing to the procedure that produced it. The defense "
            "concedes the act and redirects attention to the steps."
        ),
    },
    # 14 — Jewish couple stoned, man shielded her
    {
        "anchor": "I saw the man saving the woman from stones by bending over her.",
        "response": (
            "Classical apologetics emphasises that the stoning was applied to a Jewish couple "
            "by Jewish law — Muhammad ruled according to the Torah's own provisions (Leviticus "
            "20:10, Deuteronomy 22:22), not by imposing Islamic punishment on Jews. The "
            "husband's attempt to shield the wife is preserved in the hadith as a human "
            "detail, not as moral critique of the sentence. The episode is evidence that "
            "Islamic justice, even when applied to non-Muslims, respected their own scriptural "
            "law."
        ),
        "refutation": (
            "The \"applied their own law to them\" defense runs into its own problem: Islam "
            "elsewhere claims the Torah was corrupted (<em>tahrif</em>), so applying its "
            "punishment assumes the authority of a text Islam otherwise rejects. If the Torah "
            "was reliable enough to stone by, it was reliable enough to be consulted on other "
            "questions where Islam disagrees — which is the Islamic Dilemma in miniature. The "
            "husband's shielding is preserved in the canonical narrative without moral "
            "discomfort, which tells us the hadith's editors thought the punishment was just "
            "and the victim's protective instinct was merely a biographical detail. A "
            "scripture-attested prophet who stones couples while the partner tries to shield "
            "the beloved with their body has been told about the ethical ranking."
        ),
    },
    # 15 — Q 2:223 revealed to correct Jewish midwife superstition
    {
        "anchor": "Jabir:",
        "response": (
            "Apologists argue the hadith's occasion of revelation is a minor pedagogical moment "
            "— correcting a specific local misconception about sexual positions — not a "
            "reduction of divine revelation to folklore-correction. The larger ethical claim "
            "of 2:223 (\"your wives are a tilth for you\") is about the permanence and "
            "centrality of marriage, expressed in agricultural imagery common to the ancient "
            "Near East. Modern apologists emphasise that the verse's point is the "
            "<em>exclusivity</em> of sexual relations within marriage, not a denigration of "
            "women through the metaphor."
        ),
        "refutation": (
            "If the verse's occasion was correcting Jewish midwife folklore about squinting "
            "babies, its origin is scripture-level response to village gossip — which is not "
            "the profile of eternal divine law. The \"tilth\" metaphor is also not neutral: it "
            "frames women as the ground a man cultivates, with the man as agent and the woman "
            "as passive soil. The ancient-Near-Eastern idiom is real but is exactly what a "
            "human author immersed in that culture would write. A universal divine scripture "
            "should either avoid culture-bound imagery or flag it as provisional; 2:223 does "
            "neither. The combination — occasion in folklore and metaphor in agrarian "
            "subordination — is the signature of a text written from inside its culture, not "
            "above it."
        ),
    },
    # 16 — Perfume-wearing woman is fornicator
    {
        "anchor": "Any woman who wears perfume and passes by a people so that they perceive",
        "response": (
            "Apologists argue the hadith addresses a specific cultural context: in 7th-century "
            "Arabia, the deliberate public display of perfume by a woman in a mixed assembly "
            "was a recognised sexual signaling behavior — analogous to explicit flirtation, "
            "not ordinary grooming. The category of <em>zaniyah</em> (\"fornicator\") is used "
            "rhetorically to indicate serious moral impropriety in intent, not literal "
            "fornication. Modern apologists emphasise that the hadith presumes active "
            "seduction, not merely the wearing of scent in private or among family."
        ),
        "refutation": (
            "The \"sexual signaling behavior\" reading is retrofitted: the hadith's language "
            "is not restricted to deliberate seductive display — it covers any woman whose "
            "fragrance is perceived by men she passes. Classical jurisprudence extended the "
            "principle to public modesty codes broadly, and contemporary conservative Muslim "
            "discourse still cites the hadith to restrict women's use of scent in mixed "
            "spaces. The rhetorical-fornicator reading does not relieve the ethical "
            "asymmetry: a moral status (<em>zaniyah</em>) is assigned based on others' "
            "sensory experience of her, not on her actions or consent. That is not sexual "
            "ethics; it is surveillance logic applied to women's ambient presence."
        ),
    },
    # 17 — Aisha child marriage
    {
        "anchor": "Allah's Messenger married her when she was six and consummated it when she was n",
        "response": (
            "The standard apologetic claims are covered elsewhere in the catalog (physical "
            "maturity, cultural norms, Aisha's agency). For this specific hadith, apologists "
            "add that the six-nine framing must be understood as the contract-consummation "
            "distinction — the marriage was legally contracted at six but consummated only "
            "after puberty, which was marked in pre-modern societies at nine or ten. Some "
            "modern apologists argue the traditional calendar dating is uncertain and that "
            "Aisha may have been older at consummation than the straight reading implies."
        ),
        "refutation": (
            "The traditional apologetic responses are answered elsewhere; what is specific to "
            "this hadith is that it is the template for fourteen centuries of legally "
            "sanctioned child marriage. Modern jurisdictions permitting very young marriage "
            "(parts of Yemen, Nigeria, Afghanistan, Saudi Arabia historically) cite this "
            "narrative as prophetic precedent. Revisionist redating (arguing Aisha was older) "
            "requires rejecting multiple independent chains of <em>sahih</em> transmission in "
            "Bukhari and Muslim — the same chains used elsewhere to establish doctrine. If "
            "Aisha's own testimony about her own age is unreliable, the methodology of the "
            "hadith canon collapses. The text is not an old text to be historicised; it is a "
            "currently operating license for harm, renewed by every jurist who refuses to "
            "confront the source."
        ),
    },
    # 18 — Kill both doing the act of Lot's people
    {
        "anchor": "Whoever you find doing the action of the people of Lut, then kill the one doing",
        "response": (
            "Apologists argue the hadith's authenticity is contested — it is a <em>hasan</em> "
            "rather than <em>sahih</em> grade in some classifications, and its chain is "
            "weaker than the most canonical hadiths. Classical jurisprudence varied widely on "
            "the punishment: some schools prescribed death, others lighter discretionary "
            "punishment (<em>ta'zir</em>), some required the <em>zina</em> evidentiary bar "
            "(four witnesses) before any penalty. Modern reformist scholars argue the hadith "
            "should be discounted, and that the Quran itself is silent on a specific penalty."
        ),
        "refutation": (
            "The \"weaker chain\" defense is real for some transmissions but the substantive "
            "tradition across the Hanafi, Maliki, Shafi'i, and Hanbali schools codified death "
            "as the penalty for same-sex acts — a consensus strong enough that modern "
            "jurisdictions applying classical law (Iran, Saudi Arabia, Afghanistan, Brunei) "
            "maintain it. The hadith supplied the death penalty jurists would otherwise lack "
            "from the Quran alone, which is precisely why it has historical weight that "
            "weaker grade-classification does not erase. A tradition whose function was to "
            "supply capital punishment for private consensual acts is a tradition whose "
            "ethical profile has been set by the function, regardless of chain grade."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/muslim.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

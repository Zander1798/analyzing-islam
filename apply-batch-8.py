#!/usr/bin/env python3
"""Batch 8: All 23 Abu Dawud Strong entries."""
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
    # 1 — Apostasy death
    {
        "anchor": "Whoever changes his religion, execute him.",
        "response": (
            "Classical apologetics narrows the hadith's application to public apostasy combined "
            "with treason or rebellion — the standard move is that this hadith addresses "
            "defection to enemy ranks, not private belief change. Modern scholars (like "
            "Abdullah Saeed, Taha Jabir al-Alwani) argue the text should be read against "
            "Quran 2:256 (\"no compulsion in religion\"), with the Quranic principle prevailing. "
            "The hadith is thus restricted in applicability to specific political crises, not "
            "a standing rule against private apostates."
        ),
        "refutation": (
            "The restrictive reading is modern; the classical consensus across all four Sunni "
            "schools and Jaʿfari Shia law treated apostasy itself as capital, without requiring "
            "an additional act of war. Contemporary Muslim-majority jurisdictions enforcing "
            "apostasy death penalties (Saudi Arabia, Iran, Mauritania, parts of Somalia) apply "
            "them to private belief change, which is how the classical law has historically "
            "operated. The tension with 2:256 is real, not apologetically dissolvable: "
            "\"no compulsion\" and \"leaving Islam is punishable by death\" cannot coherently "
            "both operate. The classical solution was to abrogate 2:256 — a solution modern "
            "apologists quietly abandon while still citing 2:256 as proof of Islamic tolerance."
        ),
    },
    # 2 — Aisha consummation at 9
    {
        "anchor": "Umm Ruman came to me when I was on a swing",
        "response": (
            "The standard apologetic responses (physical maturity, cultural norms, revisionist "
            "redating) are covered in the Bukhari and Muslim parallels. For this specific "
            "Abu Dawud transmission, apologists emphasise that the details Aisha narrates "
            "(the swing, the handover arrangements) confirm this was a culturally normal "
            "process in her community, not an aberrant event. Defenders further argue that "
            "the hadith's preservation of Aisha's own voice (first-person narration) "
            "demonstrates that the tradition does not censor or sanitise its founding stories, "
            "which is evidence of its truthfulness."
        ),
        "refutation": (
            "The preservation of Aisha's voice is what makes the apologetic redating "
            "impossible — she is the eyewitness and the narrator. Her testimony about her own "
            "age, preserved across Bukhari, Muslim, Abu Dawud, Tirmidhi, and Ibn Majah, cannot "
            "be overturned without repudiating the entire canonical hadith-science framework. "
            "The \"culturally normal\" defense concedes that the ethics are historically "
            "contingent — which is precisely the problem with treating the practice as "
            "prophetic precedent for eternal law. A moral exemplar (Quran 33:21) whose "
            "behavior requires the defense \"it was normal at the time\" is not functioning as "
            "a universal moral exemplar."
        ),
    },
    # 3 — Pregnant woman stoned
    {
        "anchor": "A woman from Ghamid came to the Prophet and said: 'I have committed immorality.'",
        "response": (
            "Classical apologetics emphasises the hadith's procedural rigor as evidence of "
            "Islamic legal care: Muhammad repeatedly sent the woman away, waited for her to "
            "give birth, waited for the child to be weaned, accepted another woman's agreement "
            "to nurse the child — all before sentence was carried out. The stoning was her "
            "own repeated request, not something imposed upon her. Modern apologists also note "
            "that the high evidentiary bar for <em>zina</em> (four witnesses to actual "
            "penetration) means such executions were extraordinarily rare in practice; they "
            "occurred only on voluntary confession."
        ),
        "refutation": (
            "Procedural delay before execution does not alter the moral status of the "
            "execution — it makes it premeditated rather than impulsive. Muhammad could have "
            "declined her confession, accepted her repentance, refused to build the "
            "apparatus. He did not. The tender details preserved in the hadith (her "
            "insistence, the nursing period, the praise he offered after her death) are "
            "themselves evidence that the community that preserved the story saw no moral "
            "problem in what occurred. The \"voluntary confession\" framing does not neutralize "
            "a legal system that offered death as an outlet for religious guilt — a system "
            "in which confession and execution operated as spiritual transaction. A legal "
            "system whose paradigmatic \"repentance\" narrative culminates in a pregnant "
            "woman's deliberate stoning has revealed something about its moral imagination."
        ),
    },
    # 4 — Mut'ah
    {
        "anchor": "The Messenger of Allah forbade Mut'ah with women.",
        "response": (
            "The mainstream Sunni position is that <em>mut'ah</em> was permitted temporarily "
            "during specific military campaigns as a concession to the hardship of extended "
            "deployments, then definitively prohibited at Khaybar or during the Farewell "
            "Pilgrimage. The sequence is not confused revision but progressive revelation — a "
            "temporary allowance followed by final prohibition. Sunni-Shia disagreement "
            "reflects divergent readings of the same sequence, not doctrinal instability in "
            "the hadith record itself."
        ),
        "refutation": (
            "The sequence apologists give (permitted, prohibited, permitted again, prohibited "
            "again) is preserved in the <em>sahih</em> canon itself. \"Progressive revelation\" "
            "does not conceal the fact that a sexual-law rule changed multiple times. The "
            "Sunni-Shia split on <em>mut'ah</em> has lasted 1,400 years precisely because the "
            "canonical hadith record supports both readings — either the abrogation succeeded "
            "and Shia law is wrong, or <em>mut'ah</em> remains permitted and Sunni law is "
            "wrong. A divine sex-law whose final position cannot be determined from the "
            "tradition's own evidence is a law whose divine origin is indistinguishable from "
            "ordinary legal development under conflicting testimony. And structurally, "
            "<em>mut'ah</em> — payment for time-limited sexual access — has no coherent "
            "distinction from prostitution."
        ),
    },
    # 5 — Breastfeed adult man
    {
        "anchor": "The wife of Abu Hudhaifah, Sahlah bint Suhail",
        "response": (
            "Classical apologetics holds that the Salim ruling was a specific dispensation "
            "(<em>rukhsah</em>) for one household's particular circumstance, not a general "
            "principle. Muhammad's other wives rejected extending it to their own cases, which "
            "the tradition preserves as evidence the ruling was narrow. Some modern apologists "
            "argue the breastfeeding was symbolic — creating legal kinship for access — not "
            "literal nursing; the \"five breastfeedings\" verse (in the abrogation tradition) "
            "codifies the ritual category but doesn't require actual breast contact in adult "
            "cases."
        ),
        "refutation": (
            "The \"specific dispensation\" framing does not insulate the ruling from its "
            "implications: the tradition concedes that legal kinship can be established by "
            "adult breastfeeding, and classical jurists debated the conditions under which "
            "this applied. More recent controversy (a 2007 fatwa in Egypt applying the "
            "Salim precedent to workplace mixed-gender relations) shows the ruling continues "
            "to have operational use. The \"symbolic not literal\" reading is modern and "
            "retrofitted — the classical sources discuss actual nursing, with detailed "
            "requirements about the number of feedings. A legal category whose foundational "
            "case is \"Muhammad permitted my nephew to nurse from my wife to create kinship\" "
            "is a category whose existence cannot be defended by relegating it to rare cases."
        ),
    },
    # 6 — Fatimah and young slave
    {
        "anchor": "The Prophet brought a slave to Fatimah whom he had given to her",
        "response": (
            "The apologetic reading frames the hadith as establishing a <em>mahram</em>-like "
            "boundary where the slave's dependent status removes sexual-access concerns — "
            "the slave is structurally closer to family-servant than to outside male, so "
            "Fatimah's modesty concerns are assuaged by the slave's status. The hadith is "
            "not about undermining modesty norms but recalibrating them for the specific "
            "domestic context of slave-owning households common in 7th-century society."
        ),
        "refutation": (
            "The recalibration reveals the framework: the rule turns on the slave's legal "
            "status, not on anything about his character, intentions, or sexuality. A young "
            "male slave is reclassified for Fatimah's convenience, with his personhood absorbed "
            "into the household's internal geometry. This is exactly the problem with how "
            "Islamic law handles slavery: the enslaved person becomes a moveable legal "
            "classification rather than an agent. The modesty framework remains intact for "
            "free men but is relaxed for slaves — which requires slaves to be structurally "
            "outside the protection modesty rules provide. A religion whose modesty code "
            "categorises male slaves as below the threshold of sexual concern has communicated "
            "something about its anthropology."
        ),
    },
    # 7 — Don't beat wife like slave
    {
        "anchor": "And do not hit your wife like one of you beats his slave girls.",
        "response": (
            "Apologists frame the hadith as a Qur'anic-era reform: in a culture where wife-"
            "beating was ordinary, the Prophet's instruction to not strike the wife "
            "<em>as severely as a slave</em> introduced relative restraint, with the long-"
            "term trajectory (supported by other hadith discouraging striking altogether) "
            "pointing toward non-violence. The hadith is evidence of graduated reform within "
            "a patriarchal society, not an endorsement of slave-beating. Muhammad's own "
            "reported practice of not beating his wives is cited as the ethical telos the "
            "hadith is pointing toward."
        ),
        "refutation": (
            "The \"graduated reform\" framing concedes that the ethics is cultural-historical "
            "rather than eternal. The hadith's structure is a differential cruelty rule: "
            "the wife is granted a concession; the slave girl is the unchanged reference "
            "point. The text does not say \"do not beat anyone\" or \"do not beat slave girls "
            "harshly\" — it says do not beat your wife <em>like</em> you beat the slave girl, "
            "which leaves the baseline beating of slaves untouched. A reform that spares one "
            "class by reinforcing the reference status of another is not abolition; it is "
            "the restructuring of cruelty. The trajectory toward non-violence is apologetic "
            "retroactive reading — fourteen centuries of Islamic jurisprudence did not read "
            "the tradition as implicitly prohibiting slave-beating."
        ),
    },
    # 8 — Beat children about prayer
    {
        "anchor": "Command your children to pray at seven years of age and beat them about it at te",
        "response": (
            "Classical apologetics emphasises the hadith as <em>religious-discipline</em> "
            "guidance in a culture where corporal correction was normative across domains "
            "(education, household, apprenticeship). The \"beating\" here is light "
            "disciplinary striking, parallel to the gentle physical correction parents of the "
            "era applied for many kinds of misbehavior. Modern apologists note that the "
            "hadith cannot reasonably be read as endorsing injury or abuse; the principle is "
            "that prayer is important enough to warrant firm parental attention, not that "
            "physical harm is divinely licensed."
        ),
        "refutation": (
            "The \"light disciplinary striking\" reading is a modern softening; the text "
            "simply says <em>idribuhum</em> (\"strike them\") without the gentle qualifications "
            "apologists add. Classical jurisprudence did not uniformly read the hadith as "
            "calling for mild correction; it was used to justify serious corporal punishment "
            "of children for religious non-compliance across many Islamic educational "
            "traditions. The \"cultural norm\" defense is not a defense of the rule as eternal "
            "law; it is an observation that the rule was written for its culture. A divine "
            "guidance that converts prayer — a practice presented as spiritually beneficial — "
            "into a coerced behavior enforced by violence against children has communicated "
            "that its conception of piety requires fear. That is not devotion; it is "
            "compliance."
        ),
    },
    # 9 — Jizya on Zoroastrians
    {
        "anchor": "Jizyah is a tax collected from people of the Book and Zoroastrians",
        "response": (
            "Apologists argue the Zoroastrian extension was principled, not ad hoc: "
            "Zoroastrianism is monotheistic in its theological core (Ahura Mazda as supreme "
            "deity), and Muslim scholars concluded Zoroastrians occupied a status analogous "
            "to People of the Book. Some classical authorities (Ibn Taymiyyah, al-Shafi'i) "
            "argued the category of <em>Ahl al-Kitab</em> should be read broadly to include "
            "any community with a revealed scripture and prophetic tradition. The extension "
            "protected Zoroastrians rather than exposing them to the harsher "
            "polytheism-treatment of 9:5."
        ),
        "refutation": (
            "The \"protected rather than exposed\" framing does not address the structure of "
            "the choice being offered: conversion or permanent second-class taxed status. "
            "The extension to Zoroastrians reveals jizya as a conquest-tax mechanism rather "
            "than a principled theological category — the category was expanded precisely "
            "when the empire needed to incorporate conquered populations whose theology did "
            "not fit the original rule. Once \"People of the Book\" is flexible enough to "
            "absorb whichever major religious community is being conquered, the category "
            "is doing political work, not theological work. A tax on religious identity, "
            "whose legal category can be expanded to fit strategic needs, is not a "
            "principled legal framework — it is an instrument."
        ),
    },
    # 10 — Ruqya permitted, amulets shirk
    {
        "anchor": "Ruqyah, amulets (Tama'im) and love charms are Shirk",
        "response": (
            "Classical scholars distinguish between <em>ruqya shar'iyya</em> (permitted "
            "recitation-based supplication) and <em>ruqya mushrika</em> (forbidden practices "
            "involving amulets, objects, or invocations of beings other than Allah). The "
            "apologetic defense holds that spoken recitation directs the supplication to "
            "Allah, while object-amulets attribute causal power to the object or the "
            "attached entity — which slides toward shirk. The distinction is not arbitrary "
            "but tracks the direction of theological intentionality."
        ),
        "refutation": (
            "The intentionality framing works in theory but collapses in practice. An amulet "
            "containing Quranic verses is functionally identical to a spoken recitation of "
            "those verses: both use the text for protective effect, both presume the text has "
            "power when deployed correctly. The apologetic distinction — object-focused vs "
            "speech-focused — is a scholastic invention not grounded in the Quran. The broader "
            "Islamic tradition has simultaneously rejected object-amulets and embraced "
            "object-relics (Muhammad's hair preserved in Topkapi, dust from his tomb, the "
            "Kiswa covering of the Ka'ba) with essentially the same structure as what is "
            "condemned elsewhere. The selective enforcement reveals the category as political-"
            "theological, not principled."
        ),
    },
    # 11 — Jinn at nightfall
    {
        "anchor": "When night comes, for the jinn spread about",
        "response": (
            "Classical Islamic theology accepts the existence of jinn as a distinct creation "
            "mentioned repeatedly in the Quran (Surah al-Jinn). The hadith's specific "
            "nocturnal activity pattern is cited as part of a consistent theological framework, "
            "not pre-Islamic superstition retained accidentally. Protective practices "
            "(covering children, shutting doors, reciting specific verses) are cited as "
            "rational responses to real supernatural entities whose existence Islam affirms. "
            "Modern apologists note that Quranic jinn are morally complex (some Muslims, some "
            "not) and not merely malevolent nocturnal demons."
        ),
        "refutation": (
            "The specific details — jinn particularly active at sunset, children particularly "
            "vulnerable, covered pot-lids providing protection, specific verbal formulas "
            "warding them off — are indistinguishable from pre-Islamic Mesopotamian and "
            "Arabian nocturnal-demon folklore. The Quranic jinn are theologically general; "
            "the hadith corpus fills in the sunset-activity, child-vulnerability, and "
            "kitchen-utensil specifics. That filling-in is the signature of the tradition "
            "retaining pre-existing folklore under a monotheist banner. Islam's own "
            "anti-<em>jahiliyya</em> rhetoric commits it to rejecting pagan superstition — "
            "but the tradition preserved the superstition while relabeling its ontology. "
            "Having rebadged demons as \"jinn\" does not redeem the epistemology."
        ),
    },
    # 12 — Jews expelled from Medina (chapter title)
    {
        "anchor": "[Chapter title:]",
        "response": (
            "The classical apologetic holds that the expulsions of the Qaynuqa, Nadir, and "
            "Qurayza tribes from Medina were responses to specific breaches of treaty or "
            "acts of treason in the context of active war — particular communities that "
            "violated particular agreements, not a general anti-Jewish policy. Modern "
            "apologists emphasise that the Qurayza case was adjudicated by Sa'd ibn Mu'adh "
            "applying Jewish scriptural law to a tribe that had allied with besieging enemies. "
            "The chapter heading catalogs events without endorsing an exclusion principle."
        ),
        "refutation": (
            "The \"specific breaches\" framing works for each case individually but collapses "
            "when the cumulative effect is considered: three separate Jewish tribal groups "
            "were expelled or massacred within a few years, with the eventual result of "
            "Medina being ethnically cleansed of its Jewish population. The "
            "\"Arabia is Muslim-exclusive\" principle is not Abu Dawud's invention; it is "
            "the outcome these events collectively produced and the principle subsequent "
            "Islamic law (and contemporary Saudi state policy) has applied. The chapter "
            "heading's neutrality is telling: the tradition catalogs the <em>how</em> of "
            "expulsion without questioning the <em>whether</em>. A tradition whose "
            "organizing question about a community's removal is \"by what method\" has "
            "already accepted that removal is the conclusion."
        ),
    },
    # 13 — Pit for stoning
    {
        "anchor": "He ordered that a pit be dug for her, and he ordered that she be stoned.",
        "response": (
            "The classical apologetic defense here parallels the Ghamidiyya discussion: the "
            "pit was not a cruelty-enhancement but a practical accommodation — it allowed the "
            "condemned person to be partially buried so the stoning would produce death more "
            "quickly, reducing the suffering compared to stoning an unrestrained person. The "
            "preparation shows procedural care, not malice. Modern apologists emphasise that "
            "the high evidentiary bar for <em>zina</em> made such executions exceptionally "
            "rare in practice."
        ),
        "refutation": (
            "The \"reduces suffering\" framing concedes the logic of calibrated execution "
            "while defending its design. A person buried to the chest cannot escape; the "
            "pit's function is to hold the victim in place while others throw stones. Death "
            "takes minutes to hours, depending on the stone-throwing efficiency. The "
            "infrastructure is not \"humane\"; it is purposeful. And the rarity argument is "
            "historically selective: stonings have occurred across Islamic history, including "
            "in the modern era (Iran's documented cases, Afghanistan under the Taliban, parts "
            "of Nigeria and Sudan). The institutional apparatus is the problem, not its "
            "frequency of deployment."
        ),
    },
    # 14 — Aisha's dolls
    {
        "anchor": "'Aishah's dolls that she played with",
        "response": (
            "Apologists argue the doll-playing narrative documents Aisha's continued "
            "friendship with girl-companions after the consummation of her marriage, "
            "illustrating that she was not isolated or abused but remained in normal "
            "childhood social life. Muhammad's acceptance of the doll-play is cited as "
            "evidence of his kindness and non-restrictive household management. Modern "
            "apologists note that the hadith's inclusion in the canonical record shows the "
            "tradition did not sanitise Aisha's biography to hide her age."
        ),
        "refutation": (
            "The non-sanitisation is the apologetic problem, not its solution. A girl old "
            "enough for consummation but young enough for dolls is exactly what the hadith "
            "corpus preserves, and the preservation is honest but damning. Defenders who "
            "argue Aisha was older (the \"19 not 9\" revisionists) cannot consistently accept "
            "the doll-playing as historical. Defenders who argue the consummation was normal "
            "must address that the same hadith preserves her as still playing with toys. The "
            "two claims — physical maturity sufficient for sex, developmental profile "
            "still engaged in doll-play — cannot be reconciled without conceding that sexual "
            "maturity in this framework was defined by physiology alone, not by developmental "
            "wholeness. That is the position classical Islamic jurisprudence actually took, "
            "and it is the position modern apologetics tries not to name."
        ),
    },
    # 15 — Poisoned sheep
    {
        "anchor": "A Jewish woman brought a poisoned sheep (meat) to the Messenger of Allah",
        "response": (
            "Classical apologetics emphasises the miraculous element: the meat reportedly "
            "spoke to Muhammad, warning him of the poison, which allowed him to avoid full "
            "consumption. The fact that he nonetheless experienced lingering effects is "
            "framed as evidence of his <em>human</em> nature — prophets suffer like other "
            "humans, and Muhammad's eventual death with reference to the poisoning confirms "
            "his mortality (against any claim of divine invulnerability). The episode "
            "illustrates both prophetic insight and human vulnerability."
        ),
        "refutation": (
            "The \"speaking meat\" element undermines rather than supports the defense: a "
            "miraculous warning that arrived too late to prevent ingestion is a miracle that "
            "didn't work. The hadith presents Muhammad's companion eating the poisoned meat "
            "and dying from it, while Muhammad himself survives with lasting effects — "
            "which is a narrative structure in which divine protection is partial and "
            "selectively operative. The \"Allah would never give them power over you\" "
            "promise in the Quran (5:67) is then in tension with the hadith's claim that "
            "poison reached Muhammad and affected his health for years. The episode "
            "documents exactly the failure mode a skeptical reader would predict from a "
            "human prophet with human mortality, told through a hagiographic lens that "
            "cannot quite absorb the facts it preserves."
        ),
    },
    # 16 — Dog lick seven washes
    {
        "anchor": "The purification of a container from which a dog has licked",
        "response": (
            "Apologists argue the rule reflects a genuine 7th-century public-health concern: "
            "dogs in Arabian society carried rabies and parasites at rates that modern "
            "urban dogs generally do not, and the seven-wash rule with earth (which has "
            "adsorbent properties) was a practical decontamination protocol. Modern "
            "apologists cite studies showing that specific clays can have antimicrobial "
            "effects, suggesting the earth-wash had genuine medical rationale. The rule was "
            "pragmatic guidance, not arbitrary ritual."
        ),
        "refutation": (
            "The public-health framing does not explain the specific combinatorics: seven "
            "washes (a ritually significant number), one with earth (a specifically-required "
            "medium), and the targeting of dogs but not cats, sheep, or other animals with "
            "comparable microbial profiles. Cats carry toxoplasmosis and rabies; sheep carry "
            "their own zoonoses; neither triggers the rule. The cat exception is especially "
            "diagnostic — cats have a religiously privileged status in the tradition for "
            "reasons unconnected to biology. The rule is a cultural classification system "
            "about clean/unclean animals, not a hygiene protocol. \"Earth has adsorbent "
            "properties\" is a modern apologetic reaching for a scientific foothold; the "
            "classical rule was ritual, not biomedical."
        ),
    },
    # 17 — Ghilah
    {
        "anchor": "[Chapter heading:]",
        "response": (
            "Apologists frame the Ghilah discussion as evidence of the Prophet's openness to "
            "empirical learning: when his initial reaction (concern that sex during "
            "breastfeeding harmed the child) was not confirmed by experience of non-Arab "
            "communities who did not observe the taboo, he revised his view. This is cited "
            "as prophetic modesty — willingness to be corrected by evidence, a trait "
            "apologists contrast favourably with dogmatic religious leaders elsewhere."
        ),
        "refutation": (
            "The evidence-based revision is good epistemology — which is the problem. A "
            "prophet functioning as divine conduit should not need to revise biological "
            "claims based on observed outcomes in other cultures; the Creator of biology "
            "would simply communicate what is true. Muhammad's revision is what ordinary "
            "human investigators do: hold a hypothesis, compare with data, update. This is "
            "what we would predict from a religious teacher reasoning about medical matters "
            "using 7th-century folk knowledge. The \"humility\" framing is accurate but "
            "undercuts the claim of revelation-backed certainty that elsewhere permeates "
            "the hadith corpus. Either the prophet receives facts by revelation (in which "
            "case Ghilah was never necessary to revise) or he reasons like other humans "
            "(in which case the revelation-backed certainty claims elsewhere are "
            "overstated)."
        ),
    },
    # 18 — Kissing dead vs grave visits
    {
        "anchor": "[Chapter heading:]",
        "response": (
            "Apologists argue the rules address different moments of grief with different "
            "pastoral needs. Kissing the deceased at the immediate moment of washing is a "
            "natural expression of grief within the specific sacramental act of funerary "
            "preparation; grave-visits afterward are a separate practice with different "
            "pastoral implications — including the risk of women's grief becoming public "
            "spectacle, vulnerable to exploitation, or sliding into grave-veneration "
            "(which Islam prohibits for anyone). The gender distinction reflects different "
            "social risks in 7th-century context, not a claim about women's dignity."
        ),
        "refutation": (
            "The \"different social risks\" defense requires women to be the subjects of "
            "special religious restriction because of what might happen to them — which "
            "places the burden of preventive regulation on the bereaved, not on the "
            "community structures that would produce the risk. The rule's asymmetry is "
            "diagnostic: men may visit graves freely; women face cursing by prophetic "
            "authority. That is not pastoral adaptation; that is gender-coded restriction. "
            "The coherent rendering the tradition cannot supply is why the same woman can "
            "kiss her father's face at his washing but is cursed for visiting his grave "
            "the next month. The difference tracks women's visibility in public space, not "
            "the moral character of the grieving act."
        ),
    },
    # 19 — Hand amputation for quarter dinar
    {
        "anchor": "The Messenger of Allah would cut off the hand of a thief for a quarter dinar",
        "response": (
            "Classical jurisprudence built extensive procedural restrictions around this "
            "penalty: the goods must be of the minimum value (<em>nisab</em>), stored in a "
            "secure place (<em>hirz</em>), and the thief must not be starving. Umar famously "
            "suspended amputation during a famine. Apologists argue these conditions make "
            "the rule effectively rare, acting as deterrent rather than routine. Modern "
            "apologists note the symbolic force of the rule — permanent consequence for "
            "violation of trust — without requiring frequent literal enforcement."
        ),
        "refutation": (
            "The procedural restrictions are real but are juristic constructions added "
            "later — the Quranic text (5:38) and this hadith are unconditional. The "
            "\"effectively rare\" argument is not how the rule has operated in recent "
            "practice: Saudi Arabia, Iran, and parts of Sudan, Nigeria, and Somalia have "
            "continued to apply judicial amputations, often in cases where the "
            "conditions Umar invoked (famine, extreme need) are not honestly investigated. "
            "The \"symbolic deterrent\" framing cannot be squared with actual continuing "
            "amputations. Permanent disability as the penalty for a remediable offense "
            "(theft, which restitution can address) is disproportionate by any modern "
            "standard, and the classical procedural patches do not alter that proportion."
        ),
    },
    # 20 — Seven Ajwa dates
    {
        "anchor": "Whoever eats seven 'Ajwah dates in the morning, he will not be harmed by poison",
        "response": (
            "Apologists frame the hadith as traditional medicine or prayer-style protection — "
            "not a literal pharmaceutical claim. 'Ajwa dates do have demonstrated nutritional "
            "value (fiber, potassium, antioxidants), and the hadith's emphasis on seven "
            "dates-in-the-morning is read as a regimen for general health rather than a "
            "magical-immunity claim. The \"poison and witchcraft\" framing is understood "
            "within the theological framework of Allah's protective action for those who "
            "practice prophetic recommendations."
        ),
        "refutation": (
            "The \"nutritional value\" framing does not reach the hadith's content. Dates are "
            "nutritious; they do not neutralise poisons or witchcraft. The hadith's promise "
            "is specific and falsifiable: immunity from poisoning for the day. The fact that "
            "this promise routinely fails is handled by the standard apologetic move "
            "(\"you didn't have sufficient faith,\" \"the dates must be of specific origin,\" "
            "etc.) — which is unfalsifiability by design. \"Prophetic medicine\" industries "
            "have built entire commercial frameworks around 'Ajwa dates based on this hadith, "
            "which tells us that the tradition's readers have not received the apologetic "
            "framing. A revelation that makes testable medical claims and fails the test is "
            "not rescued by reinterpreting the claim as spiritual encouragement."
        ),
    },
    # 21 — Resurrected uncircumcised
    {
        "anchor": "People would be resurrected barefoot, naked, and uncircumcised.",
        "response": (
            "Classical apologetics treats the resurrection imagery as restoration to "
            "<em>fitra</em> — the natural human state before cultural-legal markings are "
            "added. Circumcision, though an Islamic practice, is positioned as a "
            "religiously-added mark that the final restoration undoes alongside clothing "
            "and footwear. The hadith does not undermine circumcision's legal status in "
            "this life; it describes the metaphysical state of resurrection, which "
            "transcends legal categories."
        ),
        "refutation": (
            "Circumcision is one of the five acts of <em>fitra</em> per the hadith corpus — "
            "meaning it is framed as a restoration of the natural state, not an addition to "
            "it. If resurrection returns humans to the pre-circumcision state, either "
            "circumcision is not part of <em>fitra</em> (contradicting the hadith saying it "
            "is) or the resurrection does not return to <em>fitra</em> (contradicting the "
            "hadith saying it does). The two positions cannot both be true. The tradition "
            "preserves both because both appeared in different transmission contexts, and "
            "the coherence problem is a patch the classical commentators have not resolved. "
            "A religion's eschatology should be internally consistent; when it is not, the "
            "inconsistencies reveal the cumulative nature of the source material."
        ),
    },
    # 22 — Abu Rafi assassination
    {
        "anchor": "They entered his room at night and killed him in his bed.",
        "response": (
            "Classical apologetics treats the Abu Rafi killing as a legitimate military "
            "operation against an enemy combatant who had organised anti-Muslim coalitions. "
            "Abu Rafi was a Jewish leader who actively worked to mobilise tribal forces "
            "against Medina, placing him in the category of combatant rather than civilian. "
            "The targeting of a specific military-political leader is distinguished from "
            "attacks on general civilians; the bedroom raid is framed as a tactical "
            "choice against a well-guarded enemy, not a violation of combatant norms."
        ),
        "refutation": (
            "The \"combatant not civilian\" framing describes Abu Rafi's activities but does "
            "not address the method: a night-raid into a man's bedroom, with the accompanying "
            "hostage-taking or threatening of his wife to prevent her from crying out. The "
            "archetype of treacherous killing — silently entering a sleeping enemy's home "
            "and dispatching him unarmed — is exactly what the pre-modern warfare norms "
            "(in most cultures, including Arab) classified as a violation of honour. The "
            "operation is preserved in the canonical record as a prophetic sunnah — meaning "
            "it is not merely narrated but presented as a model. A religion whose founding "
            "biography includes covert political assassinations as model conduct has "
            "embedded the method into its template of ethically permissible action."
        ),
    },
    # 23 — Women's wet dreams
    {
        "anchor": "Does a woman have to do ghusl if she has a wet dream?",
        "response": (
            "Apologists frame the hadith as evidence of Islamic juridical thoroughness — "
            "addressing even private biological matters with specific ritual guidance, "
            "demonstrating that Islamic law covers all domains of life. The ruling (yes, "
            "she must perform <em>ghusl</em>) is cited as treating male and female bodies "
            "with equivalent ritual seriousness, an anti-misogynist gesture in the cultural "
            "context. The specific biology invoked (women's arousal producing fluid) "
            "reflects the 7th-century understanding and does not claim medical originality."
        ),
        "refutation": (
            "The \"equivalent ritual seriousness\" is available as a framing but the content "
            "reveals something more problematic: pre-modern physiology continues to operate "
            "as eternal ritual law. The hadith's biology is wrong — female orgasmic or "
            "arousal-related fluid production is not parallel to male ejaculation in the "
            "generative sense the hadith implies, and modern medicine does not support the "
            "specific physiological picture the ruling presumes. A scriptural ritual system "
            "built on 7th-century reproductive-biology assumptions carries those assumptions "
            "forward permanently as religious law. If the biology is superseded, the ritual "
            "rule is operating on superseded grounds — which is exactly the kind of "
            "cultural-historical contingency the Quran is supposed to transcend."
        ),
    },
]


applied = 0
path = ROOT / "site/catalog/abu-dawud.html"
for spec in BATCH:
    ok, err = apply_content(path, spec["anchor"], spec["response"], spec["refutation"])
    if ok:
        applied += 1
        print(f"OK  {spec['anchor'][:60]}...")
    else:
        print(f"SKIP {spec['anchor'][:60]}... — {err}")

print(f"\nApplied: {applied}/{len(BATCH)}")

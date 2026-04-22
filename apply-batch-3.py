#!/usr/bin/env python3
"""Batch 3: 17 more Strong Quran entries (31-50, skipping 41/43/44 duplicates)."""
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
    # 31 — Mountains as pegs
    {
        "anchor": "Have We not made the earth a resting place? And the mountains as stakes?",
        "response": (
            "The scientific-miracle defense (Bucaille, Naik, the <em>i'jaz 'ilmi</em> movement) "
            "holds that the Quran is describing mountain <em>roots</em> — the isostatic "
            "foundations extending deep into the crust. Modern geology confirms mountains have "
            "significant subsurface roots (the Himalayas extend 30–40 km below the surface), "
            "stabilizing crustal formations. The Arabic <em>awtad</em> (pegs/stakes) is thus an "
            "ancient term capturing a shape and function modern geology has since confirmed."
        ),
        "refutation": (
            "The \"mountain roots\" apologetic retrofits modern isostasy onto a 7th-century text "
            "that reads naturally as ancient Near Eastern cosmology. 16:15 says mountains were "
            "set to keep the earth from \"shaking with you\" — but mountains <em>cause</em> "
            "earthquakes; they do not prevent them. The Himalayas are the ongoing product of "
            "tectonic collision, not a stabilizing brake. Had the verse genuinely anticipated "
            "isostasy, a classical commentator somewhere in fourteen centuries of tafsir should "
            "have extracted the claim before 20th-century geology made it retroactively fit. "
            "None did. \"Scientific miracles\" of this kind are always identified after the "
            "science settles, never before — the pattern of compatibility-after-the-fact, not "
            "prediction. A 7th-century Arab hearing \"pegs\" heard the flat-earth cosmology of "
            "his culture; that is what the audience would understand, and that is what the text "
            "says."
        ),
    },
    # 32 — Preserved Tablet vs piecemeal
    {
        "anchor": "But it is a glorious Quran, [inscribed] in a Preserved Slate.",
        "response": (
            "The classical theological answer is that the Quran exists eternally in the "
            "<em>Lawh al-Mahfuz</em> (Preserved Tablet) and was revealed in stages to "
            "accommodate the community's capacity to receive it. Allah knew the historical "
            "contexts in advance; the <em>asbab al-nuzul</em> describe when verses arrived in "
            "human time, not when they came into existence. Progressive revelation is a "
            "pedagogical kindness, not evidence of contingent authorship. A text eternal in "
            "heaven can still be timed to earthly events — the two descriptions are at different "
            "metaphysical levels."
        ),
        "refutation": (
            "The defense requires Allah to have authored, in eternity, a revelation whose "
            "content includes specific personal interventions in Muhammad's 7th-century domestic "
            "life — Zaynab, Mariyah and Hafsa, the slander of Aisha, the curse of Abu Lahab. "
            "Those interventions make sense only if the revelation is responsive to Muhammad's "
            "evolving circumstances. If they were pre-written in the Preserved Tablet, their "
            "content was still contingent on choices Muhammad would make and conflicts he would "
            "have — meaning Allah composed eternally a text custom-tailored to one man's "
            "biography. At that point the \"eternal\" label is doing no explanatory work; it "
            "simply means \"whatever the text turns out to be, written before it arrived.\" "
            "The <em>asbab al-nuzul</em> tradition is itself an admission that verses were "
            "received as responses to specific events — exactly what you predict from a text "
            "composed by a human author whose community's situations evolved."
        ),
    },
    # 33 — Creation days
    {
        "anchor": "Indeed, your Lord is Allah, who created the heavens and earth in six days",
        "response": (
            "The classical reconciliation (Tabari, Ibn Kathir, Qurtubi) is that the \"four days\" "
            "of 41:10 <em>includes</em> the prior \"two days\" of 41:9 — the periods overlap "
            "rather than sum sequentially. On this reading: 2 days for earth, the same 2 days "
            "plus 2 more for mountains and blessings (counted as \"four\" inclusive), then 2 "
            "days for the heavens — total 6. Modern apologists add a second reading: "
            "<em>yawm</em> (day) here does not denote a 24-hour period but a general phase of "
            "creation, and the numbers are relative durations, not strict arithmetic."
        ),
        "refutation": (
            "The \"overlapping count\" reading is the move of a commentator trying to rescue a "
            "contradiction — it is not the natural reading of \"in two days… in four days… in "
            "two days,\" which reads as three sequential stages summing to 8. The reconciliation "
            "treats \"four\" as \"two additional days counted together with the prior two,\" "
            "which is not how counts work in ordinary language. The \"general phase\" reading "
            "fails because <em>yawm</em> is used throughout the Quran with ordinary count value, "
            "and the supposed phases still have to add up. A divine revelation that requires "
            "arithmetic reinterpretation to avoid contradicting itself across three verses in "
            "one surah is a text whose self-described clarity (11:1, 16:89) is undermined by its "
            "own structure. The simplest account is that the author drew on two overlapping "
            "traditions — Genesis's six days and an older eight-stage Mesopotamian cosmogony — "
            "and did not fully reconcile them."
        ),
    },
    # 34 — Islamic Dilemma
    {
        "anchor": "And how is it that they come to you for judgement while they have the Torah",
        "response": (
            "The standard apologetic is that the Torah and Gospel were composite in Muhammad's "
            "time — containing authentic divine material alongside corruption. The Quran's "
            "command to \"judge by the Gospel\" (5:47) refers to the authentic portions (per "
            "Ibn Taymiyyah, Zakir Naik, others). <em>Tahrif</em> is not the claim that the "
            "entire text is fabricated, but that specific teachings (Jesus's divinity, "
            "crucifixion, Trinity) were distorted through interpretive misdirection. The "
            "command to verify with the People of the Book (10:94) addresses Muhammad about "
            "prophetic continuity, not about the corrupted form of their current text."
        ),
        "refutation": (
            "The rescue requires a \"partially authentic\" Bible whose authentic parts "
            "coincidentally do not include the central Christian and Jewish doctrines the Quran "
            "rejects. That stipulation has no independent evidence: textual, historical, or "
            "manuscript. The earliest Christian literature (Paul's letters, c. 50s CE) affirms "
            "the crucifixion as foundational, and no early Christian manuscript tradition "
            "lacks it. The position requires a conspiracy-theoretic textual history no New "
            "Testament scholar of any religious background endorses. Worse, 6:115 and 10:64 "
            "state plainly that \"none can alter\" Allah's words — meaning if the Gospel "
            "contained revelation, its present form should still contain it. Either Allah's "
            "words cannot be altered (and the Bible is authentic, including the crucifixion) or "
            "they can be altered (and the Quran's own preservation claim is falsified). The "
            "Dilemma bites because the escape routes cancel each other."
        ),
    },
    # 35 — Judge by the Gospel
    {
        "anchor": "And let the People of the Gospel judge by what Allah has revealed therein",
        "response": (
            "Apologists argue 5:47 addressed a specific 7th-century community (the Christians "
            "of Najran, say) and referenced the revelation they then possessed — which, on the "
            "partial-<em>tahrif</em> view, still retained enough authentic teaching to judge "
            "by. The command is historical and particular, not universal: it tells Christians "
            "of that time to judge by what remained true in their scriptures, not a mandate for "
            "all Christians everywhere to accept the current Bible as final. Modern Christian "
            "acceptance of the crucifixion as doctrine is framed as a later development (or "
            "corruption), not the content Allah authenticated."
        ),
        "refutation": (
            "The \"historical, not universal\" reading cannot be sustained against the text. "
            "5:47's phrasing (\"let the People of the Gospel judge by what Allah has revealed "
            "therein\") is present-tense and unqualified — no \"authentic parts only,\" no "
            "\"parts not yet corrupted.\" The audience is told to judge by the Gospel they "
            "actually possess. The earliest layer of Christian writing (Paul in the 50s CE, "
            "Mark in the 60s–70s) already affirms the crucifixion, meaning apologists must "
            "argue the corruption occurred <em>before</em> the Quran was revealed — at which "
            "point 5:47 is commanding Christians to judge by an already-corrupted text, which "
            "is incoherent. Alternatively, they must argue it occurred after Muhammad, which "
            "requires a conspiratorial transmission history unsupported by any manuscript "
            "evidence. The verse binds the Quran to the Gospel's authority; the Gospel's "
            "unanimous content includes precisely what the Quran denies."
        ),
    },
    # 36 — "None can alter" vs tahrif
    {
        "anchor": "None can alter His words. And He is the Hearing, the Knowing.",
        "response": (
            "Classical and modern apologists (Ibn Taymiyyah, Ibn Qayyim, Zakir Naik) draw a "
            "distinction between <em>tahrif al-ma'na</em> (corruption of meaning) and "
            "<em>tahrif al-nass</em> (corruption of the text). On the former view, Jews and "
            "Christians did not edit the physical words — they misinterpreted them. Allah's "
            "words are physically unchangeable; human understanding is not. \"None can alter "
            "His words\" is thus preserved while permitting the community's departure from the "
            "original meaning."
        ),
        "refutation": (
            "The <em>tahrif al-ma'na</em> rescue does not save the Quran's critique of the "
            "Bible. If the words are unchanged and only the interpretation corrupted, Muslims "
            "could simply consult the unchanged text and extract the true meaning — which they "
            "do not, because the unchanged text contradicts the Quran on every major Christian "
            "doctrine. Classical Muslim polemic (Ibn Hazm, al-Biruni) in fact charged both "
            "<em>tahrif al-ma'na</em> and <em>tahrif al-nass</em> depending on the specific "
            "argument being made — the two categories have historically functioned as moving "
            "goalposts, not as a coherent theory. The logical structure remains broken: either "
            "the Bible's text preserves what Allah revealed (in which case it contradicts the "
            "Quran), or it does not (in which case \"none can alter His words\" is falsified "
            "by Jewish and Christian scribes). The apologetic fork does not dissolve the "
            "dilemma; it only relocates the incoherence."
        ),
    },
    # 37 — 3:28 allies unless pretending
    {
        "anchor": "Let not believers take disbelievers as allies rather than believers",
        "response": (
            "The mainstream apologetic reading is that the verse addresses wartime context — "
            "specifically the Meccan pagan threat — and does not forbid friendship with "
            "peaceful non-Muslims. <em>Awliya'</em> (\"allies\") in Quranic usage often refers "
            "to military-political alliance, not personal friendship. Modern scholars (Tariq "
            "Ramadan, Yasir Qadhi, and others) emphasize that the \"fear\" clause was a "
            "dispensation for Muslims living under hostile rule — not a general principle of "
            "duplicity. Classical tafsir acknowledged these conditions and did not extract a "
            "general license for deception."
        ),
        "refutation": (
            "The verse's key phrase — <em>illa an tattaqu minhum tuqatan</em> (\"except when "
            "taking precaution against them\") — is the textual source of the classical "
            "<em>taqiyya</em> doctrine. The wartime reading applies to the alliance prohibition; "
            "the escape clause permitting dissimulation is not so limited in the text, and "
            "classical legal tradition (Sunni more narrowly, Shia more broadly) developed it as "
            "a general principle that public truthfulness about Muslim identity can be "
            "suspended under threat. Modern apologetic narrowing is a 20th-century development "
            "responsive to Muslim life in pluralistic societies; it is not the classical "
            "reading. The deeper structural problem is unavoidable: a religion that authorizes "
            "concealment of one's identity under any conditions has built an epistemic "
            "asymmetry into interfaith relations — non-Muslims cannot verify that public Muslim "
            "statements reflect private conviction, which corrodes trust by design."
        ),
    },
    # 38 — Table from heaven
    {
        "anchor": "The disciples said, 'O Jesus, can your Lord send down to us a table",
        "response": (
            "Apologists argue the story is preserved in the Quran because it genuinely "
            "happened and the Gospels lost the tradition — perhaps a parallel to the "
            "institution of the Eucharist, or a distinct miracle that circulated in Aramaic "
            "oral tradition before being omitted from the written Greek Gospels. Alternatively, "
            "even if legendary, the Quran's inclusion draws on its moral content (the "
            "disciples' faith, their request, Allah's provision) rather than asserting the "
            "historicity of every detail."
        ),
        "refutation": (
            "No Christian tradition — canonical, apocryphal Greek, Coptic, Syriac, or Armenian "
            "— records Jesus's disciples requesting a meal from heaven. The story has no "
            "pre-Islamic attestation anywhere. If it genuinely occurred, something of the "
            "narrative should have survived in the early Christian memory that produced four "
            "Gospels, Acts, and extensive apocryphal literature within two centuries of Jesus. "
            "The \"moral content\" defense concedes the historicity: if the Quran is telling "
            "a didactic parable rather than recording an event, it is borrowing a fictional "
            "narrative and treating it as scriptural revelation. A divine author narrating "
            "Jesus's ministry should distinguish history from parable; Surat al-Ma'idah does "
            "not."
        ),
    },
    # 39 — Best of plotters
    {
        "anchor": "They planned [to kill Jesus], but Allah planned. And Allah is the best",
        "response": (
            "Apologists argue <em>makr</em> in Arabic carries a broader semantic range than "
            "English \"deceive\" — it can mean \"plan,\" \"strategy,\" or \"counter-measure\" "
            "without the moral negativity of deliberate deceit. When applied to human enemies "
            "plotting against Jesus, the word carries their evil intent; when applied to "
            "Allah's response, it simply denotes His superior strategy. Saheeh International's "
            "\"best of planners\" captures this. The classical tafsir on 4:157 — that Allah "
            "made another look like Jesus to deceive witnesses — is framed by apologists as an "
            "apocryphal expansion drawn from Docetic tradition, not the natural Quranic "
            "reading."
        ),
        "refutation": (
            "<em>Makr</em> in the Quran consistently carries deceptive connotations where "
            "humans are its agents (3:54a, 7:99, 27:50). The same word in the same grammatical "
            "context cannot honestly mean \"deceive\" when humans do it and \"plan innocently\" "
            "when Allah does it — especially in a single verse that directly pairs the two "
            "usages. The moral weight is built into the root's semantic range, which the "
            "Arabic verb genuinely carries. And the classical tafsir of 4:157 (a person made "
            "to look like Jesus, substituting for him on the cross) is not apocryphal — it is "
            "the mainstream Sunni reading, cited directly by Tabari and Ibn Kathir. That "
            "reading requires Allah to deceive witnesses at the crucifixion, which is "
            "precisely the kind of \"plot\" 3:54 references. A God whose signature act "
            "includes cosmic deception of eyewitnesses to history is a God whose ethics of "
            "truth-telling requires an explanation the text does not supply."
        ),
    },
    # 40 — Don't be soft in speech
    {
        "anchor": "Do not be soft in speech, lest he in whose heart is disease should covet",
        "response": (
            "The apologetic reading holds that 33:32 addresses the Prophet's wives specifically "
            "— the <em>Ummahat al-Mu'minin</em>, whose public-religious role made conversational "
            "care especially important. The command is not universalized to all Muslim women; "
            "it identifies a distinctive obligation for the Prophet's household. Modern "
            "apologists further argue that \"soft in speech\" (<em>khada'a</em>) means an "
            "alluring or flirtatious register, not ordinary feminine speech — the prohibition "
            "is on seductive affect, not on ordinary conversation."
        ),
        "refutation": (
            "Classical Islamic jurisprudence (across all four Sunni schools) extended 33:32's "
            "principle to all Muslim women, not just to the Prophet's wives — exactly as "
            "apologists elsewhere extract broad legal principle from Prophet-addressed verses. "
            "Mainstream <em>fiqh</em> manuals cite 33:32 as the textual basis for restrictions "
            "on women's public speech in mixed-gender settings (prohibitions on women reciting "
            "the call to prayer, on public speaking, on audible Quran recitation in the "
            "presence of unrelated men). The \"only his wives\" narrowing is a modern "
            "apologetic move that does not track the tradition's application. More "
            "fundamentally, the verse locates moral responsibility for male lustful response "
            "on female vocal quality — an ethical reversal a reflective system would not "
            "embrace. 24:30's command that men lower their gaze is present in the Quran, but "
            "33:32 reintroduces the asymmetry in the domain of voice."
        ),
    },
    # 42 — Haman and the tower
    {
        "anchor": "Pharaoh said: 'O Haman, kindle [a fire] for me on the clay",
        "response": (
            "Apologists argue two points. (1) Archaeological evidence shows fired-clay bricks "
            "were in fact used in some Egyptian constructions (not only sun-dried mud), so the "
            "Quranic detail is not necessarily anachronistic. (2) \"Haman\" in the Quran is not "
            "identified with the Haman of the Book of Esther (the Persian court under "
            "Ahasuerus) but with a differently named Egyptian official whose name happens to "
            "match — a coincidence of names, not a historical confusion. Some apologists "
            "further suggest Haman may be a title or functional name (\"high priest,\" or "
            "similar) rather than a personal name."
        ),
        "refutation": (
            "Fired-clay bricks were rare in Egyptian construction — monumental buildings used "
            "dressed stone, and the narrative's tower-to-reach-heaven motif is the Tower of "
            "Babel (Genesis 11), a distinctively Mesopotamian story. The \"different Haman\" "
            "defense is unattested: no Egyptian record contains a vizier or official by this "
            "name in any dynasty. Haman is the Persian-Jewish villain of Esther, set in the "
            "5th century BCE — fifteen hundred years after the Exodus-era Pharaoh of the Quran. "
            "The \"title, not name\" hypothesis is a pure stipulation with no Egyptological "
            "basis. A divine narrator recounting Egyptian history to correct Biblical errors "
            "should not be relocating a Persian court figure to Moses's Egypt and having him "
            "commission a Mesopotamian-style ziggurat. The narrative is a composite of stories "
            "circulating in the 7th-century Near East, not an independent historical report."
        ),
    },
    # 45 — Mufarib punishment
    {
        "anchor": "The penalty for those who wage war against Allah and His Messenger and strive",
        "response": (
            "The classical apologetic holds that the menu of punishments in 5:33 allows judges "
            "flexibility to match penalty to crime: execution for those who killed, "
            "cross-amputation for violent robbery, banishment for lesser offense. Traditional "
            "jurisprudence (Hanafi, Shafi'i) built procedural restrictions around the verse "
            "requiring specific conditions before any penalty applies. Crucifixion in this "
            "context is a method of public execution, not prolonged torture — the condemned is "
            "killed first and then displayed. Modern applications (Saudi Arabia's "
            "crucifixion-after-execution for specific crimes) retain this narrower form."
        ),
        "refutation": (
            "The flexibility argument does not rehabilitate the penalty menu — it concedes it. "
            "A system that offers crucifixion and cross-side amputation as divinely authorized "
            "options is a system whose severity cannot be squared with any modern "
            "proportionality standard. The \"killed first, then displayed\" reading is not "
            "universal in classical sources: some jurisprudential opinions permitted live "
            "crucifixion under specific conditions, and even where the condemned is killed "
            "first, the ongoing public display is itself a form of punishment of the corpse "
            "beyond the death penalty. Cross-amputation (right hand, left foot) produces "
            "permanent and disabling mutilation — a punishment whose continuing applicability "
            "as divine law requires defending its moral adequacy in every century, not only "
            "the 7th."
        ),
    },
    # 46 — Stones of baked clay on Lot's people
    {
        "anchor": "We made the highest part [of the city] its lowest and rained upon them stones",
        "response": (
            "The classical theological reading is that Sodom's destruction was a specific "
            "divine intervention against a community that had exhausted repentance — the "
            "sexual violence reported by Lot's visitors (Quran 15:67-71, paralleling Genesis "
            "19) was the final evidence of complete moral collapse, not merely same-sex "
            "attraction. The collective punishment was proportionate because the community as "
            "a whole had turned to the practice and rejected Lot's prophetic warnings. "
            "Innocent righteous persons (Lot, his daughters) were rescued before the "
            "destruction, showing divine discrimination between guilty and innocent even "
            "within the city."
        ),
        "refutation": (
            "The defense does not address the collective punishment including infants and "
            "children, who cannot have \"exhausted repentance\" at any age. The apologetic "
            "appeal to \"sexual violence\" requires reading the Sodom narrative through its "
            "Genesis 19 inflection; the Quranic narrative focuses on \"approaching men with "
            "desire instead of women\" (7:81) as the transgression named, which is same-sex "
            "attraction broadly, not violence specifically. Classical tafsir (Tabari, Ibn "
            "Kathir) is explicit that each stone was named for its individual victim — an "
            "image that makes the non-discrimination worse, not better. A divine response to "
            "a moral wrong whose expression includes bombardment of a city's civilian "
            "population is a response that fails every modern proportionality test, regardless "
            "of the exit Allah arranged for the one righteous family."
        ),
    },
    # 47 — Men with desire instead of women
    {
        "anchor": "Indeed, you approach men with desire instead of women. Rather, you are a transgressing",
        "response": (
            "The apologetic reading holds that the verse condemns specific sexual <em>acts</em> "
            "(same-sex intercourse), not sexual orientation as such — a Muslim who experiences "
            "same-sex attraction but does not act on it is not condemned. Classical and modern "
            "jurisprudence distinguished the <em>fi'l</em> (the act) from <em>mayl</em> "
            "(inclination). Further, the sin named in 7:81 is situated within a broader pattern "
            "of moral corruption in Lot's city; apologists argue the verse addresses the "
            "communal embrace of the practice, not private personal orientation."
        ),
        "refutation": (
            "The act-versus-orientation distinction is a modern apologetic refinement. Classical "
            "Islamic law did not extensively distinguish between \"orientation\" (a concept "
            "modern) and \"act\"; it criminalized the act under penalty of death in the "
            "Hanafi, Maliki, Shafi'i, and Hanbali schools. That criminalization persists in "
            "contemporary Islamic-law jurisdictions (Iran, Saudi Arabia, Afghanistan, Brunei) "
            "as a matter of current legal enforcement. Even granting the apologetic "
            "act/inclination split, the Quran's classification of the act as \"transgression\" "
            "(<em>musrifun</em>) embeds into eternal divine law a moral judgment on a "
            "biological variation that modern psychological and medical science does not "
            "classify as pathology or moral failing. A revelation whose eternal moral categories "
            "criminalize something persons do not choose to be is one whose moral categories "
            "cannot be both universal and just."
        ),
    },
    # 48 — Chaste women accused without four witnesses
    {
        "anchor": "Those who accuse chaste women and then do not produce four witnesses",
        "response": (
            "The apologetic defense holds that the four-witness rule is a protection for the "
            "accused, not a punishment for the accuser — it makes false accusation of unchastity "
            "(<em>qadhf</em>) a serious offense precisely to prevent character assassination. "
            "The 80 lashes apply to <em>false</em> accusation without evidence, not to rape "
            "victims. A genuine rape complaint is handled under <em>ghasb</em> (coercion), not "
            "under <em>zina</em>, and classical jurisprudence recognized that a woman's "
            "complaint of rape was not itself an admission of illicit intercourse requiring "
            "four witnesses. Pakistan's Hudood Ordinance (1979) was a specific national "
            "misapplication of classical rules, not a necessary consequence of the Quran."
        ),
        "refutation": (
            "The classical jurisprudence is less tidy than the modern apologetic suggests. Rape "
            "prosecution under classical Sunni law did often require four witnesses where the "
            "accused denied the charge and the woman's complaint was treated as an accusation "
            "of <em>zina</em> needing the <em>zina</em> evidentiary standard. Multiple "
            "contemporary Muslim-majority jurisdictions (Pakistan's Hudood Ordinance era, "
            "northern Nigeria, parts of Sudan) have operationalized 24:4 in exactly the way "
            "apologists say was accidental — with pregnant rape victims charged with <em>zina</em> "
            "based on visible evidence. If the Quranic rule were genuinely protective, its "
            "systematic misapplication across centuries should not have been possible without "
            "textual warrant. A rule that requires four eyewitnesses of actual penetration — a "
            "near-impossible evidentiary bar — does, in practice, shield predators by making "
            "successful prosecution nearly unattainable from the victim's side."
        ),
    },
    # 49 — Not for a prophet to have captives
    {
        "anchor": "It is not for a prophet to have captives [of war] until he inflicts a massacre",
        "response": (
            "The apologetic reading is that 8:67 was a specific rebuke to the community after "
            "Badr for accepting ransom from captives who should have been engaged more "
            "decisively on the battlefield — the verse addresses a one-time situation, not a "
            "standing rule. \"Until he has inflicted a massacre\" is idiomatic for \"has "
            "thoroughly defeated the enemy,\" meaning the war should be won decisively before "
            "prisoner-taking begins. The subsequent revelation (8:68, 8:70) clarifies that "
            "once captives are taken, they may be ransomed or freed — Allah is gracious in "
            "permitting a pragmatic outcome after the initial rebuke."
        ),
        "refutation": (
            "The \"idiomatic for decisive defeat\" reading softens a verse that directly uses "
            "the language of massacre (<em>yuthkhina fi al-ard</em>, \"to inflict slaughter on "
            "the earth\"). The ethical direction is unambiguous: the rebuke is for taking "
            "captives <em>before</em> sufficient killing, not for failing to protect them. A "
            "prophetic ethics whose prescriptive nudge is toward maximum lethality before "
            "clemency becomes permissible is not a pacifist ethic, however much later context "
            "softens individual outcomes. The verse's architecture — rebuke for insufficient "
            "killing, then permission for ransom after the slaughter quota is met — is "
            "structurally violent. That it exists in a text claimed as eternal moral guidance "
            "is the problem apologists must address, not defuse by redefining the verbs."
        ),
    },
    # 50 — Allah mocks them
    {
        "anchor": "Allah mocks them and prolongs them in their transgression",
        "response": (
            "Classical theological reading treats divine \"mockery\" anthropomorphically — as "
            "a human-language description of Allah's action, not a claim that He literally "
            "experiences human-like sarcasm. The verb reflects the believers' perspective: from "
            "the righteous vantage, the hypocrites' self-deception looks like an object of "
            "mockery. \"Prolongs in transgression\" is read not as Allah causing the sin but "
            "as Allah withholding guidance from those who have persistently rejected it — a "
            "passive letting-be, not an active compounding. Compatibilist theology (Ash'arite "
            "<em>khalq</em>/<em>kasb</em>) places moral responsibility on the human acquisition, "
            "not on Allah's metaphysical creation of the act."
        ),
        "refutation": (
            "The \"perspective of the believers\" reading does not match the verse's grammar: "
            "Allah is named as the subject of the mocking (<em>Allahu yastahzi'u bihim</em>), "
            "not the righteous community. Anthropomorphic dilution of the claim is available "
            "but it is also available for every problematic divine action in the Quran — which "
            "erodes its force as a general principle. The \"withholding guidance\" reading of "
            "<em>yamudduhum</em> (\"prolongs them\") is philologically strained; the verb "
            "carries active extension, not passive non-intervention. And the Ash'arite "
            "compatibilism is a scholastic invention centuries later to manage exactly this "
            "problem, whose opacity is proverbial even within Islamic theology. The simplest "
            "reading — Allah mocks and actively extends the sinners' path to compound their "
            "punishment — is the one the text delivers, and its moral profile is exactly what "
            "the verse presents."
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

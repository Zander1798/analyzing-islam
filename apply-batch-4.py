#!/usr/bin/env python3
"""Batch 4: Remaining Strong Quran entries (51-73, skipping duplicates 62, 63, 66)."""
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
    # 51 — Wrapped one
    {
        "anchor": "O you who covers himself [with a garment].",
        "response": (
            "The classical reading treats the wrapping as a natural human response to the "
            "overwhelming experience of first receiving revelation. Gabriel's earliest "
            "appearances, per the traditional biography, left Muhammad physically shaken — a "
            "reaction continuous with other prophetic accounts (Moses at Sinai, Isaiah's \"woe "
            "is me,\" Daniel's collapse). The wrapping is not evidence of mental disturbance "
            "but of appropriate awe before divine majesty; subsequent revelation stabilises "
            "the prophet."
        ),
        "refutation": (
            "The \"overwhelming majesty\" framing does not distinguish Muhammad's early "
            "experience from the countless pre-modern mystical and visionary encounters reported "
            "across cultures — Near Eastern shamans, Greek oracular figures, Nordic "
            "<em>volva</em>, Central Asian ecstatic mystics. Every such tradition reports "
            "physical overwhelm (tremors, wrapping, fainting) as <em>authentication</em> of "
            "supernatural contact, and every such tradition is indistinguishable from ordinary "
            "mystical-psychological states by any external observer. A divine revelation "
            "authenticating itself to a prophet would presumably produce a different profile "
            "than the experiences common to every ecstatic tradition humans have produced."
        ),
    },
    # 52 — Jews most hostile
    {
        "anchor": "You will surely find the most intense of the people in animosity toward the believers",
        "response": (
            "Apologists argue the verse is a historically-bounded observation about the "
            "specific Jewish and pagan communities Muhammad encountered in Mecca and Medina — "
            "a descriptive report on particular groups, not a universal theological ranking. "
            "Classical tafsir (Ibn Abbas in Tabari) connects it to specific Medinan Jewish "
            "tribes that had broken alliances with Muhammad. Modern apologists emphasise the "
            "paired praise for Christians (\"nearest in affection\") as evidence the verse is "
            "relational observation, not a claim about Jewish character."
        ),
        "refutation": (
            "The \"historically bounded\" reading cannot be maintained against fourteen "
            "centuries of Islamic use. Classical jurisprudence and popular religious discourse "
            "have historically treated 5:82 as a standing evaluation, and the verse's phrasing "
            "(\"you will surely find…\") invites exactly the universal reading it received. "
            "Grouping \"Jews and polytheists\" in a single hostility category places Jewish-"
            "Muslim relations on a structurally worse footing than Christian-Muslim relations "
            "as a scriptural claim, not a local report. Modern Islamic attitudes toward Jews "
            "in many cultures are not misreadings — they are applications. A scripture that "
            "officially rates an entire religious community's animosity as maximum has done "
            "work no amount of context-bounding can undo."
        ),
    },
    # 53 — Cursed them
    {
        "anchor": "For their breaking of the covenant, We cursed them and made their hearts hard.",
        "response": (
            "The classical theological reading treats the cursing and heart-hardening as "
            "<em>consequence</em>, not cause — a response to the Jewish community's persistent "
            "covenant-breaking, not a pre-existing determination that removed their moral "
            "freedom. The verse describes a collective moral history: a community that "
            "repeatedly abandoned its covenant earned a consequent spiritual resistance. "
            "Allah's action is just because it is proportionate to the community's "
            "demonstrated rejection. Individual Jews who return to faith are not bound by the "
            "collective description."
        ),
        "refutation": (
            "The \"consequence not cause\" reading runs into the same problem as 2:6-7 (Allah "
            "seals hearts, then punishes for disbelief). Either the hardening is doing causal "
            "work — in which case moral responsibility for the resulting disbelief is partly "
            "Allah's — or it is pure metaphor, in which case the verse communicates nothing "
            "about divine action. Classical Ash'arite theology frankly accepts the causal "
            "reading and solves the problem by denying libertarian free will. The modern "
            "\"just a consequence\" rescue requires a stronger free-will doctrine than the "
            "tradition holds. The collective framing is also unjust by the Quran's own "
            "principle that no soul bears the burden of another (17:15) — yet whole communities "
            "are cursed for ancestral conduct here."
        ),
    },
    # 54 — Don't linger at Prophet's house
    {
        "anchor": "Enter not the houses of the Prophet",
        "response": (
            "Apologists argue the verse addresses a specific social problem: some visitors "
            "were overstaying their welcome in the Prophet's household, infringing on his wives' "
            "privacy and on the Prophet's time for worship and governance. The revelation "
            "provided guidance for a real dignity issue. Modern apologists further note the "
            "verse's <em>broader</em> principle — respect for household privacy — is "
            "universalisable, so while the occasion was specific, the ethics are not."
        ),
        "refutation": (
            "The \"broader principle\" is legitimately extractable, but the verse does not "
            "deliver a general principle. It delivers a specific rule about the Prophet's "
            "household. Every Muslim for fourteen centuries has recited as eternal scripture a "
            "passage about departing from Muhammad's dinner table promptly. Aisha's own "
            "observation — \"your Lord hastens to fulfil your wishes\" — is more telling than "
            "the apologetic frame. A universal revelation for all humanity does not need "
            "specific social etiquette at a specific 7th-century household; the presence of "
            "such specificity in an \"eternal\" text is evidence that the content is "
            "responsive to one man's circumstances rather than addressed to all times."
        ),
    },
    # 55 — Slave girl marriage
    {
        "anchor": "whoever among you cannot afford to marry free, believing women, then [he may marry]",
        "response": (
            "Apologists frame the verse as a <em>protection</em> for slave women: by permitting "
            "marriage (not merely concubinage) to slaves, Islam elevated their status to that "
            "of wives, required the consent of their owners as guardians, and gave them "
            "enforceable rights. The \"marry free women if you can afford them\" framing reflects "
            "practical economics in a stratified society, not a hierarchy of human worth. Over "
            "time, the encouragement of marriage (rather than concubinage) was supposed to "
            "reduce the institution of slavery, by merging the slave into the marriage-freedom "
            "pipeline."
        ),
        "refutation": (
            "The \"elevation\" reading concedes the point: a marriage law that ranks free "
            "believing women as first choice and slave women as economic alternative has "
            "embedded the slave-free distinction into eternal divine law. If the verse genuinely "
            "intended abolition-by-integration, it could have simply forbidden slavery — as "
            "it forbade, say, wine. It did not. And the requirement that marriage happen with "
            "the owner's permission locates ultimate authority over the slave woman's life "
            "with her owner, not with herself. The institution was not dissolved; it was "
            "regulated. A divine marriage code for all time should not carry \"free\" and "
            "\"owned\" as moral-economic categories of women."
        ),
    },
    # 56 — Do not deride
    {
        "anchor": "Let not a people ridicule [another] people; perhaps they may be better than them",
        "response": (
            "The apologetic reading takes the verse as a straightforward call to humility — "
            "telling Muslims not to mock others because divine evaluation does not track human "
            "social ranking. The rhetorical structure (\"perhaps they may be better\") functions "
            "as a reminder that believers cannot confidently rank others in Allah's sight. The "
            "verse is an egalitarian corrective, not a ranking formula."
        ),
        "refutation": (
            "The verse's own justification preserves the hierarchy it is pretending to soften. "
            "\"They may be better than you\" presupposes that \"better\" and \"worse\" are "
            "meaningful categories — the appeal is to humility about one's position in the "
            "ranking, not to a rejection of ranking itself. A genuinely egalitarian ethic "
            "would say \"do not mock others because all persons have equal worth,\" not "
            "\"do not mock others because you might be below them.\" The verse's rhetorical "
            "architecture is an admission that ranking human worth remained the framework "
            "within which the ethical adjustment was being made."
        ),
    },
    # 57 — Slave and free parable
    {
        "anchor": "a slave [who is] owned and unable to do a thing and he to whom We have provided",
        "response": (
            "The apologetic reading holds that the parable uses slavery as a rhetorical "
            "<em>contrast</em> rather than an endorsement — Allah is making a theological "
            "point about power and sufficiency using familiar social categories the audience "
            "would immediately grasp. The parable no more endorses slavery than the Quran's "
            "use of \"the blind and the seeing\" endorses blindness as superior. Rhetorical "
            "comparison uses available categories; it does not moralise them."
        ),
        "refutation": (
            "A rhetorical comparison that uses \"the owned slave unable to do anything\" as "
            "the self-evidently lesser term is a comparison whose force depends on the "
            "audience accepting slavery as an unquestioned backdrop. Divine rhetoric that "
            "leans on the moral givenness of a hierarchy is rhetoric that ratifies the "
            "hierarchy — even without explicitly endorsing it. If the Quran had wanted to "
            "communicate without entrenching the category, it could have used other "
            "contrasts. Choosing \"owned slave\" as the image for incapacity preserves the "
            "institution inside the divine scripture as a permanent feature of moral "
            "vocabulary."
        ),
    },
    # 58 — Moon split
    {
        "anchor": "The Hour has come near, and the moon has split [in two].",
        "response": (
            "The classical reading holds that the splitting of the moon was a miracle "
            "performed in response to Meccan pagan demands for a sign — genuinely witnessed "
            "by Muhammad's contemporaries, reported in multiple <em>sahih</em> hadiths "
            "(Bukhari 3637, Muslim 2800, and others). The absence of the event in Chinese or "
            "Byzantine astronomical records is explained by either (a) the miracle was "
            "localized to the Arabian viewing angle, (b) the event was brief enough to escape "
            "notice in non-Arab astronomical traditions focused elsewhere, or (c) records of "
            "that date simply did not survive. Modern apologists sometimes point to NASA "
            "imagery of the lunar \"rille\" as possible physical evidence."
        ),
        "refutation": (
            "The \"localised miracle\" rescue does not match the verse's language: \"the moon "
            "has split\" is a cosmological claim, not a perspectival one. The moon is "
            "visible from every longitude, and a genuine splitting-and-rejoining would have "
            "been recorded by Chinese astronomers (who kept meticulous lunar observation "
            "records throughout the 7th century), by Indian observers, by Byzantine "
            "chroniclers, and by any traveller who happened to look up. Their total silence "
            "is diagnostic. The NASA \"rille\" claim is a modern misreading of geological "
            "features formed by ordinary lunar tectonics billions of years before Islam. A "
            "miracle whose only evidence is the testimony of the community that already "
            "believed is indistinguishable from a claim."
        ),
    },
    # 59 — Envier evil
    {
        "anchor": "And from the evil of an envier when he envies.",
        "response": (
            "Apologists read the verse symbolically: the envier's evil is not a supernatural "
            "curse but the real-world harm that envy motivates — the envier slanders, plots, "
            "undermines, obstructs. Seeking refuge from it is seeking Allah's protection from "
            "the practical consequences of another's malice, not from a magical evil-eye "
            "emanation. Classical tafsir, while acknowledging the ancient Near Eastern evil-eye "
            "context, emphasised moral and spiritual protection rather than amulet-style magic."
        ),
        "refutation": (
            "The symbolic reading does not match the classical tradition, which treated evil-"
            "eye protection (<em>ruqya</em>, amulets, specific incantations) as a standing "
            "Islamic practice derived in part from these verses. Mainstream hadith (Bukhari "
            "5738, Muslim 2187) endorse the reality of the evil eye as a physical cause of "
            "harm, with Muhammad himself recommending specific prayers and practices against "
            "it. The \"symbolic not magical\" reading is a modern apologetic move that Islam's "
            "actual popular and scholarly tradition does not support. A divine scripture that "
            "confirms folk beliefs about cursed glances has aligned itself with the village, "
            "not with a corrected understanding of how causation works."
        ),
    },
    # 60 — Earth shaken
    {
        "anchor": "When the earth is shaken with its [final] earthquake and the earth discharges its burdens",
        "response": (
            "The apologetic reading treats the passage as poetic-eschatological imagery, not "
            "literal geology — a theologically vivid description of the Last Day designed to "
            "move the reader's heart. Similar personifying language (\"the sky was split,\" "
            "\"the mountains were scattered like carded wool\") is standard apocalyptic "
            "register across Jewish, Christian, and Zoroastrian eschatology. The Quran uses "
            "the genre's conventions to communicate moral urgency, not to assert a geological "
            "mechanism."
        ),
        "refutation": (
            "\"Apocalyptic register\" is a fair description of the genre, but it concedes the "
            "core point: the Quran's eschatology is working with the same poetic-mythological "
            "conventions as Jewish and Christian apocalyptic literature of the 1st–7th "
            "centuries. That is exactly what a human author immersed in the Near-Eastern "
            "apocalyptic tradition would produce. A divine text that meant to deliver a "
            "unique revelation should look less like convention and more like breakthrough. "
            "The poetic-imagery framing does not differentiate the Quran's end-times account "
            "from the surrounding religious literature; it embeds it in it."
        ),
    },
    # 61 — Zaqqum tree
    {
        "anchor": "Indeed, the tree of Zaqqum is food for the sinful",
        "response": (
            "Classical apologetics treats Zaqqum as an otherworldly substance whose description "
            "in earthly terms (tree, boiling, eaten) is an accommodation to human language — "
            "paradise's wine that does not intoxicate is a parallel accommodation. The hellish "
            "vocabulary (tree rising from hell-fire) is not biological claim but literary "
            "horror designed to make the reality of damnation vivid for a finite audience. "
            "Modern apologists add that the vividness is a <em>mercy</em> — better to be "
            "horrified by scripture and avoid hell than to reach it unwarned."
        ),
        "refutation": (
            "The \"accommodation to human language\" defense is convenient but unconstrained: "
            "anything impossible or morally troubling in scripture can be defused this way, "
            "and if it can defuse anything, it means nothing. Classical tafsir did not read "
            "Zaqqum as poetic metaphor — it read the tree as a real feature of hell, with the "
            "specific physical properties named. More fundamentally, an ethics of deterrence "
            "built on nightmare-imagery (tree of scalp-heads, boiling stomachs, skin roasted "
            "and replaced) has traded away proportionality for shock. Divine justice whose "
            "strongest argument is spectacular horror is not communicating justice — it is "
            "communicating threat, and its content is measured by how much terror it can "
            "produce."
        ),
    },
    # 64 — No iddah for virgin divorce
    {
        "anchor": "when you marry believing women and then divorce them before you have touched",
        "response": (
            "The apologetic reading holds that 33:49 addresses a legal technicality — no "
            "waiting period is required for a woman divorced before consummation because there "
            "is no pregnancy risk to manage. The verse does not institute or endorse "
            "unconsummated marriages; it simply provides a rule for cases where such marriages "
            "existed and then dissolved. The ethical core is fairness — a woman unconsummated "
            "should not be burdened with an unnecessary waiting period."
        ),
        "refutation": (
            "The \"legal technicality\" framing cannot be separated from what it implicitly "
            "normalises. A divine legal code that carries a category for \"married but not yet "
            "touched\" as a standing possibility has embedded into its structure the practice "
            "of marriages contracted before the bride is physically mature enough for "
            "consummation — which is the principal historical use of the category. Fourteen "
            "centuries of Islamic jurisprudence used 33:49 alongside 65:4 to underwrite child "
            "marriages with deferred consummation, and the category persists in modern "
            "jurisdictions that permit such arrangements. If the Quran meant no more than "
            "\"no waiting period when no consummation,\" it could have said so without giving "
            "the category permanent scriptural standing."
        ),
    },
    # 65 — Son gets double of daughter
    {
        "anchor": "Allah instructs you concerning your children: for the male, what is equal to the share",
        "response": (
            "The classical apologetic rests on economic role: in 7th-century Arabia, men "
            "provided financially for women (wives, daughters, elderly mothers), so a 2:1 "
            "inheritance ratio reflected the son's heavier financial obligation. On this "
            "view, the rule was effectively equal — men received more because they had to "
            "spend more. Women's inheritance was private wealth; men's was burdened by "
            "support obligations. Modern apologists acknowledge the rule is less defensible "
            "in economies where women are financially independent, and some argue the verse "
            "was circumstance-responsive rather than eternal."
        ),
        "refutation": (
            "The \"circumstance-responsive\" acknowledgment is itself corrosive to the "
            "Quran's self-description as eternal divine law. If the 2:1 ratio was calibrated "
            "for 7th-century economics, then the Quran's inheritance law is dated, not "
            "universal — which is a substantial concession. More importantly, even in the "
            "original economy, the \"men bear costs\" justification does not reach every "
            "case: the rule applies uniformly, including to daughters with no brothers, to "
            "women who had independent wealth, and to situations where the economic "
            "asymmetry did not hold. And the Quran could have pegged the ratio to "
            "circumstance (\"if the son bears costs, he receives more\") rather than to sex. "
            "Fixing it to gender embedded the 7th-century pattern into eternal law, which is "
            "the problem."
        ),
    },
    # 67 — Men have degree over women
    {
        "anchor": "the wives is similar to what is expected of them, according to what is reasonable",
        "response": (
            "The apologetic reading holds that the \"degree\" (<em>daraja</em>) is functional, "
            "not moral — it refers to the husband's leadership responsibilities (provision, "
            "protection, representation) rather than any intrinsic superiority. The verse's "
            "opening affirms reciprocity of rights; the \"degree\" clause simply acknowledges "
            "the asymmetric responsibilities that accompany male headship of the household. "
            "Modern apologists emphasise that the Quran also affirms spiritual equality "
            "(33:35), meaning the \"degree\" is a role, not a rank."
        ),
        "refutation": (
            "<em>Daraja</em> in Quranic usage consistently carries ranking semantics — it is "
            "the word used in 4:95 for fighters who have a \"degree\" of spiritual excellence "
            "above those who sit, in 6:165 for hierarchical ordering in worldly life, and "
            "elsewhere for rank. Reading it as \"more responsibility, not higher status\" is "
            "a modern apologetic move not supported by the word's Quranic use elsewhere. "
            "Mainstream Islamic jurisprudence — for over a millennium — has read 2:228 and "
            "related verses as establishing male authority in marriage, not merely functional "
            "division of labour. The reformist \"functional only\" reading is a modern "
            "minority, driven by the desire to reconcile the verse with contemporary equality, "
            "not by how the Arabic and the tradition actually use the word."
        ),
    },
    # 68 — Polygamy 2/3/4
    {
        "anchor": "Then marry those that please you of [other] women, two or three or four",
        "response": (
            "Apologists argue the verse is historically restrictive, not permissive: it capped "
            "an unlimited polygamy norm of 7th-century Arabia at four, included a demanding "
            "condition of equal justice, and was meant as a transitional rule toward monogamy. "
            "Some scholars (including contemporary Islamic reformers) argue the subsequent "
            "admission in 4:129 — that men cannot actually be equally just between wives — "
            "is the Quran's implicit indication that polygamy should not be practiced at all. "
            "The verse's original pragmatic function was the care of war-orphans and widows, "
            "not recreational polygamy."
        ),
        "refutation": (
            "The \"transitional to monogamy\" reading is a 20th-century apologetic innovation "
            "without support in fourteen centuries of Islamic jurisprudence, which treated "
            "polygamy as a permanent permission. If the Quran meant to cap polygamy at zero, "
            "it could have prohibited the practice rather than regulate it. The 4:129 "
            "\"implicit abolition\" reading requires treating 4:3's permission as functionally "
            "void — an enormous interpretive move the tradition never made. The orphan-care "
            "motive covers some cases but not all: the verse's scope is general (\"women\"), "
            "not restricted to widows of fallen fighters. And the structural asymmetry is "
            "untouched: men may marry four women, but women cannot marry multiple husbands. "
            "This is not an accidental oversight but a designed hierarchy."
        ),
    },
    # 69 — You cannot be equal
    {
        "anchor": "you will never be able to be equal [in feeling] between wives",
        "response": (
            "The classical distinction is between emotional and material justice: 4:3 "
            "demanded material equality (equal nights, equal financial support) which men can "
            "achieve; 4:129 acknowledges emotional equality is beyond human capacity. The "
            "verses address different dimensions, so they do not contradict. Modern apologists "
            "add that 4:129 is also a counsel to restraint — knowing perfect justice is "
            "impossible, a man should favour monogamy in practice, which produces a Quran-"
            "internal nudge toward single-wife marriage."
        ),
        "refutation": (
            "The material/emotional split is textually invented — 4:3 and 4:129 do not draw "
            "the distinction, and the reader must import it to save the logic. More importantly, "
            "if polygamy cannot deliver on its ethical precondition (justice between wives), "
            "the institution itself is indicted — the Quran has licensed a practice and then "
            "admitted the practice is intrinsically unjust. The \"counsel to restraint\" "
            "reading is post-hoc; classical Islamic jurisprudence did not treat 4:129 as "
            "effectively abolishing 4:3. A scripture that says \"do X only under condition Y\" "
            "and then says \"you cannot actually achieve Y\" has disowned the only argument "
            "for licensing X."
        ),
    },
    # 70 — Guard private parts except captives
    {
        "anchor": "except from their wives or those their right hands possess",
        "response": (
            "The classical position holds that the verse reflects the lived reality of 7th-"
            "century Arabian society, where concubinage was universal. Islamic law "
            "<em>regulated</em> rather than abolished the practice, while tightening it — "
            "requiring specific waiting periods, forbidding sexual contact without ownership, "
            "permitting the slave woman to earn her freedom through childbirth "
            "(<em>umm walad</em>). On this view, the verse is a transitional norm pointing "
            "toward the abolition the community never completed."
        ),
        "refutation": (
            "The \"transitional\" reading requires reading into the Quran a trajectory the text "
            "does not supply. The verse simply groups wives and right-hand-possessed women as "
            "the two categories with whom sexual relations are permitted, without suggesting "
            "one is provisional. A piety framework that defines \"guarding private parts\" as "
            "compatible with sexual access to captured women has not articulated sexual "
            "ethics — it has articulated privilege. The \"not blamed\" framing of the next "
            "clause explicitly rules out even considering the question of the captive's "
            "consent. For fourteen centuries, Islamic law has read these verses exactly as "
            "they appear: as permission, not as transitional prohibition."
        ),
    },
    # 71 — Prophet special license
    {
        "anchor": "indeed We have made lawful to you your wives... and those your right hand possesses from",
        "response": (
            "Apologists argue 33:50's extraordinary permissions served specific political and "
            "social functions. The alliance-marriages (Juwayriyya, Safiyya) stabilised Muslim "
            "relations with conquered tribes. Mariyah's relationship was within the Arabian "
            "cultural framework of concubinage. The cousin-marriage permissions closed lineage "
            "questions. The general unrestricted-number clause reflects the Prophet's "
            "distinctive responsibilities in the nascent community. Modern apologists note "
            "33:52 subsequently froze further marriages, treating the permissions as "
            "historically specific rather than eternal."
        ),
        "refutation": (
            "The \"political function\" framing does not remove what the verse does: it "
            "licenses the Prophet's sexual access to captured women from his own military "
            "campaigns as a distinct category of marital right, not a historical accident. "
            "Safiyya's father and husband were killed in the same campaign that delivered her "
            "to Muhammad's household; Juwayriyya was a war captive. The Quran does not "
            "sanitise this — it formalises it. Modern apologists focus on individual outcomes "
            "(Safiyya converted, was elevated, etc.) but the structural issue is the "
            "scriptural warrant for the sexual claim. A divine scripture that delivers "
            "sexual access to a prophet as part of his military spoils has not elevated "
            "prophetic status — it has hallowed an appetite the broader surrounding verses "
            "elsewhere describe as needing restraint."
        ),
    },
    # 72 — Triple talaq
    {
        "anchor": "Divorce is twice. Then, either keep [her] in an acceptable manner",
        "response": (
            "The classical jurisprudential reading places substantial restrictions around "
            "divorce in the Sunni schools: three pronouncements must be spaced over three "
            "menstrual cycles with a mandatory reconciliation interval, not delivered "
            "instantly. The Quran's preference, drawn from 4:35, is always for reconciliation "
            "via family mediation. The infamous \"triple talaq\" instant-divorce practice is "
            "a distortion of the Quranic process, criticized by reformist jurists and "
            "formally banned in several Muslim-majority states (Egypt's 1929 and 1985 reforms, "
            "India's 2019 legislation, Pakistan). Women have parallel recourse through "
            "<em>khula</em> (judicial divorce)."
        ),
        "refutation": (
            "The reformist reading is correct about the Quran's preferred process — but "
            "\"triple talaq\" as immediate dissolution was the majority practice across the "
            "Sunni world for over a millennium, and its abolition has required state "
            "intervention against religious resistance. The fact that reform is necessary is "
            "the diagnostic: the text's structure permits the abusive practice readily enough "
            "that fourteen centuries of classical jurists endorsed it. <em>Khula</em> is a "
            "real provision but is structurally unequal: a husband pronounces; a wife must "
            "petition, often with judicial or familial gatekeeping. The divorce asymmetry is "
            "scripturally encoded, and reform has required reading the Quran against the grain "
            "of the classical consensus — which is effectively admitting the Quranic rule "
            "needs supplement to achieve basic parity."
        ),
    },
    # 73 — Don't marry polytheist women
    {
        "anchor": "do not marry polytheistic women until they believe. And a believing slave woman",
        "response": (
            "The classical reading frames this as a religious-community boundary consistent "
            "with similar rules in Jewish and Christian law (Nehemiah 13:23-27, 2 Corinthians "
            "6:14). Religious-in-group marriage is a feature of most ancient religious "
            "traditions, not a uniquely Islamic invention. The \"believing slave better than a "
            "polytheist\" framing emphasises that faith is the supreme virtue — an egalitarian "
            "point in its own way, since it flattens social class in favour of religious "
            "standing. Muslim men are permitted to marry \"People of the Book\" "
            "(Christians, Jews), so the rule is not blanket religious exclusivism."
        ),
        "refutation": (
            "The classical reading concedes the rule's <em>comparative</em> point but not its "
            "asymmetry. Muslim men may marry Christian or Jewish women; Muslim women may not "
            "marry Christian or Jewish men. The asymmetric interfaith rule is scripturally "
            "encoded and consistently applied across jurisprudential tradition. Comparing it "
            "to biblical in-group rules does not rehabilitate it as universal ethics — the "
            "biblical rules are themselves products of particular ancient settings and are "
            "not defended by modern Jews or Christians as eternal universal law. The \"faith "
            "trumps status\" framing is real but incomplete: the same verse that trumps "
            "status with faith simultaneously classifies free believing women as the first "
            "choice and slave women as secondary — so the supposed egalitarianism is tiered, "
            "not flat. Any ranking system that sorts persons into marriageable categories by "
            "religion and legal status is a ranking system, even if faith is one of its "
            "axes."
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

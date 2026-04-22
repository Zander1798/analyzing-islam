#!/usr/bin/env python3
"""Batch 12: Remaining 46 Bukhari Strong entries (41-86)."""
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
        "anchor": "Umar expelled the Jews and the Christians from Hijaz",
        "response": (
            "Apologists frame the expulsion as a specific political measure within the "
            "Arabian Peninsula's sacred-space framework — not religious cleansing but "
            "geographic restriction consistent with the <em>dhimma</em> contract elsewhere "
            "maintained. Non-Muslim religious communities continued to thrive in territories "
            "conquered by later Muslim empires (Egypt, Spain, Persia), so the hadith reflects "
            "a specific Hijaz policy, not a universal principle."
        ),
        "refutation": (
            "\"Specific to Hijaz\" is accurate but cannot neutralise what the policy communicates: "
            "the Prophet's stated intention (per the hadith) was that the Arabian Peninsula "
            "would have no coexistence with non-Muslim communities, and Umar implemented that "
            "vision. Saudi Arabia enforces this to the day, barring non-Muslims from Mecca and "
            "Medina and historically restricting their residence generally. The \"other "
            "conquered territories\" defense does not repair the principle — it is selective "
            "enforcement of a rule the tradition preserves as prophetic commission."
        ),
    },
    {
        "anchor": "Allah's Apostle sent some men from the Ansar to (kill) Abu Rafi",
        "response": (
            "Classical apologetics treats Abu Rafi as a military-political leader actively "
            "mobilising anti-Muslim tribal coalitions — a legitimate combatant in the framework "
            "of the period. The night-raid method was tactical adaptation to a well-guarded "
            "enemy, not a violation of combatant norms. The Prophet sent specific companions "
            "for a specific operation, which is standard wartime targeted action."
        ),
        "refutation": (
            "The \"combatant\" framing describes Abu Rafi's activities but does not address the "
            "method: a night-raid into a man's bedroom, with threats to his wife to prevent her "
            "from crying out. Pre-modern warfare norms in most cultures — Arab included — "
            "classified silently entering a sleeping enemy's home as treacherous. The "
            "assassination is preserved in the canonical record as <em>sunnah</em>, meaning "
            "it is presented as prophetic model. A religion that includes covert "
            "bedroom-assassinations as template conduct has sanctified the method, not "
            "merely recorded it."
        ),
    },
    {
        "anchor": "Allah's Apostle said, 'Collect for me all the Jews present in this are",
        "response": (
            "Classical apologetics reads the hadith as addressed to the specific Jews of Medina "
            "who had repeatedly broken treaties with Muhammad — a categorical statement made in "
            "the heat of wartime confrontation, not a standing theological verdict on Jewish "
            "communities everywhere and for all time. Modern Muslims who do not draw "
            "eschatological conclusions from it read it as historical record of a specific "
            "conflict."
        ),
        "refutation": (
            "The hadith's plain text says \"the Jews\" as a category, with eternal hellfire as "
            "the stated fate. Classical commentators read the verdict as substantive — not "
            "merely rhetorical during conflict. The \"specific Jews of Medina\" narrowing is "
            "modern apologetic work; fourteen centuries of Muslim-Jewish relations have been "
            "shaped by exactly the universal reading this defense now disavows. A founder "
            "consigning a religious community to eternal hell in direct speech has done "
            "theological work that no context-narrowing erases."
        ),
    },
    {
        "anchor": "Heraclius was a foreteller and an astrologer.",
        "response": (
            "Apologists argue the hadith records the historical suggestion made by Byzantine "
            "advisors — it does not endorse the proposal, only preserves it as narrative "
            "detail. The story's larger point is Heraclius's recognition of Muhammad's "
            "prophethood through astrological foresight, which Byzantine culture preserved "
            "through its pagan substrate. The hadith documents Byzantine Christian thinking, "
            "not Islamic policy."
        ),
        "refutation": (
            "The hadith's narrative structure is diagnostic: the \"kill every Jew\" suggestion "
            "is presented uncritiqued within the Muhammad-is-prophesied recognition story, "
            "with no moral commentary. A divinely-inspired tradition preserving such content "
            "without comment has signaled that the suggestion, while not officially "
            "endorsed, was also not theologically objectionable enough to flag. The framing "
            "puts Jewish extermination in the mouth of an astrological Byzantine advisor, "
            "which provides deniability while the substantive content enters the Muslim "
            "imagination through repetition."
        ),
    },
    {
        "anchor": "The magic was worked on Allah's Apostle so that he began to fancy",
        "response": (
            "Classical theology preserves the bewitchment as genuine supernatural attack that "
            "did not compromise prophetic function — revelation during the period remained "
            "protected, and Surah al-Falaq and al-Nas were revealed as the divinely-sanctioned "
            "response to sorcery. Apologists emphasise the hadith's candour (the tradition "
            "does not sanitise Muhammad's vulnerability) as evidence of its authenticity."
        ),
        "refutation": (
            "The \"cognitively bewitched but prophetically intact\" distinction is modern "
            "retrofit. If a Jewish sorcerer could implant false memories in Muhammad for "
            "months, the claim that no revelation was tainted cannot be verified within the "
            "tradition's own framework — it is stipulated by the same sources that document "
            "the vulnerability. Quran 5:67's promise of divine protection is directly "
            "undermined. The tradition's candour is real, and its cost to the prophetic "
            "authority claim is what apologetic work must manage."
        ),
    },
    {
        "anchor": "An-Nadr bin al-Harith was a Meccan storyteller who competed with Muham",
        "response": (
            "Classical apologetics frames An-Nadr's execution as lawful wartime penalty: he "
            "was a Meccan prisoner taken at Badr who had actively mocked the Prophet, "
            "competed with revelation by reciting Persian tales as equivalents, and "
            "contributed to anti-Muslim tribal mobilisation. Muhammad's authorisation of his "
            "execution was a military-legal judgment, not silencing of a literary critic per "
            "se."
        ),
        "refutation": (
            "\"Wartime penalty\" does not dissolve what the underlying offense was: An-Nadr's "
            "primary activity was cultural — competing with Muhammad's revelations through "
            "Persian storytelling performance. That is literary rivalry, and its punishment "
            "is death. The Badr prisoner context does not change the selection criterion: "
            "other prisoners were ransomed or spared; An-Nadr was executed specifically. A "
            "religion whose foundational narrative includes the execution of a cultural "
            "competitor has modelled a response to intellectual rivalry that does not "
            "reflect well on the moral profile its tradition claims."
        ),
    },
    {
        "anchor": "A Jew crushed the head of a girl between two stones.",
        "response": (
            "Classical apologetics frames the Prophet's judgment as applying the principle of "
            "<em>qisas</em> (equal retribution) as articulated in Quran 5:45, which the Torah "
            "also teaches. The offender is executed by the method he used. Modern apologists "
            "argue such literal <em>lex talionis</em> application was exceptional rather than "
            "standing practice, with monetary <em>diyya</em> (blood-money) typically "
            "substituting for physical retaliation."
        ),
        "refutation": (
            "The <em>qisas</em> framework is accurate but does not address the method's "
            "ethical content: head-crushing execution is torture-level violence regardless of "
            "its match to the original crime. Modern <em>lex talionis</em> systems (where they "
            "exist) execute by methods that minimise suffering (lethal injection, gas "
            "chamber), not by replicating the torture. A religion whose <em>qisas</em> system "
            "authorised matched-torture execution has preserved a penalty regime whose "
            "content even modern retributivist frameworks reject as cruel."
        ),
    },
    {
        "anchor": "Khubaib said, 'O Allah! Count them and kill them one by one",
        "response": (
            "Apologists contextualise Khubaib's death-curse as the imprecatory prayer of a "
            "tortured martyr facing execution — a psychologically understandable response "
            "preserved in the record as evidence of his steadfastness, not as prescriptive "
            "teaching. The prayer's supposed effectiveness is framed as Allah's vindication "
            "of an innocent believer, not a model for ordinary petition."
        ),
        "refutation": (
            "Canonising such prayers as effective instruments of collective retribution is "
            "itself the problem — the tradition preserves not only the prayer but its "
            "purported supernatural fulfilment. That makes imprecation a standing religious "
            "instrument, not a one-time biographical detail. Muhammad himself is preserved "
            "cursing entire tribes by name for a month after atrocities, establishing the "
            "same pattern. A framework in which supernatural death-curses on entire groups "
            "are theologically workable has weaponised prayer itself."
        ),
    },
    {
        "anchor": "When the (upper) edge of the sun appears (in the morning)",
        "response": (
            "Apologists read the \"Satan's horns\" motif as symbolic — a theological marker "
            "for the pagan Arab practice of sun-worship at sunrise and sunset, not a "
            "cosmological claim about solar trajectory. The prayer-timing rule derives from "
            "the need to prevent conflation of Islamic prayer with pagan sun-veneration, with "
            "the \"horns\" language serving as rhetorical distancing."
        ),
        "refutation": (
            "Classical tafsir (Tabari, Ibn Kathir) read the Satan's-horns language as "
            "referring to a real metaphysical state of the sun at rising and setting, not a "
            "pure rhetorical flourish. The hadith's cosmology — where the sun has a single "
            "physical location relative to Satan's horns — presupposes flat-Earth cosmology, "
            "since a spherical Earth places the sun above different longitudes "
            "simultaneously. The \"symbolic only\" reading is retrofit; the tradition "
            "preserved the horns-language because its cosmology accommodated it."
        ),
    },
    {
        "anchor": "'Umar bin Al-Khattab addressed the Corner (Black Stone)",
        "response": (
            "Classical apologetics treats the <em>ramal</em> (ritual jog) origin story as "
            "evidence of prophetic pedagogical wisdom: Muhammad used what would impress a "
            "hostile pagan audience (a display of Muslim strength) and then preserved the "
            "action as ritual because its spiritual significance continued after the "
            "original audience was gone. The transformation of tactical performance into "
            "sanctified practice is part of Islamic ritual development."
        ),
        "refutation": (
            "\"Performance becomes ritual\" is exactly the pattern that diagnoses the "
            "practice's origin: the Ka'ba rituals' presentation as ancient Abrahamic "
            "observance is undermined when the tradition itself preserves specific "
            "<em>innovations</em> with documented PR origins. The <em>ramal</em>'s story is "
            "one case; the Black Stone kiss, the Safa-Marwa run, and the circumambulation "
            "direction have similar non-revelation histories. Ritual that is "
            "self-admittedly performance cannot simultaneously be eternally-revealed "
            "sanctified practice without the tradition tripping over its own evidence."
        ),
    },
    {
        "anchor": "Were your people not close",
        "response": (
            "Classical apologetics treats the hadith as evidence of Muhammad's political "
            "pragmatism within a Meccan society still transitioning from polytheism — he "
            "accepted suboptimal Ka'ba architecture (short of the Abrahamic original) because "
            "full reform would have alienated new Muslims who were psychologically attached to "
            "the existing structure. The tradition preserves the Prophet's awareness that "
            "reformist change must be phased."
        ),
        "refutation": (
            "The hadith admits that the central sanctuary of Islam remained a pagan structure "
            "the Prophet knew was incorrectly configured for monotheism — and decided not to "
            "correct for political reasons. That concedes what classical apologetics denies "
            "elsewhere: the Ka'ba is a pre-Islamic polytheistic shrine whose Abrahamic "
            "pedigree is asserted, not independently established. Muhammad's own preserved "
            "admission that \"if your people were not so new to Islam\" he would have "
            "reshaped the Ka'ba means he knew its form was wrong — but the pragmatic "
            "accommodation became eternal practice."
        ),
    },
    {
        "anchor": "We went with Allah's Apostle, in the Ghazwa of Banu Al-Mustaliq",
        "response": (
            "Classical apologetics frames the Banu Mustaliq episode within the "
            "progressive-regulation trajectory: Islam inherited concubinage from 7th-century "
            "custom and tightened its conditions (required ownership, mandated "
            "<em>istibra</em> waiting periods, permitted manumission via "
            "<em>umm walad</em> doctrine). The <em>'azl</em> discussion reflects practical "
            "questions about descendant-rights and property-value, not moral endorsement of "
            "the underlying sexual access."
        ),
        "refutation": (
            "Classical jurisprudence treated concubinage as permanent permission, not a "
            "trajectory toward abolition. The \"progressive regulation\" framing is 20th-"
            "century apologetic retrofit. The hadith's Q&A with Muhammad accepted the "
            "underlying transaction (sex with captive married women) and regulated "
            "contraception. ISIS cited this exact hadith with classical legal footnoting in "
            "its 2014 enslavement of Yazidi women. A religion that regulates the technique "
            "of sex with captured married women has ratified the transaction and moved on "
            "to its parameters."
        ),
    },
    {
        "anchor": "I have been given five things which were not given to any one else",
        "response": (
            "Classical apologetics reads \"booty was made lawful for me\" within the broader "
            "framework of Islam's war-ethics: spoils distributed in fixed proportions "
            "(warriors 4/5, the state 1/5), regulated against theft, intended for community "
            "benefit. Prior prophets had different dispensations because their communities "
            "had different needs; Islam's war-ethics is not a rejection of prior prophetic "
            "standards but a specific historical application of divine wisdom."
        ),
        "refutation": (
            "The hadith plainly concedes that booty-taking was not lawful for previous "
            "prophets — Abraham, Moses, David, Jesus. That means Islamic war-ethics "
            "includes a privilege earlier prophets did not possess. If earlier divine "
            "standards prohibited it, either the earlier standards were wrong (which "
            "Islamic theology cannot say about divinely-given prior law) or the new "
            "standards represent a loosening, not a tightening, of prior ethics. The "
            "boast's structure is the problem: Muhammad is preserved as declaring that he "
            "has access to what previous prophets did not, with booty being the specific "
            "item named."
        ),
    },
    {
        "anchor": "And to pay Al-Khumus (one fifth of the booty to be given in Allah's Ca",
        "response": (
            "Classical apologetics treats the <em>khumus</em> as funding for public-religious "
            "purposes (support for orphans, the poor, travellers, and the Prophet's "
            "household in its representative function). The Prophet's personal use of the "
            "share was for public role-related expenses, not personal luxury; his recorded "
            "simple lifestyle is evidence that the <em>khumus</em> did not enrich him."
        ),
        "refutation": (
            "\"Public purposes including prophet's household\" is structural dependency of "
            "prophetic authority on war-generated revenue. A religious leader's income tied "
            "to the volume of plunder creates an institutional incentive favouring "
            "continued military operation. The \"simple lifestyle\" observation does not "
            "address the design flaw: revenue from violence fuels the authority whose "
            "revelation endorses the violence. A system that fuses prophecy with "
            "procurement has a structural problem no amount of modest-personal-living "
            "rhetoric repairs."
        ),
    },
    {
        "anchor": "Three persons will get their reward twice.",
        "response": (
            "Classical apologetics frames the double-reward as evidence of Islam's "
            "trajectory toward elevating slaves: a Muslim who educates, liberates, and "
            "marries his slave girl receives extra spiritual credit precisely because this "
            "pathway was meant to dissolve the institution. The hadith's structure "
            "incentivises the dissolution mechanism — manumission through marriage — rather "
            "than endorsing the underlying ownership."
        ),
        "refutation": (
            "The reward presupposes the ownership — the entire pipeline (acquire, educate, "
            "free, marry) requires slavery as the starting point. If the hadith were "
            "genuinely abolitionist, it would incentivise refusing to own slaves in the "
            "first place. Instead, it rewards the owner for processing a specific slave "
            "through a religiously-approved path, while slavery itself remains in "
            "permanent operation. A reward structure whose first step is \"own a female "
            "slave\" has endorsed the first step as much as the last."
        ),
    },
    {
        "anchor": "As if I were looking at him, a black person with thin legs plucking",
        "response": (
            "Classical apologetics reads the eschatological description as specific "
            "prophecy — the Prophet is identifying a future Ethiopian figure whose "
            "physical features are given as recognition criteria, not as racial disparagement. "
            "The description functions as a miraculous sign: when such a person arrives, "
            "Muslims will know the end is near. The physical specificity is prophecy-"
            "function, not prejudice."
        ),
        "refutation": (
            "\"Recognition criteria\" through racialised physical description is exactly "
            "the problem: the prophecy locates evil cosmic agency in a specific ethnicity "
            "and body-type. Contrast the Dajjal (marked as one-eyed, a non-ethnic trait). "
            "The Ethiopian villain is marked by ethnicity and skin colour — features that "
            "describe a community, not a single person. The prophecy provides theological "
            "warrant for associating Black physical features with end-times evil, which "
            "has resonated through Islamic history in ways that are not merely incidental."
        ),
    },
    {
        "anchor": "Nobody who dies and finds good from Allah (in the Hereafter) would wish",
        "response": (
            "Classical theology reads the hadith as expressing the martyr's voluntary "
            "devotion — the paradise reward is so satisfying that he would gladly repeat "
            "the sacrifice. The language is affirmative of faith-commitment, not a call to "
            "recruit suicide-fighters; the context is paradise-based devotion, not "
            "strategic calculation."
        ),
        "refutation": (
            "The hadith's structure — martyr wishes to die ten times for the paradise "
            "reward — has been cited in every extremist recruitment tradition from medieval "
            "jihad letters to modern suicide-bombing materials. The \"devotional language\" "
            "reading is available but does not neutralise the operational use. A "
            "scripture-status text that represents paradise as offering sufficient "
            "compensation to warrant repeated death is a text whose reward-for-sacrifice "
            "framework has exactly the incentive structure it appears to have."
        ),
    },
    {
        "anchor": "When a man sits in between the four parts (arms and legs of his wife)",
        "response": (
            "Classical apologetics argues the hadith provides necessary ritual-purity "
            "guidance for an intimate matter requiring precise legal specification. The "
            "\"four parts\" framing is a discreet referent to sexual penetration, with "
            "the bath requirement reflecting sexual activity's ritual-impurity status. "
            "The specificity is legal-technical, not salacious."
        ),
        "refutation": (
            "The concession that the Quran needed to specify \"when a man sits in between "
            "the four parts\" is itself the problem: a divine scripture is descending to "
            "the geometric details of the marriage bed as standing ritual law. \"Legal-"
            "technical specification\" is the apologetic framing for content that would be "
            "judged inappropriate if preserved in any other religious tradition. The "
            "embedding of such specifics into eternal scripture reveals the imagination "
            "that authored it — one concerned with the mechanics of sexuality as a "
            "domain of divine regulation."
        ),
    },
    {
        "anchor": "The Prophet ordered that both of them be stoned to death",
        "response": (
            "Classical apologetics situates the Jewish-couple stoning within "
            "<em>ahl al-kitab</em> jurisprudence: Muhammad ruled according to the Torah's "
            "own standard (Leviticus 20:10) for adjudicating a case involving Jewish "
            "parties. The episode is procedural justice, not Islamic imposition."
        ),
        "refutation": (
            "\"Their own law\" commits Islam to the Torah's reliability — which it "
            "elsewhere dismisses as corrupted (<em>tahrif</em>). Applying Torah "
            "punishments while rejecting Torah doctrines is selective appropriation. And "
            "the stoning method is adopted in Islamic law thereafter (through the "
            "<em>naskh al-tilawa</em> doctrine) — which means Muhammad's ruling did not "
            "merely acknowledge Torah law for that case but adopted it into Islamic "
            "criminal procedure. The \"adjudicating their law\" framing is rhetorical "
            "cover for what was the adoption of Torah-style stoning into Islamic "
            "jurisprudence from an allegedly corrupted source."
        ),
    },
    {
        "anchor": "The hand of a thief should be cut off for stealing something that is w",
        "response": (
            "See the parallel in Abu Dawud and the Quran 5:38: classical jurisprudence "
            "added procedural restrictions (<em>nisab</em> minimum, <em>hirz</em> secure "
            "storage, Umar's famine suspension). The punishment's stated deterrent function "
            "and rarity of actual application in classical practice are cited as "
            "mitigating context."
        ),
        "refutation": (
            "The procedural restrictions are juristic additions not in the hadith or the "
            "verse, and modern jurisdictions (Saudi Arabia, Iran, northern Nigeria, parts "
            "of Sudan) continue to perform amputations. The punishment's permanence for a "
            "remediable offense (theft) is disproportionate by modern standards, and the "
            "class-blind application means poor thieves (who steal out of necessity) face "
            "the same blade as wealthy embezzlers — a feature the classical jurisprudence "
            "did not systematically address."
        ),
    },
    {
        "anchor": "Treat women nicely, for a woman is created from a rib",
        "response": (
            "Classical apologetics reads the rib-metaphor as pedagogical gentleness: the "
            "Prophet is counseling patience with women's distinctive nature, not denigrating "
            "it. The \"crooked rib\" is specifically about not attempting to change women's "
            "character through force — a corrective against Arab men who might have tried "
            "to remake their wives. The metaphor uses the Genesis creation account but "
            "frames it as a call to acceptance and kindness."
        ),
        "refutation": (
            "The \"pedagogical gentleness\" reading still imports woman's naturally-bent "
            "moral character as a revealed theological premise. The Genesis 2 folk-anatomy "
            "(Eve from Adam's rib) is brought into Islamic scripture as authoritative "
            "biology — with the rib's curvature standing for female intellectual/moral "
            "quality. Modern medicine does not support the creation-from-rib claim in any "
            "literal sense; the metaphor stands because the tradition treats women's "
            "character as intrinsically curved. \"Be kind to the crooked\" is kindness, "
            "but it is kindness that has already judged."
        ),
    },
    {
        "anchor": "I was playing with my girlfriends on a see-saw when my mother called m",
        "response": (
            "Standard apologetic responses for Aisha's age are covered across the other "
            "canonical collections. For this Bukhari preservation specifically, apologists "
            "cite the collection's rigorous chain-authentication as confirming the age "
            "detail without allowing revisionist redating to dismiss it."
        ),
        "refutation": (
            "Candid preservation is the problem. Aisha's first-person narration places her "
            "on a swing immediately before being delivered for consummation. Her own voice "
            "describes the event as a child describes interrupted play — no adult "
            "recognition of what was coming. The apologetic must choose: accept the "
            "childhood details and address what the consummation meant, or reject them "
            "and repudiate canonical hadith. The tradition preserves the details, which "
            "tells us the 7th-century community saw nothing ethically problematic about "
            "the scene."
        ),
    },
    {
        "anchor": "The Prophet was lying down with his thighs or calves uncovered",
        "response": (
            "Classical apologetics reads the thigh-exposure hadith as evidence of Muhammad's "
            "relaxed intimacy in a household context — the Prophet is shown in "
            "unselfconscious posture among close companions, indicating both his humanity "
            "and the distinction between informal household life and public modesty. The "
            "differential response to companions (relaxed with Abu Bakr and Umar, covering "
            "for Uthman) reflects Uthman's specific dignified demeanor warranting more "
            "formal greeting."
        ),
        "refutation": (
            "The <em>'awrah</em> (private-parts coverage) rules are elsewhere treated as "
            "universal — the male <em>'awrah</em> from navel to knee must be covered at "
            "all times outside specific private contexts. The hadith's differential "
            "treatment of three companions contradicts the universal rule: Muhammad "
            "covered for one guest but not for two others, which means the rule depends "
            "on interpersonal factors rather than on objective legal category. A ritual "
            "code whose foundational example bends for personal comfort has conceded that "
            "its legal framework is more flexible than its apologetic insists."
        ),
    },
    {
        "anchor": "Those who make these pictures will be punished on the Day of Resurrect",
        "response": (
            "Classical apologetics reads the picture-prohibition as specific to idolatry-"
            "related imagery in the 7th-century context — pre-Islamic Arabia's artistic "
            "tradition was primarily idol-making, so the Prophet's prohibition targeted "
            "images that functioned as objects of worship. Modern apologists distinguish "
            "between idol-associated images and non-worship artistic representation, "
            "allowing photography and some representational art under the narrower reading."
        ),
        "refutation": (
            "Classical Islamic scholarship did not uniformly apply the narrow \"only "
            "idolatry-related\" reading. Sunni jurisprudence broadly prohibited "
            "representational painting and sculpture of animate beings, which is why "
            "classical Islamic art developed its distinctive non-figurative tradition. "
            "Modern extremist iconoclasm — Taliban's destruction of the Bamiyan Buddhas, "
            "ISIS's destruction of Assyrian statues in Mosul — cites exactly this "
            "hadith. The narrow reading is a modern softening that fourteen centuries of "
            "classical art-theology did not deliver."
        ),
    },
    {
        "anchor": "Whoever sees me in a dream has seen me in reality, for Satan cannot ta",
        "response": (
            "Classical theology treats prophetic dreams as authentic supernatural events "
            "— Muhammad's form cannot be imitated by Satan, providing a rare legitimate "
            "channel of spiritual experience. Classical scholars developed criteria for "
            "distinguishing authentic prophetic dreams from mere psychological imagery "
            "(al-Nawawi's conditions). The hadith is not an invitation to build doctrine "
            "on dreams but a reassurance about a specific narrow channel."
        ),
        "refutation": (
            "The \"criteria for authenticity\" have proven unable to adjudicate 1,400 "
            "years of competing dream-based religious claims. Sufi masters, Mahdi "
            "claimants, reform-movement founders, and local spiritual authorities have "
            "all cited dream-encounters with Muhammad as validation for their teachings "
            "or authority. If the hadith genuinely protected against false dream-claims, "
            "such conflicts should be adjudicable within the tradition — they are not. "
            "The hadith's rule creates the religious-authority structure it claims to "
            "prevent."
        ),
    },
    {
        "anchor": "The prayer is annulled by a passing donkey, dog and woman",
        "response": (
            "Classical apologetics cites Aisha's own objection to this hadith as evidence "
            "of the tradition's honest preservation of contested material. Different "
            "schools (Shafi'i) restricted or qualified the annulment rule, recognising "
            "the theological tension. Modern apologists treat the hadith as historically "
            "attested but juristically marginal."
        ),
        "refutation": (
            "The hadith remains <em>sahih</em> — Aisha's objection did not remove it from "
            "the canonical corpus. Its preservation at the highest authority level means "
            "the category (women grouped with donkeys and dogs as prayer-invalidators) "
            "has institutional weight regardless of juristic discomfort. Aisha's "
            "objection documents her awareness of the theological problem; the canon's "
            "retention documents that her objection was insufficient to override the "
            "chain-authentication. The episode reveals both her reasoning and the "
            "tradition's willingness to preserve anti-female material against her "
            "reasoning."
        ),
    },
    {
        "anchor": "You people read the Torah with its corruption",
        "response": (
            "Classical apologetics defends the <em>tahrif</em> claim as referring to "
            "interpretive corruption (<em>tahrif al-ma'na</em>) rather than textual "
            "corruption (<em>tahrif al-nass</em>) — the Torah's words remain, but Jews "
            "distort their meaning. This reading preserves the Torah as divinely-revealed "
            "while allowing Islamic polemic against Jewish doctrines that contradict the "
            "Quran."
        ),
        "refutation": (
            "Manuscript evidence shows the Torah has been remarkably textually stable — "
            "the Dead Sea Scrolls (pre-Christian era) preserve texts essentially identical "
            "to the Masoretic text. If only interpretation is corrupted, the interpretive "
            "history should be addressable, not dismissible. The classical Muslim "
            "polemic (Ibn Hazm, al-Biruni) oscillated between <em>tahrif al-ma'na</em> "
            "and <em>tahrif al-nass</em> depending on the polemical need — a moving "
            "goalpost structure that reveals the doctrine as instrumental rather than "
            "evidential."
        ),
    },
    {
        "anchor": "Some Zanadiqa (atheists) were brought to Ali and he burnt them.",
        "response": (
            "Classical apologetics notes that Ibn Abbas's objection was specifically to the "
            "<em>method</em> of execution, not to the punishment itself — burning with fire "
            "was prohibited because fire-punishment is Allah's prerogative, but the "
            "underlying apostasy death penalty was confirmed. The hadith demonstrates "
            "Islamic legal procedural sophistication even while enforcing apostasy law."
        ),
        "refutation": (
            "The apologetic concedes the problem it claims to solve: both companions "
            "agreed the apostates should be killed — the only debate was whether to burn "
            "them. Neither questioned the underlying punishment. That unanimity across "
            "Ali and Ibn Abbas establishes the apostasy death penalty as consensus "
            "classical doctrine. Modern apologetic narrowing (to political apostasy + "
            "hostility) is not the reading the canonical record delivers."
        ),
    },
    {
        "anchor": "Whoever changes his Islamic religion, then kill him.",
        "response": (
            "Covered in the Abu Dawud and Nasa'i parallels: modern apologetic narrowing to "
            "public-political apostasy combined with hostility, prioritisation of 2:256, "
            "contextualisation as 7th-century political circumstances. The hadith's "
            "preservation across canonical collections is framed as evidence of authenticity "
            "not authorisation of modern practice."
        ),
        "refutation": (
            "Classical consensus across all four Sunni schools and Jaʿfari Shia law treated "
            "apostasy itself as capital. Current enforcement in multiple jurisdictions "
            "applies to private belief change. Cross-collection attestation (six canonical "
            "sources) makes the \"fringe hadith\" dismissal impossible. The "
            "\"no compulsion\" tension is real; the classical solution was abrogation of "
            "2:256, which modern apologists quietly abandon while still invoking it."
        ),
    },
    {
        "anchor": "Umar said, 'O Allah's Apostle! Allow me to chop off his neck!'",
        "response": (
            "Classical apologetics emphasises the Prophet's refusal as the hadith's moral "
            "center: restraint against summary execution is what the tradition models, not "
            "Umar's proposal. The preservation of Umar's request alongside the refusal "
            "demonstrates Islamic legal proceduralism — the right response to dissent is "
            "not execution but continued engagement."
        ),
        "refutation": (
            "Muhammad's refusal was pragmatic (\"people would say Muhammad kills his "
            "companions\"), not principled. Umar's default response of proposing "
            "beheading for dissent is preserved without moral rebuke, and Umar "
            "subsequently became the second caliph whose reign is celebrated as "
            "exemplary. The hadith's structural effect is to normalise the "
            "\"let me behead him\" proposal as understandable even if not adopted — "
            "which is different from prohibiting it. A tradition that preserves summary-"
            "execution proposals as character detail has communicated something about "
            "what it considers reasonable disagreement."
        ),
    },
    {
        "anchor": "Allah reduced ten (prayers) for me.",
        "response": (
            "Classical theology reads the prayer-negotiation as pedagogical narrative: "
            "Allah's initial 50-prayer prescription and progressive reduction demonstrate "
            "divine mercy built into the revelation itself. Moses's role is not correction "
            "of Allah but participation in showing the community how much mercy exists in "
            "the final five-prayer requirement. The lesson is about gratitude for the "
            "mercy that brought 50 down to 5."
        ),
        "refutation": (
            "The narrative structure has Allah making an initial prescription He then "
            "revokes at Moses's urging. If the original prescription was what Allah "
            "actually wanted, the reduction is compromise; if the reduction was what "
            "Allah wanted, the original was performative. Either way, a supposedly "
            "omniscient deity is depicted as needing Moses's advice about human "
            "endurance. \"Pedagogical\" is modern retrofit; the classical commentators "
            "read the sequence as actual negotiation, with Moses's voice functioning as "
            "advisor to divine legislation — a structure that does not fit Islam's "
            "elsewhere-affirmed divine self-sufficiency."
        ),
    },
    {
        "anchor": "Our Lord, the Blessed, the Superior, comes every night down",
        "response": (
            "Classical Athari theology (Ibn Taymiyyah, Salafi tradition) affirms Allah's "
            "nightly descent literally while consigning its <em>how</em> (<em>kayfiyya</em>) "
            "to Allah's knowledge — Allah descends, but we do not know how. This preserves "
            "the hadith's plain sense without requiring anthropomorphic physical claims. "
            "Ash'arite theology reads the descent metaphorically as an expression of "
            "Allah's special nearness during the last third of the night."
        ),
        "refutation": (
            "The <em>kayfiyya</em> consignment concedes that the literal reading is "
            "anthropomorphic and requires divine physical location. The Athari position "
            "preserves the surface claim while explicitly refusing to explain it, which "
            "is epistemic unfalsifiability. The Ash'arite metaphorical reading has its "
            "own problem: \"nightly descent\" as metaphor implies specific temporal "
            "structure (the last third of every night, everywhere on Earth) that does "
            "not make sense with a round rotating planet. The 7th-century flat-Earth "
            "cosmology is what makes the hadith coherent; modern cosmology is not."
        ),
    },
    {
        "anchor": "Consensus fiqh ruling, derived from hadith corpus:",
        "response": (
            "Classical apologetics argues the half-<em>diyya</em> for women reflects the "
            "economic reality of 7th-century Arabia, where men were primary breadwinners "
            "and their deaths caused greater material loss to dependents. The "
            "<em>diyya</em> system is compensatory, not valuational — the amount "
            "reflects economic support lost, not intrinsic human worth. Modern reformist "
            "jurisprudence increasingly equalises <em>diyya</em> across genders."
        ),
        "refutation": (
            "\"Economic compensation\" is the apologetic frame for what operates as a "
            "ranked valuation system: non-Muslim women receive even less (1/16 of a "
            "Muslim man in some classical schedules), which cannot be explained by "
            "economic contribution and tracks religious hierarchy. Current enforcement "
            "in several jurisdictions (Saudi Arabia, Iran) applies the ratio. Modern "
            "reformist equalisation is welcome but requires reading the tradition "
            "against its classical grain. An eternal legal framework whose foundational "
            "<em>diyya</em> schedules tier human worth by sex and religion has embedded "
            "hierarchy into law, regardless of how it is softened in practice."
        ),
    },
    {
        "anchor": "Hear and obey even if an Abyssinian slave whose head is like a raisin",
        "response": (
            "Classical apologetics frames the obedience hadith as establishing social "
            "order against the fitna (chaos) of rebellion — the Prophet urges patient "
            "endurance of even imperfect leadership to prevent the greater evil of civil "
            "war. This is political stability doctrine, not endorsement of tyranny. "
            "Modern reformists argue the hadith should be read alongside the Quran's "
            "<em>shura</em> (consultation) verses, which support accountable governance."
        ),
        "refutation": (
            "\"Stability doctrine\" describes the hadith's operational effect: 1,400 years "
            "of Muslim political thought has cited this hadith to discourage rebellion "
            "against rulers regardless of their abuses. Every major Muslim despot from "
            "the Umayyads onward has invoked the obedience tradition against dissent. "
            "The <em>shura</em> verses exist but have not operated as check on caliphal "
            "and sultanic authority — the obedience hadith has. Modern reformist "
            "rereadings are welcome but run against fourteen centuries of classical "
            "application. A religion whose political theology prioritises obedience to "
            "rulers even when they flog and exile has given tyranny a theological warrant."
        ),
    },
    {
        "anchor": "Sahla bint Suhayl came to the Prophet and said, 'O Messenger of Allah",
        "response": (
            "Classical apologetics treats the Salim breastfeeding ruling as specific "
            "dispensation (<em>rukhsah</em>) for one household's particular situation. "
            "Other wives of Muhammad rejected extending the dispensation to their own "
            "cases, demonstrating that the ruling was narrow rather than a general rule. "
            "Modern apologists argue the 2007 Egyptian fatwa (Izzat Atiya) misapplied "
            "the narrow precedent."
        ),
        "refutation": (
            "The Egyptian fatwa's widespread ridicule confirms that the underlying hadith's "
            "content is uncomfortable — but it also demonstrates that the \"narrow "
            "dispensation\" has continued to generate legal questions. Classical "
            "jurisprudence did debate the scope of adult breastfeeding as a legitimate "
            "kinship-creation mechanism, because the hadith was canonical. A legal "
            "category whose foundational case is \"permit my nephew to nurse from my wife "
            "to create kinship-access\" is a category whose mere existence the "
            "tradition cannot relegate to irrelevance."
        ),
    },
    {
        "anchor": "Classical sources: Abdullah ibn Mas'ud",
        "response": (
            "Classical apologetics frames Ibn Mas'ud's disagreement as personal juristic "
            "opinion that did not prevail in the community's consensus. The fact that the "
            "Sahabi's position is preserved in the tradition's historical record "
            "demonstrates honest transmission; the community's adoption of the "
            "<em>mushaf</em> that includes 113 and 114 reflects broader consensus on the "
            "canonical form."
        ),
        "refutation": (
            "Ibn Mas'ud was one of four companions the Prophet personally commended as "
            "Quran-teachers — he was not a minor figure whose personal view can be "
            "dismissed. His rejection of 113 and 114 as Quranic means either (a) the "
            "Prophet endorsed as Quran-teacher a companion with an incomplete Quran, or "
            "(b) the final canon was contested even among the Prophet's inner circle. "
            "Either conclusion undermines the \"one preserved Quran\" claim. The "
            "community's \"consensus\" was produced by Uthman's standardisation, which "
            "burned Ibn Mas'ud's codex — the disagreement was resolved by fire, not by "
            "argument."
        ),
    },
    {
        "anchor": "Ubayy ibn Ka'b's mushaf contained two additional suras",
        "response": (
            "Classical apologetics treats Ubayy's extra suras (al-Khal' and al-Hafd) as "
            "<em>dua</em> (supplications) that Ubayy personally included in his codex for "
            "liturgical-memorial purposes, not as claimed revelations. The classical "
            "scholarship's preservation of this detail is evidence of transmission "
            "honesty, not of Quranic boundary uncertainty."
        ),
        "refutation": (
            "Umar himself is preserved as treating these passages as Quran — which means "
            "a man the Prophet particularly loved included material the canonical text "
            "excludes. The \"personal liturgical addition\" framing is apologetic "
            "retrofit; the classical sources describe the passages being recited in "
            "prayer as scripture. The canonical boundary was not settled even among top "
            "companions. A text whose boundary requires a post-Prophet standardisation "
            "process (which then had to be enforced by destroying alternatives) is a "
            "text whose preservation-claim history is more complicated than the "
            "tradition's self-description."
        ),
    },
    {
        "anchor": "Uthman sent to every Muslim province one copy of what they had copied",
        "response": (
            "Classical apologetics frames Uthman's standardisation as necessary response "
            "to dialectal drift — Arab tribes in different regions were reciting with "
            "different pronunciations, creating concern about community unity. Uthman's "
            "action standardised the consonantal text while preserving the divinely-"
            "sanctioned <em>qira'at</em> (recitation modes) as variants within the "
            "unified framework. The burning prevented schism, not preservation failure."
        ),
        "refutation": (
            "If the Quran were preserved by Allah (as 15:9 claims), human intervention "
            "through burning would be unnecessary for preservation. The act of destroying "
            "competing codices contradicts the preservation claim: textual uniformity "
            "was enforced by fire, not secured by divine providence. The companions "
            "whose codices were destroyed (Ibn Mas'ud, Ubayy ibn Ka'b, others) had "
            "significant textual differences with the Uthmanic standard — which is why "
            "their codices had to be destroyed. Ancient manuscripts that survive "
            "(Sana'a palimpsest) show the Uthmanic standardisation process was more "
            "editorial than apologists typically acknowledge."
        ),
    },
    {
        "anchor": "Q 6:14:",
        "response": (
            "Classical tafsir resolves the \"first Muslim\" question through contextual "
            "reading: each passage refers to the respective prophet as \"first Muslim\" "
            "of his specific community — Muhammad was the first Muslim of his community, "
            "Moses of the Israelites, Abraham of his era. The word <em>muslim</em> "
            "(submitted one) applies to all prophets as monotheist submitters to Allah, "
            "with the \"first\" marker indexed to each prophet's local community."
        ),
        "refutation": (
            "The \"first of his community\" reading is the apologetic patch required to "
            "handle the surface contradiction. The Quran's plain text in each case says "
            "\"I am the first Muslim\" — without the community-qualifier the apologetic "
            "supplies. And the broader Islamic claim is that Islam is the eternal "
            "religion from Adam onward, which makes the \"first\" language odd for any "
            "post-Adam figure. If monotheism is the eternal truth, neither Muhammad nor "
            "Moses nor Abraham is \"first\" in any absolute sense — they are all later "
            "iterations. The apologetic patch works, but at the cost of conceding that "
            "\"first Muslim\" is rhetorical framing rather than precise claim."
        ),
    },
    {
        "anchor": "If a housefly falls in the drink of anyone of you, he should dip it",
        "response": (
            "Same as the first Bukhari entry's apologetic: modern bacteriophage research, "
            "pre-scientific microbiology framing, 7th-century vocabulary. Apologists "
            "emphasise the claim's retroactive compatibility with specific findings about "
            "fly-borne microbial agents."
        ),
        "refutation": (
            "Same refutation as the first fly-in-drink entry: modern microbiology does "
            "not support the \"opposite wings\" claim, the retroactive fit is apologetic "
            "pattern not prediction, and classical tafsir did not extract the "
            "bacteriophage reading before 20th-century biology made it possible to "
            "retrofit. A universal medical claim preserved across Bukhari and the "
            "broader canon that modern medicine specifically warns against is a claim "
            "whose scripture-status is the problem, not its interpretation."
        ),
    },
    {
        "anchor": "Naskh al-hukm wa al-tilawa (both ruling and wording abrogated)",
        "response": (
            "Classical apologetics defends the three-type abrogation system as "
            "theological-jurisprudential sophistication: different categories of "
            "abrogation serve different theological purposes (full revocation, "
            "ruling-retention with text-removal, text-retention with ruling-suspension), "
            "each preserving specific aspects of the divine pedagogy. The system is "
            "evidence of classical scholarship's rigor, not of textual incoherence."
        ),
        "refutation": (
            "Each category creates its own theological problem. \"Both abrogated\" removes "
            "material from the Quran entirely — meaning revelation was lost. \"Wording "
            "abrogated, ruling remains\" (the stoning rule) means the most severe "
            "Islamic punishment rests on a verse claimed-to-have-existed but absent "
            "from the canonical text. \"Ruling abrogated, wording remains\" means the "
            "Quran preserves commands that are no longer operative, requiring an "
            "external abrogation tradition to know which commands are binding. Any of "
            "these alone would be a doctrinal problem; all three together are the "
            "signature of a cumulative editorial history wearing theological "
            "sophistication as a costume."
        ),
    },
    {
        "anchor": "Classical tafsir on Q 68:1 (the letter",
        "response": (
            "Classical apologetics treats the \"Nun\" interpretations as pre-scientific "
            "cosmological speculation by tafsir scholars attempting to explain "
            "mysterious Quranic letter-openings. The fish-and-ox imagery is classical "
            "commentary, not Quranic text; modern interpretations reject the literal "
            "claim while retaining the letter's theological mystery as part of Islamic "
            "esoteric tradition."
        ),
        "refutation": (
            "Classical tafsir is the interpretive framework through which fourteen "
            "centuries of Muslim scholarship has understood the Quran — dismissing it "
            "as \"pre-scientific speculation\" leaves Islamic theology cut off from its "
            "own hermeneutical tradition. The fish-and-ox cosmology is a direct import "
            "from Hindu and Babylonian mythology, confirming that the tafsir tradition "
            "absorbed regional folk cosmologies. Modern apologetic distance from "
            "classical tafsir is possible but it requires conceding that the community's "
            "authoritative interpreters were reading the Quran through inherited "
            "mythology."
        ),
    },
    {
        "anchor": "Whoever usurps even one span of the land of somebody",
        "response": (
            "Modern apologetic readings reinterpret the \"seven earths\" as tectonic "
            "plates, earth layers (crust, mantle, core), or inhabited parallel realms — "
            "retrofit readings that attempt to align the cosmology with modern geology. "
            "Some apologists cite the <em>i'jaz 'ilmi</em> (scientific miracles) "
            "literature as demonstrating the hadith's compatibility with current "
            "earth-science."
        ),
        "refutation": (
            "The \"seven earths\" cosmology is a direct parallel to the Mesopotamian "
            "<em>Kur</em> (seven underworlds) that preceded Islam by millennia. The "
            "tectonic-plates retrofit requires reading the hadith's \"each with its own "
            "creatures\" as referring to layered habitable worlds — something modern "
            "geology does not support. The <em>i'jaz 'ilmi</em> industry reads modern "
            "science back into the hadith rather than reading the hadith forward to "
            "modern science; the pattern is compatibility after the fact, not "
            "prediction. The hadith preserves the inherited cosmology, relabeled."
        ),
    },
    {
        "anchor": "When the Prophet came to Madina, he saw the Jews fasting on the day of",
        "response": (
            "Classical apologetics frames the Ashura fast adoption as restoration of a "
            "genuine prophetic tradition: the Jews' fast commemorated Moses's deliverance, "
            "which Islam (as the inheritor of the Abrahamic tradition) also affirms. "
            "Muhammad's subsequent adjustment to add the 9th or 11th day was "
            "differentiation from Jewish practice once the Muslim community had "
            "established its independent identity, not invention of a new ritual."
        ),
        "refutation": (
            "The sequence the hadith preserves — Muhammad adopts Jewish practice, then "
            "adjusts it specifically to differentiate from Jews — reveals ritual as "
            "social positioning. If Ashura genuinely preserved an Abrahamic prophetic "
            "fast, the form should not have needed to be modified to <em>differ</em> "
            "from Jewish observance. The modification exists precisely because the "
            "Prophet did not want Muslims to look like Jews. That is identity politics "
            "in ritual vocabulary, and it exposes the \"restoration\" framing as "
            "retrospective ideology rather than historical description."
        ),
    },
    {
        "anchor": "I looked at Paradise and saw that the majority of its dwellers were th",
        "response": (
            "Classical apologetics reads the hadith as local observational comment about "
            "the Prophet's community — addressable faults (ingratitude, cursing) were "
            "more common among women of his era because of specific social conditions, "
            "not because of intrinsic female spiritual deficiency. Paired with Quran "
            "33:35's affirmation of spiritual equality, the hadith is contextual "
            "observation, not essentialist claim."
        ),
        "refutation": (
            "Cross-collection preservation (Bukhari, Muslim, Tirmidhi, Ibn Majah) of the "
            "female-majority-hell claim at <em>sahih</em> grade makes \"local observation\" "
            "implausible — the tradition treats the demographic as standing eschatological "
            "fact, not period-specific report. The reasons given (ingratitude to husbands, "
            "excessive cursing) are exactly the kind of gendered-behavioural framing a "
            "patriarchal culture would extract as explanation for its already-assumed "
            "conclusion. A religion whose eschatology includes a gendered hell-majority "
            "has articulated something about half its adherents that 33:35's abstract "
            "equality verse does not neutralise."
        ),
    },
    {
        "anchor": "When the word (of torment) is fulfilled upon them",
        "response": (
            "Classical eschatology treats the Beast of the Earth as a specific end-time "
            "creature whose role is to mark believers and unbelievers at the final "
            "judgment — a prophecy whose specific physical form will become clear when "
            "it occurs. Classical tafsir's variations in description reflect different "
            "transmission chains rather than fundamental uncertainty about the "
            "creature's function."
        ),
        "refutation": (
            "A talking zoological creature as eschatological marker is folkloric, not "
            "theological — its closest structural parallels are in Zoroastrian and "
            "Christian apocalyptic traditions that preceded Islam. Classical tafsir's "
            "variations (the Beast is an ant-sized giant, or a particular animal with a "
            "specific location in Mecca, or a hybrid creature with multiple body parts) "
            "are irreconcilable; the tradition preserves them all because the source "
            "material was already inconsistent when it entered the canon. An "
            "eschatological figure whose description contradicts itself across "
            "transmissions is a figure whose \"specific form will become clear\" promise "
            "cannot be falsified, which is the structure of unfalsifiable myth."
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

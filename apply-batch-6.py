#!/usr/bin/env python3
"""Batch 6: Muslim Strong entries 19-34 (remaining 16)."""
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
    # 19 — Mukhannathun exiled
    {
        "anchor": "The Prophet expelled mukhannathun (effeminate men)",
        "response": (
            "Apologists argue the exile targeted specific individuals whose public presentation "
            "enabled inappropriate access to women's private quarters — in 7th-century Medina, "
            "<em>mukhannathun</em> were often employed as intermediaries in female-only "
            "spaces. The Prophet's rebuke, on this reading, responded to a specific case where "
            "a <em>mukhannath</em> described female anatomy to a male client in ways that "
            "violated privacy norms. The exile was a public-safety measure for the women of "
            "Medina, not a sweeping condemnation of gender presentation."
        ),
        "refutation": (
            "The \"privacy incident\" framing domesticates a collective exile. The hadith names "
            "multiple individuals and applies the penalty based on their presentation, not on "
            "specific acts of boundary-violation by each person. Classical jurisprudence (Ibn "
            "Taymiyyah, al-Nawawi) treated the hadith as establishing a standing "
            "juristic category — the <em>mukhannath</em> as a person deserving social "
            "restriction. Contemporary anti-LGBTQ enforcement in multiple Muslim-majority "
            "states cites this and parallel hadith as prophetic precedent. A religion that "
            "exiles people for their manner of being has made conformity a condition of "
            "community membership — and the specific-incident reading does not change the "
            "scope of the precedent it created."
        ),
    },
    # 20 — Prophet's sole intercession
    {
        "anchor": "I shall be the first intercessor in Paradise",
        "response": (
            "Classical theology distinguishes between two senses of intercession. The Quran "
            "forbids intercession <em>against Allah's will</em> — no one can override divine "
            "justice by pleading. But intercession <em>with Allah's permission</em> is "
            "explicitly allowed (2:255, 21:28), and the Prophet's intercession on the Day of "
            "Judgment is understood as permission granted, not authority asserted. The "
            "hadith's language of \"first intercessor\" means first in the divinely-sanctioned "
            "sequence, not a priestly authority."
        ),
        "refutation": (
            "The permission-vs-authority distinction is real in the theological framework, "
            "but the hadith's functional structure is priestly: the Prophet opens the gates "
            "of paradise, no one enters before him, and his intercession is the mechanism by "
            "which others are granted access. Functionally, this is the role of a mediator — "
            "a role Islam elsewhere denies to Jesus and, more sharply, criticises in "
            "Christian ecclesiology. The hadith restores for Muhammad precisely the "
            "intercessory structure Islam claims to have abolished. \"Only with permission\" "
            "is a theological caveat; the operational effect is the same as any priest-"
            "mediator model the Quran polemicises against."
        ),
    },
    # 21 — Polytheists impure / Mecca
    {
        "anchor": "O you who have believed, indeed the polytheists are unclean; so let them not app",
        "response": (
            "Covered under the Quran entry (9:28). Specifically for this hadith in Muslim's "
            "pilgrimage chapters, apologists argue the restriction to Mecca and Medina is a "
            "bounded sacred-geography rule, analogous to pre-Islamic Jewish restrictions on "
            "Gentile access to certain Temple zones. The non-Muslim ban is a ceremonial "
            "boundary, not a statement about the dignity of non-Muslims as persons. Outside "
            "the sacred cities, Muslim-non-Muslim interaction has operated without such "
            "spatial apartheid."
        ),
        "refutation": (
            "The Temple analogy breaks down at scale: Jerusalem's Temple had restricted zones "
            "for Gentiles but the city was not forbidden to them. Mecca and Medina are "
            "entirely closed to every non-Muslim on earth as a matter of Saudi state law "
            "directly derived from this tradition. The \"sacred geography\" framing cannot "
            "absorb a permanent universal exclusion of over six billion people from two cities. "
            "Classifying non-Muslim bodies as ritually impure — regardless of their personal "
            "conduct — remains what the text does, and it has produced exactly the exclusion "
            "the text prescribes. Bounded sacred geography would be a mosque's prayer hall; "
            "excluding the world's non-Muslims from two cities is apartheid under a "
            "theological banner."
        ),
    },
    # 22 — 70000 Jews follow Dajjal
    {
        "anchor": "The Dajjal will be followed by seventy thousand Jews of Isfahan",
        "response": (
            "Classical apologetics treats the hadith as eschatological prediction, not a "
            "standing indictment of Jews. The <em>Dajjal</em> is a supernatural antichrist; "
            "his followers in the prophecy are drawn from a specific geographical and "
            "historical setting. Apologists further argue that \"70,000\" is idiomatic for "
            "\"a large number\" and should not be taken as a literal ethnic roll-call. "
            "The hadith describes a future cosmic battle, not a present moral status."
        ),
        "refutation": (
            "The \"eschatological future only\" framing cannot insulate the text from its "
            "present-day use. The hadith is cited explicitly in modern antisemitic Muslim "
            "rhetoric, including in mainstream political discourse. A scripture-status "
            "tradition that assigns an entire ethno-religious group to the role of antichrist's "
            "foot-soldiers is not neutralized by saying the battle is in the future — the "
            "moral category is established now. The \"70,000 is idiomatic\" defense does not "
            "explain why a prophecy about a future army specifies the army's ethnicity and "
            "dress code. A divine text naming one specific people as the Antichrist's "
            "followers has scripted collective enmity into eternal theology."
        ),
    },
    # 23 — Jewish rabbi hiding stoning verse
    {
        "anchor": "A rabbi put his hand over the verse of stoning",
        "response": (
            "Apologists read the hadith as evidence of Muhammad's scriptural knowledge and "
            "interfaith engagement — he knew the Torah's contents well enough to identify what "
            "was being concealed. The episode is cited to show that Islam affirms the Torah's "
            "authenticity (at least in the 7th century) and to document specific rabbinic "
            "attempts to avoid the full weight of Mosaic law. The hadith is a historical "
            "anecdote about Muhammad's engagement with Jewish scholarship, not a general "
            "indictment of Jewish textual transmission."
        ),
        "refutation": (
            "The episode is stage-managed for polemical effect. The Torah's stoning verses "
            "(Leviticus 20:10, Deuteronomy 22:22) are part of the public textual tradition "
            "that Jewish communities preserved, copied, and discussed openly — there was no "
            "verse to hide because all verses were known. The rabbi's theatrical gesture is "
            "narrative framing, not recorded rabbinic practice. The hadith works narratively "
            "for an audience unfamiliar with Jewish textual culture: the villain is a Jew "
            "covering scripture with his hand, the hero is the Arab prophet exposing the "
            "concealment. A scene whose rhetorical work depends on the listener's ignorance "
            "of how Torah scrolls actually function is scene built for oral propaganda, not "
            "preserved historical fact."
        ),
    },
    # 24 — Blood in three cases incl apostasy
    {
        "anchor": "The blood of a Muslim is not lawful except in one of three cases",
        "response": (
            "Classical apologetics frames the three-case hadith as restrictive rather than "
            "permissive: it <em>limits</em> the conditions under which Muslim blood may be "
            "shed to three narrowly-defined cases, against a backdrop of tribal Arabia where "
            "killing was less regulated. The apostasy case is defended as applying to those "
            "who combine apostasy with active hostility (<em>harb</em>), not to private belief "
            "change. Modern reformist scholars (Jasser Auda, Abdullah Saeed) argue the hadith "
            "should be read against the Quran's 2:256, giving priority to religious freedom."
        ),
        "refutation": (
            "The \"restrictive not permissive\" framing is not wrong but also not responsive: "
            "the restriction includes apostasy as one of only three grounds for execution, "
            "equating private religious change with murder and adultery as capital offenses. "
            "The \"hostility requirement\" is an addition modern apologists put onto the "
            "hadith; classical jurisprudence across all four Sunni schools and Jaʿfari Shia "
            "law treated apostasy itself as capital, with hostility not required. "
            "Contemporary enforcement (Saudi Arabia, Iran, Afghanistan, Mauritania) applies "
            "the death penalty to private belief-change, not just armed rebellion. A moral "
            "code whose three death-warrants include \"changed his mind\" has not elevated "
            "human life; it has ritualised conformity."
        ),
    },
    # 25 — Khawarij are dogs of hellfire
    {
        "anchor": "They are the dogs of the people of Hellfire.",
        "response": (
            "Apologists argue the condemnation is specific to the historical Khawarij — an "
            "early sect that declared all other Muslims apostate and legitimized killing them "
            "— not a template for general sectarian anathema. The hadith's harsh language "
            "reflects the Khawarij's specific practice of <em>takfir</em> and the existential "
            "threat they posed to the Muslim community. Modern apologists use the hadith to "
            "critique contemporary extremist groups (ISIS, al-Qaeda), who are described as "
            "\"neo-Khawarij.\""
        ),
        "refutation": (
            "The apologetic is accurate about the hadith's original target, but that does not "
            "remove its template-setting function. By pre-damning a specific theological "
            "faction, the tradition established the principle of scriptural "
            "excommunication — a tool that has been used against every reform and dissenting "
            "movement in subsequent Islamic history (Mutazilites, Ismailis, Ahmadis, "
            "Shia groups from Sunni polemics and vice versa). The \"dogs of hellfire\" "
            "framing dehumanises dissenters rather than refutes their arguments. A prophetic "
            "precedent of theological sub-humanisation is what makes mutual <em>takfir</em> "
            "structurally available — and that structure has outlasted any original target."
        ),
    },
    # 26 — Usama killed man who said shahada
    {
        "anchor": "Did you kill him after he professed 'There is no god but Allah?'",
        "response": (
            "The classical apologetic emphasises the hadith's corrective force: Muhammad's "
            "rebuke of Usama is preserved in <em>sahih</em> canon precisely because killing a "
            "convert — even a late, battlefield convert — was unacceptable. The hadith is "
            "cited as evidence that Islam strictly protects religious profession: a formal "
            "declaration of faith stops all lawful killing, regardless of the killer's "
            "assessment of sincerity. Modern apologists point to this as the Prophet's most "
            "famous \"no compulsion\" episode in practice."
        ),
        "refutation": (
            "The rebuke was verbal; the killing was not punished. Usama faced no legal "
            "consequence for having killed a professing Muslim — only moral reproach. For a "
            "system claiming the sanctity of the <em>shahada</em>, the absence of consequence "
            "is diagnostic. More troubling: the episode establishes that the only protection "
            "against battlefield execution is a split-second verbal profession, evaluated by "
            "the killer's assessment of interior sincerity — an unverifiable test made in "
            "high-stress combat by a person holding a sword. The protective rule sets a "
            "standard no one could reliably meet under threat, which in practice shifts all "
            "discretion to the killer. \"No compulsion\" cannot operate as a principle when "
            "the only enforcement mechanism is the better nature of the swordsman."
        ),
    },
    # 27 — Adam 60 cubits, image
    {
        "anchor": "Allah created Adam in His image, sixty cubits long.",
        "response": (
            "Classical theologians (Ibn Taymiyyah, the Athari school) defended the hadith by "
            "saying \"in His image\" means Adam was created with the <em>attributes Allah "
            "approves</em> — reasoning, moral agency, speech — not that Allah has a "
            "physical form. \"Sixty cubits\" refers to Adam's stature in paradise before the "
            "fall, not his size as we know humans now. The hadith is cited by Athari theology "
            "as consistent with divine incorporeality despite its anthropomorphic language, "
            "under the principle of <em>tafwid</em> (consigning meaning to Allah)."
        ),
        "refutation": (
            "\"In His image\" is borrowed directly from Genesis 1:27, and the hadith's "
            "physicality (specific cubit count) presses against the abstract theological "
            "reading the apologetic offers. Classical Mu'tazilite and later Ash'arite theology "
            "found the hadith problematic enough to require extensive interpretive work — a "
            "sign that the plain sense was troubling, not merely foreign. The "
            "<em>tafwid</em> principle (consign meaning to Allah) is an honest admission that "
            "the hadith's content exceeds what Islamic theology can coherently accept: borrow "
            "the phrase, consign the meaning, and hope the borrowing does not drag its source "
            "into the theology. It did."
        ),
    },
    # 28 — Rulers from Quraysh
    {
        "anchor": "This matter will remain with the Quraysh as long as two of them remain.",
        "response": (
            "Apologists read the hadith as a historical-political observation rather than a "
            "standing legal rule — in the formative period, Quraysh's standing as Muhammad's "
            "own tribe gave its leaders natural legitimacy. Classical jurisprudence formally "
            "required Qurayshi descent for caliphs but many jurists (including al-Mawardi) "
            "allowed the criterion to be relaxed under necessity. The majority of later "
            "Muslim-majority polities accepted non-Qurayshi rulers (Ottomans, Safavids, "
            "Mughals), treating the hadith as principle rather than absolute requirement."
        ),
        "refutation": (
            "The \"principle not requirement\" reading is retrofitted: classical "
            "jurisprudence (al-Mawardi's <em>al-Ahkam al-Sultaniyya</em>) included Qurayshi "
            "descent among the essential conditions for the caliphate. The fact that later "
            "empires ignored the rule is not a refinement of the doctrine; it is a silent "
            "abandonment. The hadith is incompatible with the Farewell Sermon's "
            "\"no superiority except in piety\" — a contradiction the apologetic framework "
            "cannot dissolve except by prioritising one passage over the other. A scripture "
            "that encodes hereditary theocracy and also declares egalitarianism has produced "
            "1,400 years of contested political theology, not guidance."
        ),
    },
    # 29 — Mut'ah oscillation
    {
        "anchor": "Sabrah al-Juhani:",
        "response": (
            "The classical Sunni position is that <em>mut'ah</em> was permitted at specific "
            "points during Muhammad's lifetime (notably on certain campaigns) as a concession "
            "to specific conditions, then definitively forbidden at Khaybar or during the "
            "Farewell Pilgrimage. The sequence is not confused revision but progressive "
            "revelation: the concession was temporary, its abrogation final. The Sunni-Shia "
            "disagreement about final abrogation reflects different readings of the same "
            "sequence, not doctrinal instability in the tradition itself."
        ),
        "refutation": (
            "The sequence the apologetic gives — permitted, abrogated, permitted again, "
            "abrogated again — is itself what the hadith record shows, and the "
            "\"progressive revelation\" label does not hide the fact that a sexual-law rule "
            "changed multiple times in a short period. The Sunni-Shia split on "
            "<em>mut'ah</em> has lasted 1,400 years precisely because the <em>sahih</em> "
            "canon contains material supporting both positions. Either the abrogation "
            "succeeded and Shia law is wrong, or <em>mut'ah</em> remains permitted and Sunni "
            "law is wrong. A divine sex-law whose final position cannot be determined from "
            "the tradition itself is a law whose divine origin is indistinguishable from "
            "human legal development under conflicting testimony."
        ),
    },
    # 30 — No omens but evil eye real
    {
        "anchor": "There is no transitive disease, no bird-omen, and no hama (ghost)",
        "response": (
            "Apologists argue the hadith is making a theological distinction rather than a "
            "blanket denial: it rejects pre-Islamic superstitions that attributed independent "
            "causal power to disease, birds, and ghosts, while affirming the evil eye as a "
            "real phenomenon within the divinely-ordered world. \"No contagion\" means no "
            "causation independent of Allah; disease and misfortune happen by Allah's will, "
            "not by autonomous natural causes. The evil eye is real because it is a "
            "manifestation of envy, which has a spiritual dimension Islam recognises."
        ),
        "refutation": (
            "The \"no independent causation\" reading has its own problem — it turns every "
            "disease and death into direct divine agency, which Ash'arite theology embraces "
            "but at the cost of ordinary natural causation. Classical Islamic medicine "
            "cited the \"no contagion\" hadith in early responses to plague, with "
            "disastrous consequences for public-health responses before modern jurisprudence "
            "began arguing for compatibility with germ theory. The selective anti-"
            "superstition — rejecting pagan beliefs about bird-omens while affirming folk "
            "beliefs about envy-eye — is the signature of a text working <em>within</em> its "
            "culture's cosmology rather than transcending it. The evil-eye preservation is "
            "exactly what survives from pre-Islamic Arabian folk religion."
        ),
    },
    # 31 — Adam wins argument with Moses (predestination)
    {
        "anchor": "Moses said to Adam: 'You are the one whose sin expelled humanity from paradise",
        "response": (
            "Classical theology reads the hadith as establishing the doctrine of divine "
            "predestination (<em>qadar</em>) without licensing human fatalism. Adam's victory "
            "is on a specific metaphysical point: Allah's foreknowledge preceded his act. But "
            "the hadith does not say Adam was <em>forced</em> to sin — only that Allah had "
            "inscribed the event in His register before it happened. The Ash'arite "
            "<em>khalq</em>/<em>kasb</em> distinction (Allah creates the act; the human "
            "acquires responsibility) resolves the apparent contradiction between "
            "foreknowledge and moral accountability."
        ),
        "refutation": (
            "The Ash'arite compatibilism is the theological scaffolding developed precisely "
            "to manage this contradiction — and its opacity is proverbial. Adam's argument "
            "in the hadith is structurally the defense of every sinner: \"I was written that "
            "way.\" If the defense works for the first human, the scripture has licensed it "
            "in principle for every human. The religion still hands out eternal punishment "
            "for disbelief — which is inconsistent with accepting Adam's defense. Either "
            "foreknowledge plus creation renders the sinner unfree (in which case hell is "
            "unjust), or the sinner is free and Adam's argument should fail (in which case "
            "the hadith is wrong). The tradition has tried to have both; the hadith records "
            "the cost of that attempt."
        ),
    },
    # 32 — Fasting Arafat erases 2 years
    {
        "anchor": "Fasting on the day of Arafat erases the sins of the preceding year",
        "response": (
            "Classical apologetics argues the \"erasure\" applies only to minor sins "
            "(<em>saghair</em>), not major sins (<em>kaba'ir</em>), which still require "
            "repentance and restitution. The hadith is a theological encouragement to virtuous "
            "practice, not a mechanical exchange of ritual for moral escape. The Quran's "
            "principle that each soul gets what it earned (2:286, 53:39) is preserved because "
            "the person doing the fasting is themselves earning the mercy — fasting is an "
            "effort, and the reward is an effort-proportional mercy."
        ),
        "refutation": (
            "The minor-vs-major distinction is a classical patch, not in the hadith itself. "
            "The hadith says \"sins of the preceding year and the year ahead,\" without the "
            "qualification. More fundamentally, the moral economy of \"one day of hunger "
            "erases two years of sin\" is structurally a discount, regardless of which sins "
            "are covered. The Quran's per-person-per-effort principle sits awkwardly beside "
            "a hadith that exchanges ritual compliance for moral release at a dramatic "
            "exchange rate. A framework that provides such discounts has not taught "
            "restraint; it has marketed a mechanism. If major sins still require repentance "
            "(as apologists say), the hadith's erasure is mostly administrative — and "
            "administrative forgiveness has no moral weight."
        ),
    },
    # 33 — Buraq / Dome of the Rock
    {
        "anchor": "I was brought al-Buraq, a white long animal larger than a donkey",
        "response": (
            "Classical apologetics treats the Isra and Mi'raj as a genuine miraculous journey "
            "— an event whose details (flying mount, seven heavens, prophetic meetings) "
            "exceed ordinary physics precisely because it was a divine miracle. Resemblances "
            "to Zoroastrian Arda Viraf or Jewish Merkabah mysticism are cited by apologists "
            "as evidence that all genuine traditions of heavenly ascent preserve authentic "
            "structural knowledge of the spiritual cosmos. Aisha's reported view that the "
            "journey was spiritual rather than physical is one classical minority position "
            "still available to modern readers."
        ),
        "refutation": (
            "The \"all traditions preserve authentic cosmos-structure\" defense is available "
            "but comes at high cost: it grants legitimacy to Zoroastrian Arda Viraf Namag, "
            "Jewish Merkabah mysticism, Christian apocalyptic, and other rival traditions "
            "Islam otherwise treats as deviations. The Buraq's structural resemblance to "
            "Ezekiel's chariot and to Zoroastrian heavenly mounts is not coincidence — it is "
            "a literary family. The \"seven heavens\" architecture is Mesopotamian "
            "cosmology, not physics. A miraculous journey whose form is indistinguishable "
            "from the pre-existing apocalyptic-ascent genre of the Near East is a journey "
            "that looks much more like participation in the genre than independent divine "
            "disclosure."
        ),
    },
    # 34 — Sandals boil brain in hell
    {
        "anchor": "The least punished person in Hell will be a man having sandals made of fire",
        "response": (
            "Classical apologetics treats the hadith as eschatological emphasis: the "
            "<em>least</em> punishment is this severe, establishing the unimaginable intensity "
            "of hell's fullest punishments. The imagery is pedagogical — warning believers by "
            "vivid contrast. \"Brain-boiling sandals\" is a concrete image for spiritual "
            "suffering that human language cannot otherwise express. Modern apologists add "
            "that the hadith pairs with traditions of hell's immense depth and duration to "
            "emphasise both breadth and intensity of eschatological consequence."
        ),
        "refutation": (
            "\"Pedagogical vivid imagery\" is the defense for every piece of hadith body-"
            "horror in the eschatological corpus: molars the size of Mount Uhud, skin roasted "
            "and replaced, boiling water poured on heads, tree of Zaqqum. The accumulation "
            "of explicit physical torment is not pedagogy; it is the aesthetic of threat. A "
            "tradition whose \"least punishment\" opens with sandal-induced brain boiling has "
            "replaced moral seriousness with body-horror escalation — the threats get more "
            "vivid, not more moral. An ethics built on terror is admitting that its "
            "positive arguments do not suffice, and the vivid torments are what remains "
            "when positive argument is exhausted."
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

# Hadith Duplicate Audit — 2026-05-26

Total hadith entries scanned: **1311** across 6 sources

---

## Class A — Cross-Source Exact-ID Collisions

**3 found.** These are hard bugs — two different entry `<div>` blocks share the same anchor ID.
One must be removed from one of the files. Decide which source is the definitive home.

- `aisha-age` appears in: bukhari, muslim
- `fight-until-testify` appears in: bukhari, muslim
- `women-majority-hell` appears in: bukhari, muslim

## Class B — Exact Title Duplicates (Cross-Source)

**6 groups.** Same title in different collections.
Common cause: the hadith appears in multiple authoritative compilations.
Recommended action: keep the entry with more analytical content; drop the thinner one.

### "A donkey, a black dog, or a woman invalidates prayer"
- **[abu-dawud]** `prayer-invalidate-dog-woman` | ref: Abu Dawud #702
  > "The prayer is invalidated by a donkey, a black dog, or a woman passing in front of the worshipper."…
- **[tirmidhi]** `prayer-invalid-dog-donkey-woman-tirmidhi` | ref: Tirmidhi #338
  > "The prayer is invalidated by a donkey, a black dog, and a menstruating woman passing in front."…

### "A slave who marries without his master's permission is a fornicator"
- **[tirmidhi]** `tirmidhi-slave-marriage-master-permission` | ref: Tirmidhi #1111
  > "Any slave who marries without his master's permission, his marriage is invalid; and if he has intercourse with her, he is a fornicator."…
- **[nasai]** `nasai-slave-cannot-marry-without-master` | ref: Ibn Majah #1693
  > "Any slave who marries without his master's permission is a fornicator."…

### "A tree in paradise whose shade takes 100 years to cross"
- **[muslim]** `muslim-paradise-tree-shade-100-years` | ref: Muslim #2594
  > "In Paradise there is a tree under whose shade a rider can travel for one hundred years without crossing it."…
- **[tirmidhi]** `paradise-tree-100-years` | ref: Tirmidhi #3377
  > "Indeed in Paradise there is a tree under whose shade a rider can travel for one-hundred years without stopping."…

### "A virgin's silence is her consent to marriage"
- **[nasai]** `nasai-father-virgin-silent-consent` | ref: Nasa'i #3266
  > "A virgin is consulted about her marriage — her silence is her consent."…
- **[ibn-majah]** `ibnmajah-virgin-silent-consent` | ref: Nasa'i #3266
  > "A virgin's permission is her silence."…

### "Hand amputation for theft of a quarter dinar"
- **[abu-dawud]** `amputation-quarter-dinar-thief` | ref: Abu Dawud #4385
  > "The Messenger of Allah would cut off the hand of a thief for a quarter dinar...""Even if Fatimah bint Muhammad were to steal, I would cut off her han…
- **[tirmidhi]** `tirmidhi-killed-cut-bone` | ref: Bukhari #6543
  > "The hand is not amputated except for a quarter of a dinar or more."…

### "Satan flees the call to prayer while passing wind"
- **[bukhari]** `satan-farts-adhan` | ref: Bukhari 594
  > "When the call for the prayer is pronounced, Satan takes to his heels, passing wind with noise. When the call for the prayer is finished, he comes bac…
- **[muslim]** `devil-farts-at-adhan` | ref: Muslim 757
  > "When Satan hears the call to prayer, he runs away to a distance like that of Rauha... Satan runs back and breaks wind so as not to hear the call bein…

## Class C — Near-Title Duplicates (≥82% similarity, cross-source)

**39 pairs found.** Similar titles in different sources — may be intentional variants or duplicates.
Review each pair; mark as `KEEP_BOTH`, `DROP_FIRST`, or `DROP_SECOND`.

### 97% match
- **[muslim]** `do-not-greet-jews-and-christians-first-and-force-them-to-the-fb8216df` | Muslim #5515
  Title: ""Do not greet Jews and Christians first — force them to the narrowest part of the road""
  > "Abu Huraira reported Allah's Messenger as saying: Do not greet the Jews and the Christians before they greet you, and when you meet any one of them o…
- **[nasai]** `nasai-no-first-greeting-ahl-kitab` | Muslim #5515
  Title: "Do not greet Jews and Christians first — force them to the narrow part of the road"
  > Nasa'i preserves the same social-humiliation hadith: Muslims must push non-Muslims to the narrow side of streets and not initiate greetings.…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 97% match
- **[tirmidhi]** `tirmidhi-jesus-descent-kill-pigs` | Tirmidhi #2301
  Title: "Jesus descends to kill pigs, break crosses, and abolish the jizya"
  > "Jesus son of Mary will descend... He will break the cross, kill the pig, and abolish the jizya."…
- **[ibn-majah]** `ibnmajah-jesus-descend-kill-pig` | Ibn Majah #3815
  Title: "Jesus descends to kill pigs, break crosses, and abolish jizya"
  > "Jesus son of Mary will descend, kill the pig, break the cross, and abolish the jizya."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 93% match
- **[bukhari]** `devils-chained-ramadan` | Bukhari 1831
  Title: "All devils are chained during Ramadan — yet Muslims still sin"
  > "When the month of Ramadan comes, the gates of Paradise are opened and the gates of the (Hell) Fire are closed, and the devils are chained."…
- **[tirmidhi]** `tirmidhi-devils-chained-ramadan` | Tirmidhi #682
  Title: "Devils are chained in Ramadan — yet Muslims still sin"
  > "When Ramadan comes, the gates of Paradise are opened, the gates of Hell are closed, and the devils are chained."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 93% match
- **[muslim]** `jews-graves-mosques-curse` | Muslim 1089
  Title: "Muhammad cursed Jews and Christians for worshipping at prophets' graves"
  > "Allah cursed the Jews and the Christians because they took the graves of their prophets as places of worship."…
- **[tirmidhi]** `tirmidhi-pagan-graves-cursed` | Bukhari #429
  Title: "Muhammad cursed Jews and Christians for praying at prophets' graves"
  > "May Allah curse the Jews and Christians — they took the graves of their prophets as places of worship."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 92% match
- **[abu-dawud]** `satan-third-man-woman` | Abu Dawud #2149
  Title: ""Satan is always the third" when a man and woman are alone"
  > "No man should be alone with a woman, for Satan is the third with them."…
- **[ibn-majah]** `ibnmajah-prayer-between-two-people` | 
  Title: "Satan is the third when a man and woman are alone"
  > "No man is alone with a woman but Satan is the third among them."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 92% match
- **[nasai]** `nasai-breath-bad-mouth-fasting` | Nasa'i #2216
  Title: "A fasting person's bad breath is sweeter to Allah than musk"
  > "The breath of a fasting person is sweeter with Allah than the fragrance of musk."…
- **[ibn-majah]** `ibnmajah-fasting-breath` | Ibn Majah #1372
  Title: "A fasting person's breath smells sweeter to Allah than musk"
  > "The breath of the fasting person is sweeter with Allah than the fragrance of musk."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 91% match
- **[tirmidhi]** `tirmidhi-imam-lead-forbidden-hate` | Tirmidhi #360
  Title: "Three whose prayer is rejected — including a wife whose husband is angry"
  > "Three whose prayer does not rise above their heads even a hand-span: a man who leads people in prayer while they hate him, a woman whose husband is a…
- **[ibn-majah]** `ibnmajah-wife-prayer-reward-rejected` | Ibn Majah #971
  Title: "Three whose prayer is rejected — including a wife whose husband is displeased"
  > "There are three whose prayer does not pass beyond their ears: a runaway slave... a wife who goes to bed while her husband is displeased with her... a…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 91% match
- **[bukhari]** `kafir-eats-seven-intestines` | Bukhari 5179
  Title: ""The believer eats in one intestine, the disbeliever eats in seven""
  > "A believer eats in one intestine, whereas a non-believer eats in seven intestines."…
- **[ibn-majah]** `ibnmajah-believer-one-intestine-disbeliever-seven` | Ibn Majah #2992
  Title: "The believer eats with one intestine; the disbeliever eats with seven"
  > "The believer eats with one intestine, and the disbeliever eats with seven intestines."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 91% match
- **[abu-dawud]** `kill-doer-done-to-lut` | Abu Dawud #4464
  Title: "Kill the active and passive partner — the death sentence for same-sex acts"
  > "Allah's Messenger said: 'Whoever of you find doing the action of the people of Lut, kill the one who does it and the one to whom it is done.'"…
- **[ibn-majah]** `ibnmajah-kill-doer-done-to` | Ibn Majah #2297
  Title: "Kill the active and passive partner — death penalty for same-sex acts"
  > "Whoever you find doing the act of the people of Lut, kill the one doing it and the one to whom it is done."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 90% match
- **[tirmidhi]** `women-created-from-rib` | Tirmidhi #1192
  Title: "Women are created from crooked ribs — cannot be straightened without breaking"
  > "Woman was created from a rib. The most crooked part of the rib is its top. If you try to straighten it, you will break it. If you leave it, it will r…
- **[ibn-majah]** `ibnmajah-wife-like-crooked-rib` | Ibn Majah #1851
  Title: "Women are like crooked ribs — cannot be straightened without breaking"
  > "Woman was created from a rib. If you try to straighten her, you will break her."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 90% match
- **[abu-dawud]** `iddah-widow-house-confined` | Abu Dawud 2300
  Title: "A widow confined to her husband's house for four months and ten days"
  > "It is obligatory upon a widow to spend her 'Iddah period in the same house..."…
- **[ibn-majah]** `ibnmajah-iddah-widow-confinement` | Ibn Majah #1821
  Title: "A widow confined to her home for four months and ten days"
  > "A widow remains in her house for four months and ten days, not leaving except for necessity."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 90% match
- **[bukhari]** `camel-complained-to-prophet` | Abu Dawud #2549
  Title: "A camel complained to Muhammad about its overwork"
  > "The Prophet entered a garden belonging to a man of the Ansar and, behold, there was a camel. When the Prophet saw the camel it moaned and its eyes sh…
- **[ibn-majah]** `ibnmajah-camel-crying-prophet` | Ibn Majah #3342
  Title: "A camel complained to Muhammad about its master"
  > "The camel wept, and the Prophet stroked its head; he said: 'The owner has abused it and starved it.'"…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 90% match
- **[muslim]** `muhammad-died-armor-mortgaged` | Bukhari #4266
  Title: "Muhammad died with his armor mortgaged to a Jew for barley"
  > "The Prophet pawned his armour with a Jew for thirty sa's of barley. When he died, his armour was still pawned."…
- **[ibn-majah]** `ibnmajah-prophet-armor-mortgaged` | Tirmidhi #1222
  Title: "Muhammad died with his armor mortgaged to a Jew"
  > "When the Prophet died, his shield was mortgaged with a Jew for 30 sa's of barley."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 89% match
- **[tirmidhi]** `tirmidhi-kawthar-river-cups-pearl-stars` | Tirmidhi #2512
  Title: "Al-Kawthar has cups as numerous as the stars"
  > "Its vessels are as numerous as the stars in the sky."…
- **[nasai]** `nasai-kawthar-river-cups-stars` | Tirmidhi #2514
  Title: "Al-Kawthar — its cups are as numerous as the stars"
  > "Its cups are as the stars of heaven."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 89% match
- **[bukhari]** `muhammad-weeping-trunk` | Bukhari 3434
  Title: "A date-palm trunk cried when Muhammad stopped leaning on it"
  > "The Prophet used to stand by a tree or a date-palm trunk on Friday. Then an Ansari woman or man said, 'O Allah's Apostle! Shall we make a pulpit for …
- **[nasai]** `nasai-tree-trunk-wept-prophet` | Nasai #1396
  Title: "A palm trunk wept when Muhammad stopped leaning on it"
  > "A palm trunk wept audibly when the Prophet stopped leaning on it for a new pulpit."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 89% match
- **[tirmidhi]** `tirmidhi-mosque-urinator` | Tirmidhi #147
  Title: "A Bedouin urinated in the mosque — Muhammad ordered water poured"
  > "A Bedouin stood up and urinated in the mosque. The people stood up to deal with him. The Prophet said: 'Leave him alone, and pour a bucket of water o…
- **[nasai]** `nasai-water-mosque-bedouin` | Nasa'i #56
  Title: "A Bedouin urinated in the mosque — Muhammad ordered water, not punishment"
  > "A Bedouin stood up and urinated in a corner of the mosque. The companions rebuked him. The Prophet said: 'Leave him. Do not interrupt his urination.'…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 88% match
- **[bukhari]** `hellfire-seventy-times-hotter` | Bukhari 3131
  Title: "Hellfire is seventy times hotter than earthly fire"
  > "This fire of yours is one of seventy parts of the (Hell) Fire... The (Hell) Fire has 69 parts more than the ordinary (worldly) fire."…
- **[tirmidhi]** `tirmidhi-hellfire-seventy-times-earthly` | Tirmidhi #2659
  Title: "Hellfire is seventy times hotter than all earthly fire combined"
  > "This Fire of yours, which the sons of Adam kindle, is one part from seventy parts of the heat of the Hell." They said: "By Allah! Would it not have b…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 88% match
- **[abu-dawud]** `virgin-silence-permission` | Tirmidhi #1109
  Title: "A virgin's silence counts as consent to marriage"
  > "The virgin's permission should be sought and her silence is her permission."…
- **[nasai]** `nasai-father-virgin-silent-consent` | Nasa'i #3266
  Title: "A virgin's silence is her consent to marriage"
  > "A virgin is consulted about her marriage — her silence is her consent."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 88% match
- **[abu-dawud]** `virgin-silence-permission` | Tirmidhi #1109
  Title: "A virgin's silence counts as consent to marriage"
  > "The virgin's permission should be sought and her silence is her permission."…
- **[ibn-majah]** `ibnmajah-virgin-silent-consent` | Nasa'i #3266
  Title: "A virgin's silence is her consent to marriage"
  > "A virgin's permission is her silence."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 88% match
- **[nasai]** `nasai-dhimmi-insulting-prophet-no-retribution` | Abu Dawud #4361 (Nasa'i parallel)
  Title: "A blind man killed his pregnant slave-mistress for insulting Muhammad"
  > "A blind man had an umm walad who used to abuse the Prophet. He killed her. The Prophet said: 'Bear witness, no retaliation is due for her blood.'"…
- **[ibn-majah]** `ibnmajah-dhimmi-insulting-prophet-death` | Ibn Majah #1119
  Title: "A blind man killed his pregnant slave-mistress for insulting the Prophet"
  > "A blind man had an umm walad who used to insult the Prophet. He stabbed her with a dagger and killed her. The Prophet said: 'Bear witness, no retalia…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 88% match
- **[bukhari]** `tree-trunk-wept-prophet` | Bukhari 896
  Title: "A tree trunk wept aloud when Muhammad stopped leaning on it"
  > "When the pulpit was made for him, the trunk of the tree wept audibly, as if a newborn child... until the Prophet came down and embraced it."…
- **[nasai]** `nasai-tree-trunk-wept-prophet` | Nasai #1396
  Title: "A palm trunk wept when Muhammad stopped leaning on it"
  > "A palm trunk wept audibly when the Prophet stopped leaning on it for a new pulpit."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 88% match
- **[abu-dawud]** `throne-on-mountain-goats` | Abu Dawud #4725
  Title: "Allah's Throne rests on eight angelic mountain goats above seven heavens"
  > "Then above that there are eight mountain goats. The distance between their hooves and their knees is like the distance between one heaven and the nex…
- **[tirmidhi]** `tirmidhi-throne-on-eight-goats` | Tirmidhi #3404
  Title: "Allah's Throne rests on eight angelic goats above seven seas and heavens"
  > "Above the seventh heaven is a sea. Between its highest part and its lowest is just as there is between one heaven to another heaven. Above that are e…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 87% match
- **[nasai]** `nasai-prayer-invalid-dog-woman` | Nasa'i #752
  Title: "Prayer invalidated by a passing woman, donkey, or black dog — Nasa'i parallel"
  > "The prayer is nullified by a woman, a donkey, or a black dog." (Nasa'i #752: "…his prayer is nullified by a woman, a donkey or a black dog.")…
- **[ibn-majah]** `ibnmajah-prayer-invalid-dog-woman` | Ibn Majah #686
  Title: "Prayer invalidated by a passing woman, donkey, or black dog"
  > "The prayer is cut by a black dog, a donkey, and a woman."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 87% match
- **[tirmidhi]** `tirmidhi-killing-muslim-not-for-kafir` | Tirmidhi #2706
  Title: "A Muslim is not executed in retaliation for killing a non-Muslim"
  > "A believer is not killed for a disbeliever."…
- **[ibn-majah]** `ibnmajah-men-killed-for-dhimmi` | Abu Dawud #2752
  Title: "A Muslim is not executed for killing a non-Muslim"
  > "A believer is not killed for a disbeliever."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 86% match
- **[abu-dawud]** `bad-dream-spit-three-left` | Abu Dawud #5019
  Title: "Bad dreams — spit three times to the left"
  > "A good dream is from Allah and a bad dream is from Satan. Spit three times to your left and seek refuge."…
- **[ibn-majah]** `ibnmajah-spit-three-left-bad-dream` | Ibn Majah #3909
  Title: "After a bad dream, spit three times to the left"
  > "If one of you sees a dream he dislikes, let him spit three times on his left, seek refuge with Allah from Satan, and it will not harm him."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 86% match
- **[muslim]** `poor-enter-paradise-first` | Muslim 216
  Title: "The poor enter Paradise five hundred years before the rich"
  > "The poor believers would enter paradise five hundred years before the rich."…
- **[nasai]** `nasai-paradise-entered-one-thousand-five-hundred-years` | Abu Dawud #3667
  Title: "The poor enter paradise 500 years before the rich"
  > "The poor Muslims will enter Paradise five hundred years before the rich ones."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 86% match
- **[bukhari]** `satan-in-blood` | Bukhari #1961
  Title: "Satan circulates in the human body like blood"
  > "Satan reaches everywhere in the human body as blood reaches in it. I was afraid lest Satan might insert an evil thought in your minds."…
- **[tirmidhi]** `tirmidhi-jinn-in-veins` | Bukhari #1964
  Title: "Satan circulates in the son of Adam like blood"
  > "Satan circulates in the son of Adam like the circulation of blood."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 85% match
- **[muslim]** `woman-travel-mahram` | Muslim 3138
  Title: "A woman may not travel more than a day without a male guardian"
  > "A woman should not travel for two days duration, but only when there is a Mahram with her or her husband."…
- **[abu-dawud]** `mahram-required-female-travel` | Abu Dawud #1724
  Title: "A woman may not travel without a male guardian"
  > "[A woman should not travel] except with a Mahram."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 84% match
- **[bukhari]** `hellfire-seventy-times-hotter` | Bukhari 3131
  Title: "Hellfire is seventy times hotter than earthly fire"
  > "This fire of yours is one of seventy parts of the (Hell) Fire... The (Hell) Fire has 69 parts more than the ordinary (worldly) fire."…
- **[nasai]** `nasai-hell-seventy-times-earth-fire` | Nasa'i cross-reference tradition
  Title: "Hellfire 70 times hotter than earth fire"
  > "Your fire is one-seventieth of the heat of hellfire."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 84% match
- **[abu-dawud]** `black-seed-all-illnesses` | Ibn Majah #3183
  Title: "Black seed cures every illness except death"
  > "In the black seed there is healing for every illness except death."…
- **[ibn-majah]** `ibnmajah-nigella-cure-everything-except-death` | Ibn Majah #3185
  Title: "Black seed — cure for every disease except death"
  > "Use this black seed regularly, because it is a cure for every disease except death."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 83% match
- **[bukhari]** `no-omen-but-omen` | Bukhari #4888
  Title: ""There is no evil omen" — except in women, horses, and houses"
  > "The Prophet said: 'Evil omen is in three things: The horse, the woman and the house.' " "There is neither 'Adha nor Tiyara, and an evil omen is only …
- **[tirmidhi]** `tirmidhi-bad-omen-rejected-women-horse` | Bukhari #5549
  Title: ""No omen" — except in women, houses, and horses"
  > "There is no Tiyara [evil omen], but the evil omen is only in three: the woman, the house, and the horse."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 83% match
- **[bukhari]** `sun-rises-west-repentance-closed` | Bukhari 4429
  Title: "When the sun rises from the west, repentance is permanently closed"
  > "The Hour will not be established until the sun rises from the west. And when the people see it, then whoever will be living on the surface of the ear…
- **[abu-dawud]** `sun-west-rise-close-repentance` | Bukhari #6267
  Title: "When the sun rises from the west, repentance is no longer accepted"
  > "When the sun rises from the west, no repentance will be accepted."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 83% match
- **[abu-dawud]** `dogs-all-killed-reversed` | Abu Dawud #2845
  Title: "Muhammad ordered all dogs killed, then reversed for hunting and farm dogs"
  > "The Messenger ordered all the dogs in Medina be killed. He then granted permission for hunting dogs..."…
- **[tirmidhi]** `tirmidhi-dogs-killed` | Tirmidhi #1486
  Title: "Muhammad ordered all dogs killed — then exempted hunting and shepherd dogs"
  > "The Prophet ordered dogs to be killed. Then he said: 'What is the matter with me and the dogs?' Then he allowed the keeping of hunting dogs and sheph…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 83% match
- **[muslim]** `muslim-nation-perishes-woman-ruler` | Bukhari #6834
  Title: ""A people who entrust their affairs to a woman will not prosper""
  > "Never will a people who entrust their affair to a woman succeed."…
- **[nasai]** `nasai-women-cannot-rule-nation` | Nasa'i #5397
  Title: ""A nation that entrusts its affairs to a woman will not prosper""
  > "A people who entrust their affairs to a woman will never prosper."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 83% match
- **[nasai]** `nasai-sun-rises-west-repentance-closed` | Ibn Majah #4088
  Title: "Sun rises from the west — repentance closed"
  > "The Hour will not begin until the sun rises from the west — and then no believing soul's belief will benefit it."…
- **[ibn-majah]** `ibnmajah-sun-rises-west-repentance-closed` | Ibn Majah #4088
  Title: "The sun rises from the west — repentance is closed thereafter"
  > "The Hour will not begin until the sun rises from the west. When people see that, they will believe — but their belief will not benefit them."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 83% match
- **[bukhari]** `black-cumin-cure` | Bukhari #5474
  Title: "Black cumin cures every disease except death"
  > "I heard Allah's Apostle saying, 'There is healing in black cumin for all diseases except death.'"…
- **[ibn-majah]** `ibnmajah-nigella-cure-everything-except-death` | Ibn Majah #3185
  Title: "Black seed — cure for every disease except death"
  > "Use this black seed regularly, because it is a cure for every disease except death."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 82% match
- **[nasai]** `nasai-fate-written-50k-years-before` | 
  Title: "Fates written 50,000 years before creation"
  > "Allah decreed the measures of all things fifty thousand years before He created the heavens and the earth."…
- **[ibn-majah]** `ibnmajah-fate-written-50000-years-before` | Ibn Majah #4159
  Title: "All destinies were written 50,000 years before creation"
  > "Allah decreed the measures [of all things] fifty thousand years before He created the heavens and the earth."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 82% match
- **[muslim]** `black-stone-from-paradise` | Tirmidhi #878
  Title: "The Black Stone descended from paradise white — human sin blackened it"
  > "The Black Stone descended from paradise and it was more intensely white than milk, but it was blackened by the sins of the sons of Adam."…
- **[tirmidhi]** `tirmidhi-black-stone-paradise-sins-whitened-blackened` | Tirmidhi #878
  Title: "The Black Stone descended from Paradise — whiter than milk, blackened by human sins"
  > "The Black Stone descended from the Paradise, and it was more white than milk, then it was blackened by the sins of the children of Adam." (Tirmidhi #…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

### 82% match
- **[tirmidhi]** `seventy-three-sects-fire` | Tirmidhi #2641
  Title: ""My ummah will split into 73 sects — all in the Fire except one""
  > "The Jews split into 71 sects, the Christians split into 72 sects, and my nation will split into 73 sects — all of them in the Fire except one." They …
- **[ibn-majah]** `ibnmajah-seventy-three-sects` | Ibn Majah #3729
  Title: "The ummah splits into 73 sects — all in hell except one"
  > "My nation will split into seventy-three sects, all of them in the Fire except one."…
  **Decision:** KEEP_BOTH / DROP_FIRST / DROP_SECOND

## Class D — Same-Source Same-Ref Duplicates

**69 groups.** Two entries within the same collection cite the same hadith reference number.
May be legitimate (different aspects highlighted) or true duplicates.

### [abu-dawud] Abu Dawud #2149
- `satan-third-man-woman` | ""Satan is always the third" when a man and woman are alone"
  > "No man should be alone with a woman, for Satan is the third with them."…
- `first-glance-rule` | "First glance forgiven; second is sin"
  > "Do not follow a glance with another glance. The first is allowed; the second is not."…

### [abu-dawud] Abu Dawud #2684
- `abudawud-treacherous-eye-ibn-abi-sarh` | "Muhammad wished his Companions had killed the apostate he just pardoned"
  > "He turned to his Companions and said: 'Is not there any intelligent man among you who would stand to this (man) when he saw me desisting from receivi…
- `abu-dawud-fath-al-makkah-kill` | "The death list at the conquest of Mecca — satirists marked for execution"
  > "On the day of the conquest of Makkah, the Prophet gave protection to all people except four men and two women, whom he said should be killed even if …

### [abu-dawud] Abu Dawud #4353
- `abudawud-apostasy-kill-those-who-change-their-religion` | ""Kill those who change their religion" — Abu Dawud's unconditional death sentence for apos"
  > "'Ali burned some people who retreated from Islam... Ibn 'Abbas said: 'I would have killed them on account of the statement of the Messenger of Allah:…
- `ghulat-ibn-abbas-burned` | "Ali burned apostates alive — Ibn Abbas cited a prophetic prohibition on fire-punishment"
  > "I would not have burned them with fire, because the Messenger of Allah said: 'Do not punish with the punishment of Allah.' I would have executed them…

### [abu-dawud] Abu Dawud #4366
- `uraniyyin-hands-eyes-water` | "Uraniyyin: hands cut, eyes branded with heated nails, denied water to die"
  > "He ordered that their hands and feet be cut off and their eyes be branded, then they were thrown in the Harrah where they asked for water but were no…
- `abu-dawud-camel-urine-cure` | "Drink camel urine for your health — the Uraniyyin prescription"
  > "The Messenger of Allah told them to go to the milch-camels and drink their urine and milk."…

### [abu-dawud] Abu Dawud 2300
- `iddah-widow-house-confined` | "A widow confined to her husband's house for four months and ten days"
  > "It is obligatory upon a widow to spend her 'Iddah period in the same house..."…
- `abu-dawud-2175-iddah-divorce-pregnant-child` | "Waiting period for girls "who have not yet menstruated" — the pre-pubescent divorce rule"
  > "The waiting period of the one who is divorced three times, of the slave-girl, and the one who has not menstruated is three months." [Implementing Q 6…

### [abu-dawud] Abu Dawud 3883
- `amulets-cursed-ruqya-allowed` | "Amulets are shirk — but ruqya (incantation) is permitted"
  > "Ruqyah, amulets (Tama'im) and love charms are Shirk (polytheism)."[Elsewhere, Muhammad performs ruqyah and recommends it.]…
- `ghilah-intercourse-breastfeeding` | "Al-Ghilah — intercourse with a breastfeeding wife said to harm the child"
  > [Chapter heading:] "Al-Ghilah (Intercourse With A Breastfeeding Woman)"[Hadith content:] Muhammad initially thought al-ghilah harmed the breastfeeding…

### [abu-dawud] Bukhari #789
- `yemen-fire-end-times` | "A fire will emerge from Yemen driving people to the gathering"
  > "The last [sign] is a fire that will come out of Yemen."…
- `beast-of-earth-talks` | "A talking beast will emerge from the earth — end-times sign"
  > [Q 27:82:] "We will bring forth for them a beast from the earth, speaking to them..."…

### [bukhari] Bukhari #1468
- `bukhari-women-jihad-is-hajj-aisha-asked` | "Women told jihad is Hajj — but Bukhari records a woman in naval jihad"
  > "O Messenger of Allah, we consider jihad the best deed. Should we not fight in Allah's cause?" He said: "No — but the best jihad [for women] is an acc…
- `bukhari-constantinople-conquest-prophecy-time-bomb` | ""The first army who invades Caesar's City will be forgiven" — conquered 821 years later"
  > "Paradise is granted to the first batch of my followers who will undertake a naval expedition... The first army among my followers who will invade Cae…

### [bukhari] Bukhari #18
- `kiss-black-stone` | "Umar kissed the Black Stone while acknowledging it has no power"
  > "'Umar came near the Black Stone and kissed it and said: 'No doubt, I know that you are a stone and cannot benefit anyone or harm anyone. Had I not se…
- `ramal-show-off-pagans` | "The Tawaf ritual jog was invented to impress pagans — and preserved after they were gone"
  > "'Umar bin Al-Khattab addressed the Corner (Black Stone) saying, 'By Allah! I know that you are a stone and can neither benefit nor harm...' Then he k…
- `hajj-pagan-rituals-preserved-explicit` | "The Hajj preserves pre-Islamic pagan rituals intact — Umar confessed as much"
  > Umar, at the Black Stone: "No doubt, I know that you are a stone and can neither benefit anyone nor harm anyone. Had I not seen Allah's Apostle kissin…

### [bukhari] Bukhari #26
- `bukhari-best-deed-conflicting-rankings` | ""What is the best deed?" — Bukhari preserves four mutually inconsistent answers"
  > Bukhari #26: faith → jihad → Hajj. / Bukhari #2670: prayer on time → good to parents → jihad. / Bukhari #2418: faith and jihad together → freeing a sl…
- `jihad-better-than-mecca-pilgrimage` | "Jihad ranks above Hajj — Islam's hierarchy of virtues"
  > "Allah's Apostle was asked, 'What is the best deed?' He replied, 'To believe in Allah and His Apostle (Muhammad).' The questioner then asked, 'What is…

### [bukhari] Bukhari 1831
- `two-fasting-doors` | "In Ramadan, gates of Paradise open; gates of Hell close; devils are chained"
  > "Allah's Apostle said, 'When the month of Ramadan starts, the gates of the heaven are opened and the gates of Hell are closed and the devils are chain…
- `devils-chained-ramadan` | "All devils are chained during Ramadan — yet Muslims still sin"
  > "When the month of Ramadan comes, the gates of Paradise are opened and the gates of the (Hell) Fire are closed, and the devils are chained."…

### [bukhari] Bukhari 216
- `grave-torture-urine` | "Graves torture those who didn't carefully avoid urine splashes"
  > "Once the Prophet, while passing through one of the grave-yards of Medina or Mecca heard the voices of two persons who were being tortured in their gr…
- `grave-torture-for-gossip-urine` | "Grave torture for gossip and for not shielding from urine"
  > "Both of them are being tortured, and they are not being tortured for a major sin. The first used to carry tales (gossip) between people; the second u…

### [bukhari] Bukhari 2249
- `expel-jews-arabia` | "Umar expelled all Jews and Christians from the Arabian Peninsula — fulfilling Muhammad's s"
  > "Umar bin Al-Khattab expelled all the Jews and Christians from the land of Hijaz... When Allah's Apostle had conquered Khaibar, he wanted to expel the…
- `jews-expelled-medina-khaybar` | "Muhammad wanted to expel all Jews from the Hijaz"
  > "Umar expelled the Jews and the Christians from the land of the Hijaz... The Prophet, on conquering Khaibar, had wished to expel the Jews from it."…

### [bukhari] Bukhari 2443
- `double-reward-slave-marry` | "Double paradise reward for the man who owns, educates, frees, and marries his slave girl"
  > "Three persons will get their reward twice. (One is) a person who has a slave girl and he educates her properly and teaches her good manners properly …
- `obey-master-obey-allah-double-reward` | "Slave who obeys both Allah and master receives double paradise reward"
  > "The slave who worships his Lord in a perfect manner, and is dutiful and obedient to his master, will get a double reward."…

### [bukhari] Bukhari 2512
- `poisoned-sheep` | "A Jewess poisoned Muhammad — and he didn't know until he tasted it"
  > "A Jewess brought a poisoned (cooked) sheep for the Prophet who ate from it. She was brought to the Prophet and he was asked, 'Shall we kill her?' He …
- `muhammad-poisoned-long-illness` | "Muhammad attributed his fatal illness to Khaybar poisoning three years earlier"
  > "The Prophet in his ailment in which he died, used to say, 'O 'Aisha! I still feel the pain caused by the food I ate at Khaibar, and at this time, I f…

### [bukhari] Bukhari 2807
- `trees-stones-jew-genocide` | ""O Muslim! There is a Jew hiding behind me, so kill him" — trees and stones call out at th"
  > "Allah's Apostle said, 'You (i.e. Muslims) will fight with the Jews till some of them will hide behind stones. The stones will (betray them) saying, "…
- `gharqad-tree-not-betray-jews` | "Trees and stones will betray hiding Jews to Muslim killers"
  > "The last hour will not come until the Muslims fight the Jews... the stones and trees will say, 'O Muslim! O servant of Allah! there is a Jew behind m…

### [bukhari] Bukhari 2895
- `apostasy-death` | ""If somebody discards his religion, kill him""
  > "Ali burnt some people and this news reached Ibn 'Abbas, who said, 'Had I been in his place I would not have burnt them... No doubt, I would have kill…
- `ali-burned-apostates-alive` | "Ali burned apostates alive; Ibn Abbas objected only to the method"
  > "Some Zanadiqa (atheists) were brought to Ali and he burnt them. The news of this reached Ibn Abbas, who said, 'If I had been in his place I would not…

### [bukhari] Bukhari 2907
- `uhud-tooth` | "Muhammad was wounded and had a tooth broken at the Battle of Uhud"
  > "Allah's Apostle was struck on the day of Uhud and the helmet broke over his head and his face bled. His front tooth was broken and Fatima washed the …
- `kab-ashraf-assassination` | "Muhammad orders the assassination of Ka'b bin al-Ashraf — a poet who criticized him"
  > "The Prophet said, 'Who is ready to kill Ka'b bin Al-Ashraf who has really hurt Allah and His Apostle?' Muhammad bin Maslama said, 'O Allah's Apostle!…

### [bukhari] Bukhari 301
- `women-deficient` | "Women are "deficient in intelligence and religion" — most of Hell is women"
  > "[Muhammad] said: 'O women! Give alms, for I have seen that the majority of the dwellers of Hell-Fire were you (women).'... He replied, 'O women! You …
- `deficient-intelligence-witness` | "Women's "deficient intelligence" proved by a witness rule that itself rests on their defic"
  > "Muhammad said: 'Is not the evidence of two women equal to the witness of one man?' They replied in the affirmative. He said, 'This is the deficiency …

### [bukhari] Bukhari 3075
- `fetal-stages-40-days` | "Embryo development in 40+40+40 day stages — soul enters at day 120"
  > "Allah's Apostle said, '(The matter of the Creation of) a human being is put together in the womb of the mother in forty days, and then he becomes a c…
- `angel-predestination` | "An angel writes your entire life story — deeds, death date, and paradise or hell — before "
  > "Allah sends an angel who is ordered to write four things. He is ordered to write down his (i.e. the new creature's) deeds, his livelihood, his (date …

### [bukhari] Bukhari 345
- `heart-opened-golden-tray` | "Gabriel cut open Muhammad's chest and filled it with wisdom from a golden tray"
  > "Allah's Apostle said, 'While I was at Mecca the roof of my house was opened and Gabriel descended, opened my chest, and washed it with Zam-zam water.…
- `fifty-prayers-negotiation` | "Allah prescribed 50 daily prayers; Moses helped negotiate them down to 5"
  > "Allah enjoined fifty prayers on my followers... I passed by Moses who asked, 'What has Allah enjoined on your followers?' I replied, 'He has enjoined…

### [bukhari] Bukhari 367
- `safiya-khaybar` | "Muhammad married Safiya the same day he killed her husband and family at Khaybar"
  > "Dihya came and said, 'O Allah's Prophet! Give me a slave girl from the captives.' The Prophet said, 'Go and take any slave girl.' He took Safiya bint…
- `muhammad-thighs-safiyya` | "Anas saw "the whiteness of the Prophet's thigh" at Khaybar"
  > "The Prophet passed through the lane of Khaibar quickly and my knee was touching the thigh of the Prophet. He uncovered his thigh and I saw the whiten…

### [bukhari] Bukhari 3731
- `aisha-age` | "Muhammad married Aisha at six, consummated at nine"
  > "The Prophet engaged me when I was a girl of six (years)... Unexpectedly Allah's Apostle came to me in the forenoon and my mother handed me over to hi…
- `aisha-bride-prep-mother-swing` | "Aisha's mother pulled her from a swing to prepare her for consummation"
  > "I was playing with my girlfriends on a see-saw when my mother called me. I did not know why she was calling me. She took me by the hand... washed my …

### [bukhari] Bukhari 5813
- `wife-beating-camel` | ""Don't beat your wife like a stallion camel and then sleep with her the same night""
  > "The Prophet forbade laughing at a person who passes wind, and said, 'How does anyone of you beat his wife as he beats the stallion camel and then he …
- `beat-slave-sleep-with-her` | ""How does one beat his slave like a camel and then embrace her?" — wife and slave intercha"
  > "The Prophet forbade laughing at a person who passes wind, and said, 'How does anyone of you beat his wife as he beats the stallion camel and then he …

### [bukhari] Bukhari 81
- `every-born-alive-year` | "End-time sign: women will outnumber men 50-to-1"
  > "The Prophet said: 'From among the portents of the Hour are: Religious knowledge will decrease... Women will increase in number and men will decrease …
- `minor-major-signs-qiyamah` | "Minor and major signs of the Hour — knowledge taken, adultery common, women outnumber men "
  > "From among the portents of the Hour are: knowledge will be taken away, there will appear religious ignorance, there will be prevalence of adultery, a…

### [ibn-majah] Abu Dawud #2752
- `ibnmajah-men-killed-for-dhimmi` | "A Muslim is not executed for killing a non-Muslim"
  > "A believer is not killed for a disbeliever."…
- `ibnmajah-dhimmi-distinctive-clothing` | "Dhimmis required to wear distinctive clothing — the zunnar belt"
  > Classical Sunni fiqh: "The dhimmi shall wear the zunnar (distinguishing belt) over his outer garments."…

### [ibn-majah] Ibn Majah #1610
- `ibnmajah-aisha-marriage-nine-consummation` | "Ibn Majah reiterates: Aisha married at 6, consummated at 9"
  > "The Prophet married me when I was six years old, and he consummated the marriage when I was nine years old."…
- `ibnmajah-girl-playing-swing-consummation` | "Aisha taken from a swing to consummate marriage"
  > "Umm Ruman came to me — I was on a swing with my girlfriends. She called me, washed my face with water, and took me into the house."…

### [ibn-majah] Ibn Majah #3188
- `ibnmajah-honey-recurrent-diarrhea` | "Honey prescribed three times for diarrhea — "your brother's stomach is lying""
  > "A man complained that his brother had a stomach ache. The Prophet said: 'Let him drink honey.' He returned saying it had not helped. The Prophet said…
- `ibnmajah-honey-every-disease` | ""In honey there is healing for every disease""
  > "Use these two cures: honey and the Quran."…

### [ibn-majah] Ibn Majah #3812
- `ibnmajah-jesus-breath-kills-disbelievers` | "Jesus descends and his breath kills every disbeliever within eyeshot"
  > "Allah will send 'Eisa bin Maryam... Every disbeliever who smells the fragrance of his breath will die, and his breath will reach as far as his eye ca…
- `ibnmajah-gog-magog-breach-wall` | "Gog and Magog — breaching the wall, licking up seas, killing everything"
  > "Gog and Magog will be released. They will drink everything until not a drop is left; they will kill everyone they find."…

### [ibn-majah] Ibn Majah #4003
- `ibnmajah-women-majority-hell` | "Most hell inhabitants are women — Ibn Majah echoes four canonical sources"
  > "I looked into the Fire and saw that most of its inhabitants were women. They asked: 'Why?' He said: 'Because they are ungrateful to their companions …
- `ibnmajah-women-deficient-intellect` | "Women are deficient in intellect and religion — Ibn Majah preserves"
  > "Have I not seen anyone more deficient in reason and religion than you... The testimony of two women equals that of one man. That is the deficiency of…

### [ibn-majah] Ibn Majah #4075
- `ibnmajah-dajjal-forty-days` | "The Dajjal will remain for 40 days — one day as long as a year"
  > "The Dajjal will remain for forty days — one day as long as a year, one day like a month, one day like a week, and the remaining days like your ordina…
- `ibnmajah-jesus-two-angels-wings-descent` | "Jesus descends with his hands on two angels' wings"
  > "Jesus son of Mary will descend at the white minaret east of Damascus, wearing two yellow garments, his hands placed on the wings of two angels."…

### [ibn-majah] Ibn Majah #4085
- `ibnmajah-mahdi-7-years-descendant` | "The Mahdi from Fatima's descendants — 1,400 years of false claimants"
  > "The Mahdi is from my family, from the descendants of Fatima."…
- `ibnmajah-mahdi-seven-years-mountain-treasure` | ""A Mahdi will rule, and the Euphrates will uncover a mountain of gold""
  > "The Hour will not come until the Euphrates recedes and uncovers a mountain of gold, for which people will fight; 99 out of every 100 will be killed."…

### [ibn-majah] Ibn Majah #4159
- `ibnmajah-fate-written-50000-years-before` | "All destinies were written 50,000 years before creation"
  > "Allah decreed the measures [of all things] fifty thousand years before He created the heavens and the earth."…
- `ibn-majah-4159-adam-musa-debate-predestination` | "Adam defeats Musa in debate: predestination absolves Adam of responsibility for the Fall"
  > "Adam and Musa debated, and Musa said to him: 'O Adam, you are our father but have deprived us and caused us to be expelled from Paradise because of y…

### [ibn-majah] Ibn Majah #4273
- `ibnmajah-angels-chain-throne-demons` | "Jinn eavesdrop on Allah's decrees; meteors are the anti-jinn projectiles"
  > "When Allah decrees a matter in heaven, the angels beat their wings... The eavesdroppers [jinn] listen out for that, one above the other... The shooti…
- `ibnmajah-angels-beat-wings` | "Angels beat their wings in submission with a sound like chains on rock"
  > "The angels beat their wings in submission to His decree with a sound like a chain beating a rock."…

### [ibn-majah] Ibn Majah #508
- `ibnmajah-sneeze-alhamdulillah` | "Sneezing protocol — conditional mercy on Arabic formula"
  > "When one of you sneezes, let him say Alhamdulillah. His brother responds Yarhamuk Allah. If he does not say it, do not respond."…
- `ibnmajah-dua-before-sex-protect-child` | "Dua before sex protects the future child from Satan"
  > "When one of you has intercourse with his wife, if he says: 'In the name of Allah, O Allah keep Satan away from us and keep Satan away from that with …

### [ibn-majah] Ibn Majah #686
- `ibnmajah-prayer-invalid-dog-woman` | "Prayer invalidated by a passing woman, donkey, or black dog"
  > "The prayer is cut by a black dog, a donkey, and a woman."…
- `ibnmajah-beautify-your-prayers` | "Black-dog Satan — the color-coded demonology"
  > "The black dog is a devil."…

### [ibn-majah] Ibn Majah #80
- `ibnmajah-allah-writes-pen-destiny` | "Allah's first creation was a pen — told to write everything that is and will be"
  > "The first thing Allah created was the Pen, and He said to it: 'Write.' It said: 'What shall I write?' He said: 'Write everything that is and will be.…
- `ibnmajah-adam-beats-moses-predestination` | "Adam won an argument against Moses — "It was written before I was created""
  > "Adam and Moses argued. Moses said: 'You are the one whose sin drove humanity from Paradise.' Adam said: 'Will you blame me for a deed Allah wrote for…

### [ibn-majah] Muslim #236
- `ibnmajah-lut-repeat-curse-homosexual` | ""Allah cursed whoever does what Lot's people did" — said three times"
  > "Cursed is the one who does what the people of Lot did. Cursed is the one who does what the people of Lot did. Cursed is the one who does what the peo…
- `ibnmajah-sodomy-kill-both-doer-done-to` | ""Kill the doer and the one it is done to" — homosexual act"
  > "Whoever you find doing the act of the people of Lot — kill the doer and the one it is being done to."…

### [muslim] Bukhari #4350
- `muslim-jewish-couple-man-shielding` | "Muhammad stoned a Jewish couple — the man shielded her body with his"
  > "I saw the man saving the woman from stones by bending over her."…
- `muslim-jews-changed-moses-instruction` | "A rabbi covered the Torah's stoning verse with his hand — Muhammad exposed it"
  > "A rabbi put his hand over the verse of stoning... the Messenger said, 'Lift your hand.' When he did, the verse of stoning was under it."…

### [muslim] Ibn Majah #3814
- `muhammad-visited-by-gabriel-as-dihyah` | "Gabriel frequently appeared as Dihya al-Kalbi — a handsome companion"
  > "Gabriel would come to him in the form of Dihya b. Khalifah al-Kalbi..."…
- `dihya-pattern-homoerotic-reading` | "Gabriel repeatedly appeared in the form of one specific handsome male companion"
  > "Gabriel used to come to the Prophet in the form of Dihya al-Kalbi — a handsome man." "I saw Gabriel and the one who most resembled him was Dihya b. K…

### [muslim] Muslim #296
- `jesus-breaks-cross` | "Jesus returns to break the cross, kill the pigs, and abolish Christianity"
  > "The son of Mary would definitely break the cross, and kill swine and abolish Jizya... This is the honour from Allah for this Ummah."…
- `jesus-grave-ready-medina` | "An empty grave in Medina waits for Jesus to return and be buried there"
  > [Classical tradition, transmitted through hadith commentaries:] "A grave lies empty next to the Prophet's tomb, reserved for Jesus son of Mary when he…
- `muslim-prophet-given-six-privileges` | "Six unique privileges granted to no prior prophet — including victory through terror"
  > "I have been given superiority over the other Prophets in six respects: I have been given comprehensive speech; I have been helped by terror; spoils o…

### [muslim] Muslim #316
- `isra-miraj` | "The Night Journey — Buraq, seven heavens, and bargaining with Moses over prayers"
  > "I was brought al-Buraq Who is an animal white and long, larger than a donkey but smaller than a mule, who would place his hoof a distance equal to th…
- `salat-fifty-to-five-negotiation` | "Prayer reduced from fifty to five — Muhammad haggled with Allah on Moses's advice"
  > "...Moses said to Muhammad: 'Your Lord has laid upon your Ummah fifty prayers. By Allah, I have tested people and I know the nature of people well. Th…

### [muslim] Muslim #3356
- `aisha-age` | "Aisha married at six, sexually consummated at nine — confirmed in Sahih Muslim"
  > "'A'isha reported: Allah's Messenger (may peace be upon him) married me when I was six years old, and I was admitted to his house at the age of nine..…
- `father-marry-not-grown` | ""It is permissible for the father to give his daughter's hand even when she is not fully g"
  > Chapter 10 heading: "It is permissible for the father to give the hand of his daughter in marriage even when she is not fully grown up." (followed by …

### [muslim] Muslim #356
- `muslim-allah-comes-in-form-other-than-his-own` | ""Allah would come to them in a form other than His own Form" on Resurrection Day"
  > "Verily you would see Him like this (as you see the sun and the moon)… Allah would then come to them in a form other than His own Form, recognisable t…
- `muslim-allah-shin-reveal-believers-prostrate` | "Allah uncovers His Shin — believers prostrate, hypocrites turn rigid"
  > "Our Lord will uncover His Shin, and all believers, male and female, will prostrate themselves before Him. But there will remain those who used to pro…

### [muslim] Muslim 2141
- `strike-aisha-chest` | "Muhammad strikes Aisha in the chest — hard enough to cause her pain"
  > "He struck me on the chest which caused me pain, and then said: Did you think that Allah and His Apostle would deal unjustly with you?"…
- `best-men-best-to-wives` | ""The best of you are best to their wives" — held alongside the chest-striking hadith"
  > "The best of you is the best of you to your wives..." — "He struck me on the chest which caused me pain..." (Muslim 2141)…

### [muslim] Muslim 316
- `baitul-mamur-70000-angels-daily` | "Seventy thousand angels enter Bait-ul-Ma'mur every day and never return"
  > "There enter into it seventy thousand angels every day, never to visit (this place) again."…
- `muslim-316-moses-bargains-fifty-prayers` | "Moses bargains Allah down from 50 to 5 daily prayers — because he knows humans better than"
  > "Allah revealed to me and He made obligatory for me fifty prayers every day and night. Then I went down to Moses and he said: What has your Lord enjoi…

### [muslim] Muslim 386
- `999-out-of-every-1-000-to-hell-the-gog-magog-allocation-4476e06a` | "999 out of every 1,000 to hell — the Gog-Magog allocation"
  > Parallel in Bukhari #2275: "Allah will say to Adam: 'The people of the Fire are nine hundred and ninety-nine out of every thousand.'"…
- `muslim-386-jesus-defers-judgment-day` | "On Judgment Day, all of humanity approaches Jesus for intercession — he refuses and defers"
  > "They would come to Jesus and would say: O Jesus, thou art the messenger of Allah and thou conversed with people in the cradle, (thou art) His Word wh…

### [muslim] Muslim 7311
- `bani-israel-eating-vermin` | "The Children of Israel were transformed — into rats, or their ancestors were rats"
  > "A group from the Children of Israel was lost... and I think they are probably rats: do you not see that when a rat is given the milk of a camel it do…
- `muslim-rat-milk-test` | "A lost Jewish tribe was transformed into rats — proven by their milk preferences"
  > "A tribe of the Children of Israel was lost... I don't see them as anything but what they are — mice. For if you put down milk from a she-camel for a …

### [muslim] Muslim 757
- `devil-farts-at-adhan` | "Satan flees the call to prayer while passing wind"
  > "When Satan hears the call to prayer, he runs away to a distance like that of Rauha... Satan runs back and breaks wind so as not to hear the call bein…
- `adhan-satan-flee-distance-rauha` | "Satan's flight distance — measured in miles"
  > "He runs away to a distance like that of Rauha..."…

### [nasai] Bukhari #678
- `nasai-women-hair-awrah` | "Allah does not accept a woman's prayer without a khimar"
  > "Allah does not accept the prayer of a woman who has reached puberty unless she wears a khimar."…
- `nasai-women-best-prayer-home` | "Women's best prayer is in her innermost room — not the mosque"
  > "Their best prayer is in their innermost rooms."…

### [nasai] Bukhari #7154
- `nasai-magic-on-prophet-story` | "Muhammad bewitched for months — false memories of things undone"
  > "Magic was worked on the Messenger of Allah until he used to imagine that he had done something when he had not done it."…
- `nasai-allah-shin-reveal-judgment` | "Allah will uncover His Shin on the Day of Judgment"
  > "Our Lord will uncover His Shin; every believer will prostrate; but those who prostrated in this world for show will be unable to do so, their backs b…

### [nasai] Muslim #1667
- `nasai-dajjal-forty-days-signs` | "The Dajjal's 40-day reign — and Jesus's descent beside a white minaret"
  > "Jesus son of Mary will descend at the white minaret east of Damascus, wearing two yellow garments, hands on the wings of two angels."…
- `nasai-allah-descends-lowest-heaven-night` | "Allah descends nightly to the lowest heaven"
  > "Our Lord descends to the lowest heaven each night, when the last third of the night remains."…
- `nasai-moon-split-prophet-miracle` | "Moon split in Muhammad's lifetime"
  > "The moon was split into two halves during the time of Allah's Messenger."…

### [nasai] Nasa'i #306
- `nasai-uraniyyin-eyes-branded` | "Uraniyyin — eyes branded, limbs cut off, left to die of thirst"
  > "Their eyes were smoldered with heated nails, their hands and feet cut off, then they were left in Al-Harrah in that state until they died."…
- `nasai-camel-urine-drink` | ""Drink camel urine and milk" — Nasa'i's version of prophetic medicine"
  > "The Messenger ordered them to go to the camels and drink their urine and milk."…

### [nasai] Nasa'i #3333
- `nasai-prophet-captured-women-sale` | "Captive women sold — soldiers had sex before the market"
  > "We took captive women from among the Arabs. We used to have intercourse with them, but we did not want them to get pregnant, so we said: Shall we pra…
- `nasai-captives-sex-ruling-withdrawal` | "Captives: sex permitted, withdrawal irrelevant, resale preserved"
  > "We took captives and used azl. The Prophet said: 'It does not matter whether you do or not — no soul decreed to exist will fail to exist.'"…

### [nasai] Nasa'i #3337
- `nasai-kill-stepson-married-fathers-wife` | "Muhammad sends a man to kill the stepson who married his father's wife — and seize his wea"
  > "The Messenger of Allah is sending me to a man who has married his father's wife after he died, to strike his neck or kill him. And he has commanded m…
- `nasai-usury-seventy-sins-zina` | ""Usury has seventy degrees, the least of which is like incest""
  > "Usury has seventy degrees, the least of which is a man committing incest with his mother."…

### [nasai] Nasai #939
- `nasai-seven-ahruf-revealed-recitation` | "The Quran was revealed in seven ahruf (forms)"
  > "This Quran has been revealed in seven ahruf."…
- `nasai-uthman-burned-variants` | "Uthman ordered all variant Quran copies burned"
  > "Uthman ordered that every leaf or copy of the Quran that differed from the standard be burnt."…

### [tirmidhi] Abu Dawud #4283
- `mahdi-will-come` | "The Mahdi will rule for 7–9 years — Tirmidhi's version"
  > "The Mahdi is from my ummah. He will rule for seven or eight or nine years. He will fill the earth with equity and justice as it was filled with tyran…
- `tirmidhi-mahdi-earth-filled-oppression` | "The Mahdi will fill the earth with justice after tyranny"
  > "If there was not left of this world except a single day, Allah would lengthen that day until He sent in it a man from my family, whose name agrees wi…

### [tirmidhi] Bukhari #3812
- `tirmidhi-Aisha-age-similar` | "Aisha's age confirmed by Tirmidhi: married at six, consummated at nine"
  > "The Messenger of Allah married 'Aishah when she was six years old, and consummated the marriage with her when she was nine."…
- `tirmidhi-aisha-kept-dolls` | "Aisha played with dolls in her husband's home — the tradition's own evidence of her age"
  > "I used to play with dolls in the presence of the Prophet, and my friends would come and play with me."…

### [tirmidhi] Bukhari #4989
- `tirmidhi-women-majority-hell-reasons` | "Women are the majority of hell's inhabitants — intellectual deficiency cited as reason"
  > "Most of its dwellers were women. They were asked: 'Why?' He said: 'They are ungrateful to their husbands, they curse much, and they are intellectuall…
- `tirmidhi-wife-hellfire-ingratitude` | "Most women in hell because of ingratitude — not disbelief"
  > "I looked into Paradise and saw its majority were the poor; I looked into Hell and saw its majority were women. They disbelieve their husbands and are…

### [tirmidhi] Ibn Majah #2535
- `seventy-two-virgins-martyrs` | "Every martyr receives 72 virgin wives in paradise"
  > "The martyr has six special favors with Allah... he is married to seventy-two Hur al-'Ayn (wide-eyed virgins); and his intercession is accepted for se…
- `best-sadaqa-give-family` | "Seven things granted immediately to the martyr — the Tirmidhi checklist"
  > "The martyr has seven special favors..."…

### [tirmidhi] Muslim #4817
- `tirmidhi-pen-tablet-abu-lahab-pre-written` | "Allah wrote Abu Lahab's damnation in the Preserved Tablet before creation"
  > "It is a book that Allah wrote before He created the Heavens, and before He created the earth. In it: Pharaoh is among the inhabitants of the Fire, an…
- `tirmidhi-khalifah-twelve-quraysh` | ""There will be twelve Caliphs — all from Quraysh""
  > "This religion will continue to be strong until there have been twelve Caliphs. All of them will be from Quraysh."…

### [tirmidhi] Tirmidhi #1173
- `prayer-woman-cat-prayer-invalid` | "A woman's prayer at home is better than her prayer at the mosque"
  > "A woman's prayer in her house is better than her prayer in her courtyard. And her prayer in her inner room is better than her prayer in her house."…
- `tirmidhi-hijab-entire-body` | "A woman's whole body is awrah — Tirmidhi-cited rule"
  > "A woman is awrah; whenever she goes out, Satan adorns her."…
- `tirmidhi-mosque-satan-shape` | "Women attending mosques — Satan's presence discussed"
  > "When a woman comes out, Satan looks at her."…

### [tirmidhi] Tirmidhi #1418
- `paradise-smell-40-years` | "Paradise's fragrance can be smelled from 40 years' travel away"
  > "Whoever kills a man from the People of the Covenant (dhimmi) unjustly will not smell the fragrance of Paradise, though its fragrance can be smelled f…
- `tirmidhi-dhimmi-killed-hellfire-smell` | "Killing a dhimmi unjustly — 40 years paradise-fragrance blocked"
  > "Whoever kills a protected non-Muslim will not smell the fragrance of Paradise — and its fragrance can be smelled at a distance of forty years."…

### [tirmidhi] Tirmidhi #1428
- `tirmidhi-half-diyya-disbeliever` | "A disbeliever's blood-money is half a Muslim's — tiered life-value rule"
  > "The Muslim is not killed for a disbeliever. And the blood-money paid for a disbeliever is half of the blood-money paid for a believer."…
- `tirmidhi-ma-iz-confessed-four-times-stoned` | "Ma'iz confessed four times to Muhammad then was stoned — Prophet turned away three times f"
  > "Ma'iz came to the Prophet and confessed he had committed zina. The Prophet turned his face away. Ma'iz repeated the confession. The Prophet turned aw…

### [tirmidhi] Tirmidhi #1590
- `tirmidhi-muhammad-six-special-privileges` | "Muhammad was given six special privileges no other prophet had"
  > "I have been given six [things] above the rest of the Prophets: concise yet comprehensive speech, I have been made victorious through terror, the spoi…
- `tirmidhi-victorious-through-terror` | ""I have been made victorious through terror""
  > "I have been made victorious through terror [cast into the hearts of my enemies]."…

### [tirmidhi] Tirmidhi #2608
- `lowest-paradise-king-of-two-thousand-years` | "The lowest paradise dweller gets a kingdom larger than Earth"
  > "The lowest in rank among the people of Paradise will have a kingdom as large as the distance a rider can travel in two thousand years."…
- `tirmidhi-72-ummah-paradise` | "Lowest paradise dweller has 72 wives — 70 from paradise, 2 human"
  > "The least in rank among the people of Paradise will have seventy-two wives."…

### [tirmidhi] Tirmidhi #2672
- `tirmidhi-men-saved-only-women-damned` | "Among the people of hellfire, women are the majority"
  > "I looked into Paradise, and most of its dwellers were the poor. I looked into Hellfire, and most of its dwellers were women."…
- `tirmidhi-most-women-ungrateful` | "Most women are ungrateful to their husbands — Muhammad saw them in hell"
  > "I looked into the Fire and saw that the majority of its inhabitants were women. They were asked: 'Why?' He said: 'They are ungrateful to their husban…

### [tirmidhi] Tirmidhi #2863
- `adultery-of-eye-ear` | "The adultery of the eye is looking; the adultery of the ear is listening"
  > "Every son of Adam has his share of fornication. The eyes commit fornication and their fornication is the look; the ears commit fornication and their …
- `tirmidhi-2863-woman-perfume-adulteress` | "A woman who wears perfume and passes a gathering "is like this and that" — meaning an adul"
  > "Every eye commits adultery, and when the woman uses perfume and she passes by a gathering, then she is like this and that." Meaning an adulteress.…

### [tirmidhi] Tirmidhi #92
- `tirmidhi-cat-pure-purity` | "Cats are pure — but dogs require seven washes"
  > "Cats are not impure. They are from those who frequent your houses."…
- `tirmidhi-cat-urine-food` | "Cats' leftover water is pure — they are "frequent visitors""
  > "Cats are not impure. They are from those who frequent your houses."…

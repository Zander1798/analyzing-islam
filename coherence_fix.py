"""
Coherence review corrections for site/catalog/muslim.html
Run: py coherence_fix.py
"""
from bs4 import BeautifulSoup, NavigableString
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('site/catalog/muslim.html', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
entries_list = soup.find_all('div', class_='entry')

def get_e(eid):
    for e in entries_list:
        if e.get('id', '') == eid:
            return e
    return None

def make_ref_span(entry, refs):
    """refs = list of (display_text, href_num_string)"""
    ref_span = entry.find('span', class_='ref')
    if not ref_span:
        return False
    ref_span.clear()
    for i, (disp, href_num) in enumerate(refs):
        if i > 0:
            ref_span.append(NavigableString(u', '))
        a = soup.new_tag('a', href='../read/muslim.html#h' + href_num)
        a.string = disp
        ref_span.append(a)
    return True

def set_strength(entry, new_strength):
    old = entry.get('data-strength', '').lower()
    if old == new_strength:
        return False
    entry['data-strength'] = new_strength
    for span in entry.find_all('span', class_=True):
        classes = list(span.get('class', []))
        old_cls = 'strength-' + old
        new_cls = 'strength-' + new_strength
        if old_cls in classes:
            classes[classes.index(old_cls)] = new_cls
            span['class'] = classes
            span.string = new_strength.capitalize()
            return True
    return False

def get_why_p(entry):
    for h4 in entry.find_all('h4'):
        if 'Why this is a problem' in h4.get_text():
            return h4.find_next_sibling('p')
    return None

changes = []

# ============================================================
# CORRECTION 1: Entry 4 - seven-ahruf INACCURATE-REF
# Ref cites Muslim #5783 (migration dream); correct is Muslim #1791-1796
# ============================================================
e = get_e('muslim-quran-seven-ahruf-textual-variants')
if e and make_ref_span(e, [('Muslim #1791', '1791'), ('#1796', '1796')]):
    changes.append('Entry 4 [INACCURATE-REF]: ref corrected from Muslim #5783 (migration dream) to Muslim #1791, #1796 (Umar/Hisham seven-ahruf dispute)')

# ============================================================
# CORRECTION 2: Entry 8 - killed-100 WEAK-FRAMING
# Fix the inaccurate claim that there was no recorded repentance
# The hadith explicitly shows the angels of mercy calling him penitent
# ============================================================
e = get_e('muslim-killed-100-distance-measured-mercy')
if e:
    why_p = get_why_p(e)
    if why_p:
        t = why_p.get_text()
        old_frag = 'The man performed no recorded act of repentance'
        if old_frag in t:
            new_t = t.replace(
                'The man performed no recorded act of repentance'
                u'—'
                'no restitution, no apology, no direct acknowledgment of wrongdoing to victims’ families. His journey had only just begun when he died.',
                'The man was in fact acknowledged as penitent by the angels of mercy'
                u' (“'
                'come as a penitant and remorseful to Allah'
                u'”), yet the deciding factor was not that acknowledged repentance but a physical measurement of his corpse’s proximity to the two cities.'
            )
            if new_t != t:
                why_p.string = new_t
                changes.append('Entry 8 [WEAK-FRAMING]: corrected misstatement that there was no recorded repentance; the hadith explicitly shows angels of mercy calling him penitent. Restated the real problem: distance-measurement supersedes acknowledged repentance as the deciding mechanism.')
            else:
                changes.append('Entry 8: WARNING - em-dash replacement failed, trying ASCII dash version')
                # Try plain replacement
                new_t2 = t.replace(
                    'The man performed no recorded act of repentance',
                    'The man was in fact acknowledged as penitent by the angels of mercy (called penitant and remorseful to Allah), yet the deciding factor was not that acknowledged repentance but a physical measurement of his corpse proximity to the two cities.'
                )
                if new_t2 != t:
                    why_p.string = new_t2
                    changes.append('Entry 8 [WEAK-FRAMING]: partial fix applied via fallback replacement')

# ============================================================
# CORRECTION 3: Entry 36 - safiyya INACCURATE-REF
# Primary ref is Abu Dawud #2159 but story is in Muslim at #3374
# ============================================================
e = get_e('safiyya-same-night')
if e and make_ref_span(e, [('Muslim #3374', '3374'), ('#3375', '3375')]):
    changes.append('Entry 36 [INACCURATE-REF]: ref corrected from Abu Dawud #2159 to Muslim #3374-3375 (Safiyya/Khaybar narrative is in Sahih Muslim)')

# ============================================================
# CORRECTION 4: Entry 39 - moon-split WRONG-STRENGTH moderate -> strong
# ============================================================
e = get_e('moon-split')
if e and set_strength(e, 'strong'):
    changes.append('Entry 39 [WRONG-STRENGTH]: upgraded MODERATE to STRONG; a globally visible astronomical event has no corroborating record from Chinese, Roman, Indian or Mayan civilizations with active astronomical traditions in 610 CE, and the argument is textually unambiguous with no easy orthodox rebuttal')

# ============================================================
# CORRECTION 5: Entry 46 - father-marry-not-grown INACCURATE-REF
# Refs Muslim #3303-3311 (mutah chapter); correct is #3356-3359 (Aisha age hadiths)
# ============================================================
e = get_e('father-marry-not-grown')
if e and make_ref_span(e, [('Muslim #3356', '3356'), ('#3357', '3357'), ('#3358', '3358'), ('#3359', '3359')]):
    changes.append('Entry 46 [INACCURATE-REF]: ref corrected from Muslim #3303-3311 (mutah chapter) to Muslim #3356-3359 (Aisha age hadiths and the chapter heading above them)')

# ============================================================
# CORRECTION 6: Entry 68 - fate-written INACCURATE-REF
# Refs Muslim #6390-6393 (visiting-sick hadiths); correct is #6558
# ============================================================
e = get_e('fate-written')
if e and make_ref_span(e, [('Muslim #6558', '6558')]):
    changes.append('Entry 68 [INACCURATE-REF]: ref corrected from Muslim #6390-6393 (visiting-sick hadiths) to Muslim #6558 (fate/womb/angel predestination hadith)')

# ============================================================
# CORRECTION 7: Entry 80 - fitra WRONG-STRENGTH strong -> moderate
# The fitra argument has a substantial Muslim rebuttal acknowledged in the entry
# ============================================================
e = get_e('every-child-is-born-on-fitra-his-parents-make-him-jew-christ-11596bc8')
if e and set_strength(e, 'moderate'):
    changes.append('Entry 80 [WRONG-STRENGTH]: downgraded STRONG to MODERATE; the fitra-as-generic-monotheist-disposition rebuttal is substantial and acknowledged in the entry itself')

# ============================================================
# CORRECTION 8: Entry 84 - painters CULTURAL-NOT-THEOLOGICAL
# Reframe WHY from ethical to theological argument
# ============================================================
e = get_e('painters-of-pictures-the-worst-punishment-on-the-day-of-resu-fa5d7231')
if e:
    why_p = get_why_p(e)
    if why_p:
        t = why_p.get_text()
        old_frag = 'No defensible ethical framework'
        if old_frag in t:
            new_t = t.replace(
                'No defensible ethical framework ranks artistic depiction of living things above murder, rape, genocide, or oppression as the gravest category of sin',
                'A God who equips humans with the impulse to represent observed creation and whose Quran instructs believers to look and reflect on the natural world (Q3:191) cannot coherently assign the worst eschatological punishment to that very representation. The ruling is theologically inconsistent with Islamic claims about Allah as the purposeful Creator who gave humans perception, craft and the capacity for visual reasoning'
            )
            if new_t != t:
                why_p.string = new_t
                changes.append('Entry 84 [CULTURAL-NOT-THEOLOGICAL]: reframed WHY from a pure ethical objection to a theological incoherence argument (criterion 7 corrected)')
            else:
                changes.append('Entry 84: WARNING - could not locate exact framing text for replacement')

# ============================================================
# CORRECTION 9: Entry 143 - jesus-descends INACCURATE-REF
# Refs Muslim #7197 (denying a date for Last Hour); correct is #294, #296
# ============================================================
e = get_e('jesus-descends-kills-swine-breaks-cross')
if e and make_ref_span(e, [('Muslim #294', '294'), ('#296', '296')]):
    changes.append('Entry 143 [INACCURATE-REF]: ref corrected from Muslim #7197 (hadith about setting no date for Last Hour) to Muslim #294, #296 (Jesus descends as just judge, breaks cross, kills swine, abolishes jizya)')

# ============================================================
# CORRECTION 10: Entry 150 - tree-stone-jew INACCURATE-REF
# Refs Muslim #7107 (ten signs of Last Hour); correct is #7158
# ============================================================
e = get_e('tree-stone-tell-hiding-jew')
if e and make_ref_span(e, [('Muslim #7158', '7158')]):
    changes.append('Entry 150 [INACCURATE-REF]: ref corrected from Muslim #7107 (ten signs of Last Hour) to Muslim #7158 (tree/stone/Jew end-times hadith)')

# ============================================================
# CORRECTION 11: Entry 167 - dihya WEAK-FRAMING
# Replace speculative homoerotic insinuation with the legitimate epistemological problem
# ============================================================
e = get_e('dihya-pattern-homoerotic-reading')
if e:
    why_p = get_why_p(e)
    if why_p:
        new_t = (
            'The pattern raises a genuine epistemological problem classical tafsir does not adequately address: '
            'if Gabriel consistently appeared as a specific named, living human companion, '
            'then every private conversation Muhammad had with Gabriel was externally indistinguishable '
            'from a conversation with Dihya al-Kalbi. The Umm Salama narration makes this concrete: '
            'observers saw what they understood to be an ordinary man. '
            'This means the divine-revelation transmission channel was, by design, unverifiable to anyone '
            'present other than Muhammad himself, undermining the evidential basis for specific prophetic '
            'claims about what Gabriel communicated in private encounters.'
        )
        why_p.string = new_t
        changes.append('Entry 167 [WEAK-FRAMING]: replaced speculative homoerotic insinuation (criterion 1 violation) with the legitimate epistemological problem about private revelation unverifiability')

# ============================================================
# CORRECTION 12: Entry 208 - ihram-marriage INACCURATE-REF
# Refs Muslim #2720 (perfume during ihram); correct is #3330-3331
# ============================================================
e = get_e('muslim-prophet-married-in-ihram-exception')
if e and make_ref_span(e, [('Muslim #3330', '3330'), ('#3331', '3331')]):
    changes.append('Entry 208 [INACCURATE-REF]: ref corrected from Muslim #2720 (perfume during ihram) to Muslim #3330 (married while a muhrim) and #3331 (Maymuna herself says he was not in ihram) — the contradiction between the two is itself the evidentiary core')

# ============================================================
# CORRECTION 13: Entry 222 - allah-shin INACCURATE-REF
# Refs Muslim #183 (Usama killed shahada); shin/saq is Bukhari-primary
# Closest Muslim hadiths are #356-359 (vision/form narratives)
# ============================================================
e = get_e('muslim-allah-shin-reveal-believers-prostrate')
if e and make_ref_span(e, [('Muslim #356', '356'), ('#359', '359')]):
    changes.append('Entry 222 [INACCURATE-REF]: ref corrected from Muslim #183 (Usama killed shahada — wrong hadith entirely) to Muslim #356, #359 (the vision/form-of-Allah resurrection narratives; note: the explicit shin/saq language is from Bukhari #7439 and Q68:42, not verbatim in Muslim)')

# ============================================================
# CORRECTION 14: Entry 235 - charity-after-death INACCURATE-REF
# Refs Muslim #1631 (Witr prayer); actual hadith is at #4094
# ============================================================
e = get_e('muslim-charity-after-death-works')
if e and make_ref_span(e, [('Muslim #4094', '4094')]):
    changes.append('Entry 235 [INACCURATE-REF]: ref corrected from Muslim #1631 (Witr prayer hadith) to Muslim #4094 (when a man dies his acts come to an end but three: sadaqa jariya, useful knowledge, righteous child who prays)')

# ============================================================
# Write output
# ============================================================
print(f'Total corrections applied: {len(changes)}')
for c in changes:
    print(f'  - {c}')

with open('site/catalog/muslim.html', 'w', encoding='utf-8') as f:
    f.write(str(soup))

print()
print('site/catalog/muslim.html written successfully.')

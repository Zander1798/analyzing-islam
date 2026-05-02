import os, re, html as html_mod
SITE = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
sources = ["bukhari","muslim","tirmidhi","ibn-majah","nasai","abu-dawud"]

test_phrases = [
    ("seventy years without", "hell-depth"),
    ("head is like a raisin", "raisin-ruler"),
    ("son of Adam had two valleys", "valleys-gold"),
    ("descends to the lowest heaven", "allah-descends"),
    ("The breath of the fasting", "fasting-breath"),
    ("The Blood Stone descended from", "black-stone"),
    ("angels do not enter a house", "angels-house"),
    ("fornication never spreads among", "fornication-plague"),
]

for phrase, label in test_phrases:
    found = False
    for src in sources:
        p = os.path.join(SITE, "read", f"{src}.html")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            c = f.read()
        # Build plain + marker version
        c2 = re.sub(r'<[^>]*\sid="(h\d+)"[^>]*>', r' ANCHOR_\1 ', c, flags=re.IGNORECASE)
        c2 = re.sub(r'<[^>]+>', ' ', c2)
        c2 = html_mod.unescape(re.sub(r'\s+', ' ', c2))

        idx = c2.lower().find(phrase.lower())
        if idx != -1:
            chunk = c2[max(0, idx-3000):idx+100]
            markers = list(re.finditer(r'ANCHOR_(h\d+)', chunk))
            anchor = markers[-1].group(1) if markers else "?"
            snippet = c2[idx:idx+100]
            print(f"[{label}] FOUND in {src}#{anchor}: ...{snippet[:80]}...")
            found = True
            break
    if not found:
        print(f"[{label}] NOT FOUND in any reader")

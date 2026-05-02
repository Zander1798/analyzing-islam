"""Second round: find correct IDs for remaining unknown cases."""
import os, re, html as html_mod

SITE     = r"C:/Users/zande/Documents/AI Workspace/Analyzing Islam/site"
READ_DIR = os.path.join(SITE, "read")

def hadith_index(source):
    p = os.path.join(READ_DIR, f"{source}.html")
    if not os.path.exists(p):
        return {}
    content = open(p, encoding="utf-8").read()
    idx = {}
    pat = re.compile(r'id="(h\d+)"', re.IGNORECASE)
    positions = [(m.group(1), m.start()) for m in pat.finditer(content)]
    for i, (hid, start) in enumerate(positions):
        end = positions[i+1][1] if i+1 < len(positions) else len(content)
        block = content[start:end]
        text = re.sub(r"<[^>]+>", " ", block)
        text = html_mod.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        idx[hid] = text
    return idx

def search(source, keywords, max_results=8):
    idx = hadith_index(source)
    print(f"\n=== {source} — {keywords} ===")
    found = 0
    kw_lower = [k.lower() for k in keywords]
    for hid, text in idx.items():
        tl = text.lower()
        if all(k in tl for k in kw_lower):
            safe = text[:200].encode('ascii', 'replace').decode('ascii')
            print(f"  {hid}: {safe}")
            found += 1
            if found >= max_results:
                print(f"  (stopping at {max_results})")
                break
    if found == 0:
        print("  (no match)")

def show(source, hid):
    idx = hadith_index(source)
    t = idx.get(hid, "(not found)")
    print(f"\n=== {source} {hid} ===")
    print(t[:300].encode('ascii','replace').decode('ascii'))

# ── d01: abu-dawud h2150 — captive iddah parallel ────────────────────────────
# "A captive woman shall not be approached for sexual intercourse until she has had a menstrual period"
search("abu-dawud", ["captive", "menstrual"])
search("abu-dawud", ["captive", "sexual", "period"])
search("abu-dawud", ["captive", "intercourse"])
search("abu-dawud", ["pregnant", "captive"])

# ── d05: abu-dawud h4582 — female diyya half ─────────────────────────────────
# "Amr ibn Shu'ayb... female diyya is half that of male"
show("abu-dawud", "h4544")  # found earlier for dhimmi blood-money
search("abu-dawud", ["woman", "half", "man", "blood-money"])
search("abu-dawud", ["female", "half"])

# ── d18: abu-dawud h4587 — diyya by religion ─────────────────────────────────
# "blood-money of Jew/Christian is half that of Muslim"
show("abu-dawud", "h4544")  # check if this covers both female and dhimmi cases
search("abu-dawud", ["blood-money", "jew"])
search("abu-dawud", ["blood-money", "christian"])
search("abu-dawud", ["blood-money", "half", "muslim"])

# ── b06: bukhari h7424 — sun prostration (Tawhid section) ────────────────────
# Check what's at/near h7141 (3rd occurrence of sun prostration we found)
show("bukhari", "h7141")
show("bukhari", "h3066")
show("bukhari", "h4596")

# ── b08: bukhari h4119 — Banu Qurayza mass execution ─────────────────────────
search("bukhari", ["banu", "qurayza"])
search("bukhari", ["qurayza"])
search("bukhari", ["tribe", "executed", "trenches"])
search("bukhari", ["trench", "kill", "tribe"])
# Try nearby IDs to h4028 (known Banu Qurayza number in standard numbering)
print("\n=== Bukhari h4000-h4050 range ===")
idx_b = hadith_index("bukhari")
for n in range(4000, 4060):
    h = f"h{n}"
    if h in idx_b:
        t = idx_b[h][:150].encode('ascii','replace').decode('ascii')
        if any(k in t.lower() for k in ["qurayza","tribe","executed","sabra","trenches","ditch"]):
            print(f"  h{n}: {t}")

# ── b09: bukhari h5158 — Safiyya Khaybar ─────────────────────────────────────
search("bukhari", ["safiyya"])
search("bukhari", ["safiya"])
# Try range near h4200
print("\n=== Bukhari h4190-h4230 range ===")
for n in range(4185, 4235):
    h = f"h{n}"
    if h in idx_b:
        t = idx_b[h][:150].encode('ascii','replace').decode('ascii')
        if any(k in t.lower() for k in ["safiyy","safiya","khaybar"]):
            print(f"  h{n}: {t}")

# ── t06: bukhari h5950 — picture painters punished severely ──────────────────
search("bukhari", ["picture", "painter", "punishment"])
search("bukhari", ["makers", "picture", "punishment"])
search("bukhari", ["image", "painter", "punishment"])
search("bukhari", ["picture", "severely"])
search("bukhari", ["those who make", "image"])
# Try range near h5950
print("\n=== Bukhari h5940-h5960 range ===")
for n in range(5935, 5965):
    h = f"h{n}"
    if h in idx_b:
        t = idx_b[h][:150].encode('ascii','replace').decode('ascii')
        if any(k in t.lower() for k in ["picture","image","paint","angel"]):
            print(f"  h{n}: {t}")

# ── t16: tirmidhi h2003 — guide me to deed equal to jihad ────────────────────
search("tirmidhi", ["guide", "deed", "jihad"])
search("tirmidhi", ["deed", "jihad"])
search("tirmidhi", ["jihad", "deed", "man came"])
# Try near h1620, h1671
print("\n=== Tirmidhi h1610-h1640 range ===")
idx_t = hadith_index("tirmidhi")
for n in range(1610, 1650):
    h = f"h{n}"
    if h in idx_t:
        t = idx_t[h][:150].encode('ascii','replace').decode('ascii')
        if any(k in t.lower() for k in ["jihad","deed equal","guide me"]):
            print(f"  h{n}: {t}")

# ── m16/m19/q15: Bukhari IDs 7420-7517 (above reader max) ───────────────────
# Searching for content these hadiths should have:

# q15 bukhari h7420: Aisha saying Muhammad "concealed within himself"
search("bukhari", ["concealed", "himself"])
search("bukhari", ["aisha", "concealed"])
search("bukhari", ["zaynab", "zayd", "concealed"])

# m19 bukhari h7437: Allah appearing in two forms / descending
search("bukhari", ["two forms"])
search("bukhari", ["recognise", "form"])
search("bukhari", ["recognise him", "shin"])  # Bukhari Day of Judgment vision

# m16 bukhari h7510: Muslim sinners eventually leaving Hell
search("bukhari", ["intercession", "hell", "muslim"])
search("bukhari", ["leave hell", "muslim"])
search("bukhari", ["fire", "muslim", "taken out"])

# b06 h7424: check if h7141 is the right Bukhari for sun prostration
show("bukhari", "h7141")

"""
Searches reader files for hadiths matching given keywords.
Prints the hadith ID and first 200 chars for each match.
"""
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

def search(source, keywords, max_results=5):
    idx = hadith_index(source)
    print(f"\n=== {source} — searching: {keywords} ===")
    count = 0
    kw_lower = [k.lower() for k in keywords]
    for hid, text in idx.items():
        tl = text.lower()
        if all(k in tl for k in kw_lower):
            safe = text[:200].encode('ascii', 'replace').decode('ascii')
            print(f"  {hid}: {safe}")
            count += 1
            if count >= max_results:
                print(f"  ... (stopping at {max_results})")
                break
    if count == 0:
        print("  (no matches)")


# ── Cases needing correct ID ─────────────────────────────────────────────────

# d01: captive woman parallel — "captive woman shall not be approached"
search("abu-dawud", ["captive", "approached"])

# d05: female diyya half — "Amr ibn Shu'ayb" + "woman" + diyya
search("abu-dawud", ["amr", "shu", "woman", "diyya"])
search("abu-dawud", ["woman", "blood-money", "half"])
search("abu-dawud", ["diyya", "woman", "half"])

# d12: change evil with hand
search("abu-dawud", ["sees an evil", "hand"])
search("abu-dawud", ["evil", "hand", "tongue", "heart"])

# d14: eclipse — Ibrahim's death
search("abu-dawud", ["eclipse", "ibrahim"])
search("abu-dawud", ["eclipsed", "ibrahim"])

# d18: diyya by religion — non-Muslim half
search("abu-dawud", ["blood-money", "dhimmi"])
search("abu-dawud", ["christian", "blood-money"])
search("abu-dawud", ["blood-money", "disbeliever"])

# b03: stoning verse — Umar fearing people will forget
search("bukhari", ["stoning", "verse", "afraid"])
search("bukhari", ["rajm", "afraid"])
search("bukhari", ["stone", "afraid", "people will say"])

# b06: sun prostration Abu Dharr — "where the sun goes"
search("bukhari", ["sun", "prostrate", "throne"])
search("bukhari", ["where the sun", "throne"])
search("bukhari", ["do you know where", "sun"])

# b08: Banu Qurayza execution
search("bukhari", ["qurayza", "killed"])
search("bukhari", ["banu qurayza"])

# b09: Safiyya at Khaybar capture
search("bukhari", ["safiyya", "khaybar"])

# b12: three lawful kills — blood of Muslim
search("bukhari", ["blood of a muslim", "three"])
search("bukhari", ["lawful", "blood", "testifies"])

# b13: strength of thirty men (sexual)
search("bukhari", ["strength", "thirty"])
search("bukhari", ["thirty men", "sexual"])
search("bukhari", ["cohabiting", "thirty"])

# b06 + m19 + m16 + q15: IDs > 7277 — check max Bukhari in reader
idx = hadith_index("bukhari")
nums = sorted(int(h[1:]) for h in idx.keys())
print(f"\n=== Bukhari reader: min={nums[0]}, max={nums[-1]}, total={len(nums)} ===")
# Check if these specific IDs exist or what's near them
for target in [7420, 7424, 7437, 7510, 7517]:
    nearby = [(n, idx[f"h{n}"]) for n in range(target-5, target+6) if f"h{n}" in idx]
    if nearby:
        print(f"  Near h{target}:")
        for n, t in nearby:
            print(f"    h{n}: {t[:100].encode('ascii','replace').decode('ascii')}")
    else:
        print(f"  h{target}: nothing in range h{target-5}..h{target+5}")

# m06: three options for non-Muslims — invite Islam / jizya / fight
search("muslim", ["invite", "islam", "jizya"])
search("muslim", ["invite them to", "jizya"])
search("muslim", ["three things", "non-muslim"])
search("muslim", ["three", "options", "fight"])

# t06: picture painters punished / angels no pictures
search("bukhari", ["those who paint", "punished"])
search("bukhari", ["paint picture", "punished"])
search("bukhari", ["picture", "punished", "severely"])

# t16: jihad supreme deed — "came to messenger / deed equal to jihad"
search("tirmidhi", ["deed equal", "jihad"])
search("tirmidhi", ["deed equival", "jihad"])
search("tirmidhi", ["guide me to a deed", "jihad"])

# i02: sahla/salim breastfeeding
search("ibn-majah", ["salim", "breastfeed"])
search("ibn-majah", ["sahla", "breastfeed"])
search("ibn-majah", ["breastfeed", "grown"])

# t19: Tirmidhi h2209 — is "two books" actually predestination related?
idx_t = hadith_index("tirmidhi")
if "h2209" in idx_t:
    print("\n=== tirmidhi h2209 full text (200 chars) ===")
    print(idx_t["h2209"][:200].encode('ascii','replace').decode('ascii'))
if "h2205" in idx_t:
    print("\n=== tirmidhi h2205 full text (200 chars) ===")
    print(idx_t["h2205"][:200].encode('ascii','replace').decode('ascii'))

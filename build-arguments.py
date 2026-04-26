"""
Build the Dossiers tab — landing page + 7 source pages + per-argument pages.

Reads JSON from arguments-data/ and writes static HTML pages into:

  site/arguments.html                             - dossiers landing (7 source cards)
  site/arguments/{slug}.html                      - per-source case index (TOC of 20)
  site/arguments/{slug}/{entry_id}.html           - one page per argument

Per-argument pages have Prev / Next / All-cases links that navigate to
real URLs (no in-page scrolling) and a sidebar TOC for jumping between
the 20 cases in the same source.

URL paths still use "arguments" (rather than "dossiers") for stability;
only the visible label says "Dossiers".

The pages are auth-gated: the rendered content is hidden until
window.__authReady resolves and a session is detected. When signed
out, a sign-in prompt is shown instead.

Run after editing any of the JSON files.
"""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "arguments-data"
SITE_DIR = ROOT / "site"
ARGS_DIR = SITE_DIR / "arguments"


# ============================================================
# Reference linking — turn "Q 4:34", "Bukhari 5134", "Bukhari 5134, 5158, 3894",
# "Muslim 1422 / 1404-1407", etc. into anchor links pointing at the matching
# verse/hadith inside the readable source pages.
#
# Anchor schemes (mirrors link-refs.py used by the catalog tab):
#   Quran     {prefix}/quran.html      #s{surah}v{verse}
#   Bukhari   {prefix}/bukhari.html    #h{idInBook}
#   Muslim    {prefix}/muslim.html     #h{idInBook}
#   Abu Dawud {prefix}/abu-dawud.html  #h{idInBook}
#   Tirmidhi  {prefix}/tirmidhi.html   #h{idInBook}
#   Nasa'i    {prefix}/nasai.html      #h{idInBook}
#   Ibn Majah {prefix}/ibn-majah.html  #h{idInBook}
#
# `{prefix}` is the path-relative root of the read/ directory — depends on the
# depth of the page calling link_refs:
#   site/arguments/{slug}.html              -> "../read"
#   site/arguments/{slug}/{entry}.html      -> "../../read"
#
# It's set globally via set_path_prefix() before each render so that the
# helper functions below can stay simple.
# ============================================================

DASH = r"[-–—]"

_QURAN_RE = re.compile(rf"(?<![A-Za-z\d])Q\s+(?P<surah>\d+):(?P<verse>\d+)(?:{DASH}\d+)?")
_BARE_VERSE_RE = re.compile(rf"(?<![A-Za-z\d:.])(?P<surah>\d{{1,3}}):(?P<verse>\d{{1,3}})(?:{DASH}\d{{1,3}})?(?![A-Za-z\d:#])")
_BUKHARI_RE = re.compile(rf"(?<![A-Za-z])(?:S[aā]ḥīḥ\s+(?:al-)?|Sahih\s+(?:al-)?)?Bukh[aā]r[iī]\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_MUSLIM_RE = re.compile(rf"(?<![A-Za-z])(?:S[aā]ḥīḥ\s+|Sahih\s+)?Muslim\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_ABU_DAWUD_RE = re.compile(rf"(?<![A-Za-z])(?:Sunan\s+)?Ab[iuū]\s+D[aā]w[uū]d\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_TIRMIDHI_RE = re.compile(rf"(?<![A-Za-z])(?:J[aā]mi[ʿ'’`]?\s+(?:at-|al-)?)?(?:at-|al-)?Tirmidh[iī]\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_NASAI_RE = re.compile(rf"(?<![A-Za-z])(?:Sunan\s+(?:an-|al-)?)?Nas[aā][ʾ’‘'”]?[iī]\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_IBN_MAJAH_RE = re.compile(rf"(?<![A-Za-z])(?:Sunan\s+)?Ibn\s+M[aā]jah\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_CONTINUATION_RE = re.compile(rf"(\s*[,/]\s*)#?(\d+)(?:{DASH}#?\d+)?")
_ALREADY_LINKED_RE = re.compile(r"<a\s[^>]*>.*?</a>", re.DOTALL)

# Mutable path prefix used by the link-helpers below. Set by set_path_prefix()
# at the start of each render_* function based on the page's depth.
PATH_PREFIX = "../read"


def set_path_prefix(prefix: str) -> None:
    global PATH_PREFIX
    PATH_PREFIX = prefix


def _q_link(m: re.Match) -> str:
    surah = m.group("surah")
    verse = m.group("verse")
    return f'<a class="cite-link" href="{PATH_PREFIX}/quran.html#s{surah}v{verse}">{m.group(0)}</a>'


def _bare_verse_link(m: re.Match) -> str:
    surah = int(m.group("surah"))
    verse = int(m.group("verse"))
    if not (1 <= surah <= 114 and 1 <= verse <= 286):
        return m.group(0)
    return f'<a class="cite-link" href="{PATH_PREFIX}/quran.html#s{surah}v{verse}">{m.group(0)}</a>'


_HADITH_PATTERNS = [
    ("bukhari", _BUKHARI_RE),
    ("muslim", _MUSLIM_RE),
    ("abu-dawud", _ABU_DAWUD_RE),
    ("tirmidhi", _TIRMIDHI_RE),
    ("nasai", _NASAI_RE),
    ("ibn-majah", _IBN_MAJAH_RE),
]


def _protected_spans(s: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _ALREADY_LINKED_RE.finditer(s)]


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    for ps, pe in spans:
        if start < pe and end > ps:
            return True
    return False


def _apply_pattern(text: str, pattern: re.Pattern, repl_fn) -> str:
    spans = _protected_spans(text)
    out: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        if _overlaps(m.start(), m.end(), spans):
            continue
        out.append(text[last:m.start()])
        out.append(repl_fn(m))
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def _apply_with_continuations(text: str, pattern: re.Pattern, slug: str) -> str:
    spans = _protected_spans(text)
    out: list[str] = []
    last = 0
    pos = 0
    while pos < len(text):
        m = pattern.search(text, pos)
        if not m:
            break
        if _overlaps(m.start(), m.end(), spans):
            pos = m.end()
            continue
        out.append(text[last:m.start()])
        href = f'{PATH_PREFIX}/{slug}.html#h{m.group("num")}'
        out.append(f'<a class="cite-link" href="{href}">{m.group(0)}</a>')
        cursor = m.end()
        while True:
            cont = _CONTINUATION_RE.match(text, cursor)
            if not cont:
                break
            sep = cont.group(1)
            num = cont.group(2)
            full = cont.group(0)
            link_text = full[len(sep):]
            href = f'{PATH_PREFIX}/{slug}.html#h{num}'
            out.append(sep)
            out.append(f'<a class="cite-link" href="{href}">{link_text}</a>')
            cursor += len(full)
        last = cursor
        pos = cursor
    out.append(text[last:])
    return "".join(out)


def link_refs(escaped_text: str) -> str:
    if not escaped_text:
        return escaped_text
    text = escaped_text
    text = _apply_pattern(text, _QURAN_RE, _q_link)
    if "Q " in escaped_text or "Quran" in escaped_text:
        text = _apply_pattern(text, _BARE_VERSE_RE, _bare_verse_link)
    for slug, pat in _HADITH_PATTERNS:
        text = _apply_with_continuations(text, pat, slug)
    return text


def _esc_link(text: str) -> str:
    return link_refs(escape(text))


# (slug, json filename, display name, eyebrow, intro)
SOURCES = [
    (
        "quran",
        "quran.json",
        "The Qur'ān",
        "Primary source",
        "The strongest arguments against Islam drawn from the Qur'ān itself — starting with the Islamic Dilemma, then ranging across legal, moral, scientific, and historical problems in the text.",
    ),
    (
        "bukhari",
        "bukhari.json",
        "Ṣaḥīḥ al-Bukhārī",
        "Hadith · 6 Sunni canonical",
        "The strongest arguments drawn from Ṣaḥīḥ al-Bukhārī — the highest-rated Sunni hadith collection. Cases of child marriage, mass execution, prophetic-magic, lost Qurānic verses, and pre-modern cosmology preserved as canonical teaching.",
    ),
    (
        "muslim",
        "muslim.json",
        "Ṣaḥīḥ Muslim",
        "Hadith · 6 Sunni canonical",
        "The strongest arguments drawn from Ṣaḥīḥ Muslim — the second-highest Sunni collection. Mutʿa, captive sex, women in Hell, the Sunni-Shia split, and theological antisemitism preserved as canonical teaching.",
    ),
    (
        "abu-dawud",
        "abu-dawud.json",
        "Sunan Abī Dāwūd",
        "Hadith · 6 Sunni canonical",
        "The strongest arguments drawn from Sunan Abī Dāwūd — a foundational legal-genre Sunan. Awtas captives, blasphemy killings, jizya humiliation, vigilantism, and stoning preserved as operative law.",
    ),
    (
        "tirmidhi",
        "tirmidhi.json",
        "Jāmiʿ at-Tirmidhī",
        "Hadith · 6 Sunni canonical",
        "The strongest arguments drawn from Jāmiʿ at-Tirmidhī. Two pre-written books of paradise/fire, the Mahdi/Dajjal eschatology, monkey-stoning, anthropomorphism, and the predestination-effort paradox.",
    ),
    (
        "nasai",
        "nasai.json",
        "Sunan an-Nasā'ī",
        "Hadith · 6 Sunni canonical",
        "The strongest arguments drawn from Sunan an-Nasā'ī. Killing-a-kafir guarantees not sharing Hell with him, eclipses as signs, the 80-lash rule for wine, captive distribution as spoils, and the differential blood-money framework.",
    ),
    (
        "ibn-majah",
        "ibn-majah.json",
        "Sunan Ibn Mājah",
        "Hadith · 6 Sunni canonical",
        "The strongest arguments drawn from Sunan Ibn Mājah. Dead Ansari child may not be in Paradise, adult breastfeeding, marital-prostration framing, end-times Jew-killing, and the martyrdom-violence incentive structure.",
    ),
]


# ----------------- shared HTML pieces -----------------

NAV_LINKS = [
    ("index.html", "Home", False),
    ("catalog.html", "Catalog", False),
    ("arguments.html", "Dossiers", True),  # URL kept as arguments.html for stability
    ("read.html", "Read", False),
    ("compare.html", "Compare", False),
    ("build.html", "Build", False),
    ("stats.html", "Stats", False),
    ("about.html", "About", False),
    ("faq.html", "FAQ", False),
]


def render_nav(prefix: str) -> str:
    parts = []
    for filename, label, _ in NAV_LINKS:
        href = prefix + filename
        cls = ' class="active"' if filename == "arguments.html" else ""
        parts.append(f'      <a href="{href}"{cls}>{label}</a>')
    return "\n".join(parts)


def head_block(title: str, description: str, prefix: str, og_url_path: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{escape(description, quote=True)}">
<link rel="icon" type="image/png" sizes="32x32" href="{prefix}assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="{prefix}assets/icons/favicon-16.png">
<link rel="icon" href="{prefix}assets/icons/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="{prefix}assets/icons/apple-touch-icon.png">
<link rel="manifest" href="{prefix}assets/icons/site.webmanifest">
<meta name="theme-color" content="#0a0a0a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Analyzing Islam">
<meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="{escape(description, quote=True)}">
<meta property="og:url" content="https://analyzingislam.com/{og_url_path}">
<meta property="og:image" content="https://analyzingislam.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Analyzing Islam">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title, quote=True)}">
<meta name="twitter:description" content="{escape(description, quote=True)}">
<meta name="twitter:image" content="https://analyzingislam.com/assets/og-image.png">
<title>{escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/css/style.css">
<link rel="stylesheet" href="{prefix}assets/css/arguments.css">
</head>"""


def auth_scripts(prefix: str) -> str:
    return f"""<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="{prefix}assets/js/config.js"></script>
<script src="{prefix}assets/js/auth.js" defer></script>
<script src="{prefix}assets/js/auth-ui.js" defer></script>
<script src="{prefix}assets/js/goat.js" defer></script>
<script src="{prefix}assets/js/snap-to-hash.js" defer></script>"""


# ----------------- dossiers landing (arguments.html) -----------------

def render_landing() -> str:
    set_path_prefix("read")  # cite-links unused on this page; safe default

    cards = []
    for slug, _, name, eyebrow, intro in SOURCES:
        href = f"arguments/{slug}.html"
        cards.append(f"""    <a href="{href}" class="args-card">
      <div>
        <div class="args-eyebrow">{escape(eyebrow)}</div>
        <h2>{escape(name)}</h2>
        <p>{escape(intro)}</p>
      </div>
      <div class="args-meta">
        <span>20 arguments</span>
        <span class="args-arrow" aria-hidden="true">→</span>
      </div>
    </a>""")

    cards_html = "\n".join(cards)

    head = head_block(
        title="Dossiers — Analyzing Islam",
        description="Seven dossiers compiling 140 long-form arguments against Islam, drawn directly from the Qur'ān and the six canonical Sunni hadith collections. Each argument quotes the verse or hadith verbatim, fixes the historical context, states the premises and conclusion, then walks through the most common Muslim responses with a counter-response to each.",
        prefix="",
        og_url_path="arguments.html",
    )

    return f"""{head}
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
{render_nav("")}
    </div>
  </div>
</nav>

<main>
  <div id="args-shell" class="args-shell is-loading">

    <section class="args-hero">
      <h1>Dossiers</h1>
      <p>Seven dossiers — one for the Qur'ān and one for each of the six canonical Sunni hadith collections — compiling 140 long-form arguments against Islam directly from the source texts. Every argument quotes the verse or hadith verbatim, fixes the historical context, states the premises and conclusion, and walks through the most common Muslim responses with a counter-response to each. The cases are not summaries; they are evidence files built to be checked against the originals.</p>
    </section>

    <div class="args-grid">
{cards_html}
    </div>

  </div>

  <div id="args-gate-mount"></div>
</main>

<footer class="site-footer">
  Account-only content. Created for honest engagement with the source texts — not for harassment.
</footer>

{auth_scripts("")}
<script>
(function () {{
  "use strict";
  const shell = document.getElementById("args-shell");
  const mount = document.getElementById("args-gate-mount");

  function render() {{
    const sess = window.__session;
    if (!sess || !sess.user) {{
      shell.style.display = "none";
      mount.innerHTML =
        '<div class="args-gate">' +
        '<h2>Sign in to read</h2>' +
        '<p>The Dossiers library is available to account-holders only. ' +
        '<a href="login.html?return=arguments.html">Sign in</a> ' +
        'or <a href="signup.html">create an account</a> to continue.</p>' +
        '</div>';
      return;
    }}
    shell.style.display = "";
    shell.classList.remove("is-loading");
    mount.innerHTML = "";
  }}

  if (window.__authReady) {{
    window.__authReady.then(render);
  }} else {{
    render();
  }}
  window.addEventListener("auth-state", render);
}})();
</script>

</body>
</html>
"""


# ----------------- per-source case index (arguments/{slug}.html) -----------------

def render_source_index_items(entries: list[dict], slug: str) -> str:
    items = []
    for i, e in enumerate(entries, start=1):
        eid = e["id"]
        title = escape(e["title"])
        ref = escape(e["ref"])
        items.append(f"""    <a href="{slug}/{escape(eid, quote=True)}.html" class="args-index-card">
      <div class="args-index-num">{i:02d}</div>
      <div class="args-index-body">
        <div class="args-index-title">{title}</div>
        <div class="args-index-ref">{ref}</div>
      </div>
      <div class="args-index-arrow" aria-hidden="true">→</div>
    </a>""")
    return "\n".join(items)


def render_source_page(slug: str, name: str, intro: str, entries: list[dict]) -> str:
    set_path_prefix("../read")

    head = head_block(
        title=f"{name} — Dossiers — Analyzing Islam",
        description=intro,
        prefix="../",
        og_url_path=f"arguments/{slug}.html",
    )

    items_html = render_source_index_items(entries, slug)
    total = len(entries)

    return f"""{head}
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
{render_nav("../")}
    </div>
  </div>
</nav>

<main>
  <div id="args-shell" class="args-shell is-loading">
    <a href="../arguments.html" class="args-back-link">← All sources</a>

    <h1 class="args-source-title">{escape(name)}</h1>
    <p class="args-source-intro">{escape(intro)}</p>

    <div class="args-index-meta">{total} cases · click any case to read it</div>

    <div class="args-index">
{items_html}
    </div>
  </div>

  <div id="args-gate-mount"></div>
</main>

<footer class="site-footer">
  Account-only content. The texts cited above are quoted verbatim from the standard Muslim editions — verify before citing.
</footer>

{auth_scripts("../")}
<script>
(function () {{
  "use strict";
  const shell = document.getElementById("args-shell");
  const mount = document.getElementById("args-gate-mount");

  function render() {{
    const sess = window.__session;
    if (!sess || !sess.user) {{
      shell.style.display = "none";
      const returnHere = location.pathname.replace(/^\\//, "") + (location.hash || "");
      const returnEnc = encodeURIComponent(returnHere);
      mount.innerHTML =
        '<div class="args-gate">' +
        '<h2>Sign in to read</h2>' +
        '<p>The Dossiers library is available to account-holders only. ' +
        '<a href="../login.html?return=' + returnEnc + '">Sign in</a> ' +
        'or <a href="../signup.html">create an account</a> to continue.</p>' +
        '</div>';
      return;
    }}
    shell.style.display = "";
    shell.classList.remove("is-loading");
    mount.innerHTML = "";
  }}

  if (window.__authReady) {{
    window.__authReady.then(render);
  }} else {{
    render();
  }}
  window.addEventListener("auth-state", render);
}})();
</script>

</body>
</html>
"""


# ----------------- per-argument page (arguments/{slug}/{id}.html) -----------------

def render_premises(premises: list[str]) -> str:
    items = "\n".join(f"        <li>{_esc_link(p)}</li>" for p in premises)
    return f"""      <ol class="arg-premises">
{items}
      </ol>"""


def render_responses(responses: list[dict]) -> str:
    items = []
    for i, item in enumerate(responses, start=1):
        items.append(f"""        <div class="arg-response-item">
          <div class="arg-response-label">Common Muslim response · {i}</div>
          <p class="arg-response-text">{_esc_link(item.get('response', ''))}</p>
          <div class="arg-counter-label">Counter-response</div>
          <p class="arg-counter-text">{_esc_link(item.get('counter', ''))}</p>
        </div>""")
    body = "\n".join(items)
    return f"""      <div class="arg-responses">
{body}
      </div>"""


def render_sidebar_toc(entries: list[dict], active_eid: str) -> str:
    items = []
    for i, e in enumerate(entries, start=1):
        cls = ' class="active"' if e["id"] == active_eid else ""
        items.append(
            f'        <li><a href="{escape(e["id"], quote=True)}.html"{cls}><span class="args-toc-num">{i:02d}</span>{escape(e["title"])}</a></li>'
        )
    body = "\n".join(items)
    return f"""    <aside class="args-toc">
      <div class="args-toc-title">All 20 cases</div>
      <ul class="args-toc-list">
{body}
      </ul>
    </aside>"""


def render_argument_page(
    entry: dict,
    idx: int,
    total: int,
    slug: str,
    source_name: str,
    all_entries: list[dict],
    prev_entry: dict | None,
    next_entry: dict | None,
) -> str:
    set_path_prefix("../../read")

    eid = entry["id"]
    title = entry["title"]
    ref = entry["ref"]
    verse_text = entry["verse_text"]
    context = entry["context"]
    premises = entry.get("premises", [])
    conclusion = entry.get("conclusion", "")
    responses = entry.get("muslim_responses", [])

    context_paras = "\n".join(
        f"        <p>{_esc_link(p)}</p>" for p in context.split("\n\n") if p.strip()
    )
    conclusion_paras = "\n".join(
        f"        <p>{_esc_link(p)}</p>" for p in conclusion.split("\n\n") if p.strip()
    )

    if prev_entry is not None:
        prev_link = f'<a href="{escape(prev_entry["id"], quote=True)}.html" class="prev">← Previous argument</a>'
    else:
        prev_link = '<a class="prev disabled" aria-disabled="true">← Previous argument</a>'

    if next_entry is not None:
        next_link = f'<a href="{escape(next_entry["id"], quote=True)}.html" class="next">Next argument →</a>'
    else:
        next_link = '<a class="next disabled" aria-disabled="true">Next argument →</a>'

    head = head_block(
        title=f"{title} — {source_name} — Dossiers — Analyzing Islam",
        description=f"{title}. Argument {idx} of {total} from {source_name}.",
        prefix="../../",
        og_url_path=f"arguments/{slug}/{eid}.html",
    )

    sidebar = render_sidebar_toc(all_entries, eid)

    return f"""{head}
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
{render_nav("../../")}
    </div>
  </div>
</nav>

<main>
  <div id="args-shell" class="args-shell is-loading">
    <a href="../{slug}.html" class="args-back-link">← All cases · {escape(source_name)}</a>

    <div class="args-source-shell">
{sidebar}
      <div class="args-main">
        <article class="arg-article" data-arg-id="{escape(eid, quote=True)}">
          <div class="arg-header">
            <div>
              <div class="arg-num">Argument {idx} of {total} · {escape(source_name)}</div>
              <h2 class="arg-title">{escape(title)}</h2>
              <div class="arg-ref">{_esc_link(ref)}</div>
            </div>
            <button type="button" class="arg-share-btn" aria-label="Copy link to this dossier">
              <span class="arg-share-icon" aria-hidden="true">⤴</span>
              <span class="arg-share-text">Share</span>
            </button>
          </div>

          <div class="arg-section-label">The text</div>
          <div class="arg-verse-box">{_esc_link(verse_text)}</div>

          <div class="arg-section-label">Context</div>
          <div class="arg-context">
{context_paras}
          </div>

          <div class="arg-section-label">Premises</div>
{render_premises(premises)}

          <div class="arg-section-label">Conclusion</div>
          <div class="arg-conclusion-box">
{conclusion_paras}
          </div>

          <div class="arg-section-label">Common Muslim responses · with counter-responses</div>
{render_responses(responses)}

          <nav class="arg-pager">
            {prev_link}
            <a href="../{slug}.html" class="next" style="flex:0 1 auto;">All cases</a>
            {next_link}
          </nav>
        </article>
      </div>
    </div>
  </div>

  <div id="args-gate-mount"></div>
</main>

<footer class="site-footer">
  Account-only content. The texts cited above are quoted verbatim from the standard Muslim editions — verify before citing.
</footer>

{auth_scripts("../../")}
<script>
(function () {{
  "use strict";
  const shell = document.getElementById("args-shell");
  const mount = document.getElementById("args-gate-mount");
  let toastEl = null;
  let toastTimer = null;

  function showToast(msg) {{
    if (!toastEl) {{
      toastEl = document.createElement("div");
      toastEl.className = "arg-toast";
      document.body.appendChild(toastEl);
    }}
    toastEl.textContent = msg;
    requestAnimationFrame(function () {{
      toastEl.classList.add("is-visible");
    }});
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {{
      toastEl.classList.remove("is-visible");
    }}, 1800);
  }}

  function copyToClipboard(text) {{
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      return navigator.clipboard.writeText(text);
    }}
    return new Promise(function (resolve, reject) {{
      try {{
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        resolve();
      }} catch (e) {{
        reject(e);
      }}
    }});
  }}

  function wireShareButton() {{
    const btn = document.querySelector(".arg-share-btn");
    if (!btn || btn.dataset.shareWired) return;
    btn.dataset.shareWired = "1";
    btn.addEventListener("click", function (e) {{
      e.preventDefault();
      const url = window.location.origin + window.location.pathname;
      const labelEl = btn.querySelector(".arg-share-text");
      const original = labelEl.textContent;
      copyToClipboard(url).then(function () {{
        btn.classList.add("is-copied");
        labelEl.textContent = "Copied";
        showToast("Link copied: " + url);
        setTimeout(function () {{
          btn.classList.remove("is-copied");
          labelEl.textContent = original;
        }}, 1800);
      }}).catch(function () {{
        window.prompt("Copy this link:", url);
      }});
    }});
  }}

  function render() {{
    const sess = window.__session;
    if (!sess || !sess.user) {{
      shell.style.display = "none";
      const returnHere = location.pathname.replace(/^\\//, "") + (location.hash || "");
      const returnEnc = encodeURIComponent(returnHere);
      mount.innerHTML =
        '<div class="args-gate">' +
        '<h2>Sign in to read</h2>' +
        '<p>The Dossiers library is available to account-holders only. ' +
        '<a href="../../login.html?return=' + returnEnc + '">Sign in</a> ' +
        'or <a href="../../signup.html">create an account</a> to continue.</p>' +
        '</div>';
      return;
    }}
    shell.style.display = "";
    shell.classList.remove("is-loading");
    mount.innerHTML = "";
    wireShareButton();
  }}

  if (window.__authReady) {{
    window.__authReady.then(render);
  }} else {{
    render();
  }}
  window.addEventListener("auth-state", render);
}})();
</script>

</body>
</html>
"""


# ----------------- driver -----------------

# Allow only filename-safe characters in entry IDs used as URL slugs.
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_id(eid: str) -> str:
    cleaned = _SAFE_ID_RE.sub("-", eid).strip("-")
    return cleaned or "argument"


def main() -> None:
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Missing data dir: {DATA_DIR}")

    ARGS_DIR.mkdir(parents=True, exist_ok=True)

    for slug, fname, name, _eyebrow, intro in SOURCES:
        json_path = DATA_DIR / fname
        if not json_path.exists():
            print(f"  skip {slug}: no JSON at {json_path}")
            continue

        entries = json.loads(json_path.read_text(encoding="utf-8"))
        if len(entries) != 20:
            print(f"  warn {slug}: expected 20 entries, got {len(entries)}")

        # Normalise IDs once so source-page links and per-arg filenames agree.
        for e in entries:
            e["id"] = safe_id(e["id"])

        # 1. Per-source case index.
        index_html = render_source_page(slug, name, intro, entries)
        (ARGS_DIR / f"{slug}.html").write_text(index_html, encoding="utf-8")
        print(f"  wrote arguments/{slug}.html ({len(entries)} cases)")

        # 2. One page per argument under arguments/{slug}/{id}.html.
        slug_dir = ARGS_DIR / slug
        slug_dir.mkdir(parents=True, exist_ok=True)
        existing = {p.name for p in slug_dir.glob("*.html")}
        kept: set[str] = set()
        total = len(entries)
        for i, entry in enumerate(entries, start=1):
            prev_entry = entries[i - 2] if i > 1 else None
            next_entry = entries[i] if i < total else None
            html = render_argument_page(
                entry=entry,
                idx=i,
                total=total,
                slug=slug,
                source_name=name,
                all_entries=entries,
                prev_entry=prev_entry,
                next_entry=next_entry,
            )
            out = slug_dir / f"{entry['id']}.html"
            out.write_text(html, encoding="utf-8")
            kept.add(out.name)

        # Remove orphaned per-arg files (e.g. an entry was renamed/removed).
        for stale in existing - kept:
            try:
                (slug_dir / stale).unlink()
                print(f"  removed stale arguments/{slug}/{stale}")
            except OSError:
                pass

        print(f"  wrote {len(kept)} per-argument pages under arguments/{slug}/")

    # 3. Dossiers landing.
    landing_html = render_landing()
    (SITE_DIR / "arguments.html").write_text(landing_html, encoding="utf-8")
    print("  wrote arguments.html")

    print("Done.")


if __name__ == "__main__":
    main()

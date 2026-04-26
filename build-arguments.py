"""
Build the Dossiers tab — landing page + 7 source pages.

Reads JSON from arguments-data/ and writes static HTML pages into
site/arguments/ (per-source) and site/arguments.html (landing).
File paths still use "arguments" for URL stability; only the visible
tab/page label is "Dossiers".

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
#   Quran     ../read/quran.html      #s{surah}v{verse}
#   Bukhari   ../read/bukhari.html    #h{idInBook}
#   Muslim    ../read/muslim.html     #h{idInBook}
#   Abu Dawud ../read/abu-dawud.html  #h{idInBook}
#   Tirmidhi  ../read/tirmidhi.html   #h{idInBook}
#   Nasa'i    ../read/nasai.html      #h{idInBook}
#   Ibn Majah ../read/ibn-majah.html  #h{idInBook}
#
# For ranges ("4141-4146"), the whole range becomes one link to the first
# number — same convention link-refs.py uses on the catalog pages. For
# comma/slash lists ("Bukhari 5134, 5158, 3894"), each number is linked
# separately so the reader can jump to any of them.
# ============================================================

DASH = r"[-–—]"

# "Q 4:34" / "Q 4:11-12" — the explicit-Quran form used in our JSON.
_QURAN_RE = re.compile(rf"(?<![A-Za-z\d])Q\s+(?P<surah>\d+):(?P<verse>\d+)(?:{DASH}\d+)?")

# Bare "N:M" continuations after an explicit Q reference — only activated when
# the surrounding text already mentioned "Q ".
_BARE_VERSE_RE = re.compile(rf"(?<![A-Za-z\d:.])(?P<surah>\d{{1,3}}):(?P<verse>\d{{1,3}})(?:{DASH}\d{{1,3}})?(?![A-Za-z\d:#])")

# Hadith collection patterns. Each captures the source name plus the FIRST
# number; comma/slash continuations are handled by a follow-on pass on the
# numbers immediately after the matched anchor.
_BUKHARI_RE = re.compile(rf"(?<![A-Za-z])(?:S[aā]ḥīḥ\s+(?:al-)?|Sahih\s+(?:al-)?)?Bukh[aā]r[iī]\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_MUSLIM_RE = re.compile(rf"(?<![A-Za-z])(?:S[aā]ḥīḥ\s+|Sahih\s+)?Muslim\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_ABU_DAWUD_RE = re.compile(rf"(?<![A-Za-z])(?:Sunan\s+)?Ab[iuū]\s+D[aā]w[uū]d\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_TIRMIDHI_RE = re.compile(rf"(?<![A-Za-z])(?:J[aā]mi[ʿ'’`]?\s+(?:at-|al-)?)?(?:at-|al-)?Tirmidh[iī]\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_NASAI_RE = re.compile(rf"(?<![A-Za-z])(?:Sunan\s+(?:an-|al-)?)?Nas[aā][ʾ’‘'”]?[iī]\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")
_IBN_MAJAH_RE = re.compile(rf"(?<![A-Za-z])(?:Sunan\s+)?Ibn\s+M[aā]jah\s+#?(?P<num>\d+)(?:{DASH}#?\d+)?")

# After we've placed an anchor for (e.g.) "Bukhari 5134", look at the text
# that immediately follows. If it's a comma/slash separator followed by more
# numbers (e.g., ", 5158, 3894" or " / 3268"), link each of those numbers
# under the same source slug too.
_CONTINUATION_RE = re.compile(rf"(\s*[,/]\s*)#?(\d+)(?:{DASH}#?\d+)?")

# Already-linked tokens — protect them from being re-matched.
_ALREADY_LINKED_RE = re.compile(r"<a\s[^>]*>.*?</a>", re.DOTALL)

PATH_PREFIX = "../read"  # relative to site/arguments/{slug}.html


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


def _hadith_linker(slug: str):
    def fn(m: re.Match) -> str:
        return f'<a class="cite-link" href="{PATH_PREFIX}/{slug}.html#h{m.group("num")}">{m.group(0)}</a>'
    return fn


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
    """Run pattern.sub with overlap-protection against already-linked spans
    AND with continuation-linking: after each successful link, walk forward
    through ", N, N" / " / N" continuations and link them under the same slug
    (for hadith patterns only — handled by the slug captured via repl_fn)."""
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
    """For hadith sources only: link the primary 'Source N' and any trailing
    ', N, N' / ' / N' continuations to the same slug."""
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
        # Anchor the primary number.
        href = f'{PATH_PREFIX}/{slug}.html#h{m.group("num")}'
        out.append(f'<a class="cite-link" href="{href}">{m.group(0)}</a>')
        cursor = m.end()
        # Walk forward through "[, /] N(-N)?" continuations and link each.
        while True:
            cont = _CONTINUATION_RE.match(text, cursor)
            if not cont:
                break
            sep = cont.group(1)              # ", " / " / " / etc.
            num = cont.group(2)              # the first number — used for href
            full = cont.group(0)             # entire matched continuation
            link_text = full[len(sep):]      # everything after the separator
            href = f'{PATH_PREFIX}/{slug}.html#h{num}'
            out.append(sep)
            out.append(f'<a class="cite-link" href="{href}">{link_text}</a>')
            cursor += len(full)
        last = cursor
        pos = cursor
    out.append(text[last:])
    return "".join(out)


def link_refs(escaped_text: str) -> str:
    """Insert <a class='cite-link'> anchors over every reference token in the
    given (already-HTML-escaped) text. Safe to call on any of the rendered
    fields — verse_text, context, premises, conclusion, response/counter."""
    if not escaped_text:
        return escaped_text

    text = escaped_text

    # 1) Quran — explicit "Q N:M" first.
    text = _apply_pattern(text, _QURAN_RE, _q_link)

    # 2) Bare "N:M" — only meaningful when the original mentioned "Q ".
    if "Q " in escaped_text or "Quran" in escaped_text:
        text = _apply_pattern(text, _BARE_VERSE_RE, _bare_verse_link)

    # 3) Each hadith collection, with continuation linking for ", N, N" lists.
    for slug, pat in _HADITH_PATTERNS:
        text = _apply_with_continuations(text, pat, slug)

    return text

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
    ("read.html", "Read", False),
    ("arguments.html", "Dossiers", True),  # this is the new tab (URL kept as arguments.html for stability)
    ("compare.html", "Compare", False),
    ("build.html", "Build", False),
    ("stats.html", "Stats", False),
    ("about.html", "About", False),
    ("faq.html", "FAQ", False),
]


def render_nav(prefix: str, active_filename: str) -> str:
    parts = []
    for filename, label, _ in NAV_LINKS:
        href = prefix + filename
        cls = ' class="active"' if filename == active_filename else ""
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


# ----------------- landing page -----------------

def render_landing() -> str:
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
{render_nav("", "arguments.html")}
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


# ----------------- per-source page -----------------

def _esc_link(text: str) -> str:
    """Escape HTML, then insert ref-link anchors. Order matters: escape first
    so that quotation marks and angle brackets in the source text don't break
    the anchor tags we then add."""
    return link_refs(escape(text))


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


def render_article(entry: dict, idx: int, total: int, source_slug: str) -> str:
    eid = entry["id"]
    title = entry["title"]
    ref = entry["ref"]
    verse_text = entry["verse_text"]
    context = entry["context"]
    premises = entry.get("premises", [])
    conclusion = entry.get("conclusion", "")
    responses = entry.get("muslim_responses", [])

    # Context can have paragraph breaks separated by \n\n
    context_paras = "\n".join(
        f"        <p>{_esc_link(p)}</p>" for p in context.split("\n\n") if p.strip()
    )
    conclusion_paras = "\n".join(
        f"        <p>{_esc_link(p)}</p>" for p in conclusion.split("\n\n") if p.strip()
    )

    prev_link = ""
    next_link = ""
    if idx > 1:
        prev_id = f"#arg-{idx - 1:02d}"
        prev_link = f'<a href="{prev_id}" class="prev">← Previous argument</a>'
    else:
        prev_link = '<a class="prev disabled" aria-disabled="true">← Previous argument</a>'

    if idx < total:
        next_id = f"#arg-{idx + 1:02d}"
        next_link = f'<a href="{next_id}" class="next">Next argument →</a>'
    else:
        next_link = '<a class="next disabled" aria-disabled="true">Next argument →</a>'

    return f"""    <article class="arg-article" id="arg-{idx:02d}" data-arg-id="{escape(eid, quote=True)}">
      <div class="arg-header">
        <div>
          <div class="arg-num">Dossier {idx} of {total}</div>
          <h2 class="arg-title">{escape(title)}</h2>
          <div class="arg-ref">{_esc_link(ref)}</div>
        </div>
        <button type="button" class="arg-share-btn" data-share-target="arg-{idx:02d}" aria-label="Copy link to this dossier">
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
        <a href="#args-toc" class="next" style="flex:0 1 auto;">Back to top</a>
        {next_link}
      </nav>
    </article>"""


def render_toc(entries: list[dict]) -> str:
    items = []
    for i, e in enumerate(entries, start=1):
        items.append(
            f'        <li><a href="#arg-{i:02d}" data-toc-target="arg-{i:02d}"><span class="args-toc-num">{i:02d}</span>{escape(e["title"])}</a></li>'
        )
    body = "\n".join(items)
    return f"""    <aside class="args-toc" id="args-toc">
      <div class="args-toc-title">All 20 arguments</div>
      <ul class="args-toc-list">
{body}
      </ul>
    </aside>"""


def render_source_page(slug: str, name: str, intro: str, entries: list[dict]) -> str:
    head = head_block(
        title=f"{name} — Dossiers — Analyzing Islam",
        description=intro,
        prefix="../",
        og_url_path=f"arguments/{slug}.html",
    )

    articles = "\n".join(
        render_article(e, i, len(entries), slug) for i, e in enumerate(entries, start=1)
    )

    return f"""{head}
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="../index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
{render_nav("../", "arguments.html")}
    </div>
  </div>
</nav>

<main>
  <div id="args-shell" class="args-shell is-loading">
    <a href="../arguments.html" class="args-back-link">← All sources</a>

    <h1 class="args-source-title">{escape(name)}</h1>
    <p class="args-source-intro">{escape(intro)}</p>

    <div class="args-source-shell">
{render_toc(entries)}
      <div class="args-main">
{articles}
      </div>
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

  function buildShareUrl(targetId) {{
    return window.location.origin + window.location.pathname + "#" + targetId;
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

  function wireShareButtons() {{
    const buttons = document.querySelectorAll(".arg-share-btn");
    buttons.forEach(function (btn) {{
      if (btn.dataset.shareWired) return;
      btn.dataset.shareWired = "1";
      btn.addEventListener("click", function (e) {{
        e.preventDefault();
        const target = btn.getAttribute("data-share-target");
        const url = buildShareUrl(target);
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
    }});
  }}

  function render() {{
    const sess = window.__session;
    if (!sess || !sess.user) {{
      shell.style.display = "none";
      // Preserve the visited pathname + hash so a shared deep-link still
      // lands on the right dossier after the user signs in.
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

    wireShareButtons();

    // Highlight TOC entry that matches the visible article (basic
    // scrollspy: highlight the entry whose top is closest to viewport top).
    const articles = Array.from(document.querySelectorAll(".arg-article"));
    const tocLinks = Array.from(document.querySelectorAll(".args-toc-list a"));
    function spy() {{
      let activeIdx = 0;
      const scrollY = window.scrollY + 120;
      for (let i = 0; i < articles.length; i++) {{
        if (articles[i].offsetTop <= scrollY) activeIdx = i;
      }}
      tocLinks.forEach((a, i) => a.classList.toggle("active", i === activeIdx));
    }}
    window.addEventListener("scroll", spy, {{ passive: true }});
    spy();
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

def main() -> None:
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Missing data dir: {DATA_DIR}")

    ARGS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Write each source page.
    for slug, fname, name, _eyebrow, intro in SOURCES:
        json_path = DATA_DIR / fname
        if not json_path.exists():
            print(f"  skip {slug}: no JSON at {json_path}")
            continue
        entries = json.loads(json_path.read_text(encoding="utf-8"))
        if len(entries) != 20:
            print(f"  warn {slug}: expected 20 entries, got {len(entries)}")
        html = render_source_page(slug, name, intro, entries)
        out = ARGS_DIR / f"{slug}.html"
        out.write_text(html, encoding="utf-8")
        print(f"  wrote {out.relative_to(ROOT)} ({len(entries)} entries)")

    # 2. Write landing page.
    landing_html = render_landing()
    out_landing = SITE_DIR / "arguments.html"
    out_landing.write_text(landing_html, encoding="utf-8")
    print(f"  wrote {out_landing.relative_to(ROOT)}")

    print("Done.")


if __name__ == "__main__":
    main()

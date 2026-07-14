# Contact Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dark-themed Contact page whose form emails messages directly to analyzingislam2026@gmail.com, and surface a Contact tab in the header on every page.

**Architecture:** Static HTML page (`site/contact.html`) reusing the site's `.auth-form`/`.auth-field`/`.btn-primary` styles + a small page-specific style block. Form submits via FormSubmit.co's AJAX endpoint (no backend). Header propagated by the existing `sync-nav.py`.

**Tech Stack:** Static HTML/CSS/vanilla JS; FormSubmit.co AJAX; GitHub Pages deploy.

## Global Constraints
- Dark theme via existing tokens in `site/assets/css/style.css` (`--bg #000`, `--panel #000`, `--panel-2 #0a0a0a`, `--border #1e1e1e`, `--accent #7aa2f7`, `--text #f5f5f5`, `--text-muted #9a9a9a`, `--text-dim #5a5a5a`, `--radius 0`, `--radius-lg 2px`, `--serif`, `--sans`).
- Email target: `analyzingislam2026@gmail.com`. Endpoint: `https://formsubmit.co/ajax/analyzingislam2026@gmail.com`.
- Reason options: Entry inquiry, Dossier revision, Report an error / correction, Contribute an entry, Other.
- Header nav order (canonical): Home, Catalog, Dossiers, Read, Compare, Build, Watch, Stats, About, FAQ, **Contact**.
- Every page ships the identical nav; contact.html marks Contact `class="active"`.

---

### Task 1: Create `site/contact.html`

**Files:**
- Create: `site/contact.html`

**Interfaces:**
- Produces: a page whose `<div class="site-nav-links">` block is the canonical 11-item nav (Contact active), a `#contact-form`, and inline submit JS.

- [ ] **Step 1: Create the file** with the exact content below (head/nav/footer/scripts modeled on `faq.html`).

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Contact the Analyzing Islam project — report an error or correction, ask about an entry, suggest a dossier revision, or contribute a source.">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png">
<link rel="icon" href="/assets/icons/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/assets/icons/site.webmanifest">
<meta name="theme-color" content="#0a0a0a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Analyzing Islam">
<meta property="og:title" content="Contact — Analyzing Islam">
<meta property="og:description" content="Report an error, ask about an entry, suggest a dossier revision, or contribute a source.">
<meta property="og:url" content="https://analyzingislam.com/contact.html">
<meta property="og:image" content="https://analyzingislam.com/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Analyzing Islam — 1,524 entries across 31 categories">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Contact — Analyzing Islam">
<meta name="twitter:description" content="Report an error, ask about an entry, suggest a dossier revision, or contribute a source.">
<meta name="twitter:image" content="https://analyzingislam.com/assets/og-image.png">
<title>Contact — Analyzing Islam</title>
<link rel="stylesheet" href="assets/css/style.css">
<style>
  .contact-wrap { display:grid; grid-template-columns:1fr 1.1fr; gap:48px; margin-top:28px; align-items:start; }
  .contact-intro h1 { margin:0 0 18px; }
  .contact-intro p { color:var(--text-muted); line-height:1.7; margin:0 0 16px; }
  .contact-intro p:last-child { margin-bottom:0; }
  .contact-email { color:var(--accent); }
  .contact-card { border:1px solid var(--border); background:var(--panel-2); padding:28px; border-radius:var(--radius-lg); }
  .contact-card .auth-field select {
    appearance:none; -webkit-appearance:none; background:var(--panel); border:1px solid var(--border);
    border-radius:var(--radius); padding:12px 14px; color:var(--text); font-family:inherit; font-size:15px;
    transition:border-color .2s; cursor:pointer;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%239a9a9a' stroke-width='2'><path d='M6 9l6 6 6-6'/></svg>");
    background-repeat:no-repeat; background-position:right 14px center;
  }
  .contact-card .auth-field select:invalid { color:var(--text-dim); }
  .contact-card .auth-field input:focus,
  .contact-card .auth-field select:focus,
  .contact-card .auth-field textarea:focus { outline:none; border-color:var(--accent); }
  .contact-card .auth-field .optional { text-transform:none; letter-spacing:0; color:var(--text-dim); font-weight:400; }
  .contact-send { display:inline-flex; align-items:center; gap:10px; align-self:flex-start; }
  .contact-send svg { width:16px; height:16px; }
  .contact-status { font-size:14px; margin-top:-4px; }
  .contact-status.error { color:#ff8a8a; }
  .contact-status a { color:var(--accent); }
  .contact-success { border:1px solid var(--accent); background:rgba(122,162,247,.08); padding:24px; border-radius:var(--radius-lg); color:var(--text); line-height:1.6; }
  @media (max-width:720px){ .contact-wrap { grid-template-columns:1fr; gap:32px; } }
</style>
</head>
<body>

<nav class="site-nav">
  <div class="site-nav-inner">
    <a href="index.html" class="site-brand">Analyzing Islam</a>
    <div class="site-nav-links">
      <a href="index.html">Home</a>
      <a href="catalog.html">Catalog</a>
      <a href="arguments.html">Dossiers</a>
      <a href="read.html">Read</a>
      <a href="compare.html">Compare</a>
      <a href="build.html">Build</a>
      <a href="watch.html">Watch</a>
      <a href="stats.html">Stats</a>
      <a href="about.html">About</a>
      <a href="faq.html">FAQ</a>
      <a href="contact.html" class="active">Contact</a>
    </div>
  </div>
</nav>

<div class="container-narrow">
  <div class="contact-wrap">
    <div class="contact-intro">
      <h1>We&#x27;re here to help</h1>
      <p>Spotted an error in an entry, want a dossier revisited, or have a source worth adding? Send it here. Corrections, questions about a specific passage, and well-sourced contributions are all welcome — and every message reaches the project directly.</p>
      <p>Where you can, include the exact page you&#x27;re referring to. It makes the note far easier to act on.</p>
      <p>You can also email us any time at <a class="contact-email" href="mailto:analyzingislam2026@gmail.com">analyzingislam2026@gmail.com</a>.</p>
    </div>

    <div class="contact-card">
      <form id="contact-form" class="auth-form" novalidate>
        <div class="auth-field">
          <label for="cf-email">Your email</label>
          <input id="cf-email" name="email" type="email" required placeholder="you@example.com" autocomplete="email">
        </div>
        <div class="auth-field">
          <label for="cf-reason">Reason</label>
          <select id="cf-reason" name="reason" required>
            <option value="" disabled selected>Select a reason…</option>
            <option>Entry inquiry</option>
            <option>Dossier revision</option>
            <option>Report an error / correction</option>
            <option>Contribute an entry</option>
            <option>Other</option>
          </select>
        </div>
        <div class="auth-field">
          <label for="cf-url">Entry / dossier URL <span class="optional">(optional)</span></label>
          <input id="cf-url" name="page_url" type="url" placeholder="https://analyzingislam.com/…">
        </div>
        <div class="auth-field">
          <label for="cf-message">Message</label>
          <textarea id="cf-message" name="message" required rows="6" placeholder="Your message…"></textarea>
        </div>
        <input type="text" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0">
        <button type="submit" class="btn btn-primary contact-send" id="cf-submit">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M22 2 11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 2l-7 20-4-9-9-4 20-7Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>Send message</span>
        </button>
        <div class="contact-status" id="cf-status" role="status" aria-live="polite"></div>
      </form>
    </div>
  </div>
</div>

<footer class="site-footer">
  Built from the Saheeh International translation. Every entry references a specific verse — verify before citing.
</footer>

<script>
(function () {
  var form = document.getElementById('contact-form');
  var btn = document.getElementById('cf-submit');
  var statusEl = document.getElementById('cf-status');
  var ENDPOINT = 'https://formsubmit.co/ajax/analyzingislam2026@gmail.com';
  var MAILTO = '<a class="contact-email" href="mailto:analyzingislam2026@gmail.com">analyzingislam2026@gmail.com</a>';
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    statusEl.className = 'contact-status'; statusEl.textContent = '';
    if (!form.reportValidity()) return;
    var data = new FormData(form);
    data.append('_subject', 'Analyzing Islam contact — ' + (data.get('reason') || 'message'));
    data.append('_captcha', 'false');
    data.append('_template', 'table');
    var label = btn.querySelector('span'); var orig = label.textContent;
    btn.disabled = true; label.textContent = 'Sending…';
    try {
      var res = await fetch(ENDPOINT, { method: 'POST', body: data, headers: { 'Accept': 'application/json' } });
      if (!res.ok) throw new Error('bad status ' + res.status);
      form.innerHTML = '<div class="contact-success"><strong>Thanks — your message was sent.</strong><br>' +
        'We&#x27;ll reply to the email you gave. You can also reach us any time at ' + MAILTO + '.</div>';
    } catch (err) {
      btn.disabled = false; label.textContent = orig;
      statusEl.className = 'contact-status error';
      statusEl.innerHTML = 'Something went wrong sending your message. Please email us directly at ' + MAILTO + '.';
    }
  });
})();
</script>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2" defer></script>
<script src="assets/js/config.js"></script>
<script src="assets/js/auth.js" defer></script>
<script src="assets/js/auth-ui.js" defer></script>
<script src="assets/js/track.js" defer></script>
<script src="assets/js/goat-skins.js" defer></script>
<script src="assets/js/goat.js" defer></script>
<script src="assets/js/snap-to-hash.js" defer></script>
</body>
</html>
```

- [ ] **Step 2: Verify structure.**
Run: `cd "C:/Users/zande/Documents/AI Workspace/Analyzing Islam" && grep -c 'class="active">Contact' site/contact.html && grep -c 'formsubmit.co/ajax/analyzingislam2026@gmail.com' site/contact.html && grep -oE '<option[^>]*>[^<]+' site/contact.html | wc -l`
Expected: `1`, `1`, and `6` (placeholder + 5 reasons).

- [ ] **Step 3: Commit.**
```bash
git add site/contact.html && git commit -m "feat(contact): add contact page with FormSubmit.co form"
```

---

### Task 2: Add Contact (and restore Watch) to the header on every page

**Files:**
- Modify: `sync-nav.py` (the `NAV_LINKS` list)

**Interfaces:**
- Consumes: canonical nav order from Global Constraints.
- Produces: every `site/**.html` carries the 11-item nav with correct `../` prefixes.

- [ ] **Step 1: Update `NAV_LINKS`** in `sync-nav.py` to exactly:
```python
NAV_LINKS = [
    ("Home",     "index.html"),
    ("Catalog",  "catalog.html"),
    ("Dossiers", "arguments.html"),
    ("Read",     "read.html"),
    ("Compare",  "compare.html"),
    ("Build",    "build.html"),
    ("Watch",    "watch.html"),
    ("Stats",    "stats.html"),
    ("About",    "about.html"),
    ("FAQ",      "faq.html"),
    ("Contact",  "contact.html"),
]
```

- [ ] **Step 2: Dry-check current nav counts** before running, to know the baseline:
Run: `grep -rl 'site-nav-links' site --include=*.html | wc -l` (number of pages with a nav).

- [ ] **Step 3: Run the sync.**
Run: `python sync-nav.py`

- [ ] **Step 4: Verify every page now has 11 nav links and Contact is present.**
Run:
```bash
python - <<'PY'
import re,glob
bad=[]
for f in glob.glob('site/**/*.html',recursive=True):
    t=open(f,encoding='utf-8',errors='ignore').read()
    m=re.search(r'<div class="site-nav-links">(.*?)</div>',t,re.S)
    if not m: continue
    links=re.findall(r'<a\s+href="[^"]+"[^>]*>([^<]+)</a>',m.group(1))
    if 'Contact' not in links or 'Watch' not in links or len(links)!=11:
        bad.append((f,len(links)))
print('pages with wrong nav:',len(bad))
for f,n in bad[:20]: print(' ',n,f)
PY
```
Expected: `pages with wrong nav: 0`.

- [ ] **Step 5: Spot-check relative prefixes** on a deep page (dossier) and a category page:
Run: `grep -oE 'href="[^"]*contact.html"' site/arguments/bukhari/b01-aisha-age.html site/category/women.html`
Expected: `href="../../contact.html"` (dossier) and `href="../contact.html"` (category).

- [ ] **Step 6: Commit.**
```bash
git add sync-nav.py site && git commit -m "feat(nav): add Contact tab (and restore Watch) to header on all pages"
```

---

### Task 3: Sitemap, live-submit test, deploy

**Files:**
- Modify: `build-sitemap.py` if it enumerates a static page list (else re-run picks contact.html up automatically).

- [ ] **Step 1: Check how sitemap is built.**
Run: `grep -nE "contact|faq|about|top.?level|ROOT_PAGES|\.html" build-sitemap.py | head`
If there is an explicit top-level page list, add `contact.html` to it. Otherwise no edit needed.

- [ ] **Step 2: Rebuild the sitemap and confirm contact is present.**
Run: `python build-sitemap.py && grep -c 'contact.html' site/sitemap.xml`
Expected: `1`.

- [ ] **Step 3: Commit sitemap.**
```bash
git add build-sitemap.py site/sitemap.xml && git commit -m "chore(seo): add contact page to sitemap"
```

- [ ] **Step 4: Live-fire the FormSubmit endpoint once** to trigger the one-time activation email to the Gmail (so the owner can activate delivery):
Run:
```bash
python - <<'PY'
import requests
r=requests.post('https://formsubmit.co/ajax/analyzingislam2026@gmail.com',
  data={'email':'setup-test@analyzingislam.com','reason':'Other',
        'message':'Contact form setup/activation test from build.','_captcha':'false',
        '_subject':'Analyzing Islam contact — activation test'},
  headers={'Accept':'application/json'},timeout=30)
print(r.status_code, r.text[:200])
PY
```
Expected: HTTP 200 with JSON indicating success or that a confirmation email was sent. (Owner must click the confirmation link in the Gmail once.)

- [ ] **Step 5: Push and deploy.**
```bash
git push origin main
```
Then watch the Pages deploy to success (`gh run watch <id> --exit-status`).

- [ ] **Step 6: Verify live.**
Run: `python - <<'PY'` fetching `https://analyzingislam.com/contact.html` and asserting it contains `class="active">Contact`, the form, and the 11-item nav; and fetch `https://analyzingislam.com/faq.html` asserting it now contains a Contact link.
Expected: both true.

## Self-review notes
- Spec coverage: page (Task 1), nav-on-every-page + Watch fix (Task 2), sitemap + activation + deploy (Task 3). ✓
- Fields match spec: email, reason(5), optional url, message, honeypot, send. ✓
- Reason placeholder is a disabled selected option so `required` blocks empty submits. ✓
- Reuses `.auth-form`/`.auth-field`/`.btn-primary`; only adds select + layout + status styles. ✓

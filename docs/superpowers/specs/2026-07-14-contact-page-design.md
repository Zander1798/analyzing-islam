# Contact page — design spec (2026-07-14)

## Goal
Add a **Contact** page to the Analyzing Islam site with a working form that emails
messages directly to `analyzingislam2026@gmail.com`. Add a **Contact** tab to the
site header (immediately after FAQ) and ensure the identical header appears on
**every** page, including the new one.

## Constraints / context
- Static site hosted on GitHub Pages (no backend) → email delivery via a third-party
  form service (chosen: **FormSubmit.co**, no account needed).
- Dark theme, design tokens in `site/assets/css/style.css`: `--bg #000`, `--panel-2 #0a0a0a`,
  `--border #1e1e1e`, `--accent #7aa2f7`, `--text #f5f5f5`, `--text-muted #9a9a9a`,
  `--radius 0` / `--radius-lg 2px`, `--serif` (Didot) headings, `--sans` body.
- Header nav is duplicated per page; `sync-nav.py` propagates the canonical link list
  (handles `../` prefixes + `class="active"`). NOTE: `sync-nav.py`'s `NAV_LINKS` is
  currently stale — missing **Watch** — so it must be updated before running or it
  would strip Watch from pages.
- Email address is already public on the site (mailto in FAQ), so exposing it in the
  form action is not a new disclosure.

## Page: `site/contact.html`
Standard page chrome copied from an existing page (e.g. `faq.html`): same `<head>`
(favicons, OG/Twitter meta with Contact title/description/url), full `<nav class="site-nav">`
with Contact marked `class="active"`, `<footer class="site-footer">`, and the standard
script bundle (supabase, config.js, auth.js, auth-ui.js, track.js, goat-skins.js, goat.js,
snap-to-hash.js). Page-specific CSS lives in a `<style>` block like faq.html.

### Layout
Two-column inside a centered container (~`container`/920px), **stacking to one column on
mobile** (`@media (max-width: 720px)`):
- **Left column — invitation.** `<h1>` "We're here to help" (serif) + one short paragraph
  in the site's respectful, analytical voice: corrections, entry inquiries, dossier
  feedback, and source suggestions are welcome; include the exact page where possible;
  every message reaches the project directly. No salesy tone.
- **Right column — form card.** Panel with `--border`, subtle background, padding.

### Form fields (in order)
1. **Your email** — `<input type="email" name="email" required>`. FormSubmit auto-uses a
   field named `email` as reply-to, so replies go to the sender.
2. **Reason** — `<select name="reason" required>` with a disabled placeholder "Select a
   reason…" then: *Entry inquiry*, *Dossier revision*, *Report an error / correction*,
   *Contribute an entry*, *Other*.
3. **Entry / dossier URL (optional)** — `<input type="url" name="page_url">`, placeholder
   "https://analyzingislam.com/…". Helps people point at the exact page.
4. **Message** — `<textarea name="message" required rows="6">`.
5. **Send button** — accent background, dark text, paper-plane SVG icon + "Send message".
6. Hidden: honeypot `<input name="_honey" style="display:none">`; FormSubmit controls
   `_captcha=false`, `_template=table`. `_subject` is set dynamically by JS to
   `"Analyzing Islam contact — <reason>"`.

### Submission behaviour (AJAX, no reload)
- JS intercepts submit; runs native validation (`form.reportValidity()`); if invalid, stop.
- Set `_subject` from the reason; build `FormData`; disable the button and show "Sending…".
- `fetch('https://formsubmit.co/ajax/analyzingislam2026@gmail.com', { method:'POST',
  body: FormData, headers:{ Accept:'application/json' } })`.
- On success (`res.ok` / JSON `success`): hide the form, show an inline success panel
  ("Thanks — your message was sent. We'll reply to the email you gave."); reset form.
- On failure/network error: re-enable button, show an inline error with a mailto fallback
  link to `analyzingislam2026@gmail.com`.
- Status messages use an `aria-live="polite"` region; button restores its label on error.

### Accessibility
Every input has a `<label for>`; required fields marked; `type=email`/`type=url` for
native validation and mobile keyboards; status region announced via `aria-live`; button
focus/hover states use accent; colour contrast follows existing site inputs.

### Spam handling
Honeypot `_honey` (FormSubmit silently drops bots that fill it). Captcha disabled for a
smooth flow; can be re-enabled (`_captcha=true`) later if spam appears.

## Header propagation
1. Update `sync-nav.py` `NAV_LINKS` to the full current set **plus Watch and Contact**:
   Home, Catalog, Dossiers, Read, Compare, Build, Watch, Stats, About, FAQ, **Contact**.
2. Run `python sync-nav.py`; verify every page's `site-nav-links` now has 11 items and the
   correct relative-path prefix; spot-check a root page, a `category/` page, and a deep
   `arguments/<slug>/` page.
3. `contact.html` itself ships with the full nav and Contact active.

## Also
- Add `contact.html` to `build-sitemap.py`'s URL list (or re-run it) so it's indexed.
- One-time activation: first submission triggers a FormSubmit confirmation email to the
  Gmail; owner clicks it once to enable delivery. Implementer will send a test submission
  so the activation email arrives, and confirm the success/error UI both render.

## Out of scope
No Name/Phone fields (reference photo only, not requested). No CAPTCHA UI. No backend,
database, or auth gating (the page is public). No newsletter/marketing.

## Success criteria
- Contact tab visible in the header on every page and on contact.html (active).
- Form validates, submits via FormSubmit AJAX, shows inline success without reload, and a
  real email arrives at analyzingislam2026@gmail.com after activation.
- Page matches the dark design spec and is responsive (two-col → one-col on mobile).

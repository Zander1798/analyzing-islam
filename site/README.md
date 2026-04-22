# Islam Analyzed

A filterable, systematic catalog of philosophical issues in the Quran. 88 entries across 9 categories, rated by argument strength.

## Running locally

You don't need a server. Just open `index.html` in any modern browser:

- **Windows:** double-click `index.html`, or right-click → "Open with" → your browser
- **Mac:** double-click `index.html`
- **Linux:** `xdg-open index.html` in terminal

All pages, styles, and scripts work offline. The site is 100% static — no database, no backend.

## File structure

```
site/
├── index.html              Homepage (hero, stats, featured arguments)
├── catalog.html            Filterable catalog of all 88 entries
├── about.html              Methodology and principles
├── README.md               This file
└── assets/
    ├── css/
    │   └── style.css       Shared stylesheet
    └── js/
        └── app.js          Filter + search + URL-param logic
```

## How the catalog works

- **Filters** (category + strength) narrow the visible entries in real time.
- **Search box** matches any text — verse references, keywords, phrases.
- **URL parameters** capture the current filter state, so you can share a link:
  - `catalog.html?category=women` → all Women entries
  - `catalog.html?strength=strong` → all Strong entries
  - `catalog.html?category=jesus&strength=strong` → combined
  - `catalog.html?q=crucifixion` → search prefilled
- **Deep links** — each featured entry has a stable ID (e.g., `catalog.html#islamic-dilemma`). Hover over any entry in the catalog and click the `#` to copy a permalink.

---

## Deploying to the web (Option B)

Two easy free options. Both serve static files, both give you a real HTTPS URL you can share.

### Option B-1: GitHub Pages (recommended if you already use GitHub)

1. **Create a GitHub account** if you don't have one: https://github.com/signup
2. **Create a new repository.** Click the `+` icon top-right → "New repository". Name it anything (e.g., `quran-analysis`). Set it to **Public**. Leave everything else default. Click "Create repository".
3. **Upload the site folder.** On the new repo page, click "uploading an existing file". Drag the contents of your `site/` folder (the `index.html`, `catalog.html`, etc. — NOT the `site/` folder itself, its contents) into the upload area. Scroll down and click "Commit changes".
4. **Enable GitHub Pages.** In the repo, go to Settings → Pages (left sidebar). Under "Source", select "Deploy from a branch". Under "Branch", pick `main` and `/ (root)`. Click Save.
5. **Wait 1-2 minutes.** GitHub will give you a URL like `https://your-username.github.io/quran-analysis/`. That's your live site.

**To update the site later:** edit the files on GitHub directly, or reupload. GitHub Pages redeploys automatically on every commit.

### Option B-2: Netlify Drop (simplest — no account required to start)

1. **Go to:** https://app.netlify.com/drop
2. **Drag the `site/` folder** from your computer onto the page.
3. That's it. Netlify gives you an instant URL like `https://random-name-123.netlify.app/`.
4. Create a free account if you want to claim the site, customize the URL, or get HTTPS with a custom domain.

**To update:** drag the folder again (if you haven't claimed the site). If you have claimed it, connect a GitHub repo for auto-deploy or redrop manually.

### Option B-3: Cloudflare Pages (fast CDN, requires account)

1. Sign up at https://pages.cloudflare.com/
2. Click "Create a project" → "Direct upload"
3. Drag the `site/` folder
4. Get a URL like `https://your-project.pages.dev/`

---

## Customizing

### Change the site title or nav
Edit the `<title>` and `.site-brand` in each HTML file, and the `<meta name="description">` for search engines.

### Change colors
All colors are CSS variables defined at the top of `assets/css/style.css`:
```css
:root {
  --bg: #0b0d12;         /* page background */
  --accent: #7aa2f7;      /* link and highlight blue */
  --basic: #4caf50;       /* "Basic" strength green */
  --moderate: #ff9800;    /* "Moderate" strength orange */
  --strong: #e53935;      /* "Strong" strength red */
  ...
}
```
Change these once and the whole site updates.

### Add a new entry
Open `catalog.html` and find a good spot among the existing entries (they're loosely grouped by Quranic order). Copy the structure of an existing entry and add yours. Follow the data attributes:
- `data-category="women logic"` (space-separated, use any of: `abrogation disbelievers jesus women science prophet logic contradiction strange`)
- `data-strength="moderate"` (one of `basic moderate strong`)

After adding, the catalog will automatically:
- Include it in filters
- Include it in search
- Update the total count

### Add a permalink ID
If you want an entry to be deep-linkable from the homepage:
```html
<div class="entry" id="my-stable-slug" data-category="..." data-strength="...">
```
Then link to it with `catalog.html#my-stable-slug`.

---

## Custom domain (after deploying)

If you want something like `https://quran-analysis.com/` instead of `https://your-username.github.io/quran-analysis/`:

1. **Buy a domain** (Namecheap, Cloudflare Registrar, Porkbun — ~$10/year).
2. **Follow your host's custom-domain docs:**
   - GitHub Pages: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site
   - Netlify: https://docs.netlify.com/domains-https/custom-domains/
   - Cloudflare Pages: https://developers.cloudflare.com/pages/how-to/custom-branch-aliases/
3. **HTTPS is free** on all three hosts (they'll provision a Let's Encrypt certificate automatically).

---

## Source

All verse citations come from the **Saheeh International English translation** — the Saudi-sanctioned, mainstream Sunni Quran translation widely distributed as a reference edition. Using this specific translation removes the easy dismissal "that's a hostile translation" from apologetic responses.

## License and attribution

The content of the entries is original analysis. You may use, adapt, republish, and share freely. Attribution is appreciated but not required.

The Quranic text quoted in `blockquote` elements is from Saheeh International (1997, 2004 ABUL-QASIM PUBLISHING HOUSE / AL-MUNTADA AL-ISLAMI) and is quoted under fair use / fair dealing for the purposes of criticism and commentary.

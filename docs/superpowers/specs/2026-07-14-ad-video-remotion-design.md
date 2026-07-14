# Advertising video system (Remotion) — design spec (2026-07-14)

## Goal
Stand up an isolated, reusable **Remotion** video project in the repo and produce
one flagship 30-second advertising video ("The Question") for Analyzing Islam,
rendered at three aspect ratios (vertical 9:16, landscape 16:9, square 1:1),
music-only, on-brand, and factual (verbatim sourced quotes + citations).

## Constraints / context
- Node v22.17 / npm 10.9 present. Remotion needs no GPU.
- **Isolated sub-project** at `video/` with its own `package.json`. It must NOT
  touch the static site, its build, or the GitHub Pages deploy. (Add `video/node_modules`
  and `video/out` to `.gitignore`.)
- Brand tokens (from `site/assets/css/style.css`): bg `#000`, text `#f5f5f5`,
  muted `#9a9a9a`, dim `#5a5a5a`, accent `#7aa2f7`, border `#1e1e1e`.
- Fonts: **Playfair Display** (serif — closest Google font to the site's Didot) and
  **Inter** (sans), both via `@remotion/google-fonts` (self-fetched at build; no system
  fonts in headless render). Sharp corners (radius 0) to match the site.
- Assets to reuse (copy into `video/public/`): a goat GIF
  (`site/assets/images/goat-glorious.gif`), and the wordmark is set text ("Analyzing Islam").
- Stat copy: **1,524 entries across 31 categories** (matches the site/FAQ). CTA domain:
  **analyzingislam.com**.
- Tone/policy: critique the *text*, not people. Quotes are verbatim from the
  Muslim-sanctioned translations the site uses (Qur'an: Saheeh International; hadith:
  Darussalam), each shown with its exact citation. No commentary overlaid on the quotes,
  no slurs, no imagery of people — kinetic typography only. This keeps it defensible
  under ad-platform hate-speech policies (academic/critical framing).

## Architecture — `video/`
```
video/
  package.json            # remotion, @remotion/cli, @remotion/google-fonts, @remotion/gif, react
  tsconfig.json
  remotion.config.ts      # video config (overwrite, image format)
  public/
    goat.gif              # copied from site/assets/images/goat-glorious.gif
    music/ambient.mp3     # CC0 minimal/ambient track (added during build; see Music)
  src/
    index.ts              # registerRoot(Root)
    Root.tsx              # registers 3 compositions (Vertical/Landscape/Square)
    brand/
      theme.ts            # color tokens, font families, timing helpers
      fonts.ts            # loadFont() for Playfair Display + Inter
      Background.tsx      # black bg + subtle vignette/grain, optional accent hairline
      Wordmark.tsx        # "Analyzing Islam" in Playfair
      CategoryTag.tsx     # bordered uppercase pill (matches site tag chips)
      Goat.tsx            # <Gif> wrapper for goat.gif
      Kinetic.tsx         # word-by-word / line reveal helpers (spring+interpolate)
    scenes/
      SceneQuestion.tsx   # 0-5s
      SceneFraming.tsx    # 5-9s
      SceneQuotes.tsx     # 9-20s (3x SourcedQuote)
      SourcedQuote.tsx    # one quote: verbatim text + citation + category tag
      SceneValue.tsx      # 20-26s
      SceneCTA.tsx        # 26-30s
    ads/
      TheQuestion.tsx     # composes the scenes on a <Series>/<Sequence> timeline;
                          # reads useVideoConfig() to adapt layout to orientation
    data/
      quotes.ts           # the 3 verbatim quotes + citations + categories (verified)
```
- **One component, three sizes.** `TheQuestion` is layout-responsive: it reads
  `useVideoConfig()` `{width,height}` and switches between a vertical stack and a
  landscape/square balance (font sizes and paddings scale from the shorter edge).
  `Root.tsx` registers three `<Composition>`s (1080×1920, 1920×1080, 1080×1080), all
  `fps=30`, `durationInFrames=900`, `component={TheQuestion}`.
- Motion built from `useCurrentFrame`, `interpolate`, `spring`, `<Series>`, `<Sequence>`.

## The ad — scene-by-scene (30s = 900 frames @ 30fps)
1. **SceneQuestion (0–5s / f0–150).** Black. Centered Playfair line reveals word-by-word:
   *"Is the Qur'an what it claims to be?"* A blue (`#7aa2f7`) underline wipes under "claims"
   at ~f90. Gentle scale-in.
2. **SceneFraming (5–9s / f150–270).** Line 1 *"Don't take our word for it."* rises in;
   at ~f210 it dims and *"Or theirs."* snaps in beneath. Inter, letter-spaced, muted.
3. **SceneQuotes (9–20s / f270–600).** Three `SourcedQuote`s, ~110 frames each, cross-fading:
   - **Q 4:34** — verbatim advise/forsake/strike passage (Saheeh International) · tag WOMEN
   - **Bukhari 5134** — Aisha married at six / consummated at nine (Darussalam) · tag CHILD MARRIAGE
   - **Bukhari 6922** — "Whoever changes his religion, kill him" · tag APOSTASY
   Each: serif italic quote (auto-fit size), a thin rule, then `citation · translation` in
   small-caps Inter and a bordered `CategoryTag`. Quote text slides up + fades; citation
   stamps in a beat later. **Exact wording verified against the live catalog before render.**
4. **SceneValue (20–26s / f600–780).** Fast beats: *"1,524 documented problems."* (the number
   counts up) → *"Sourced. Rated. Filterable."* → a horizontal rush of `CategoryTag`s
   (Abrogation · Warfare · Science · Apostasy · Slavery · Contradiction · Prophetic Character)
   → *"Every claim cites a primary source you can open and read."*
5. **SceneCTA (26–30s / f780–900).** Goat trots in from the side; `Wordmark` "Analyzing Islam";
   **analyzingislam.com** underlined in accent; hold to end.

Music (see below) plays under the whole thing, ducking slightly is out of scope (single bed).

## Music
CC0 minimal/ambient track, no attribution required. During implementation I identify a
genuinely CC0 / public-domain track (candidate sources: Free Music Archive CC0 collection,
Pixabay royalty-free, or a public-domain piece), **confirm the exact file + license URL with
the owner before downloading** (downloading a file is a permissioned action), place it at
`video/public/music/ambient.mp3`, and wire it via `<Audio>`. Until then the ad renders silent.

## Rendering workflow
`video/package.json` scripts:
- `dev` → `remotion studio` (live preview/editor)
- `render:vertical`  → `remotion render TheQuestionVertical  out/analyzing-islam-9x16.mp4`
- `render:landscape` → `remotion render TheQuestionLandscape out/analyzing-islam-16x9.mp4`
- `render:square`    → `remotion render TheQuestionSquare     out/analyzing-islam-1x1.mp4`
- `render:all` → runs all three.
Output: H.264 MP4 in `video/out/` (git-ignored).

## Out of scope
- No AI text-to-video, no voiceover/TTS, no GPU.
- No changes to the website, its build, deploy, or nav.
- No auto-posting to social platforms.
- Not data-driven from the live catalog yet (quotes are hand-verified constants in `data/quotes.ts`);
  a future iteration could pull entries/stats programmatically.

## Success criteria
- `npm install` in `video/` succeeds; `remotion studio` previews the ad.
- All three compositions render to MP4 without missing fonts/assets.
- The vertical render looks on-brand (Playfair, black, blue accent, goat), the three quotes
  are verbatim and correctly cited, stats read "1,524", and the CTA shows analyzingislam.com.
- The site and its deploy are untouched; `video/node_modules` and `video/out` are git-ignored.

## Open items to resolve during build
1. Verify exact verbatim wording + reference numbers of the 3 quotes against the live catalog.
2. Pick + confirm the CC0 music track (source + license) before downloading it.

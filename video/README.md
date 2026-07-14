# Analyzing Islam — video

Isolated [Remotion](https://remotion.dev) project for advertising videos. Fully
separate from the website (its own `package.json`; nothing here touches `site/`
or the GitHub Pages deploy).

## Setup
```bash
cd video
npm install        # first time (also fetches Remotion's headless Chromium)
```

## Preview (live editor)
```bash
npm run dev        # opens Remotion Studio; scrub/inspect every scene
```

## Render
```bash
npm run render:vertical    # 1080x1920  -> out/analyzing-islam-9x16.mp4   (Shorts/TikTok/Reels)
npm run render:landscape   # 1920x1080  -> out/analyzing-islam-16x9.mp4   (YouTube/X)
npm run render:square      # 1080x1080  -> out/analyzing-islam-1x1.mp4    (feeds)
npm run render:all         # all three
```
Outputs land in `video/out/` (git-ignored).

## The flagship ad — "The Question" (30s)
Composition ids: `TheQuestionVertical` / `TheQuestionLandscape` / `TheQuestionSquare`
(all the same component at different sizes). Structure:

- `src/ads/TheQuestion.tsx` — the timeline (5 scenes on a `<Series>`).
- `src/scenes/*` — question · framing · sourced quotes · stats/value · CTA.
- `src/data/quotes.ts` — the 3 verbatim sourced quotes (edit here to change them).
- `src/brand/*` — reusable kit: colors/fonts (`theme.ts`), `Wordmark`, `CategoryTag`,
  `Goat`, kinetic-typography helpers, and `layout.ts` (responsive sizing off the short edge).

## Adding music
Drop an MP3 at `video/public/music/ambient.mp3`, then uncomment the `<Audio>` line
in `src/ads/TheQuestion.tsx` and re-render. Use a royalty-free / CC0 track (no
attribution) so the ad is safe to post anywhere.

## Making more ads
Reuse `src/brand/*` and add a new composition under `src/ads/`, registered in
`src/Root.tsx`. The brand kit keeps every video visually consistent with the site.

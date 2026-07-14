# Ad Video System (Remotion) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Isolated `video/` Remotion project + a 30s flagship ad ("The Question") rendered at 9:16, 16:9, 1:1.

**Architecture:** Standalone Node/React sub-project. One layout-responsive `TheQuestion` component registered as three sized compositions. Reusable brand-kit components. Verification is by `remotion studio` preview and `remotion render` output (no unit-test framework — video project).

**Tech Stack:** Remotion 4.x, React 18, TypeScript, `@remotion/google-fonts`, `@remotion/gif`.

## Global Constraints
- Sub-project lives at `video/`; NEVER touch `site/`, site build, or deploy.
- `video/node_modules` and `video/out` git-ignored.
- Colors: bg `#000`, text `#f5f5f5`, muted `#9a9a9a`, dim `#5a5a5a`, accent `#7aa2f7`, border `#1e1e1e`. Radius 0.
- Fonts: Playfair Display (serif), Inter (sans) via `@remotion/google-fonts`.
- fps 30, duration 900 frames (30s). Compositions: Vertical 1080×1920, Landscape 1920×1080, Square 1080×1080.
- Copy: stat "1,524", domain "analyzingislam.com". Quotes verbatim + cited, verified from the live catalog. Tone: text-critique only, kinetic typography, no people imagery.

---

### Task 1: Scaffold isolated Remotion project + render smoke test

**Files:** Create `video/package.json`, `video/tsconfig.json`, `video/remotion.config.ts`, `video/src/index.ts`, `video/src/Root.tsx`; modify root `.gitignore`.

- [ ] **Step 1:** Create `video/package.json`:
```json
{
  "name": "analyzing-islam-video",
  "private": true,
  "version": "1.0.0",
  "scripts": {
    "dev": "remotion studio",
    "render:vertical": "remotion render TheQuestionVertical out/analyzing-islam-9x16.mp4",
    "render:landscape": "remotion render TheQuestionLandscape out/analyzing-islam-16x9.mp4",
    "render:square": "remotion render TheQuestionSquare out/analyzing-islam-1x1.mp4",
    "render:all": "npm run render:vertical && npm run render:landscape && npm run render:square"
  },
  "dependencies": {
    "@remotion/cli": "4.0.*",
    "@remotion/google-fonts": "4.0.*",
    "@remotion/gif": "4.0.*",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "remotion": "4.0.*"
  },
  "devDependencies": { "@types/react": "18.3.*", "typescript": "5.5.*" }
}
```
- [ ] **Step 2:** Create `video/tsconfig.json` (standard Remotion): `{"compilerOptions":{"target":"ES2020","module":"ESNext","jsx":"react-jsx","strict":true,"esModuleInterop":true,"moduleResolution":"bundler","skipLibCheck":true,"lib":["ES2020","DOM"]},"include":["src"]}`
- [ ] **Step 3:** Create `video/remotion.config.ts`:
```ts
import { Config } from "@remotion/cli/config";
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```
- [ ] **Step 4:** Create `video/src/index.ts`: `import { registerRoot } from "remotion"; import { Root } from "./Root"; registerRoot(Root);`
- [ ] **Step 5:** Create `video/src/Root.tsx` with a placeholder composition (temporary) to smoke-test:
```tsx
import { Composition, AbsoluteFill } from "remotion";
const Hello: React.FC = () => (<AbsoluteFill style={{background:"#000",color:"#f5f5f5",justifyContent:"center",alignItems:"center",fontSize:80}}>ok</AbsoluteFill>);
export const Root: React.FC = () => (
  <Composition id="Smoke" component={Hello} durationInFrames={30} fps={30} width={1080} height={1920} />
);
```
- [ ] **Step 6:** Add to root `.gitignore`: `video/node_modules/` and `video/out/`.
- [ ] **Step 7:** Install: `cd video && npm install` (expect success; Remotion pulls a Chromium).
- [ ] **Step 8:** Smoke render: `cd video && npx remotion render Smoke out/smoke.mp4 --frames=0-5`. Expect `out/smoke.mp4` created. Delete it after.
- [ ] **Step 9:** Commit: `git add video/package.json video/tsconfig.json video/remotion.config.ts video/src .gitignore && git commit -m "chore(video): scaffold isolated Remotion project"`

---

### Task 2: Brand kit (theme, fonts, primitives, goat asset)

**Files:** Create `video/src/brand/{theme.ts,fonts.ts,Background.tsx,Wordmark.tsx,CategoryTag.tsx,Goat.tsx,Kinetic.tsx}`; copy goat gif to `video/public/goat.gif`.

**Interfaces (Produces):**
- `theme.ts` exports `COLORS` (`bg,text,muted,dim,accent,border`) and `FONTS` `{serif, sans}` (family-name strings, populated after `fonts.ts` load).
- `fonts.ts` exports `loadFonts(): void` (idempotent) that calls `@remotion/google-fonts` loaders for Playfair Display + Inter and sets `FONTS.serif/sans`.
- `Kinetic.tsx` exports `Reveal({children, delay, from})` and `WordReveal({text, startFrame, stagger, style})`.
- `CategoryTag.tsx` exports `CategoryTag({label, style?})`.
- `Goat.tsx` exports `Goat({height})` wrapping `@remotion/gif` `<Gif src={staticFile("goat.gif")}/>`.
- `Wordmark.tsx` exports `Wordmark({size})`.
- `Background.tsx` exports `Background({children})` (black fill + faint radial vignette).

- [ ] **Step 1:** Copy asset: `cp "site/assets/images/goat-glorious.gif" video/public/goat.gif` (create `video/public/` first).
- [ ] **Step 2:** Write `theme.ts` + `fonts.ts`. fonts.ts pattern:
```ts
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { FONTS } from "./theme";
let done = false;
export function loadFonts() {
  if (done) return; done = true;
  FONTS.serif = loadPlayfair().fontFamily;
  FONTS.sans = loadInter().fontFamily;
}
```
- [ ] **Step 3:** Write the primitives (`Background`, `Wordmark`, `CategoryTag`, `Goat`, `Kinetic`) using `useCurrentFrame`, `interpolate`, `spring`, `staticFile`, `AbsoluteFill`. CategoryTag = uppercase Inter, 0.2em tracking, 1px `border`, transparent bg, small padding, sharp corners.
- [ ] **Step 4:** Temporarily add a `BrandTest` composition to `Root.tsx` that renders Background + Wordmark + a CategoryTag row + Goat, and `loadFonts()` at module top.
- [ ] **Step 5:** Verify in studio: `cd video && npm run dev`, open `BrandTest`, confirm Playfair wordmark, tag chips, goat animate. (Or render a still: `npx remotion still BrandTest out/brand.png --frame=20` and open it.)
- [ ] **Step 6:** Commit: `git add video/src/brand video/public && git commit -m "feat(video): brand kit (fonts, colors, wordmark, category tag, goat)"`

---

### Task 3: Verify + encode the three sourced quotes

**Files:** Create `video/src/data/quotes.ts`.

- [ ] **Step 1:** Pull exact verbatim wording + reference numbers from the live catalog for: Q 4:34 (Women), Bukhari 5134 (Child marriage), Bukhari 6922 (Apostasy). Use the site readers / catalog data:
  `grep`/read `site/read/quran.html` for 4:34 and `site/read/bukhari.html` (or the entries data in `../Analyzing Islam Books/data/`) for the two hadith. Confirm the citation numbers render correctly on the site.
- [ ] **Step 2:** Write `quotes.ts`:
```ts
export interface Quote { text: string; citation: string; translation: string; category: string; }
export const QUOTES: Quote[] = [
  { text: "…", citation: "Qur'an 4:34", translation: "Saheeh International", category: "Women" },
  { text: "…", citation: "Sahih al-Bukhari 5134", translation: "Darussalam", category: "Child Marriage" },
  { text: "Whoever changes his religion, kill him.", citation: "Sahih al-Bukhari 6922", translation: "Darussalam", category: "Apostasy" },
];
```
  (Fill `…` with the verified verbatim text. Keep each ≤ ~240 chars so it fits; if a passage is long, use the exact salient clause with an ellipsis that the site itself uses.)
- [ ] **Step 3:** Commit: `git add video/src/data && git commit -m "feat(video): verified sourced quotes for the ad"`

---

### Task 4: Scenes

**Files:** Create `video/src/scenes/{SceneQuestion.tsx,SceneFraming.tsx,SourcedQuote.tsx,SceneQuotes.tsx,SceneValue.tsx,SceneCTA.tsx}`.

**Interfaces:** each scene is `React.FC` sized to fill its parent `<Sequence>`; reads `useVideoConfig()` for responsive font sizing (base = `Math.min(width,height)`). `SourcedQuote` takes `{quote: Quote}`. `SceneQuotes` renders 3 `<Series.Sequence>` of `SourcedQuote`.

- [ ] **Step 1:** Implement each scene per the storyboard timings (spec §"The ad"). Use `spring({frame,fps})` for entrances, `interpolate` for fades/underline wipe, `<Series>` inside `SceneQuotes`. `SceneValue` number counts 0→1524 via `interpolate` + `Math.round` with `toLocaleString()`. Category rush = row of `CategoryTag` translated by `interpolate(frame,...)`.
- [ ] **Step 2:** Add each scene temporarily to `Root.tsx` as its own composition (or preview within TheQuestion in Task 5) and eyeball in studio; adjust sizing so nothing clips at 1080×1920.
- [ ] **Step 3:** Commit: `git add video/src/scenes && git commit -m "feat(video): ad scenes (question, framing, quotes, value, CTA)"`

---

### Task 5: Compose the ad + register 3 compositions + render

**Files:** Create `video/src/ads/TheQuestion.tsx`; rewrite `video/src/Root.tsx` (remove smoke/test comps).

- [ ] **Step 1:** `TheQuestion.tsx`: `loadFonts()` at import; `<Background>` wrapping a `<Series>` with the five scenes at frame offsets 0/150/270/600/780 (durations 150/120/330/180/120). Responsive: read `useVideoConfig()`; pass an `orientation` (`width<height?"portrait":width>height?"landscape":"square"`) to scenes that need different stacking.
- [ ] **Step 2:** `Root.tsx` registers three compositions all `component={TheQuestion}`, `durationInFrames={900}`, `fps={30}`:
  `TheQuestionVertical` 1080×1920, `TheQuestionLandscape` 1920×1080, `TheQuestionSquare` 1080×1080.
- [ ] **Step 3:** Preview each in studio (`npm run dev`); confirm no clipping/overflow in any ratio; tweak the responsive sizing.
- [ ] **Step 4:** Render all: `cd video && npm run render:all`. Expect three MP4s in `video/out/`. Open the vertical one and visually verify: Playfair, black+blue, 3 correct quotes, "1,524", goat, analyzingislam.com.
- [ ] **Step 5:** Commit: `git add video/src && git commit -m "feat(video): compose 'The Question' ad, register 9x16/16x9/1x1 renders"`

---

### Task 6: Music (CC0) — requires owner confirmation

**Files:** Add `video/public/music/ambient.mp3`; modify `TheQuestion.tsx` (add `<Audio>`).

- [ ] **Step 1:** Identify a genuinely CC0 / public-domain minimal-ambient track; present the exact source URL + license to the owner and get explicit OK to download (downloading is a permissioned action).
- [ ] **Step 2:** On approval, download to `video/public/music/ambient.mp3`.
- [ ] **Step 3:** In `TheQuestion.tsx` add `<Audio src={staticFile("music/ambient.mp3")} volume={0.6} />` inside the root, trimmed/faded to 30s (`interpolate` volume fade in first ~15f, out last ~30f).
- [ ] **Step 4:** Re-render all three; verify audio present and within length.
- [ ] **Step 5:** Commit: `git add video/public/music video/src/ads/TheQuestion.tsx && git commit -m "feat(video): add CC0 ambient music bed"`

## Self-review notes
- Spec coverage: scaffold (T1), brand kit (T2), quotes (T3), scenes (T4), compose+render 3 ratios (T5), music (T6). ✓
- Isolation: `.gitignore` for node_modules/out; no site files touched. ✓
- Verification is render/preview based (no test framework) — appropriate for a video project. ✓
- Remotion `4.0.*` pinned; fonts self-fetched (no system-font dependency). ✓

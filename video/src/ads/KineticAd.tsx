import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { loadFonts } from "../brand/fonts";
import { FONTS } from "../brand/theme";
import { EASE } from "../brand/motion";
import { useLayout } from "../brand/layout";
import { Goat } from "../brand/Goat";

loadFonts();
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const ACCENT = "#3b6ef5";
const INK = "#0d0d10";
const MUTED = "#5a5a63";

/* ---------- Clean light stage (Envato look — no dark bg, no colored glow) ---------- */
const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: "#eeeef1", overflow: "hidden" }}>
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 32%, #f7f7f9 0%, #e4e4e9 100%)" }} />
    {children}
    <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(255,255,255,0.35), transparent 22%, transparent 80%, rgba(0,0,0,0.06))" }} />
  </AbsoluteFill>
);

/* ---------- Dark site screenshot in browser chrome, 3D-tiltable (2880x1800) ---------- */
const BrowserCard: React.FC<{ src: string; w: number; rotY?: number; rotX?: number; url?: string }> = ({
  src,
  w,
  rotY = 0,
  rotX = 0,
  url = "analyzingislam.com",
}) => {
  const { u } = useLayout();
  const h = w * (1800 / 2880);
  const bar = u(46);
  const dot = u(11);
  return (
    <div
      style={{
        width: w,
        transform: `rotateY(${rotY}deg) rotateX(${rotX}deg)`,
        transformStyle: "preserve-3d",
        borderRadius: u(20),
        overflow: "hidden",
        boxShadow: `0 ${u(34)}px ${u(80)}px rgba(20,20,40,0.28), 0 ${u(6)}px ${u(18)}px rgba(20,20,40,0.18)`,
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <div style={{ height: bar, background: "#161619", display: "flex", alignItems: "center", paddingLeft: u(22), gap: u(9) }}>
        <span style={{ width: dot, height: dot, borderRadius: dot, background: "#ff5f57" }} />
        <span style={{ width: dot, height: dot, borderRadius: dot, background: "#febc2e" }} />
        <span style={{ width: dot, height: dot, borderRadius: dot, background: "#28c840" }} />
        <div style={{ marginLeft: u(20), height: bar * 0.5, flex: 1, marginRight: u(22), background: "#0c0c0e", borderRadius: bar, display: "flex", alignItems: "center", paddingLeft: u(18) }}>
          <span style={{ fontFamily: FONTS.sans, fontSize: u(17), color: "#8a8a92" }}>{url}</span>
        </div>
      </div>
      <Img src={staticFile(src)} style={{ width: w, height: h, display: "block", objectFit: "cover" }} />
    </div>
  );
};

/* ---------- Bold kinetic word-stack headline ---------- */
const Headline: React.FC<{ lines: React.ReactNode[]; at: number; size: number; top: number; color?: string }> = ({ lines, at, size, top, color = INK }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u, width } = useLayout();
  return (
    <div style={{ position: "absolute", top, left: 0, width, textAlign: "center", padding: `0 ${u(70)}px` }}>
      {lines.map((ln, i) => {
        const p = spring({ frame: frame - at - i * 5, fps, config: { damping: 200 } });
        return (
          <div key={i} style={{ fontFamily: FONTS.sans, fontWeight: 800, fontSize: size, lineHeight: 1.02, letterSpacing: "-0.03em", color, opacity: p, transform: `translateY(${(1 - p) * u(34)}px)` }}>
            {ln}
          </div>
        );
      })}
    </div>
  );
};

/* ---------- Windows flying into a 3D constellation + kinetic type ---------- */
type Win = { src: string; w: number; x: number; y: number; z: number; url: string };
const WindowBeat: React.FC<{
  wins: Win[];
  rotY?: number;
  head: React.ReactNode[];
  headSize: number;
  headTop: number;
  sub?: React.ReactNode[];
  subSize?: number;
  subTop?: number;
}> = ({ wins, rotY = -20, head, headSize, headTop, sub, subSize, subTop }) => {
  const frame = useCurrentFrame();
  const { u, height } = useLayout();
  const floatY = Math.sin(frame / 55) * u(9);
  const driftRot = interpolate(frame, [0, 300], [rotY - 3, rotY + 3], clamp);
  return (
    <Stage>
      <AbsoluteFill style={{ perspective: u(2100) }}>
        {wins.map((w, i) => {
          const p = spring({ frame: frame - i * 7, fps: 60, config: { damping: 200 } });
          const fromX = w.x >= 0 ? u(180) : -u(180);
          const inX = (1 - p) * fromX;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: `translate(-50%,-50%) translate(${w.x + inX}px, ${w.y + floatY}px) translateZ(${w.z}px) scale(${0.9 + p * 0.1})`,
                opacity: p,
              }}
            >
              <BrowserCard src={w.src} w={w.w} rotY={driftRot} rotX={5} url={w.url} />
            </div>
          );
        })}
      </AbsoluteFill>
      <Headline lines={head} at={6} size={headSize} top={headTop} />
      {sub && <Headline lines={sub} at={20} size={subSize ?? u(34)} top={subTop ?? height * 0.86} />}
    </Stage>
  );
};

/* ---------- Hook: typewriter question (iBanPay technique) ---------- */
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, width, height } = useLayout();
  const text = "What does Islam actually teach?";
  const n = Math.max(0, Math.floor((frame - 8) / 1.6));
  const shown = text.slice(0, n);
  const done = n >= text.length;
  const blink = Math.floor(frame / 16) % 2 === 0;
  const answer = spring({ frame: frame - 130, fps: 60, config: { damping: 200 } });
  return (
    <Stage>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: `0 ${u(80)}px` }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontFamily: FONTS.sans, fontWeight: 800, fontSize: u(88), letterSpacing: "-0.03em", color: INK, lineHeight: 1.05 }}>
            {shown}
            <span style={{ color: ACCENT, opacity: done ? (blink ? 1 : 0) : 1 }}>|</span>
          </div>
          <div style={{ marginTop: u(40), fontFamily: FONTS.sans, fontWeight: 700, fontSize: u(44), color: MUTED, opacity: answer, transform: `translateY(${(1 - answer) * u(24)}px)` }}>
            Find out — <span style={{ color: ACCENT }}>from the sources themselves.</span>
          </div>
        </div>
      </AbsoluteFill>
    </Stage>
  );
};

/* ---------- CTA ---------- */
const CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, height } = useLayout();
  const a = spring({ frame: frame - 4, fps: 60, config: { damping: 200 } });
  const b = spring({ frame: frame - 20, fps: 60, config: { damping: 200 } });
  const c = spring({ frame: frame - 40, fps: 60, config: { damping: 200 } });
  return (
    <Stage>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ opacity: a, transform: `translateY(${(1 - a) * u(20)}px)` }}>
          <Goat height={u(230)} />
        </div>
        <div style={{ fontFamily: FONTS.serif, fontWeight: 700, fontSize: u(96), color: INK, marginTop: u(10), opacity: b, transform: `translateY(${(1 - b) * u(24)}px)` }}>
          Analyzing Islam
        </div>
        <div style={{ fontFamily: FONTS.sans, fontWeight: 700, fontSize: u(40), color: MUTED, marginTop: u(18), opacity: b }}>
          Read every source. <span style={{ color: INK }}>Decide for yourself.</span>
        </div>
        <div style={{ marginTop: u(46), fontFamily: FONTS.sans, fontWeight: 800, fontSize: u(46), color: "#fff", background: ACCENT, padding: `${u(20)}px ${u(46)}px`, borderRadius: u(14), opacity: c, transform: `scale(${0.9 + c * 0.1})` }}>
          analyzingislam.com
        </div>
      </AbsoluteFill>
    </Stage>
  );
};

/* ---------- Full ad ---------- */
const T = (dir: "from-left" | "from-right" | "from-bottom") => (
  <TransitionSeries.Transition presentation={slide({ direction: dir })} timing={linearTiming({ durationInFrames: 18 })} />
);

export const KineticAd: React.FC = () => {
  const { u, width, height } = useLayout();
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={220}>
        <Hook />
      </TransitionSeries.Sequence>
      {T("from-bottom")}

      {/* Catalog — the approved trio cascade */}
      <TransitionSeries.Sequence durationInFrames={300}>
        <WindowBeat
          head={[<>Every problem.</>, <span style={{ color: ACCENT }}>Sourced &amp; rated.</span>]}
          headSize={u(92)}
          headTop={height * 0.09}
          sub={[<><b style={{ fontWeight: 800 }}>1,524</b> entries · every claim cited to the source</>]}
          wins={[
            { src: "site/build.png", w: width * 0.56, x: -u(250), y: -u(300), z: -420, url: "analyzingislam.com/build" },
            { src: "site/reader.png", w: width * 0.58, x: u(300), y: u(340), z: -300, url: "analyzingislam.com/read" },
            { src: "site/catalog.png", w: width * 0.72, x: 0, y: u(40), z: 0, url: "analyzingislam.com/catalog" },
          ]}
        />
      </TransitionSeries.Sequence>
      {T("from-right")}

      {/* Reader */}
      <TransitionSeries.Sequence durationInFrames={260}>
        <WindowBeat
          rotY={-16}
          head={[<>Read the primary source</>, <span style={{ color: ACCENT }}>in full.</span>]}
          headSize={u(80)}
          headTop={height * 0.1}
          sub={[<>Qur'an, hadith, Tanakh, New Testament — the real text</>]}
          wins={[{ src: "site/reader.png", w: width * 0.98, x: 0, y: u(120), z: 0, url: "analyzingislam.com/read/quran/4" }]}
        />
      </TransitionSeries.Sequence>
      {T("from-right")}

      {/* Compare */}
      <TransitionSeries.Sequence durationInFrames={260}>
        <WindowBeat
          rotY={-16}
          head={[<>Every translation,</>, <span style={{ color: ACCENT }}>side by side.</span>]}
          headSize={u(80)}
          headTop={height * 0.1}
          sub={[<>Compare how the sources actually render each verse</>]}
          wins={[{ src: "site/compare.png", w: width * 0.98, x: 0, y: u(120), z: 0, url: "analyzingislam.com/compare" }]}
        />
      </TransitionSeries.Sequence>
      {T("from-right")}

      {/* Build */}
      <TransitionSeries.Sequence durationInFrames={300}>
        <WindowBeat
          rotY={-18}
          head={[<>Build your own case.</>]}
          headSize={u(84)}
          headTop={height * 0.1}
          sub={[<>Drag any verse or entry into a workspace · translate · share</>]}
          wins={[
            { src: "site/catalog.png", w: width * 0.5, x: u(280), y: -u(320), z: -360, url: "analyzingislam.com/catalog" },
            { src: "site/build.png", w: width * 0.78, x: 0, y: u(60), z: 0, url: "analyzingislam.com/build" },
          ]}
        />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 20 })} />

      <TransitionSeries.Sequence durationInFrames={260}>
        <CTA />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};

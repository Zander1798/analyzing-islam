import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFonts } from "../brand/fonts";
import { COLORS, FONTS } from "../brand/theme";
import { EASE } from "../brand/motion";
import { useLayout } from "../brand/layout";

loadFonts();

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// [frame, focusY (px in the 1080-wide image), scale]
// scale stays near 1.0 — zooming a full-width page crops the side text.
const FOCUS: [number, number, number][] = [
  [0, 900, 1.03],
  [70, 900, 1.0],
  [170, 2360, 1.0],
  [300, 2360, 1.04],
  [380, 2800, 1.0],
  [520, 2800, 1.03],
  [600, 3100, 1.0],
];
const kf = (frame: number, idx: 1 | 2) =>
  interpolate(frame, FOCUS.map((k) => k[0]), FOCUS.map((k) => k[idx]), { easing: EASE.premium, ...clamp });

const Callout: React.FC<{ text: string; a: number; b: number; c: number; d: number }> = ({ text, a, b, c, d }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u } = useLayout();
  const p = spring({ frame: frame - a, fps, config: { damping: 200 } });
  const out = interpolate(frame, [c, d], [1, 0], clamp);
  if (frame < a || frame > d) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: u(150), textAlign: "center", opacity: p * out, transform: `translateY(${(1 - p) * u(26)}px)`, padding: `0 ${u(70)}px` }}>
      <span style={{ fontFamily: FONTS.sans, fontSize: u(48), fontWeight: 700, color: COLORS.text, textShadow: "0 2px 24px rgba(0,0,0,0.9)" }}>{text}</span>
    </div>
  );
};

export const ScrollDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, width } = useLayout();
  const s = kf(frame, 2);
  const focusY = kf(frame, 1);
  // image is 1080 wide (== frame width). Put image-Y=focusY at vertical centre.
  const tx = 540 - 540 * s;
  const ty = 960 - focusY * s;
  const intro = interpolate(frame, [0, 12], [0, 1], clamp);

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden", opacity: intro }}>
      <Img
        src={staticFile("site/m-category-women.png")}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: width,
          transformOrigin: "0 0",
          transform: `translate(${tx}px, ${ty}px) scale(${s})`,
        }}
      />
      {/* legibility scrims */}
      <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 26%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, transparent 12%)" }} />

      <Callout text="Filter 1,524 sourced entries by topic." a={6} b={20} c={140} d={158} />
      <Callout text="Every claim — rated by strength." a={172} b={190} c={430} d={452} />
      <Callout text="Sourced to the exact verse — readable in full." a={466} b={484} c={575} d={595} />
    </AbsoluteFill>
  );
};

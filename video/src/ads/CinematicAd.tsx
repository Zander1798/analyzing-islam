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
import { fade } from "@remotion/transitions/fade";
import { loadFonts } from "../brand/fonts";
import { COLORS, FONTS } from "../brand/theme";
import { EASE } from "../brand/motion";
import { useLayout } from "../brand/layout";

loadFonts();
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Near-black stage with ONE soft accent glow behind the device (motivated
// lighting, not a blue wash) + heavy vignette + faint grain.
const Stage: React.FC<{ children: React.ReactNode; glowX?: string; glowY?: string }> = ({
  children,
  glowX = "50%",
  glowY = "42%",
}) => {
  const frame = useCurrentFrame();
  const pulse = 0.9 + Math.sin(frame / 55) * 0.1;
  return (
    <AbsoluteFill style={{ background: "#050506", overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(46% 42% at ${glowX} ${glowY}, rgba(122,162,247,${0.16 * pulse}), transparent 70%)`,
        }}
      />
      {children}
      <AbsoluteFill
        style={{ background: "radial-gradient(130% 100% at 50% 45%, transparent 38%, rgba(0,0,0,0.9))" }}
      />
    </AbsoluteFill>
  );
};

const Caption: React.FC<{ children: React.ReactNode; a: number }> = ({ children, a }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u, height } = useLayout();
  const p = spring({ frame: frame - a, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: height * 0.09,
        textAlign: "center",
        opacity: p,
        transform: `translateY(${(1 - p) * u(26)}px)`,
        padding: `0 ${u(70)}px`,
      }}
    >
      <span style={{ fontFamily: FONTS.sans, fontSize: u(50), fontWeight: 700, color: COLORS.text, textShadow: "0 2px 30px rgba(0,0,0,0.9)" }}>
        {children}
      </span>
    </div>
  );
};

// A big product "device" showing the real site, its content scrolling inside,
// with the whole device on a slow cinematic dolly + 3D swing.
const Device: React.FC<{ src: string; scrollFrom: number; scrollTo: number; caption: React.ReactNode; captionAt: number }> = ({
  src,
  scrollFrom,
  scrollTo,
  caption,
  captionAt,
}) => {
  const frame = useCurrentFrame();
  const { u, width, height } = useLayout();
  const winW = width * 0.84;
  const winH = height * 0.7;
  const enter = spring({ frame, fps: 60, config: { damping: 200 } });
  const scrollY = interpolate(frame, [0, 300], [scrollFrom, scrollTo], { easing: EASE.premium, ...clamp });
  const push = interpolate(frame, [0, 300], [0.98, 1.07], { easing: EASE.premium, ...clamp });
  const rotY = interpolate(frame, [0, 300], [7, -5], { easing: EASE.premium, ...clamp });
  const driftX = Math.sin(frame / 85) * u(16);

  return (
    <>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", perspective: u(2400) }}>
        <div
          style={{
            width: winW,
            height: winH,
            transform: `translateX(${driftX}px) scale(${push}) rotateY(${rotY}deg)`,
            transformStyle: "preserve-3d",
            borderRadius: u(22),
            overflow: "hidden",
            border: `1px solid ${COLORS.border}`,
            boxShadow: `0 ${u(40)}px ${u(120)}px rgba(0,0,0,0.7), 0 0 ${u(90)}px rgba(122,162,247,0.14)`,
            opacity: enter,
          }}
        >
          <Img
            src={staticFile(src)}
            style={{ width: winW, position: "absolute", top: 0, left: 0, transform: `translateY(${scrollY}px)` }}
          />
        </div>
      </AbsoluteFill>
      <Caption a={captionAt}>{caption}</Caption>
    </>
  );
};

const BeatFind: React.FC = () => (
  <Stage glowY="38%">
    <Device src="site/m-category-women.png" scrollFrom={0} scrollTo={-1600} caption={<>Every problem — <span style={{ color: COLORS.accent }}>sourced & rated.</span></>} captionAt={20} />
  </Stage>
);
const BeatRead: React.FC = () => (
  <Stage glowY="46%">
    <Device src="site/m-reader.png" scrollFrom={-200} scrollTo={-2000} caption={<>Read the primary source <span style={{ color: COLORS.accent }}>in full.</span></>} captionAt={20} />
  </Stage>
);
const BeatBuild: React.FC = () => (
  <Stage glowY="42%">
    <Device src="site/m-build.png" scrollFrom={0} scrollTo={-900} caption={<>Build your own case.</>} captionAt={20} />
  </Stage>
);

export const CinematicAd: React.FC = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence durationInFrames={230}>
      <BeatFind />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 16 })} />
    <TransitionSeries.Sequence durationInFrames={230}>
      <BeatRead />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 16 })} />
    <TransitionSeries.Sequence durationInFrames={200}>
      <BeatBuild />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);

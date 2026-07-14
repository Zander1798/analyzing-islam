import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { loadFonts } from "../brand/fonts";
import { LivingBackground } from "../brand/LivingBackground";
import { Rig, PLayer } from "../brand/CameraRig";
import { GlowWindow } from "../brand/GlowWindow";
import { Wordmark } from "../brand/Wordmark";
import { Goat } from "../brand/Goat";
import { COLORS, FONTS } from "../brand/theme";
import { useLayout } from "../brand/layout";

loadFonts();

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/* Beat 1: camera flies through UI windows placed at depth over a living bg. */
const BeatFly: React.FC = () => {
  const frame = useCurrentFrame();
  const { u } = useLayout();
  const t = frame / 60;
  // continuous camera move: directed pan + ambient drift + slow push-in
  const camX = interpolate(frame, [0, 300], [-u(120), u(140)], clamp) + Math.sin(t * 0.6) * u(40);
  const camY = interpolate(frame, [0, 300], [u(60), -u(40)], clamp) + Math.cos(t * 0.5) * u(26);
  const zoom = interpolate(frame, [0, 300], [1.02, 1.16], clamp);
  const rot = Math.sin(t * 0.35) * 1.1;
  const head = interpolate(frame, [10, 40], [0, 1], clamp);

  return (
    <AbsoluteFill>
      <Rig x={camX} y={camY} zoom={zoom} rot={rot}>
        <PLayer depth={0.55} style={{ left: "58%", top: "20%" }}>
          <GlowWindow src="site/reader.png" width={620} tilt={16} delay={4} />
        </PLayer>
        <PLayer depth={1.35} style={{ left: "6%", top: "40%" }}>
          <GlowWindow src="site/catalog.png" width={720} tilt={-16} delay={0} />
        </PLayer>
        <PLayer depth={1.9} style={{ left: "40%", top: "70%" }}>
          <GlowWindow src="site/compare.png" width={560} tilt={10} delay={8} glow="#9b7af7" />
        </PLayer>
      </Rig>
      {/* fixed kinetic headline over the moving scene */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: u(180), opacity: head }}>
        <div style={{ fontFamily: FONTS.serif, fontWeight: 700, fontSize: u(78), color: COLORS.text, textAlign: "center", maxWidth: u(900), lineHeight: 1.08 }}>
          Research the sources
          <br />
          <span style={{ color: COLORS.accent }}>yourself.</span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* Beat 2: living stat reveal + CTA, camera still breathing. */
const BeatStat: React.FC = () => {
  const frame = useCurrentFrame();
  const { u } = useLayout();
  const count = Math.round(interpolate(frame, [6, 52], [0, 1524], clamp));
  const p = interpolate(frame, [0, 16], [0, 1], clamp);
  const cta = interpolate(frame, [70, 90], [0, 1], clamp);
  const zoom = 1.05 + Math.sin(frame / 60) * 0.02;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `scale(${zoom})` }}>
      <div style={{ opacity: p, textAlign: "center" }}>
        <div style={{ fontFamily: FONTS.serif, fontWeight: 700, fontSize: u(210), color: COLORS.text, lineHeight: 1, letterSpacing: "-0.02em" }}>
          {count.toLocaleString("en-US")}
        </div>
        <div style={{ fontFamily: FONTS.sans, fontSize: u(40), color: COLORS.muted, marginTop: u(14) }}>
          sourced entries. <span style={{ color: COLORS.accent }}>Rated. Filterable.</span>
        </div>
      </div>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: u(160), opacity: cta, gap: u(16) }}>
        <Goat height={u(200)} />
        <Wordmark size={u(72)} />
        <div style={{ fontFamily: FONTS.sans, fontSize: u(34), fontWeight: 600, color: COLORS.accent }}>analyzingislam.com</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Proof: React.FC = () => (
  <LivingBackground>
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={300}>
        <BeatFly />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={slide({ direction: "from-right" })}
        timing={linearTiming({ durationInFrames: 22 })}
      />
      <TransitionSeries.Sequence durationInFrames={200}>
        <BeatStat />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  </LivingBackground>
);

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, FONTS } from "../brand/theme";
import { useLayout } from "../brand/layout";
import { EASE, SPRING } from "../brand/motion";
import { TypedCaption } from "../brand/TypedCaption";
import { GlowWindow } from "../brand/GlowWindow";
import { CategoryTag } from "../brand/CategoryTag";
import { Goat } from "../brand/Goat";
import { Wordmark } from "../brand/Wordmark";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const fade = (f: number, a: number, b: number, c: number, d: number) =>
  interpolate(f, [a, b, c, d], [0, 1, 1, 0], clamp);

// Caption chip anchored near the bottom of the frame.
const Caption: React.FC<{ children: React.ReactNode; delay?: number }> = ({
  children,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u, height } = useLayout();
  const p = spring({ frame: frame - delay, fps, config: SPRING.premium });
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: height * 0.12,
        textAlign: "center",
        opacity: p,
        transform: `translateY(${(1 - p) * u(24)}px)`,
        padding: `0 ${u(80)}px`,
      }}
    >
      <span style={{ fontFamily: FONTS.sans, fontSize: u(40), fontWeight: 600, color: COLORS.text }}>
        {children}
      </span>
    </div>
  );
};

/* ---------- 0-4s HOOK ---------- */
export const SceneHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, width } = useLayout();
  const out = interpolate(frame, [104, 120], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: out }}>
      <div style={{ maxWidth: width * 0.84, textAlign: "center" }}>
        <div style={{ fontSize: u(72), lineHeight: 1.15, fontWeight: 600, minHeight: u(170) }}>
          <TypedCaption text="Want to actually research Islam's texts?" startFrame={4} cps={30} />
        </div>
        <div style={{ marginTop: u(34), fontFamily: FONTS.serif, fontSize: u(60), color: COLORS.accent, opacity: interpolate(frame, [70, 88], [0, 1], clamp) }}>
          Here&#39;s your toolkit.
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- 4-9s FIND ---------- */
export const SceneFind: React.FC = () => {
  const frame = useCurrentFrame();
  const { u } = useLayout();
  const chips = ["Women", "Warfare", "Apostasy", "Science"];
  const active = 0;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: fade(frame, 0, 12, 138, 150) }}>
      <GlowWindow src="site/catalog.png" width={900} tilt={-14} delay={2} />
      <div style={{ display: "flex", gap: u(16), marginTop: u(48) }}>
        {chips.map((c, i) => {
          const lit = i === active ? interpolate(frame, [30, 46], [0, 1], clamp) : 0;
          return (
            <CategoryTag
              key={c}
              label={c}
              scale={u(1.1)}
              style={{
                color: lit > 0.5 ? COLORS.accent : COLORS.muted,
                borderColor: lit > 0.5 ? COLORS.accent : COLORS.border,
                boxShadow: lit > 0.5 ? `0 0 ${u(24)}px ${COLORS.accent}55` : undefined,
              }}
            />
          );
        })}
      </div>
      <Caption delay={40}>
        <b style={{ fontFamily: FONTS.serif }}>1,524</b> entries — filtered in seconds.
      </Caption>
    </AbsoluteFill>
  );
};

/* ---------- 9-15s VERIFY ---------- */
export const SceneVerify: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u } = useLayout();
  const stamp = spring({ frame: frame - 40, fps, config: SPRING.pop });
  const pill = spring({ frame: frame - 66, fps, config: SPRING.pop });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: fade(frame, 0, 12, 168, 180) }}>
      <GlowWindow src="site/reader.png" width={860} tilt={12} delay={2} />
      {/* citation stamp */}
      <div
        style={{
          marginTop: u(44),
          display: "flex",
          gap: u(16),
          alignItems: "center",
          opacity: stamp,
          transform: `scale(${interpolate(stamp, [0, 1], [0.8, 1])})`,
        }}
      >
        <span style={{ fontFamily: FONTS.sans, fontSize: u(28), fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: COLORS.muted }}>
          Qur&#39;an 4:34 &middot; Saheeh International
        </span>
        {/* strength pill flips to Strong */}
        <span
          style={{
            opacity: pill,
            transform: `scale(${interpolate(pill, [0, 1], [0.7, 1])})`,
            fontFamily: FONTS.sans,
            fontSize: u(26),
            fontWeight: 700,
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: COLORS.accent,
            border: `1px solid ${COLORS.accent}`,
            boxShadow: `0 0 ${u(26)}px ${COLORS.accent}55`,
            padding: `${u(8)}px ${u(16)}px`,
          }}
        >
          Strong
        </span>
      </div>
      <Caption delay={78}>Every claim — sourced, rated, readable in full.</Caption>
    </AbsoluteFill>
  );
};

/* ---------- 15-19s COMPARE ---------- */
export const SceneCompare: React.FC = () => {
  const frame = useCurrentFrame();
  const { u } = useLayout();
  const split = interpolate(frame, [8, 40], [0, 1], { ...clamp, easing: EASE.premium });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: fade(frame, 0, 12, 108, 120) }}>
      <div style={{ display: "flex", gap: interpolate(split, [0, 1], [u(0), u(28)]) }}>
        <div style={{ transform: `translateX(${(1 - split) * u(120)}px)` }}>
          <GlowWindow src="site/reader.png" width={470} tilt={8} delay={2} imgStyle={{ transform: "scale(1.15)" }} />
        </div>
        <div style={{ transform: `translateX(${(1 - split) * -u(120)}px)` }}>
          <GlowWindow src="site/compare.png" width={470} tilt={-8} delay={6} imgStyle={{ transform: "scale(1.15)" }} />
        </div>
      </div>
      <Caption delay={30}>Put two sources head-to-head.</Caption>
    </AbsoluteFill>
  );
};

/* ---------- 19-25s BUILD (recreated interaction) ---------- */
export const SceneBuild: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, width } = useLayout();
  const paneW = u(430);
  const paneH = u(560);
  // drag the highlighted block from right pane into the left editor
  const drag = interpolate(frame, [40, 78], [0, 1], { ...clamp, easing: EASE.premium });
  const dropped = frame > 78;
  const morph = interpolate(frame, [110, 130], [0, 1], clamp); // arabic -> english
  const paneStyle: React.CSSProperties = {
    width: paneW,
    height: paneH,
    borderRadius: u(14),
    border: `1px solid ${COLORS.border}`,
    background: "#080808",
    boxShadow: `0 ${u(24)}px ${u(70)}px rgba(0,0,0,0.6)`,
    padding: u(22),
    position: "relative",
    overflow: "hidden",
  };
  const label: React.CSSProperties = {
    fontFamily: FONTS.sans,
    fontSize: u(18),
    letterSpacing: "0.18em",
    textTransform: "uppercase",
    color: COLORS.dim,
    marginBottom: u(16),
  };
  const block = (children: React.ReactNode, extra?: React.CSSProperties) => (
    <div style={{ border: `1px solid ${COLORS.accent}`, boxShadow: `0 0 ${u(20)}px ${COLORS.accent}44`, borderRadius: u(8), padding: u(16), fontFamily: FONTS.serif, fontSize: u(24), color: COLORS.text, lineHeight: 1.35, ...extra }}>
      {children}
    </div>
  );
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: fade(frame, 0, 12, 168, 180) }}>
      <div style={{ display: "flex", gap: u(40), alignItems: "flex-start" }}>
        {/* editor (left) */}
        <div style={paneStyle}>
          <div style={label}>Your argument</div>
          {dropped && (
            <div style={{ opacity: interpolate(frame, [78, 90], [0, 1], clamp), transform: `translateY(${interpolate(frame, [78, 90], [u(12), 0], clamp)}px)` }}>
              {block(
                <span>
                  {morph < 0.5 ? (
                    <span style={{ opacity: 1 - morph * 2 }}>ٱضْرِبُوهُنَّ</span>
                  ) : (
                    <span style={{ opacity: (morph - 0.5) * 2, color: COLORS.accent }}>&ldquo;strike them&rdquo;</span>
                  )}
                  {" — Qur'an 4:34"}
                </span>
              )}
            </div>
          )}
        </div>
        {/* source browser (right) */}
        <div style={paneStyle}>
          <div style={label}>Sources</div>
          <div style={{ opacity: dropped ? 0.25 : 1, transform: `translateX(${drag * (- (paneW + u(40)) - u(10))}px) translateY(${drag * -u(20)}px)`, position: dropped ? "static" : "relative", zIndex: 5 }}>
            {block(<span>…advise them; forsake them in bed; and strike them.</span>)}
          </div>
        </div>
      </div>
      <Caption delay={92}>Build your own case — check the Arabic yourself.</Caption>
    </AbsoluteFill>
  );
};

/* ---------- 25-30s SAVE / SHARE + CTA ---------- */
export const SceneShare: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u } = useLayout();
  const star = spring({ frame: frame - 6, fps, config: SPRING.pop });
  const toast = spring({ frame: frame - 26, fps, config: SPRING.premium });
  const ctaP = spring({ frame: frame - 60, fps, config: SPRING.premium });
  const chipsOut = interpolate(frame, [58, 74], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* save + share micro-interactions, then they clear for the CTA */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: u(28), opacity: chipsOut }}>
        <div style={{ display: "flex", alignItems: "center", gap: u(14), transform: `scale(${interpolate(star, [0, 1], [0.7, 1])})` }}>
          <svg width={u(44)} height={u(44)} viewBox="0 0 24 24" fill={COLORS.accent} stroke={COLORS.accent} strokeWidth={1.5}>
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14l-5-4.87 6.91-1.01L12 2z" />
          </svg>
          <span style={{ fontFamily: FONTS.sans, fontSize: u(40), fontWeight: 600, color: COLORS.text, opacity: star }}>Saved</span>
        </div>
        <div style={{ opacity: toast, transform: `translateY(${(1 - toast) * u(16)}px)`, fontFamily: FONTS.sans, fontSize: u(30), color: COLORS.muted, border: `1px solid ${COLORS.border}`, padding: `${u(12)}px ${u(22)}px`, borderRadius: u(4) }}>
          Share link copied
        </div>
      </AbsoluteFill>

      {/* CTA */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: u(22), opacity: ctaP, transform: `translateY(${(1 - ctaP) * u(20)}px)` }}>
        <Goat height={u(240)} />
        <Wordmark size={u(84)} />
        <div style={{ fontFamily: FONTS.sans, fontSize: u(34), fontWeight: 600, color: COLORS.accent, letterSpacing: "0.05em" }}>
          analyzingislam.com
        </div>
        <div style={{ fontFamily: FONTS.sans, fontSize: u(26), color: COLORS.muted, maxWidth: u(760), textAlign: "center", marginTop: u(6) }}>
          Everything you need to research the sources — in one place.
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

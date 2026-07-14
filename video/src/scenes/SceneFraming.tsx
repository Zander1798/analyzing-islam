import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONTS } from "../brand/theme";
import { Reveal } from "../brand/Kinetic";
import { useLayout } from "../brand/layout";

export const SceneFraming: React.FC = () => {
  const frame = useCurrentFrame();
  const { u } = useLayout();
  const dim = interpolate(frame, [46, 64], [1, 0.32], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const out = interpolate(frame, [104, 120], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const line: React.CSSProperties = {
    fontFamily: FONTS.sans,
    fontSize: u(52),
    fontWeight: 600,
    letterSpacing: "0.02em",
  };
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        gap: u(18),
        opacity: out,
      }}
    >
      <div style={{ opacity: dim }}>
        <Reveal delay={4} style={{ ...line, color: COLORS.muted }}>
          Don&#39;t take our word for it.
        </Reveal>
      </div>
      <Reveal delay={52} style={{ ...line, color: COLORS.text }}>
        Or theirs.
      </Reveal>
    </AbsoluteFill>
  );
};

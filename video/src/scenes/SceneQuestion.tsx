import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONTS } from "../brand/theme";
import { WordReveal } from "../brand/Kinetic";
import { useLayout } from "../brand/layout";

export const SceneQuestion: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, width } = useLayout();
  const underline = interpolate(frame, [70, 105], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const out = interpolate(frame, [130, 150], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center", opacity: out }}
    >
      <div style={{ maxWidth: width * 0.86, textAlign: "center" }}>
        <WordReveal
          text="Is the Qur'an what it claims to be?"
          startFrame={6}
          stagger={7}
          accentWord="claims"
          accentColor={COLORS.accent}
          style={{
            fontFamily: FONTS.serif,
            fontWeight: 700,
            fontSize: u(96),
            lineHeight: 1.08,
            color: COLORS.text,
            letterSpacing: "-0.02em",
          }}
        />
        <div
          style={{
            height: u(3),
            width: `${underline * 42}%`,
            background: COLORS.accent,
            margin: `${u(34)}px auto 0`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

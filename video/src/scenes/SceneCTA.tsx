import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONTS } from "../brand/theme";
import { Wordmark } from "../brand/Wordmark";
import { Goat } from "../brand/Goat";
import { useLayout } from "../brand/layout";

export const SceneCTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u } = useLayout();

  const goatIn = spring({ frame: frame - 2, fps, config: { damping: 200 } });
  const wordP = spring({ frame: frame - 16, fps, config: { damping: 200 } });
  const domainP = interpolate(frame, [30, 46], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const underline = interpolate(frame, [40, 62], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center", gap: u(24) }}
    >
      <div
        style={{
          opacity: goatIn,
          transform: `translateX(${(1 - goatIn) * -u(220)}px)`,
        }}
      >
        <Goat height={u(300)} />
      </div>

      <div
        style={{
          opacity: wordP,
          transform: `translateY(${(1 - wordP) * u(20)}px)`,
        }}
      >
        <Wordmark size={u(96)} />
      </div>

      <div style={{ opacity: domainP, textAlign: "center" }}>
        <span
          style={{
            fontFamily: FONTS.sans,
            fontSize: u(40),
            fontWeight: 600,
            letterSpacing: "0.06em",
            color: COLORS.accent,
          }}
        >
          analyzingislam.com
        </span>
        <div
          style={{
            height: u(3),
            width: `${underline * 100}%`,
            background: COLORS.accent,
            margin: `${u(10)}px auto 0`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONTS } from "../brand/theme";
import { CategoryTag } from "../brand/CategoryTag";
import { useLayout } from "../brand/layout";

const CATS = [
  "Abrogation",
  "Warfare",
  "Science",
  "Apostasy",
  "Slavery",
  "Contradiction",
  "Prophetic Character",
];

const fade = (frame: number, a: number, b: number, c: number, d: number) =>
  interpolate(frame, [a, b, c, d], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

export const SceneValue: React.FC = () => {
  const frame = useCurrentFrame();
  const { u, width } = useLayout();

  // Block A: counting number (f0–72)
  const count = Math.round(
    interpolate(frame, [4, 58], [0, 1524], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  const aOp = fade(frame, 0, 10, 60, 72);
  // Block B: "Sourced. Rated. Filterable." (f66–120)
  const bOp = fade(frame, 66, 80, 108, 120);
  // Block C: category rush + closing line (f116–180)
  const cOp = interpolate(frame, [116, 132], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const marquee = interpolate(frame, [116, 180], [width * 0.28, -width * 0.5], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      {/* A */}
      <AbsoluteFill
        style={{ justifyContent: "center", alignItems: "center", opacity: aOp }}
      >
        <div
          style={{
            fontFamily: FONTS.serif,
            fontWeight: 700,
            fontSize: u(200),
            color: COLORS.text,
            lineHeight: 1,
            letterSpacing: "-0.02em",
          }}
        >
          {count.toLocaleString("en-US")}
        </div>
        <div
          style={{
            fontFamily: FONTS.sans,
            fontSize: u(40),
            color: COLORS.muted,
            marginTop: u(20),
            letterSpacing: "0.02em",
          }}
        >
          documented problems.
        </div>
      </AbsoluteFill>

      {/* B */}
      <AbsoluteFill
        style={{ justifyContent: "center", alignItems: "center", opacity: bOp }}
      >
        <div
          style={{
            fontFamily: FONTS.serif,
            fontWeight: 700,
            fontSize: u(84),
            color: COLORS.text,
            textAlign: "center",
          }}
        >
          Sourced. <span style={{ color: COLORS.accent }}>Rated.</span> Filterable.
        </div>
      </AbsoluteFill>

      {/* C */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          opacity: cOp,
          gap: u(40),
        }}
      >
        <div style={{ width: "100%", overflow: "hidden", display: "flex" }}>
          <div
            style={{
              display: "flex",
              gap: u(18),
              transform: `translateX(${marquee}px)`,
              whiteSpace: "nowrap",
            }}
          >
            {[...CATS, ...CATS].map((c, i) => (
              <CategoryTag key={i} label={c} scale={u(1.15)} />
            ))}
          </div>
        </div>
        <div
          style={{
            fontFamily: FONTS.sans,
            fontSize: u(38),
            color: COLORS.text,
            textAlign: "center",
            maxWidth: width * 0.8,
            lineHeight: 1.4,
          }}
        >
          Every claim cites a primary source you can open and read.
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

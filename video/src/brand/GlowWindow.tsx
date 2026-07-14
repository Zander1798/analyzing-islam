import React from "react";
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS } from "./theme";
import { useLayout } from "./layout";

// A glowing rounded "browser" window that holds a screenshot (or children),
// entering with a premium settle and an optional 3D tilt (Envato look).
// Three motion layers: primary rise/opacity, secondary glow, ambient float.
export const GlowWindow: React.FC<{
  src?: string;
  children?: React.ReactNode;
  width: number; // in u() units (1080-based)
  tilt?: number; // Y-rotation degrees at rest
  delay?: number;
  imgStyle?: React.CSSProperties;
  glow?: string;
  style?: React.CSSProperties;
}> = ({ src, children, width, tilt = 0, delay = 0, imgStyle, glow = COLORS.accent, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u } = useLayout();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  const rise = interpolate(p, [0, 1], [u(60), 0]);
  const float = Math.sin((frame - delay) / 40) * u(5); // ambient
  const w = u(width);
  return (
    <div style={{ perspective: u(1800), opacity: p, ...style }}>
      <div
        style={{
          width: w,
          transform: `translateY(${rise + float}px) rotateY(${tilt}deg) rotateX(${tilt ? 2 : 0}deg)`,
          transformStyle: "preserve-3d",
          borderRadius: u(16),
          overflow: "hidden",
          border: `1px solid ${COLORS.border}`,
          boxShadow: `0 ${u(30)}px ${u(90)}px rgba(0,0,0,0.65), 0 0 ${u(70)}px ${glow}22`,
          background: "#080808",
        }}
      >
        {src ? (
          <Img
            src={staticFile(src)}
            style={{ width: "100%", display: "block", ...imgStyle }}
          />
        ) : (
          children
        )}
      </div>
    </div>
  );
};

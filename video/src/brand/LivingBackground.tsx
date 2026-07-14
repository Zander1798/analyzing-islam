import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

// deterministic pseudo-random (no per-frame Math.random -> no flicker)
const rnd = (n: number) => {
  const x = Math.sin(n * 99.137) * 43758.5453;
  return x - Math.floor(x);
};

const BLOBS = [
  { hue: "#7aa2f7", x: 28, y: 26, r: 62, sp: 0.55, ph: 0.0 },
  { hue: "#5b8def", x: 74, y: 52, r: 72, sp: 0.75, ph: 2.1 },
  { hue: "#3f5bd0", x: 52, y: 82, r: 56, sp: 0.5, ph: 4.0 },
  { hue: "#8b6cf0", x: 18, y: 66, r: 46, sp: 0.68, ph: 1.2 },
];

const Particles: React.FC<{ frame: number; count?: number }> = ({ frame, count = 60 }) => {
  const t = frame / 60;
  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const bx = rnd(i) * 100;
        const baseY = rnd(i + 7) * 120;
        const sp = 0.15 + rnd(i + 3) * 0.5;
        const depth = 0.35 + rnd(i + 5) * 0.65;
        const y = (((baseY - t * sp * 5) % 120) + 120) % 120;
        const size = 1 + depth * 3.5;
        const tw = 0.3 + 0.7 * Math.abs(Math.sin(t * (0.6 + rnd(i + 9)) + i));
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${bx}%`,
              top: `${y - 10}%`,
              width: size,
              height: size,
              borderRadius: "50%",
              background: "#aec4ff",
              opacity: 0.14 * tw * depth,
              filter: "blur(0.6px)",
            }}
          />
        );
      })}
    </>
  );
};

// Animated film grain via SVG turbulence, shifted per frame.
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

export const LivingBackground: React.FC<{
  children?: React.ReactNode;
  intensity?: number;
}> = ({ children, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const t = frame / 60;
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {BLOBS.map((b, i) => {
        const dx = Math.sin(t * b.sp + b.ph) * 9;
        const dy = Math.cos(t * b.sp * 0.8 + b.ph) * 8;
        const pulse = 1 + Math.sin(t * b.sp * 1.25 + b.ph) * 0.14;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${b.x + dx}%`,
              top: `${b.y + dy}%`,
              width: `${b.r * pulse}%`,
              height: `${b.r * pulse}%`,
              transform: "translate(-50%,-50%)",
              background: `radial-gradient(circle, ${b.hue}, transparent 66%)`,
              opacity: 0.2 * intensity,
              filter: "blur(70px)",
              mixBlendMode: "screen",
            }}
          />
        );
      })}
      <Particles frame={frame} />
      <AbsoluteFill
        style={{
          backgroundImage: GRAIN,
          backgroundPosition: `${(frame * 7) % 180}px ${(frame * 11) % 180}px`,
          opacity: 0.05,
          mixBlendMode: "overlay",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(120% 90% at 50% 42%, transparent 42%, rgba(0,0,0,0.78))",
        }}
      />
      {children}
    </AbsoluteFill>
  );
};

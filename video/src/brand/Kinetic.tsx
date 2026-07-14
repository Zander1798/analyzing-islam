import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

/** Fade + rise a block into view. */
export const Reveal: React.FC<{
  children: React.ReactNode;
  delay?: number;
  y?: number;
  style?: React.CSSProperties;
}> = ({ children, delay = 0, y = 24, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div style={{ opacity: p, transform: `translateY(${(1 - p) * y}px)`, ...style }}>
      {children}
    </div>
  );
};

/** Reveal a line word-by-word with a stagger. */
export const WordReveal: React.FC<{
  text: string;
  startFrame?: number;
  stagger?: number;
  style?: React.CSSProperties;
  accentWord?: string;
  accentColor?: string;
}> = ({ text, startFrame = 0, stagger = 6, style, accentWord, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "baseline",
        ...style,
      }}
    >
      {words.map((w, i) => {
        const p = spring({
          frame: frame - startFrame - i * stagger,
          fps,
          config: { damping: 200 },
        });
        const isAccent = accentWord && w.replace(/[^\w']/g, "") === accentWord;
        return (
          <span
            key={i}
            style={{
              opacity: p,
              transform: `translateY(${(1 - p) * 22}px)`,
              display: "inline-block",
              marginRight: "0.28em",
              color: isAccent ? accentColor : undefined,
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

import React from "react";
import { useCurrentFrame } from "remotion";
import { COLORS, FONTS } from "./theme";

// Typewriter caption with a blinking accent cursor (the iBanFirst signature).
export const TypedCaption: React.FC<{
  text: string;
  startFrame?: number;
  cps?: number; // characters per second
  style?: React.CSSProperties;
  cursor?: boolean;
}> = ({ text, startFrame = 0, cps = 26, style, cursor = true }) => {
  const frame = useCurrentFrame();
  const shown = Math.max(0, Math.floor(((frame - startFrame) / 30) * cps));
  const visible = text.slice(0, Math.min(text.length, shown));
  const done = shown >= text.length;
  const blinkOn = Math.floor(frame / 16) % 2 === 0;
  return (
    <span style={{ fontFamily: FONTS.sans, color: COLORS.text, ...style }}>
      {visible}
      {cursor && (!done || blinkOn) && (
        <span style={{ color: COLORS.accent, fontWeight: 400 }}>|</span>
      )}
    </span>
  );
};

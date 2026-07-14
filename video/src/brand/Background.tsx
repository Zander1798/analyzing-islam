import React from "react";
import { AbsoluteFill } from "remotion";
import { COLORS } from "./theme";

export const Background: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: COLORS.bg }}>
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(120% 75% at 50% 32%, rgba(122,162,247,0.07), transparent 62%)",
      }}
    />
    {children}
  </AbsoluteFill>
);

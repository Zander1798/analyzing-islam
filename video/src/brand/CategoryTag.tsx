import React from "react";
import { COLORS, FONTS } from "./theme";

export const CategoryTag: React.FC<{
  label: string;
  scale?: number;
  style?: React.CSSProperties;
}> = ({ label, scale = 1, style }) => (
  <span
    style={{
      fontFamily: FONTS.sans,
      fontSize: 22 * scale,
      fontWeight: 600,
      letterSpacing: "0.22em",
      textTransform: "uppercase",
      color: COLORS.muted,
      border: `1px solid ${COLORS.border}`,
      padding: `${8 * scale}px ${16 * scale}px`,
      whiteSpace: "nowrap",
      lineHeight: 1,
      ...style,
    }}
  >
    {label}
  </span>
);

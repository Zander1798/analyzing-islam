import React from "react";
import { COLORS, FONTS } from "./theme";

export const Wordmark: React.FC<{ size: number; style?: React.CSSProperties }> = ({
  size,
  style,
}) => (
  <span
    style={{
      fontFamily: FONTS.serif,
      fontWeight: 700,
      fontSize: size,
      color: COLORS.text,
      letterSpacing: "-0.02em",
      lineHeight: 1,
      ...style,
    }}
  >
    Analyzing Islam
  </span>
);

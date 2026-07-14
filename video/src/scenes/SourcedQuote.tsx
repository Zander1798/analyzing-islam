import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONTS } from "../brand/theme";
import { CategoryTag } from "../brand/CategoryTag";
import { useLayout } from "../brand/layout";
import type { Quote } from "../data/quotes";

// Each quote plays for `hold` frames; fades in, holds, fades out.
export const SourcedQuote: React.FC<{ quote: Quote; hold: number }> = ({
  quote,
  hold,
}) => {
  const frame = useCurrentFrame();
  const { u, width } = useLayout();
  const inP = interpolate(frame, [0, 16], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outP = interpolate(frame, [hold - 16, hold], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const rise = interpolate(frame, [0, 20], [u(28), 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const metaP = interpolate(frame, [14, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Longer quotes get a slightly smaller size so they never clip.
  const size = quote.text.length > 90 ? u(58) : u(70);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity: inP * outP,
      }}
    >
      <div
        style={{
          maxWidth: width * 0.82,
          textAlign: "center",
          transform: `translateY(${rise}px)`,
        }}
      >
        <div
          style={{
            fontFamily: FONTS.serif,
            fontStyle: "italic",
            fontWeight: 500,
            fontSize: size,
            lineHeight: 1.28,
            color: COLORS.text,
          }}
        >
          &ldquo;{quote.text}&rdquo;
        </div>

        <div style={{ opacity: metaP }}>
          <div
            style={{
              height: u(2),
              width: u(64),
              background: COLORS.border,
              margin: `${u(40)}px auto ${u(26)}px`,
            }}
          />
          <div
            style={{
              display: "flex",
              gap: u(18),
              justifyContent: "center",
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                fontFamily: FONTS.sans,
                fontSize: u(26),
                fontWeight: 600,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: COLORS.muted,
              }}
            >
              {quote.citation} &middot; {quote.translation}
            </span>
            <CategoryTag label={quote.category} scale={u(1)} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

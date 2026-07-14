import React from "react";
import { AbsoluteFill, Composition } from "remotion";
import { loadFonts } from "./brand/fonts";
import { Background } from "./brand/Background";
import { Wordmark } from "./brand/Wordmark";
import { CategoryTag } from "./brand/CategoryTag";
import { Goat } from "./brand/Goat";
import { COLORS, FONTS } from "./brand/theme";

loadFonts();

// Temporary brand-kit test (replaced by the real ad in Task 5).
const BrandTest: React.FC = () => (
  <Background>
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        gap: 60,
        padding: 80,
        textAlign: "center",
      }}
    >
      <Wordmark size={90} />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap", justifyContent: "center" }}>
        <CategoryTag label="Abrogation" />
        <CategoryTag label="Warfare" />
        <CategoryTag label="Science" />
        <CategoryTag label="Apostasy" />
      </div>
      <div style={{ fontFamily: FONTS.sans, color: COLORS.muted, fontSize: 30 }}>
        analyzingislam.com
      </div>
      <Goat height={320} />
    </AbsoluteFill>
  </Background>
);

export const Root: React.FC = () => (
  <Composition
    id="BrandTest"
    component={BrandTest}
    durationInFrames={60}
    fps={30}
    width={1080}
    height={1920}
  />
);

import React from "react";
import { Series } from "remotion";
import { loadFonts } from "../brand/fonts";
import { Background } from "../brand/Background";
import { SceneQuestion } from "../scenes/SceneQuestion";
import { SceneFraming } from "../scenes/SceneFraming";
import { SceneQuotes } from "../scenes/SceneQuotes";
import { SceneValue } from "../scenes/SceneValue";
import { SceneCTA } from "../scenes/SceneCTA";

loadFonts();

// 30s @ 30fps = 900 frames. 150 + 120 + 330 + 180 + 120 = 900.
export const TheQuestion: React.FC = () => (
  <Background>
    <Series>
      <Series.Sequence durationInFrames={150}>
        <SceneQuestion />
      </Series.Sequence>
      <Series.Sequence durationInFrames={120}>
        <SceneFraming />
      </Series.Sequence>
      <Series.Sequence durationInFrames={330}>
        <SceneQuotes />
      </Series.Sequence>
      <Series.Sequence durationInFrames={180}>
        <SceneValue />
      </Series.Sequence>
      <Series.Sequence durationInFrames={120}>
        <SceneCTA />
      </Series.Sequence>
    </Series>
  </Background>
);

import React from "react";
import { Series } from "remotion";
// To add music: drop an MP3 at public/music/ambient.mp3, then uncomment the
// import + the <Audio> element below and re-render.
// import { Audio, staticFile, interpolate } from "remotion";
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
    {/* Music (uncomment once public/music/ambient.mp3 exists):
    <Audio
      src={staticFile("music/ambient.mp3")}
      volume={(f) =>
        interpolate(f, [0, 20, 870, 900], [0, 0.55, 0.55, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      }
    /> */}
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

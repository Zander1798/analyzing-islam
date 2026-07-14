import React from "react";
import { Series } from "remotion";
import { loadFonts } from "../brand/fonts";
import { Background } from "../brand/Background";
import {
  SceneHook,
  SceneFind,
  SceneVerify,
  SceneCompare,
  SceneBuild,
  SceneShare,
} from "../tour/scenes";

loadFonts();

// 30s @ 30fps = 900. 120 + 150 + 180 + 120 + 180 + 150 = 900.
export const WorkflowTour: React.FC = () => (
  <Background>
    <Series>
      <Series.Sequence durationInFrames={120}>
        <SceneHook />
      </Series.Sequence>
      <Series.Sequence durationInFrames={150}>
        <SceneFind />
      </Series.Sequence>
      <Series.Sequence durationInFrames={180}>
        <SceneVerify />
      </Series.Sequence>
      <Series.Sequence durationInFrames={120}>
        <SceneCompare />
      </Series.Sequence>
      <Series.Sequence durationInFrames={180}>
        <SceneBuild />
      </Series.Sequence>
      <Series.Sequence durationInFrames={150}>
        <SceneShare />
      </Series.Sequence>
    </Series>
  </Background>
);

import React from "react";
import { Composition } from "remotion";
import { TheQuestion } from "./ads/TheQuestion";

const COMMON = {
  component: TheQuestion,
  durationInFrames: 900,
  fps: 30,
} as const;

export const Root: React.FC = () => (
  <>
    <Composition id="TheQuestionVertical" {...COMMON} width={1080} height={1920} />
    <Composition id="TheQuestionLandscape" {...COMMON} width={1920} height={1080} />
    <Composition id="TheQuestionSquare" {...COMMON} width={1080} height={1080} />
  </>
);

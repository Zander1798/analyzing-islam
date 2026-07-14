import React from "react";
import { Composition } from "remotion";
import { TheQuestion } from "./ads/TheQuestion";
import { WorkflowTour } from "./ads/WorkflowTour";
import { Proof } from "./ads/Proof";
import { ScrollDemo } from "./ads/ScrollDemo";

const RATIOS = [
  { suffix: "Vertical", width: 1080, height: 1920 },
  { suffix: "Landscape", width: 1920, height: 1080 },
  { suffix: "Square", width: 1080, height: 1080 },
] as const;

export const Root: React.FC = () => (
  <>
    <Composition
      id="Proof"
      component={Proof}
      durationInFrames={478}
      fps={60}
      width={1080}
      height={1920}
    />
    <Composition
      id="ScrollDemo"
      component={ScrollDemo}
      durationInFrames={600}
      fps={60}
      width={1080}
      height={1920}
    />
    {RATIOS.map((r) => (
      <Composition
        key={`q-${r.suffix}`}
        id={`TheQuestion${r.suffix}`}
        component={TheQuestion}
        durationInFrames={900}
        fps={30}
        width={r.width}
        height={r.height}
      />
    ))}
    {RATIOS.map((r) => (
      <Composition
        key={`t-${r.suffix}`}
        id={`WorkflowTour${r.suffix}`}
        component={WorkflowTour}
        durationInFrames={900}
        fps={30}
        width={r.width}
        height={r.height}
      />
    ))}
  </>
);

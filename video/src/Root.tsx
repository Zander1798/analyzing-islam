import React from "react";
import { AbsoluteFill, Composition } from "remotion";

// Temporary smoke-test composition (replaced in Task 5).
const Hello: React.FC = () => (
  <AbsoluteFill
    style={{
      background: "#000",
      color: "#f5f5f5",
      justifyContent: "center",
      alignItems: "center",
      fontSize: 80,
    }}
  >
    ok
  </AbsoluteFill>
);

export const Root: React.FC = () => (
  <Composition
    id="Smoke"
    component={Hello}
    durationInFrames={30}
    fps={30}
    width={1080}
    height={1920}
  />
);

import React, { createContext, useContext } from "react";
import { AbsoluteFill } from "remotion";

// A simple parallax "camera": the Rig sets a camera offset/zoom/rotation;
// each PLayer translates by -camera * depth, so nearer layers (depth > 1)
// move more than far ones (depth < 1) — real depth as the camera drifts.
const Cam = createContext({ x: 0, y: 0 });

export const Rig: React.FC<{
  x?: number;
  y?: number;
  zoom?: number;
  rot?: number;
  children: React.ReactNode;
}> = ({ x = 0, y = 0, zoom = 1, rot = 0, children }) => (
  <Cam.Provider value={{ x, y }}>
    <AbsoluteFill style={{ perspective: 2200, justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${zoom}) rotate(${rot}deg)`,
          transformStyle: "preserve-3d",
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  </Cam.Provider>
);

export const PLayer: React.FC<{
  depth: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ depth, children, style }) => {
  const { x, y } = useContext(Cam);
  return (
    <div
      style={{
        position: "absolute",
        transform: `translate(${-x * depth}px, ${-y * depth}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

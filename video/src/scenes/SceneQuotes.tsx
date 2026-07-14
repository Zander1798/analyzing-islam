import React from "react";
import { Series } from "remotion";
import { QUOTES } from "../data/quotes";
import { SourcedQuote } from "./SourcedQuote";

const HOLD = 110; // frames per quote (3 x 110 = 330 = 11s)

export const SceneQuotes: React.FC = () => (
  <Series>
    {QUOTES.map((q, i) => (
      <Series.Sequence key={i} durationInFrames={HOLD}>
        <SourcedQuote quote={q} hold={HOLD} />
      </Series.Sequence>
    ))}
  </Series>
);

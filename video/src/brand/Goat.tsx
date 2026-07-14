import React from "react";
import { staticFile } from "remotion";
import { Gif } from "@remotion/gif";

export const Goat: React.FC<{ height: number; style?: React.CSSProperties }> = ({
  height,
  style,
}) => (
  <Gif
    src={staticFile("goat.gif")}
    height={height}
    width={height}
    fit="contain"
    style={style}
  />
);

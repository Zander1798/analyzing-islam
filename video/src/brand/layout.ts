import { useVideoConfig } from "remotion";

export type Orientation = "portrait" | "landscape" | "square";

// The short edge is 1080 in all three target compositions, so sizing off `S`
// keeps type sizes consistent across ratios; `u(n)` scales a 1080-based value.
export function useLayout() {
  const { width, height } = useVideoConfig();
  const S = Math.min(width, height);
  const u = (n: number) => (n * S) / 1080;
  const orientation: Orientation =
    width > height ? "landscape" : width < height ? "portrait" : "square";
  return { width, height, S, u, orientation };
}

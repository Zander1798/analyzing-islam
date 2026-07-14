// Brand tokens mirrored from site/assets/css/style.css.
export const COLORS = {
  bg: "#000000",
  text: "#f5f5f5",
  muted: "#9a9a9a",
  dim: "#5a5a5a",
  accent: "#7aa2f7",
  border: "#1e1e1e",
} as const;

// Populated by brand/fonts.ts loadFonts(); components read these at render time.
export const FONTS = {
  serif: "Playfair Display, Georgia, serif",
  sans: "Inter, system-ui, sans-serif",
};

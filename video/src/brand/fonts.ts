import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { FONTS } from "./theme";

let done = false;

// Self-fetches the web fonts (no system-font dependency in headless render) and
// updates FONTS.serif / FONTS.sans in place. Idempotent; call at composition import.
export function loadFonts(): void {
  if (done) return;
  done = true;
  FONTS.serif = loadPlayfair().fontFamily;
  FONTS.sans = loadInter().fontFamily;
}

// Full-page phone-width captures of the live site, for full-screen scrolling
// footage. Viewport width 540 @2x = 1080px wide == the vertical frame width.
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const OUT = path.join(__dirname, "shots");
fs.mkdirSync(OUT, { recursive: true });
const BASE = "https://analyzingislam.com";

// name, url, max captured height in CSS px (keeps huge lists to a usable scroll)
const TARGETS = [
  { name: "m-category-women", url: `${BASE}/category/women.html`, maxH: 3400 },
  { name: "m-reader", url: `${BASE}/read/quran/4.html`, maxH: 3400 },
  { name: "m-build", url: `${BASE}/build.html`, maxH: 3000 },
  { name: "m-compare", url: `${BASE}/compare.html`, maxH: 2200 },
  { name: "m-stats", url: `${BASE}/stats.html`, maxH: 3000 },
  { name: "m-catalog", url: `${BASE}/catalog.html`, maxH: 3400 },
];

(async () => {
  const browser = await chromium.launch();
  for (const t of TARGETS) {
    try {
      // Tall viewport so the plain viewport screenshot itself is long enough
      // to scroll through full-screen (clip beyond the viewport doesn't work).
      const ctx = await browser.newContext({
        viewport: { width: 540, height: Math.round(t.maxH) },
        deviceScaleFactor: 2,
      });
      const page = await ctx.newPage();
      await page.goto(t.url, { waitUntil: "networkidle", timeout: 45000 });
      await page.waitForTimeout(1800);
      await page.screenshot({ path: path.join(OUT, `${t.name}.png`) });
      await ctx.close();
      console.log(`OK  ${t.name.padEnd(18)} | 1080 x ${t.maxH * 2}px`);
    } catch (e) {
      console.log(`ERR ${t.name.padEnd(18)} | ${String(e).slice(0, 70)}`);
    }
  }
  await browser.close();
})();

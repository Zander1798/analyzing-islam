// Capture clean high-res screenshots of the live site for use as ad footage.
// Run: node capture/capture.js
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const OUT = path.join(__dirname, "shots");
fs.mkdirSync(OUT, { recursive: true });

const BASE = "https://analyzingislam.com";
const TARGETS = [
  { name: "catalog", url: `${BASE}/catalog.html` },
  { name: "category-women", url: `${BASE}/category/women.html` },
  { name: "compare", url: `${BASE}/compare.html` },
  { name: "build", url: `${BASE}/build.html` },
  { name: "read", url: `${BASE}/read.html` },
  { name: "stats", url: `${BASE}/stats.html` },
  { name: "watch", url: `${BASE}/watch.html` },
  { name: "reader-quran4", url: `${BASE}/read/quran/4.html` },
];

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  for (const t of TARGETS) {
    try {
      await page.goto(t.url, { waitUntil: "networkidle", timeout: 45000 });
      await page.waitForTimeout(1500); // let fonts/animations settle
      const file = path.join(OUT, `${t.name}.png`);
      await page.screenshot({ path: file });
      const title = await page.title();
      console.log(`OK  ${t.name.padEnd(16)} | ${title.slice(0, 50)}`);
    } catch (e) {
      console.log(`ERR ${t.name.padEnd(16)} | ${String(e).slice(0, 70)}`);
    }
  }
  await browser.close();
})();

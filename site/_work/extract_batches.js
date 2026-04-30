// extract_batches.js
// Reads the 7 catalog HTML files, extracts strong + basic entries,
// and writes batch JSON files to site/_work/batches/
// Usage: node site/_work/extract_batches.js

const fs   = require("fs");
const path = require("path");

const CATALOG_FILES = [
  "bukhari.html",
  "quran.html",
  "muslim.html",
  "abu-dawud.html",
  "ibn-majah.html",
  "nasai.html",
  "tirmidhi.html",
];

const CATALOG_DIR  = path.join(__dirname, "..", "catalog");
const BATCHES_DIR  = path.join(__dirname, "batches");
const BATCH_SIZE   = 15;

// Make sure output dir exists
if (!fs.existsSync(BATCHES_DIR)) fs.mkdirSync(BATCHES_DIR, { recursive: true });

// Extract all <div class="entry" ...> blocks from HTML text.
// Returns array of { id, strength, html }
function extractEntries(html) {
  const entries = [];
  let i = 0;
  while (i < html.length) {
    // Find next opening <div  that has class="entry"
    const divStart = html.indexOf('<div ', i);
    if (divStart === -1) break;

    // Grab the opening tag (up to first >)
    const tagEnd = html.indexOf('>', divStart);
    if (tagEnd === -1) { i = divStart + 5; continue; }
    const openTag = html.slice(divStart, tagEnd + 1);

    if (!openTag.includes('class="entry"') && !openTag.match(/class="entry\s/)) {
      i = divStart + 5;
      continue;
    }

    // Extract id
    const idMatch = openTag.match(/\bid="([^"]+)"/);
    if (!idMatch) { i = divStart + 5; continue; }
    const id = idMatch[1];

    // Extract strength
    const strengthMatch = openTag.match(/data-strength="([^"]+)"/);
    const strength = strengthMatch ? strengthMatch[1] : "";

    // Walk forward tracking <div> depth to find the closing </div>
    let depth = 1;
    let j = tagEnd + 1;
    while (j < html.length && depth > 0) {
      const nextOpen  = html.indexOf('<div',  j);
      const nextClose = html.indexOf('</div>', j);
      if (nextClose === -1) break;
      if (nextOpen !== -1 && nextOpen < nextClose) {
        depth++;
        j = nextOpen + 4;
      } else {
        depth--;
        j = nextClose + 6;
      }
    }

    const entryHtml = html.slice(divStart, j);
    entries.push({ id, strength, html: entryHtml });
    i = j;
  }
  return entries;
}

let allStrong = [];
let allBasic  = [];

for (const filename of CATALOG_FILES) {
  const filepath = path.join(CATALOG_DIR, filename);
  if (!fs.existsSync(filepath)) {
    console.warn("  MISSING:", filepath);
    continue;
  }
  const html = fs.readFileSync(filepath, "utf8");
  const entries = extractEntries(html);

  const strong = entries.filter(e => e.strength === "strong");
  const basic  = entries.filter(e => e.strength === "basic");

  console.log(`${filename}: ${strong.length} strong, ${basic.length} basic (total ${entries.length})`);

  strong.forEach(e => allStrong.push({ ...e, file: filename }));
  basic .forEach(e => allBasic .push({ ...e, file: filename }));
}

console.log(`\nTotal strong: ${allStrong.length}`);
console.log(`Total basic:  ${allBasic.length}`);
console.log(`Total entries to process: ${allStrong.length + allBasic.length}`);

// Merge into one array and assign batch numbers
const allEntries = [
  ...allStrong.map(e => ({ ...e, task: "condense" })),
  ...allBasic .map(e => ({ ...e, task: "add-why-fails" })),
];

const totalBatches = Math.ceil(allEntries.length / BATCH_SIZE);
console.log(`\nWriting ${totalBatches} batch files (${BATCH_SIZE} entries each)...`);

for (let b = 0; b < totalBatches; b++) {
  const batch = allEntries.slice(b * BATCH_SIZE, (b + 1) * BATCH_SIZE);
  const batchNum = String(b + 1).padStart(3, "0");
  const outPath  = path.join(BATCHES_DIR, `batch_${batchNum}.json`);
  fs.writeFileSync(outPath, JSON.stringify(batch, null, 2), "utf8");
}

console.log("Done. Batches written to:", BATCHES_DIR);

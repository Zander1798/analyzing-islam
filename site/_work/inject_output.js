// inject_output.js
// Reads all JSON files from site/_work/output/ and replaces each entry
// in the corresponding catalog HTML file with the rewritten HTML.
// Usage: node site/_work/inject_output.js [--dry-run]

const fs   = require("fs");
const path = require("path");

const OUTPUT_DIR  = path.join(__dirname, "output");
const CATALOG_DIR = path.join(__dirname, "..", "catalog");
const DRY_RUN     = process.argv.includes("--dry-run");

if (DRY_RUN) console.log("[dry-run] No files will be written.\n");

// Load all output JSONs
const outputFiles = fs.readdirSync(OUTPUT_DIR)
  .filter(f => f.endsWith(".json"))
  .sort();

if (outputFiles.length === 0) {
  console.log("No output files found in", OUTPUT_DIR);
  process.exit(0);
}

// Build a map: catalogFile → array of { id, newHtml }
const fileMap = {};
let totalEntries = 0;

for (const fname of outputFiles) {
  const data = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, fname), "utf8"));
  for (const entry of data) {
    if (!entry.id || !entry.file || !entry.newHtml) {
      console.warn(`  [SKIP] Incomplete entry in ${fname}:`, entry.id || "(no id)");
      continue;
    }
    if (!fileMap[entry.file]) fileMap[entry.file] = [];
    fileMap[entry.file].push({ id: entry.id, newHtml: entry.newHtml });
    totalEntries++;
  }
}

console.log(`Loaded ${totalEntries} rewritten entries from ${outputFiles.length} output files.`);

// Replace entries in each catalog file
let replaced = 0;
let missed   = 0;

for (const [filename, entries] of Object.entries(fileMap)) {
  const filepath = path.join(CATALOG_DIR, filename);
  if (!fs.existsSync(filepath)) {
    console.warn(`  [MISSING] ${filepath}`);
    continue;
  }

  let html = fs.readFileSync(filepath, "utf8");
  let changed = false;

  for (const { id, newHtml } of entries) {
    // Find the entry's opening tag by id
    const searchStr = `id="${id}"`;
    const tagStart  = html.indexOf(searchStr);
    if (tagStart === -1) {
      console.warn(`  [NOT FOUND] id="${id}" in ${filename}`);
      missed++;
      continue;
    }

    // Walk backward to find the start of the <div
    let divStart = tagStart;
    while (divStart > 0 && html.slice(divStart, divStart + 4) !== '<div') divStart--;
    if (html.slice(divStart, divStart + 4) !== '<div') {
      console.warn(`  [PARSE ERROR] Could not find <div for id="${id}"`);
      missed++;
      continue;
    }

    // Walk forward to find the matching </div>
    const tagEnd = html.indexOf('>', divStart);
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

    // Replace
    html = html.slice(0, divStart) + newHtml + html.slice(j);
    replaced++;
    changed = true;
  }

  if (changed && !DRY_RUN) {
    fs.writeFileSync(filepath, html, "utf8");
    console.log(`  Updated ${filename}: ${entries.length} entries`);
  } else if (changed) {
    console.log(`  [dry-run] Would update ${filename}: ${entries.length} entries`);
  }
}

console.log(`\nDone. Replaced: ${replaced}, Not found: ${missed}`);

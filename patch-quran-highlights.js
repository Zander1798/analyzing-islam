// Adds highlights panel HTML to all 114 quran surah HTML files
const fs = require('fs');
const path = require('path');

const QURAN_DIR = path.join(__dirname, 'site', 'read-external', 'quran');
const files = fs.readdirSync(QURAN_DIR).filter(f => f.match(/^surah-\d+\.html$/));

const HL_PANEL = `
  <div class="splitter" data-splitter-var="--reader-hl-w" data-splitter-side="right" data-splitter-min="180" data-splitter-max="480" data-splitter-key="reader-hl" aria-label="Resize highlights panel"></div>
  <aside class="hl-card" id="hl-card" aria-label="Highlights">
    <header class="hl-card-head">
      <h3>Highlights</h3>
      <span class="hl-card-count">0</span>
    </header>
    <ol class="hl-card-list" id="hl-card-list"></ol>
    <p class="hl-card-empty">Highlight text in the reader to save it here.</p>
  </aside>
  <button type="button" class="hl-card-toggle" aria-controls="hl-card">&#9733; Highlights</button>`;

let done = 0, skipped = 0;
for (const file of files) {
  const fp = path.join(QURAN_DIR, file);
  let html = fs.readFileSync(fp, 'utf8');

  // Skip if already has the panel
  if (html.includes('hl-card-list')) { skipped++; continue; }

  // Insert panel between </main> and </div> (before <footer)
  // Actual pattern: "</main>\n\n</div>\n\n<footer"
  if (html.includes('</main>\n\n</div>')) {
    html = html.replace('</main>\n\n</div>', '</main>\n' + HL_PANEL + '\n\n</div>');
    fs.writeFileSync(fp, html, 'utf8');
    done++;
  } else {
    console.warn('Pattern not found in', file);
    skipped++;
  }
}
console.log('Patched', done, 'files,', skipped, 'skipped');

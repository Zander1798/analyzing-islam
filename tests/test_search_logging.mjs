// tests/test_search_logging.mjs — structural: the hook exists and is called with a source.
import assert from "node:assert";
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../site/assets/js/reader-search.js", import.meta.url), "utf8");
assert.ok(/AIG\s*&&\s*window\.AIG\.trackSearch|window\.AIG\s*&&\s*window\.AIG\.trackSearch/.test(src)
         || /AIG\.trackSearch\(/.test(src), "reader-search.js must call window.AIG.trackSearch");
console.log("search logging hook present");

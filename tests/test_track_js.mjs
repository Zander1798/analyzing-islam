// tests/test_track_js.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
import vm from "node:vm";

// Load track.js into a sandbox with a fake window, exposing its internals via
// window.AIG.__test (track.js attaches helpers there when window.AIG.__test exists).
function load(sandboxWindow) {
  const code = readFileSync(new URL("../site/assets/js/track.js", import.meta.url), "utf8");
  const ctx = { window: sandboxWindow, document: sandboxWindow.document, localStorage: sandboxWindow.localStorage,
                navigator: sandboxWindow.navigator, location: sandboxWindow.location, matchMedia: sandboxWindow.matchMedia,
                URL: URL, URLSearchParams: URLSearchParams, setTimeout: setTimeout, console: console };
  ctx.window.matchMedia = sandboxWindow.matchMedia;
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return ctx.window.AIG.__test;
}

function fakeWindow(over = {}) {
  const store = {};
  return {
    AIG: { __test: true },
    document: { querySelector: () => null, documentElement: { classList: { contains: () => false } },
                body: { classList: { contains: () => false } }, referrer: over.referrer || "" },
    localStorage: { getItem: (k) => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } },
    navigator: { webdriver: false, userAgent: over.ua || "Mozilla/5.0 (real browser)" },
    location: { pathname: over.pathname || "/catalog.html", hash: over.hash || "", search: over.search || "", hostname: over.hostname || "analyzingislam.com" },
    matchMedia: (q) => ({ matches: !!over.mobile }),
    addEventListener: () => {},
    __supabase: null,
  };
}

// referrerHost: host only, empty for same-site or none
{
  const t = load(fakeWindow({ referrer: "https://www.google.com/search?q=x", hostname: "analyzingislam.com" }));
  assert.equal(t.referrerHost("https://www.google.com/search?q=x", "analyzingislam.com"), "www.google.com");
  assert.equal(t.referrerHost("https://analyzingislam.com/index.html", "analyzingislam.com"), ""); // same-site
  assert.equal(t.referrerHost("", "analyzingislam.com"), "");
}
// device: mobile vs desktop
{
  const t = load(fakeWindow({ mobile: true }));
  assert.equal(t.device(), "mobile");
  const t2 = load(fakeWindow({ mobile: false }));
  assert.equal(t2.device(), "desktop");
}
// visitorId: stable across calls, persisted
{
  const w = fakeWindow();
  const t = load(w);
  const a = t.visitorId(); const b = t.visitorId();
  assert.equal(a, b);
  assert.match(a, /^[0-9a-f-]{16,}$/i);
}
// shouldSkip: bots, embed, localhost, webdriver
{
  assert.equal(load(fakeWindow({ ua: "Googlebot/2.1" })).shouldSkip(), true);
  assert.equal(load(fakeWindow({ search: "?embed=1" })).shouldSkip(), true);
  assert.equal(load(fakeWindow({ hostname: "localhost" })).shouldSkip(), true);
  const w = fakeWindow(); w.navigator.webdriver = true;
  assert.equal(load(w).shouldSkip(), true);
  assert.equal(load(fakeWindow()).shouldSkip(), false);
  // creator opt-out flag: this browser must not be counted
  const wf = fakeWindow(); wf.localStorage.setItem("aig:no-track", "1");
  assert.equal(load(wf).shouldSkip(), true);
}
// pagePath: pathname + hash
{
  const t = load(fakeWindow({ pathname: "/catalog.html", hash: "#entry-x" }));
  assert.equal(t.pagePath(), "/catalog.html#entry-x");
}
console.log("track.js helper tests passed");

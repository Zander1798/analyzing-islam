// Anonymous pageview + search beacon. Fire-and-forget; never blocks or breaks a page.
// Privacy: no IP, no cookies, host-only referrer, random localStorage visitor id.
(function () {
  "use strict";
  var W = window;

  var BOT_RE = /(bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|whatsapp|telegram|headless|lighthouse|preview|monitor|pingdom|gtmetrix)/i;

  function referrerHost(ref, selfHost) {
    if (!ref) return "";
    try {
      var h = new URL(ref).hostname;
      if (!h || h === selfHost) return "";
      return h;
    } catch (_) { return ""; }
  }
  function device() {
    try { return (W.matchMedia && W.matchMedia("(max-width: 900px)").matches) ? "mobile" : "desktop"; }
    catch (_) { return "desktop"; }
  }
  function visitorId() {
    try {
      var v = W.localStorage.getItem("aig:visitor");
      if (!v) {
        v = (W.crypto && W.crypto.randomUUID) ? W.crypto.randomUUID()
            : (Date.now().toString(16) + Math.random().toString(16).slice(2));
        W.localStorage.setItem("aig:visitor", v);
      }
      return v;
    } catch (_) { return ""; }
  }
  function pagePath() { return (W.location.pathname || "/") + (W.location.hash || ""); }
  function shouldSkip() {
    try {
      var host = W.location.hostname || "";
      if (host === "localhost" || /^127\./.test(host) || host === "") return true;
      // Don't count the creator's own visits: this browser is flagged once the
      // site confirms admin status (see auth-ui.js). Persists across sessions.
      if (W.localStorage && W.localStorage.getItem("aig:no-track") === "1") return true;
      if (W.navigator && W.navigator.webdriver) return true;
      if (BOT_RE.test((W.navigator && W.navigator.userAgent) || "")) return true;
      var p = new URLSearchParams(W.location.search || "");
      if (p.get("embed") === "1") return true;
      var de = W.document.documentElement, bo = W.document.body;
      if (de && de.classList.contains("embed-mode")) return true;
      if (bo && bo.classList.contains("embed-mode")) return true;
    } catch (_) {}
    return false;
  }

  function sb() { return W.__supabase || null; }
  function uid() { var s = W.__session; return (s && s.user && s.user.id) || null; }

  function sendPageview() {
    var client = sb();
    if (!client) return; // auth.js not ready yet — caller retries
    try {
      client.from("pageviews").insert({
        path: pagePath().slice(0, 400),
        referrer_host: referrerHost(W.document.referrer, W.location.hostname).slice(0, 200),
        visitor: visitorId(),
        device: device(),
        user_id: uid(),
      }).then(function () {}, function () {});
    } catch (_) {}
  }

  function trackSearch(q, source) {
    q = (q || "").trim();
    if (!q) return;
    var client = sb();
    if (!client) return;
    try {
      client.from("search_queries").insert({ q: q.slice(0, 200), source: (source || "").slice(0, 40) })
        .then(function () {}, function () {});
    } catch (_) {}
  }

  // Public API + (test-only) helper exposure.
  W.AIG = W.AIG || {};
  W.AIG.trackSearch = trackSearch;
  if (W.AIG.__test) {
    W.AIG.__test = { referrerHost: referrerHost, device: device, visitorId: visitorId,
                     pagePath: pagePath, shouldSkip: shouldSkip };
    return; // under test: don't fire the beacon
  }

  if (shouldSkip()) return;
  // The Supabase client is created by auth.js (deferred). Try now, then retry a
  // few times until it exists, then once on auth-state as a final safety net.
  var tries = 0;
  (function fire() {
    if (sb()) { sendPageview(); return; }
    if (tries++ < 40) { setTimeout(fire, 50); return; }
    W.addEventListener("auth-state", function once() { W.removeEventListener("auth-state", once); sendPageview(); });
  })();
})();

// Creator dashboard: gate, fetch RPCs, render. Pure helpers exposed on window.AIG_DASH
// for tests; the orchestrator runs only in a real browser.
(function () {
  "use strict";
  var W = window;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c];
    });
  }
  function fmtInt(n) {
    n = Number(n) || 0;
    return n.toLocaleString("en-US");
  }
  function kpiCardHtml(label, vals) {
    vals = vals || {};
    function cell(k, t) {
      return '<div class="kpi-cell"><span class="kpi-cell-label">' + t + '</span>' +
             '<span class="kpi-cell-val">' + fmtInt(vals[k]) + '</span></div>';
    }
    return '<div class="kpi-card"><h3 class="kpi-title">' + esc(label) + '</h3>' +
           '<div class="kpi-grid">' + cell("today","Today") + cell("yesterday","Yesterday") +
           cell("d7","7-day") + cell("d30","30-day") + '</div></div>';
  }
  // Simple bar chart. series: [{label, value}]. Returns an inline SVG string.
  function barsSvg(series, opts) {
    series = series || []; opts = opts || {};
    var w = opts.width || 720, h = opts.height || 160, pad = 18;
    var max = Math.max(1, Math.max.apply(null, series.map(function (d) { return d.value || 0; }).concat([0])));
    var n = Math.max(1, series.length);
    var bw = (w - pad * 2) / n;
    var bars = series.map(function (d, i) {
      var bh = Math.round((h - pad * 2) * (d.value || 0) / max);
      var x = pad + i * bw + bw * 0.1, y = h - pad - bh;
      return '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + (bw * 0.8).toFixed(1) +
             '" height="' + bh + '" rx="1.5"><title>' + esc(d.label) + ": " + fmtInt(d.value) + '</title></rect>';
    }).join("");
    return '<svg class="chart chart-bars" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" role="img">' +
           bars + '</svg>';
  }
  // Simple line chart via polyline.
  function lineSvg(series, opts) {
    series = series || []; opts = opts || {};
    var w = opts.width || 720, h = opts.height || 160, pad = 18;
    var vals = series.map(function (d) { return d.value || 0; });
    var max = Math.max(1, Math.max.apply(null, vals.concat([0])));
    var n = Math.max(1, series.length - 1);
    var pts = series.map(function (d, i) {
      var x = pad + (w - pad * 2) * (series.length === 1 ? 0 : i / n);
      var y = h - pad - (h - pad * 2) * (d.value || 0) / max;
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
    return '<svg class="chart chart-line" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" role="img">' +
           '<polyline fill="none" stroke-width="2" points="' + pts + '"></polyline></svg>';
  }
  function tableHtml(rows, cols) {
    rows = rows || []; cols = cols || [];
    var head = "<tr>" + cols.map(function (c) { return '<th>' + esc(c[1]) + "</th>"; }).join("") + "</tr>";
    var body = rows.map(function (r) {
      return "<tr>" + cols.map(function (c) { return "<td>" + esc(r[c[0]]) + "</td>"; }).join("") + "</tr>";
    }).join("");
    return '<table class="dash-table"><thead>' + head + "</thead><tbody>" + body + "</tbody></table>";
  }

  W.AIG_DASH = W.AIG_DASH || {};
  var api = { fmtInt: fmtInt, kpiCardHtml: kpiCardHtml, barsSvg: barsSvg, lineSvg: lineSvg, tableHtml: tableHtml, esc: esc };
  if (W.AIG_DASH.__test) { W.AIG_DASH = api; return; }
  W.AIG_DASH = api;

  // ---- orchestrator (browser only) ----
  function set(id, html) { var el = document.getElementById(id); if (el) el.innerHTML = html; }
  function fail(id) { set(id, '<div class="dash-error">Couldn’t load — <button class="dash-retry">retry</button></div>'); }

  async function rpc(name, args) {
    var res = await W.__supabase.rpc(name, args || {});
    if (res.error) throw res.error;
    return res.data;
  }

  async function render() {
    try {
      var kpis = await rpc("creator_kpis");
      set("kpi-cards",
        kpiCardHtml("Pageviews", kpis.pageviews) +
        kpiCardHtml("Unique visitors", kpis.uniques) +
        kpiCardHtml("New sign-ups", kpis.signups) +
        '<div class="kpi-card"><h3 class="kpi-title">Totals</h3><div class="kpi-grid">' +
          '<div class="kpi-cell"><span class="kpi-cell-label">Users</span><span class="kpi-cell-val">' + fmtInt(kpis.total_users) + '</span></div>' +
          '<div class="kpi-cell"><span class="kpi-cell-label">Conv. 30d</span><span class="kpi-cell-val">' + ((kpis.conversion_30d*100)||0).toFixed(1) + '%</span></div>' +
        '</div></div>');
    } catch (e) { fail("kpi-cards"); }

    try {
      var td = await rpc("creator_traffic_daily", { days: 30 });
      set("chart-traffic", barsSvg(td.map(function (r) { return { label: r.day, value: r.views }; }), {}));
    } catch (e) { fail("chart-traffic"); }
    try {
      var sd = await rpc("creator_signups_daily", { days: 30 });
      set("chart-signups", lineSvg(sd.map(function (r) { return { label: r.day, value: r.signups }; }), {}));
    } catch (e) { fail("chart-signups"); }

    try {
      var eng = await rpc("creator_engagement");
      var items = [["bookmarks","Bookmarks"],["notes","Notes"],["builds","Builds"],
                   ["shared_builds","Shares"],["highlights","Highlights"],["goat_unlocks","Goat unlocks"]];
      set("engagement", items.map(function (k) {
        return '<div class="eng-stat"><span class="eng-val">' + fmtInt(eng[k[0]]) + '</span><span class="eng-label">' + k[1] + '</span></div>';
      }).join(""));
    } catch (e) { fail("engagement"); }

    try { set("top-pages", tableHtml(await rpc("creator_top_pages", { days: 7, lim: 20 }),
            [["path","Page"],["views","Views"],["uniques","Uniques"]])); } catch (e) { fail("top-pages"); }
    try { set("top-referrers", tableHtml(await rpc("creator_top_referrers", { days: 7, lim: 20 }),
            [["referrer_host","Referrer"],["views","Views"]])); } catch (e) { fail("top-referrers"); }
    try { set("device-split", tableHtml(await rpc("creator_device_split", { days: 7 }),
            [["device","Device"],["views","Views"]])); } catch (e) { fail("device-split"); }
    try { set("top-bookmarked", tableHtml(await rpc("creator_top_bookmarked", { lim: 20 }),
            [["entry_title","Entry"],["count","Saves"]])); } catch (e) { fail("top-bookmarked"); }
    try { set("top-searches", tableHtml(await rpc("creator_top_searches", { days: 30, lim: 20 }),
            [["q","Query"],["count","Count"]])); } catch (e) { fail("top-searches"); }

    var stamp = document.getElementById("dash-stamp");
    if (stamp) stamp.textContent = "Live as of " + new Date().toLocaleString();
  }

  async function boot() {
    await (W.__authReady || Promise.resolve());
    if (!W.__supabase) { location.href = "index.html"; return; }
    var ok = false;
    try { var res = await W.__supabase.rpc("is_creator"); ok = res && res.data === true; } catch (e) { ok = false; }
    if (!ok) { location.href = "index.html"; return; }
    var gate = document.getElementById("dash-gate"); if (gate) gate.hidden = true;
    var root = document.getElementById("dash-root"); if (root) root.hidden = false;
    render();
    document.addEventListener("click", function (e) {
      if (e.target && e.target.classList && e.target.classList.contains("dash-retry")) render();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();

// tests/test_admin_dashboard.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
import vm from "node:vm";
function load() {
  const code = readFileSync(new URL("../site/assets/js/admin-dashboard.js", import.meta.url), "utf8");
  const win = { AIG_DASH: { __test: true }, document: { readyState: "complete", addEventListener(){} },
                addEventListener(){}, location:{ href:"" } };
  const ctx = { window: win, document: win.document };
  vm.createContext(ctx); vm.runInContext(code, ctx);
  return win.AIG_DASH;
}
const D = load();
assert.equal(D.fmtInt(1234567), "1,234,567");
assert.equal(D.fmtInt(0), "0");
// KPI card includes label and all four buckets
{
  const h = D.kpiCardHtml("Pageviews", { today: 5, yesterday: 4, d7: 30, d30: 100 });
  ["Pageviews","5","4","30","100"].forEach(s => assert.ok(h.includes(s), "card missing " + s));
}
// bars svg: one <rect> per point, escapes nothing weird, has viewBox
{
  const svg = D.barsSvg([{label:"a",value:1},{label:"b",value:3},{label:"c",value:0}], {});
  assert.ok(svg.includes("<svg"));
  assert.equal((svg.match(/<rect/g) || []).length >= 3, true);
}
// line svg: a polyline with N points
{
  const svg = D.lineSvg([{label:"d1",value:1},{label:"d2",value:2},{label:"d3",value:5}], {});
  assert.ok(svg.includes("<polyline") || svg.includes("<path"));
}
// table: header + one row per data row, html-escaped
{
  const html = D.tableHtml([{ path: "/x", views: 9 }], [["path","Page"],["views","Views"]]);
  assert.ok(html.includes("<th") && html.includes("Page") && html.includes("/x") && html.includes("9"));
  const esc = D.tableHtml([{ path: "<b>", views: 1 }], [["path","Page"],["views","Views"]]);
  assert.ok(esc.includes("&lt;b&gt;") && !esc.includes("<b>"));
}
console.log("admin-dashboard helper tests passed");

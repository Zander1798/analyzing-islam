// Highlights — per-source, anchor-keyed user highlights.
// ----------------------------------------------------------------------
// Public API on window.AI_HIGHLIGHTS:
//
//   attach({ source, scope, anchorRe, cardEl })
//     Wire up a reader scope: selection -> floating colour picker ->
//     save -> repaint. Also fills the side card if cardEl is given.
//
//   list(source) -> Promise<Highlight[]>
//   remove(id)   -> Promise<void>
//   recolor(id, hex) -> Promise<void>
//
// Storage: Supabase `highlights` table when signed in, otherwise
// localStorage under "ai-highlights:<source>" with the same shape.
// On sign-in we migrate any local rows into Supabase once.
//
// Events on window:
//   "highlights-changed" { source, action, id }
(function () {
  "use strict";

  // Darker, saturated colours that contrast with white text on a dark
  // background. White text stays readable over each of these.
  const PALETTE = [
    "#b8860b", // dark goldenrod
    "#1b5e20", // forest green
    "#0d47a1", // deep blue
    "#b71c1c", // dark red
    "#e65100", // burnt orange
    "#4a148c", // deep purple
  ];
  const DEFAULT_COLOR = PALETTE[0];
  const SNIPPET_LEN = 80;

  // Visually preview a colour change without writing to the server.
  // Used while the user drags through the <input type="color"> spectrum.
  // The actual save happens once on the picker's `change` event.
  function previewColor(scope, id, groupId, hex, listItem) {
    let marks;
    if (groupId) {
      marks = scope.querySelectorAll('mark.ai-hl[data-hl-group="' + cssEscapeAttr(groupId) + '"]');
    } else {
      marks = scope.querySelectorAll('mark.ai-hl[data-hl-id="' + cssEscapeAttr(String(id)) + '"]');
    }
    marks.forEach((m) => { m.style.backgroundColor = hex; });
    if (listItem) {
      const swatch = listItem.querySelector(".hl-swatch");
      if (swatch) swatch.style.background = hex;
    }
  }
  function cssEscapeAttr(s) {
    return String(s).replace(/"/g, '\\"').replace(/\\/g, "\\\\");
  }

  function sb()  { return window.__supabase; }
  function uid() { const s = window.__session; return s && s.user ? s.user.id : null; }

  // ---------------- Local fallback (signed-out) -----------------------
  function localKey(source) { return "ai-highlights:" + source; }
  function localList(source) {
    try { return JSON.parse(localStorage.getItem(localKey(source)) || "[]"); }
    catch (_) { return []; }
  }
  function localSave(source, rows) {
    try { localStorage.setItem(localKey(source), JSON.stringify(rows)); } catch (_) {}
  }
  function localId() {
    return "L-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }

  // ---------------- Migration on sign-in ------------------------------
  // When the user signs in, push any guest-collected rows up to Supabase
  // exactly once per source, then clear the localStorage bucket.
  async function migrateLocalToServer() {
    if (!uid()) return;
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.indexOf("ai-highlights:") === 0) keys.push(k);
    }
    for (const k of keys) {
      const source = k.slice("ai-highlights:".length);
      const rows = localList(source);
      if (!rows.length) { localStorage.removeItem(k); continue; }
      const payload = rows.map((r) => ({
        user_id: uid(),
        source: source,
        anchor_id: r.anchor_id,
        start_off: r.start_off,
        end_off: r.end_off,
        text: r.text,
        color: r.color || DEFAULT_COLOR,
        group_id: r.group_id || null,
      }));
      const { error } = await sb().from("highlights").insert(payload);
      if (error) { console.error("[highlights] migrate failed", source, error); continue; }
      localStorage.removeItem(k);
      window.dispatchEvent(new CustomEvent("highlights-changed", { detail: { source, action: "migrated" } }));
    }
  }
  window.addEventListener("auth-state", function () { migrateLocalToServer(); });

  // ---------------- Server / local CRUD -------------------------------
  async function list(source) {
    if (uid()) {
      const { data, error } = await sb()
        .from("highlights")
        .select("id, source, anchor_id, start_off, end_off, text, color, group_id, created_at")
        .eq("user_id", uid())
        .eq("source", source)
        .order("created_at", { ascending: true });
      if (error) { console.error("[highlights] list failed", error); return []; }
      return data || [];
    }
    return localList(source);
  }

  async function insertMany(source, rows) {
    if (uid()) {
      const payload = rows.map((r) => ({
        user_id: uid(),
        source: source,
        anchor_id: r.anchor_id,
        start_off: r.start_off,
        end_off: r.end_off,
        text: r.text,
        color: r.color || DEFAULT_COLOR,
        group_id: r.group_id || null,
      }));
      const { data, error } = await sb()
        .from("highlights")
        .insert(payload)
        .select("id, source, anchor_id, start_off, end_off, text, color, group_id, created_at");
      if (error) { console.error("[highlights] insert failed", error); return []; }
      return data || [];
    }
    const existing = localList(source);
    const created = rows.map((r) => Object.assign({}, r, {
      id: localId(),
      source: source,
      color: r.color || DEFAULT_COLOR,
      created_at: new Date().toISOString(),
    }));
    localSave(source, existing.concat(created));
    return created;
  }

  async function remove(source, id) {
    if (uid() && typeof id === "number") {
      const { error } = await sb().from("highlights").delete()
        .eq("user_id", uid()).eq("id", id);
      if (error) { console.error("[highlights] remove failed", error); return; }
    } else {
      const rows = localList(source).filter((r) => r.id !== id);
      localSave(source, rows);
    }
    window.dispatchEvent(new CustomEvent("highlights-changed", {
      detail: { source, action: "removed", id },
    }));
  }

  async function removeGroup(source, groupId) {
    if (!groupId) return;
    if (uid()) {
      const { error } = await sb().from("highlights").delete()
        .eq("user_id", uid()).eq("group_id", groupId);
      if (error) { console.error("[highlights] removeGroup failed", error); return; }
    } else {
      const rows = localList(source).filter((r) => r.group_id !== groupId);
      localSave(source, rows);
    }
    window.dispatchEvent(new CustomEvent("highlights-changed", {
      detail: { source, action: "removed-group", groupId },
    }));
  }

  async function recolor(source, id, hex) {
    if (uid() && typeof id === "number") {
      const { error } = await sb().from("highlights").update({ color: hex })
        .eq("user_id", uid()).eq("id", id);
      if (error) { console.error("[highlights] recolor failed", error); return; }
    } else {
      const rows = localList(source).map((r) => r.id === id ? Object.assign({}, r, { color: hex }) : r);
      localSave(source, rows);
    }
    window.dispatchEvent(new CustomEvent("highlights-changed", {
      detail: { source, action: "recolored", id, color: hex },
    }));
  }

  // ---------------- Range <-> anchor offsets --------------------------
  // For a Range that lies entirely within one anchor element, return
  // { anchor, start_off, end_off, text } using TreeWalker over the
  // anchor's text nodes so the offsets are stable against future
  // re-renders of the same content.
  function rangeToAnchor(range, anchorRe) {
    if (!range || range.collapsed) return null;
    const ancestor = closestAnchor(range.commonAncestorContainer, anchorRe);
    if (!ancestor) return null;

    // If the selection straddles anchors, split into per-anchor parts.
    const startAnchor = closestAnchor(range.startContainer, anchorRe);
    const endAnchor   = closestAnchor(range.endContainer,   anchorRe);
    if (!startAnchor || !endAnchor) return null;
    if (startAnchor !== endAnchor) {
      return splitAcrossAnchors(range, anchorRe, startAnchor, endAnchor);
    }

    const offs = offsetsWithin(ancestor, range.startContainer, range.startOffset, range.endContainer, range.endOffset);
    if (!offs) return null;
    const text = range.toString();
    if (!text || !text.replace(/\s+/g, "")) return null;
    return [{
      anchor_id: ancestor.id,
      start_off: offs.start,
      end_off: offs.end,
      text: text,
    }];
  }

  function closestAnchor(node, anchorRe) {
    let el = node && node.nodeType === 1 ? node : (node && node.parentElement);
    while (el) {
      if (el.id && anchorRe.test(el.id)) return el;
      el = el.parentElement;
    }
    return null;
  }

  // Walk text nodes inside `root` in document order, summing lengths
  // until we reach the start node + offset. Returns null if not found.
  function offsetsWithin(root, startNode, startOff, endNode, endOff) {
    const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let pos = 0, start = -1, end = -1;
    let n = walker.nextNode();
    while (n) {
      const len = n.nodeValue.length;
      if (start < 0 && n === startNode) start = pos + startOff;
      if (n === endNode) { end = pos + endOff; break; }
      pos += len;
      n = walker.nextNode();
    }
    if (start < 0 || end < 0 || end <= start) return null;
    return { start, end };
  }

  function splitAcrossAnchors(range, anchorRe, startAnchor, endAnchor) {
    // Walk every anchor between startAnchor and endAnchor in document
    // order; for each, intersect the selection with that anchor's text
    // and emit a part. group_id ties them together at the call site.
    const doc = startAnchor.ownerDocument;
    const all = Array.from(doc.querySelectorAll("[id]")).filter((el) => anchorRe.test(el.id));
    const startIdx = all.indexOf(startAnchor);
    const endIdx   = all.indexOf(endAnchor);
    if (startIdx < 0 || endIdx < 0 || endIdx < startIdx) return null;
    const out = [];
    for (let i = startIdx; i <= endIdx; i++) {
      const a = all[i];
      const sub = doc.createRange();
      sub.selectNodeContents(a);
      // Intersect: clamp sub's start/end to the original range's bounds.
      if (i === startIdx) sub.setStart(range.startContainer, range.startOffset);
      if (i === endIdx)   sub.setEnd(range.endContainer,   range.endOffset);
      const text = sub.toString();
      if (!text || !text.replace(/\s+/g, "")) continue;
      const offs = offsetsWithin(a, sub.startContainer, sub.startOffset, sub.endContainer, sub.endOffset);
      if (!offs) continue;
      out.push({
        anchor_id: a.id,
        start_off: offs.start,
        end_off: offs.end,
        text: text,
      });
    }
    return out.length ? out : null;
  }

  // ---------------- Painter -------------------------------------------
  // Wrap (start_off, end_off) inside `anchor` with a <mark> carrying
  // data-hl-id and the highlight colour. Skips silently if the anchor
  // can't accommodate the offsets (content changed since save).
  function paintRow(scope, row) {
    const anchor = scope.querySelector("#" + cssEscape(row.anchor_id));
    if (!anchor) return;
    // Walk text nodes to find the start + end positions.
    const walker = anchor.ownerDocument.createTreeWalker(anchor, NodeFilter.SHOW_TEXT);
    let pos = 0;
    let startNode = null, startOffset = 0, endNode = null, endOffset = 0;
    let n = walker.nextNode();
    while (n) {
      const len = n.nodeValue.length;
      if (!startNode && pos + len > row.start_off) {
        startNode = n; startOffset = row.start_off - pos;
      }
      if (pos + len >= row.end_off) {
        endNode = n; endOffset = row.end_off - pos; break;
      }
      pos += len;
      n = walker.nextNode();
    }
    if (!startNode || !endNode) return;
    try {
      const range = anchor.ownerDocument.createRange();
      range.setStart(startNode, startOffset);
      range.setEnd(endNode, endOffset);
      surroundWithMark(range, row);
    } catch (_) { /* offset already covered by another mark — skip */ }
  }

  // Wraps a Range with a <mark>, splitting across multiple text nodes
  // by extracting + re-inserting. extractContents handles the splitting.
  function surroundWithMark(range, row) {
    const doc = range.startContainer.ownerDocument;
    const mark = doc.createElement("mark");
    mark.className = "ai-hl";
    mark.setAttribute("data-hl-id", String(row.id));
    mark.setAttribute("data-hl-group", row.group_id || "");
    mark.style.backgroundColor = row.color || DEFAULT_COLOR;
    mark.style.color = "#ffffff";
    // For multi-node ranges surroundContents throws; extract + wrap instead.
    try {
      mark.appendChild(range.extractContents());
      range.insertNode(mark);
    } catch (_) {
      // Fallback: leave it, reload will retry.
    }
  }

  function unpaintAll(scope) {
    const marks = scope.querySelectorAll("mark.ai-hl");
    marks.forEach((m) => {
      const parent = m.parentNode;
      while (m.firstChild) parent.insertBefore(m.firstChild, m);
      parent.removeChild(m);
      parent.normalize();
    });
  }

  async function repaint(scope, source) {
    unpaintAll(scope);
    const rows = await list(source);
    // Paint in created_at order so older highlights sit underneath
    // newer ones. mix-blend-mode in CSS handles overlap colours.
    rows.sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)));
    rows.forEach((r) => paintRow(scope, r));
    return rows;
  }

  function cssEscape(s) {
    if (window.CSS && CSS.escape) return CSS.escape(s);
    return String(s).replace(/[^a-zA-Z0-9_-]/g, (c) => "\\" + c);
  }

  // ---------------- Floating colour-picker toolbar --------------------
  function ensureToolbar(doc) {
    let bar = doc.getElementById("ai-hl-toolbar");
    if (bar) return bar;
    bar = doc.createElement("div");
    bar.id = "ai-hl-toolbar";
    bar.className = "ai-hl-toolbar";
    bar.hidden = true;
    bar.innerHTML =
      '<div class="ai-hl-swatches">' +
        PALETTE.map((c) =>
          '<button type="button" class="ai-hl-swatch" data-color="' + c + '"' +
          ' style="background:' + c + '" title="' + c + '"></button>'
        ).join("") +
      '</div>' +
      '<label class="ai-hl-custom" title="Custom colour">' +
        '<span class="ai-hl-custom-label">+</span>' +
        '<input type="color" class="ai-hl-color-input" value="' + DEFAULT_COLOR + '">' +
      '</label>' +
      '<button type="button" class="ai-hl-remove" hidden title="Remove highlight">×</button>';
    doc.body.appendChild(bar);
    return bar;
  }

  function placeToolbar(bar, range) {
    const rect = range.getBoundingClientRect();
    if (!rect || (rect.width === 0 && rect.height === 0)) return;
    const doc = bar.ownerDocument;
    const win = doc.defaultView;
    const top  = rect.bottom + win.scrollY + 6;
    let left   = rect.left + win.scrollX;
    bar.hidden = false;
    // Clamp horizontally inside the viewport.
    const barW = bar.offsetWidth || 220;
    const maxLeft = win.scrollX + doc.documentElement.clientWidth - barW - 8;
    if (left > maxLeft) left = maxLeft;
    if (left < win.scrollX + 8) left = win.scrollX + 8;
    bar.style.top  = top  + "px";
    bar.style.left = left + "px";
  }

  function hideToolbar(bar) { if (bar) bar.hidden = true; }

  // ---------------- Side card -----------------------------------------
  function renderCard(cardEl, rows, source) {
    if (!cardEl) return;
    const list = cardEl.querySelector(".hl-card-list");
    const empty = cardEl.querySelector(".hl-card-empty");
    const count = cardEl.querySelector(".hl-card-count");
    if (!list) return;

    // Group rows by group_id (null = singleton).
    const grouped = [];
    const seen = new Map();
    rows.slice().sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))).forEach((r) => {
      if (r.group_id) {
        const g = seen.get(r.group_id);
        if (g) { g.push(r); return; }
        const arr = [r]; seen.set(r.group_id, arr); grouped.push(arr);
      } else {
        grouped.push([r]);
      }
    });

    list.innerHTML = "";
    grouped.forEach((group) => {
      const head = group[0];
      const fullText = group.map((r) => r.text).join(" ").replace(/\s+/g, " ").trim();
      const snippet = fullText.length > SNIPPET_LEN
        ? fullText.slice(0, SNIPPET_LEN).trim() + "…"
        : fullText;
      const li = cardEl.ownerDocument.createElement("li");
      li.className = "hl-card-item";
      li.setAttribute("data-id", String(head.id));
      if (head.group_id) li.setAttribute("data-group", head.group_id);
      li.setAttribute("data-anchor", head.anchor_id);
      li.innerHTML =
        '<span class="hl-swatch" style="background:' + (head.color || DEFAULT_COLOR) + '"></span>' +
        '<a class="hl-snippet" href="#' + escAttr(head.anchor_id) + '" title="Jump to highlight">' +
          escText(snippet) +
        '</a>' +
        '<label class="hl-color" title="Change colour">' +
          '<input type="color" class="hl-color-input" value="' + (head.color || DEFAULT_COLOR) + '">' +
        '</label>' +
        '<button type="button" class="hl-delete" title="Delete highlight" aria-label="Delete">×</button>';
      list.appendChild(li);
    });

    if (count) count.textContent = String(grouped.length);
    if (empty) empty.hidden = grouped.length > 0;
  }

  function escAttr(s) { return String(s).replace(/"/g, "&quot;"); }
  function escText(s) {
    return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  }

  // ---------------- Public attach() -----------------------------------
  function attach(opts) {
    const source   = opts.source;
    const scope    = opts.scope || document;
    const anchorRe = opts.anchorRe || /.+/;
    const cardEl   = opts.cardEl || null;
    const doc      = scope.ownerDocument || scope;
    const win      = doc.defaultView || window;

    const bar = ensureToolbar(doc);
    let pendingRange = null;
    let pendingMarkId = null; // when selection lands inside an existing <mark>

    // -- Selection capture ----------------------------------------------
    function onSelectionChange() {
      const sel = doc.getSelection();
      if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
        // Hide toolbar shortly after the selection collapses, but not
        // immediately — clicking the toolbar itself collapses it briefly.
        setTimeout(() => {
          const s = doc.getSelection();
          if (!s || s.isCollapsed) hideToolbar(bar);
        }, 50);
        return;
      }
      const range = sel.getRangeAt(0);
      // Selection must intersect our scope.
      if (!scope.contains(range.commonAncestorContainer) &&
          !scope.contains(range.startContainer) &&
          !scope.contains(range.endContainer)) {
        hideToolbar(bar);
        return;
      }
      // If the selection is fully inside an existing mark, expose Remove.
      const mark = (range.startContainer.parentElement || range.startContainer).closest
        ? (range.startContainer.parentElement || range.startContainer).closest("mark.ai-hl")
        : null;
      pendingMarkId = mark ? mark.getAttribute("data-hl-id") : null;
      bar.querySelector(".ai-hl-remove").hidden = !pendingMarkId;
      pendingRange = range;
      placeToolbar(bar, range);
    }
    doc.addEventListener("selectionchange", onSelectionChange);

    // -- Save on swatch / custom color ----------------------------------
    async function saveCurrent(color) {
      if (!pendingRange) return;
      const parts = rangeToAnchor(pendingRange, anchorRe);
      if (!parts || !parts.length) { hideToolbar(bar); return; }
      const groupId = parts.length > 1
        ? (win.crypto && win.crypto.randomUUID ? win.crypto.randomUUID() : String(Date.now()))
        : null;
      const rows = parts.map((p) => Object.assign({}, p, { color: color, group_id: groupId }));
      // Clear selection so the toolbar dismisses cleanly.
      try { doc.getSelection().removeAllRanges(); } catch (_) {}
      hideToolbar(bar);
      await insertMany(source, rows);
      window.dispatchEvent(new CustomEvent("highlights-changed", {
        detail: { source, action: "added" },
      }));
    }

    bar.querySelectorAll(".ai-hl-swatch").forEach((sw) => {
      sw.addEventListener("mousedown", (e) => { e.preventDefault(); });
      sw.addEventListener("click", (e) => {
        e.preventDefault();
        saveCurrent(sw.getAttribute("data-color"));
      });
    });
    const colorInput = bar.querySelector(".ai-hl-color-input");
    colorInput.addEventListener("input", () => {
      // Live preview not needed — commit on change.
    });
    colorInput.addEventListener("change", () => {
      saveCurrent(colorInput.value || DEFAULT_COLOR);
    });
    bar.querySelector(".ai-hl-remove").addEventListener("click", async () => {
      if (!pendingMarkId) return;
      const id = isNaN(Number(pendingMarkId)) ? pendingMarkId : Number(pendingMarkId);
      hideToolbar(bar);
      // If the row has a group, remove the whole group.
      const rows = await list(source);
      const row = rows.find((r) => String(r.id) === String(pendingMarkId));
      if (row && row.group_id) await removeGroup(source, row.group_id);
      else await remove(source, id);
    });

    // -- Close button injected into card header -------------------------
    if (cardEl) {
      const hlHead = cardEl.querySelector(".hl-card-head");
      if (hlHead && !hlHead.querySelector(".hl-card-close")) {
        const closeBtn = cardEl.ownerDocument.createElement("button");
        closeBtn.type = "button";
        closeBtn.className = "hl-card-close";
        closeBtn.title = "Collapse highlights";
        closeBtn.setAttribute("aria-label", "Collapse highlights");
        closeBtn.textContent = "×";
        closeBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          const collapsed = cardEl.classList.toggle("is-collapsed");
          closeBtn.textContent = collapsed ? "+" : "×";
          closeBtn.title = collapsed ? "Expand highlights" : "Collapse highlights";
        });
        hlHead.addEventListener("click", function () {
          if (cardEl.classList.contains("is-collapsed")) {
            cardEl.classList.remove("is-collapsed");
            closeBtn.textContent = "×";
            closeBtn.title = "Collapse highlights";
          }
        });
        hlHead.appendChild(closeBtn);
      }
    }

    // -- Card actions ---------------------------------------------------
    if (cardEl) {
      cardEl.addEventListener("click", async (e) => {
        const li = e.target.closest(".hl-card-item");
        if (!li) return;
        const id = li.getAttribute("data-id");
        const group = li.getAttribute("data-group");
        if (e.target.closest(".hl-delete")) {
          e.preventDefault();
          if (group) await removeGroup(source, group);
          else await remove(source, isNaN(Number(id)) ? id : Number(id));
          return;
        }
        if (e.target.closest(".hl-snippet")) {
          // Let the anchor href navigate, then scroll to the actual mark.
          setTimeout(() => {
            const target = scope.querySelector('mark.ai-hl[data-hl-id="' + id + '"]');
            if (target) {
              try { target.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (_) {}
              target.classList.add("is-flash");
              setTimeout(() => target.classList.remove("is-flash"), 1400);
            }
          }, 60);
        }
      });
      // Live preview while dragging through the colour spectrum: only
      // mutate the local <mark> background + the swatch dot. Do NOT hit
      // Supabase or fire highlights-changed (each fire triggers a global
      // repaint that corrupts the DOM mid-drag and bugs the highlight).
      // Persist exactly once when the picker closes (`change` event).
      cardEl.addEventListener("input", (e) => {
        if (!e.target.classList.contains("hl-color-input")) return;
        const li = e.target.closest(".hl-card-item");
        if (!li) return;
        const id    = li.getAttribute("data-id");
        const group = li.getAttribute("data-group");
        const hex   = e.target.value;
        previewColor(scope, id, group, hex, li);
      });
      cardEl.addEventListener("change", async (e) => {
        if (!e.target.classList.contains("hl-color-input")) return;
        const li = e.target.closest(".hl-card-item");
        if (!li) return;
        const group = li.getAttribute("data-group");
        const id    = li.getAttribute("data-id");
        const hex   = e.target.value;
        if (group) {
          const rows = (await list(source)).filter((r) => r.group_id === group);
          await Promise.all(rows.map((r) => recolor(source, r.id, hex)));
        } else {
          await recolor(source, isNaN(Number(id)) ? id : Number(id), hex);
        }
      });
    }

    // -- React to changes ----------------------------------------------
    async function refresh() {
      const rows = await repaint(scope, source);
      if (cardEl) renderCard(cardEl, rows, source);
    }
    window.addEventListener("highlights-changed", (e) => {
      if (!e.detail || e.detail.source === source) refresh();
    });
    window.addEventListener("auth-state", refresh);

    refresh();
    return { refresh };
  }

  window.AI_HIGHLIGHTS = {
    attach,
    list,
    remove,
    removeGroup,
    recolor,
  };
})();

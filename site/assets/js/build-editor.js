// Build editor controller.
// ------------------------------------------------------------------
// - Left pane: a Quill rich-text editor (Snow theme, full toolbar).
// - Right pane: a compare-style source picker + search + iframe.
// - Drag text from the iframe into Quill — relies on native DnD; the
//   iframe is same-origin, so selection drag yields a text/html payload
//   that Quill's clipboard matchers convert into a formatted insert.
// - Selection popover on the editor: formatting lives in Quill's own
//   toolbar; we add a "Translate" action that only appears when the
//   selection contains non-Latin script (Arabic, Hebrew, Greek).
// - Save writes to Supabase via window.AI_BUILDS. New builds prompt for
//   a name; existing builds keep their name (editable inline up top).
// - Share creates a shared_builds snapshot and copies a shareable URL.
(function () {
  "use strict";

  // ============ Source catalogue ======================================
  // Same list as compare.js, plus a "Catalog" group so users can pull
  // content from the curated catalog pages (by source and by category).
  const SOURCES = [
    // Qur'an
    { slug: "quran", title: "The Qurʾān (Saheeh International)", path: "read/quran.html", group: "Qurʾān" },

    // Hadith — the Six
    { slug: "bukhari",   title: "Ṣaḥīḥ al-Bukhārī",   path: "read/bukhari.html",   group: "Hadith · the Six" },
    { slug: "muslim",    title: "Ṣaḥīḥ Muslim",       path: "read/muslim.html",    group: "Hadith · the Six" },
    { slug: "abu-dawud", title: "Sunan Abī Dāwūd",    path: "read/abu-dawud.html", group: "Hadith · the Six" },
    { slug: "tirmidhi",  title: "Jāmiʿ at-Tirmidhī",  path: "read/tirmidhi.html",  group: "Hadith · the Six" },
    { slug: "nasai",     title: "Sunan an-Nasāʾī",    path: "read/nasai.html",     group: "Hadith · the Six" },
    { slug: "ibn-majah", title: "Sunan Ibn Mājah",    path: "read/ibn-majah.html", group: "Hadith · the Six" },

    // Comparative scripture
    { slug: "tanakh",             title: "The Tanakh (JPS 1917)",                         path: "read-external/tanakh.html",             group: "Comparative scripture" },
    { slug: "new-testament",      title: "The New Testament (WEB)",                       path: "read-external/new-testament.html",      group: "Comparative scripture" },
    { slug: "bible-interlinear",  title: "Interlinear Bible (Hebrew · Greek · Strong's)", path: "read-external/bible.html",              group: "Comparative scripture" },
    { slug: "apocryphal-gospels", title: "Apocryphal Infancy Gospels",                    path: "read-external/apocryphal-gospels.html", group: "Comparative scripture" },
    { slug: "book-of-enoch",      title: "The Book of Enoch (1 Enoch)",                   path: "read-external/book-of-enoch.html",      group: "Comparative scripture" },
    { slug: "mishnah",            title: "The Mishnah (Kulp)",                            path: "read-external/mishnah.html",            group: "Comparative scripture" },
    { slug: "josephus",           title: "Flavius Josephus",                              path: "read-external/josephus.html",           group: "Comparative scripture" },
    { slug: "talmud",             title: "The Talmud",                                    path: "read-external/talmud.html",             group: "Comparative scripture" },

    // Classical Islamic scholarship
    { slug: "ibn-kathir", title: "Tafsīr Ibn Kathīr", path: "read-external/ibn-kathir.html", group: "Classical Islamic scholarship" },

    // Catalog — by source
    { slug: "cat-quran",     title: "Catalog — Qur'ān entries",       path: "catalog/quran.html",     group: "Catalog · by source" },
    { slug: "cat-bukhari",   title: "Catalog — Bukhārī entries",      path: "catalog/bukhari.html",   group: "Catalog · by source" },
    { slug: "cat-muslim",    title: "Catalog — Muslim entries",       path: "catalog/muslim.html",    group: "Catalog · by source" },
    { slug: "cat-abu-dawud", title: "Catalog — Abū Dāwūd entries",    path: "catalog/abu-dawud.html", group: "Catalog · by source" },
    { slug: "cat-tirmidhi",  title: "Catalog — Tirmidhī entries",     path: "catalog/tirmidhi.html",  group: "Catalog · by source" },
    { slug: "cat-nasai",     title: "Catalog — Nasāʾī entries",       path: "catalog/nasai.html",     group: "Catalog · by source" },
    { slug: "cat-ibn-majah", title: "Catalog — Ibn Mājah entries",    path: "catalog/ibn-majah.html", group: "Catalog · by source" },

    // Catalog — by category (the 30 topical pages)
    { slug: "ct-abrogation",    title: "Abrogation",                 path: "category/abrogation.html",    group: "Catalog · by category" },
    { slug: "ct-scripture",     title: "Scripture Integrity",        path: "category/scripture.html",     group: "Catalog · by category" },
    { slug: "ct-contradiction", title: "Contradictions",             path: "category/contradiction.html", group: "Catalog · by category" },
    { slug: "ct-logic",         title: "Logical Inconsistency",      path: "category/logic.html",         group: "Catalog · by category" },
    { slug: "ct-morality",      title: "Moral Problems",             path: "category/morality.html",      group: "Catalog · by category" },
    { slug: "ct-allah",         title: "Allah's Character",          path: "category/allah.html",         group: "Catalog · by category" },
    { slug: "ct-cosmology",     title: "Cosmology",                  path: "category/cosmology.html",     group: "Catalog · by category" },
    { slug: "ct-preislamic",    title: "Pre-Islamic Borrowings",     path: "category/preislamic.html",    group: "Catalog · by category" },
    { slug: "ct-magic",         title: "Magic & Occult",             path: "category/magic.html",         group: "Catalog · by category" },
    { slug: "ct-ritual",        title: "Ritual Absurdities",         path: "category/ritual.html",        group: "Catalog · by category" },
    { slug: "ct-prophet",       title: "Prophetic Character",        path: "category/prophet.html",       group: "Catalog · by category" },
    { slug: "ct-privileges",    title: "Prophetic Privileges",       path: "category/privileges.html",    group: "Catalog · by category" },
    { slug: "ct-jesus",         title: "Jesus / Christology",        path: "category/jesus.html",         group: "Catalog · by category" },
    { slug: "ct-women",         title: "Women",                      path: "category/women.html",         group: "Catalog · by category" },
    { slug: "ct-sexual",        title: "Sexual Issues",              path: "category/sexual.html",        group: "Catalog · by category" },
    { slug: "ct-childmarriage", title: "Child Marriage",             path: "category/childmarriage.html", group: "Catalog · by category" },
    { slug: "ct-lgbtq",         title: "LGBTQ / Gender",             path: "category/lgbtq.html",         group: "Catalog · by category" },
    { slug: "ct-slavery",       title: "Slavery & Captives",         path: "category/slavery.html",       group: "Catalog · by category" },
    { slug: "ct-hudud",         title: "Hudud",                      path: "category/hudud.html",         group: "Catalog · by category" },
    { slug: "ct-warfare",       title: "Warfare & Jihad",            path: "category/warfare.html",       group: "Catalog · by category" },
    { slug: "ct-apostasy",      title: "Apostasy & Blasphemy",       path: "category/apostasy.html",      group: "Catalog · by category" },
    { slug: "ct-governance",    title: "Governance",                 path: "category/governance.html",    group: "Catalog · by category" },
    { slug: "ct-disbelievers",  title: "Disbelievers",               path: "category/disbelievers.html",  group: "Catalog · by category" },
    { slug: "ct-antisemitism",  title: "Antisemitism",               path: "category/antisemitism.html",  group: "Catalog · by category" },
    { slug: "ct-paradise",      title: "Paradise",                   path: "category/paradise.html",      group: "Catalog · by category" },
    { slug: "ct-hell",          title: "Hell",                       path: "category/hell.html",          group: "Catalog · by category" },
    { slug: "ct-eschatology",   title: "Eschatology",                path: "category/eschatology.html",   group: "Catalog · by category" },
    { slug: "ct-strange",       title: "Strange / Obscure",          path: "category/strange.html",       group: "Catalog · by category" },
    { slug: "ct-incest",        title: "Incest",                     path: "category/incest.html",        group: "Catalog · by category" },
    { slug: "ct-gross-vile",    title: "Gross / Vile",               path: "category/gross-vile.html",    group: "Catalog · by category" },
  ];
  const DEFAULT_SOURCE = "quran";
  const SOURCE_BY_SLUG = Object.create(null);
  SOURCES.forEach(function (s) { SOURCE_BY_SLUG[s.slug] = s; });

  // ============ Text content selectors inside an embedded page ========
  const CONTENT_SELECTOR = [
    ".verses li",
    ".hadith",
    ".chapter",
    ".surah > p",
    "article.surah section",
    ".entry",
    ".card",
  ].join(",");

  // ============ Non-English script detection ===========================
  const ARABIC_RE = /[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]/;
  const HEBREW_RE = /[֐-׿יִ-ﭏ]/;
  const GREEK_RE  = /[Ͱ-Ͽἀ-῿]/;

  function detectLang(text) {
    if (ARABIC_RE.test(text)) return "ar";
    if (HEBREW_RE.test(text)) return "he";
    if (GREEK_RE.test(text))  return "el";
    return null;
  }

  // ============ DOM shortcuts ==========================================
  const main = document.querySelector(".build-editor-main");
  const shell = document.getElementById("build-editor-shell");
  const modalOverlay = document.getElementById("build-modal-overlay");

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function debounce(fn, ms) {
    let t = null;
    return function () {
      const args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  // ============ Modal helpers ==========================================
  function openModal(title, bodyHtml, opts) {
    opts = opts || {};
    modalOverlay.querySelector("#build-modal-title").textContent = title;
    modalOverlay.querySelector(".build-modal-body").innerHTML = bodyHtml;
    const confirm = modalOverlay.querySelector("[data-modal-confirm]");
    const cancel  = modalOverlay.querySelector("[data-modal-cancel]");
    confirm.textContent = opts.confirmLabel || "Save";
    cancel.textContent  = opts.cancelLabel  || "Cancel";
    modalOverlay.hidden = false;
    return new Promise(function (resolve) {
      function cleanup(val) {
        modalOverlay.hidden = true;
        confirm.removeEventListener("click", onConfirm);
        cancel.removeEventListener("click", onCancel);
        resolve(val);
      }
      function onConfirm() {
        const input = modalOverlay.querySelector(".build-modal-body input");
        cleanup(input ? input.value.trim() : true);
      }
      function onCancel() { cleanup(null); }
      confirm.addEventListener("click", onConfirm);
      cancel.addEventListener("click", onCancel);
      // Focus the first input, if any.
      setTimeout(function () {
        const i = modalOverlay.querySelector(".build-modal-body input");
        if (i) { i.focus(); i.select(); }
      }, 0);
    });
  }

  // ============ Signed-out gate ========================================
  function renderSignedOut() {
    shell.innerHTML =
      '<div class="auth-message auth-message--info" style="max-width:640px; margin: 60px auto;">' +
      "You're not signed in. " +
      '<a href="login.html?return=build-editor.html' + location.search + '">Sign in</a> or <a href="signup.html">create an account</a> to start a build.' +
      "</div>";
  }

  // ============ Main editor setup ======================================
  function buildEditorShellHtml() {
    const optsGrouped = {};
    SOURCES.forEach(function (s) {
      if (!optsGrouped[s.group]) optsGrouped[s.group] = [];
      optsGrouped[s.group].push(s);
    });
    let optionsHtml = "";
    Object.keys(optsGrouped).forEach(function (groupName) {
      optionsHtml += '<optgroup label="' + escapeHtml(groupName) + '">';
      optsGrouped[groupName].forEach(function (s) {
        optionsHtml += '<option value="' + escapeHtml(s.slug) + '">' + escapeHtml(s.title) + "</option>";
      });
      optionsHtml += "</optgroup>";
    });

    return '' +
      '<div class="build-bar">' +
        '<input type="text" class="build-bar-name" id="build-name" placeholder="Untitled build" autocomplete="off" />' +
        '<div class="build-bar-status" id="build-status"></div>' +
        '<div class="build-bar-actions">' +
          '<a href="build.html" class="btn">← My builds</a>' +
          '<button type="button" class="btn" id="build-share">Share</button>' +
          '<button type="button" class="btn btn-primary" id="build-save">Save</button>' +
        '</div>' +
      '</div>' +
      '<div class="build-panes">' +
        '<section class="build-pane build-pane-editor" aria-label="Editor">' +
          '<div id="editor-toolbar"></div>' +
          '<div id="editor"></div>' +
          '<div class="build-translate-popover" id="translate-popover" hidden>' +
            '<button type="button" class="build-translate-btn" id="translate-btn">Translate</button>' +
            '<div class="build-translate-result" id="translate-result" hidden></div>' +
          '</div>' +
        '</section>' +
        '<section class="build-pane build-pane-source" aria-label="Source browser">' +
          '<div class="compare-toolbar">' +
            '<select class="compare-source" id="source-select" aria-label="Source">' + optionsHtml + '</select>' +
            '<div class="compare-search-wrap">' +
              '<input type="search" class="compare-search" id="source-search" placeholder="Search verse, keyword, phrase…" autocomplete="off" />' +
              '<div class="compare-search-results" id="source-results" hidden></div>' +
            '</div>' +
            '<div class="build-source-hint">Highlight text → drag into the editor on the left.</div>' +
          '</div>' +
          '<iframe class="compare-frame" id="source-frame" title="Source browser" loading="lazy"></iframe>' +
        '</section>' +
      '</div>';
  }

  // ============ Quill init =============================================
  function initQuill() {
    // Build a toolbar matching the MS-Office-style set the user asked
    // for: fonts, sizes, headings, bold/italic/underline/strike,
    // text/highlight colour, alignment, lists, blockquote, link, clean.
    const toolbarOptions = [
      [{ font: [] }],
      [{ size: ["small", false, "large", "huge"] }],
      [{ header: [1, 2, 3, 4, 5, 6, false] }],
      ["bold", "italic", "underline", "strike"],
      [{ color: [] }, { background: [] }],
      [{ align: [] }],
      [{ list: "ordered" }, { list: "bullet" }],
      [{ indent: "-1" }, { indent: "+1" }],
      ["blockquote"],
      [{ direction: "rtl" }],
      ["link"],
      ["clean"],
    ];

    const quill = new Quill("#editor", {
      theme: "snow",
      placeholder: "Start writing your argument. Highlight text in the right-hand pane and drag it in…",
      modules: {
        toolbar: { container: toolbarOptions },
        clipboard: { matchVisual: false },
      },
    });
    // Move Quill's generated toolbar into our placeholder slot so it
    // sits above the editor area in a predictable place.
    const qlToolbar = document.querySelector(".ql-toolbar");
    const slot = document.getElementById("editor-toolbar");
    if (qlToolbar && slot) slot.appendChild(qlToolbar);
    return quill;
  }

  // ============ Source iframe + search =================================
  function populateSelect(sel, sources) {
    // Already populated via buildEditorShellHtml; this helper exists
    // for symmetry if we later want to repopulate dynamically.
  }

  function setSource(slug, hash) {
    const source = SOURCE_BY_SLUG[slug] || SOURCE_BY_SLUG[DEFAULT_SOURCE];
    if (!source) return;
    const frame = document.getElementById("source-frame");
    let src = source.path + (source.path.indexOf("?") >= 0 ? "&" : "?") + "embed=1";
    if (hash) src += "#" + hash.replace(/^#/, "");
    if (frame.getAttribute("src") !== src) frame.src = src;
    const sel = document.getElementById("source-select");
    sel.value = slug;
    const search  = document.getElementById("source-search");
    const results = document.getElementById("source-results");
    search.value = "";
    results.hidden = true;
    results.innerHTML = "";
  }

  function iframeDoc(frame) {
    try { return frame.contentDocument || (frame.contentWindow && frame.contentWindow.document); }
    catch (_) { return null; }
  }

  function buildSnippet(text, query) {
    const flat = text.replace(/\s+/g, " ").trim();
    const lower = flat.toLowerCase();
    const q = query.toLowerCase();
    const idx = lower.indexOf(q);
    if (idx < 0) return flat.slice(0, 140);
    const start = Math.max(0, idx - 40);
    const end = Math.min(flat.length, idx + q.length + 80);
    const pre = start > 0 ? "…" : "";
    const suf = end < flat.length ? "…" : "";
    const before = flat.slice(start, idx);
    const hit    = flat.slice(idx, idx + q.length);
    const after  = flat.slice(idx + q.length, end);
    return pre + escapeHtml(before) + "<mark>" + escapeHtml(hit) + "</mark>" + escapeHtml(after) + suf;
  }

  function scrollFrameTo(frame, el) {
    const doc = iframeDoc(frame);
    if (!doc || !el) return;
    try {
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      const prev = el.style.animation;
      el.style.animation = "compare-jump-flash 1.5s ease-out 1";
      setTimeout(function () { el.style.animation = prev || ""; }, 1700);
    } catch (_) {}
  }

  function performSearch() {
    const search  = document.getElementById("source-search");
    const results = document.getElementById("source-results");
    const frame   = document.getElementById("source-frame");
    const query = search.value.trim();
    if (!query) {
      results.hidden = true;
      results.innerHTML = "";
      return;
    }
    const doc = iframeDoc(frame);
    if (!doc) {
      results.innerHTML = '<div class="compare-search-status">Iframe still loading — try again in a moment.</div>';
      results.hidden = false;
      return;
    }
    // Exact anchor match first (supports "s9v5", "genesis-15-6", "h2749").
    const asId = query.replace(/^#/, "").toLowerCase();
    if (/^[a-z0-9][a-z0-9\-]*$/.test(asId) && asId.length <= 40) {
      const byId = doc.getElementById(asId);
      if (byId) {
        scrollFrameTo(frame, byId);
        results.innerHTML = '<div class="compare-search-status">Jumped to #' + escapeHtml(asId) + ".</div>";
        results.hidden = false;
        setTimeout(function () { results.hidden = true; }, 1800);
        return;
      }
    }
    const items = doc.querySelectorAll(CONTENT_SELECTOR);
    const qLower = query.toLowerCase();
    const matches = [];
    for (let i = 0; i < items.length && matches.length < 100; i++) {
      const el = items[i];
      const txt = el.textContent || "";
      if (txt.toLowerCase().indexOf(qLower) >= 0) {
        matches.push({ el: el, ref: el.id || "", snippet: buildSnippet(txt, query) });
      }
    }
    results.innerHTML = "";
    if (!matches.length) {
      results.innerHTML = '<div class="compare-search-status">No matches for "' + escapeHtml(query) + '".</div>';
      results.hidden = false;
      return;
    }
    const hdr = document.createElement("div");
    hdr.className = "compare-search-status";
    hdr.textContent = matches.length + " match" + (matches.length === 1 ? "" : "es") + (matches.length >= 50 ? " (showing first 50)" : "");
    results.appendChild(hdr);
    matches.slice(0, 50).forEach(function (m) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "compare-search-result";
      btn.innerHTML =
        '<span class="ref">' + escapeHtml(m.ref).replace(/[<>&]/g, "") + "</span>" +
        '<span class="snippet">' + m.snippet + "</span>";
      btn.addEventListener("click", function () {
        scrollFrameTo(frame, m.el);
        results.hidden = true;
      });
      results.appendChild(btn);
    });
    results.hidden = false;
  }

  // ============ Drag-drop bridge (iframe → Quill) ======================
  // Same-origin iframes technically support native text drag, but browsers
  // are inconsistent about populating DataTransfer.text/html when the drag
  // crosses frame boundaries — and Quill's default drop handler bails when
  // both text and html are empty. We stamp the selection into DataTransfer
  // from inside the iframe on dragstart, then handle drop on the Quill root
  // ourselves (converting html → Delta and inserting at the cursor).
  function wireDragDropBridge(quill) {
    const frame = document.getElementById("source-frame");
    if (!frame) return;
    const Delta = Quill.import("delta");

    function attachFrameHandlers() {
      let doc = null, win = null;
      try { doc = frame.contentDocument; win = frame.contentWindow; } catch (_) { return; }
      if (!doc || !win) return;
      // Each iframe navigation replaces the document, so we re-bind on
      // every load. The flag prevents double-binding within one doc.
      if (doc.__buildDragBound) return;
      doc.__buildDragBound = true;
      doc.addEventListener("dragstart", function (e) {
        const sel = win.getSelection();
        if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
        const range = sel.getRangeAt(0);
        const container = doc.createElement("div");
        container.appendChild(range.cloneContents());
        try {
          e.dataTransfer.setData("text/html", container.innerHTML);
          e.dataTransfer.setData("text/plain", sel.toString());
          e.dataTransfer.effectAllowed = "copy";
        } catch (_) {}
      });
    }
    frame.addEventListener("load", attachFrameHandlers);
    attachFrameHandlers(); // in case it already loaded

    const root = quill.root;
    root.addEventListener("dragover", function (e) {
      e.preventDefault();
      if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    });
    root.addEventListener("drop", function (e) {
      const dt = e.dataTransfer;
      if (!dt) return;
      const html = dt.getData("text/html");
      const text = dt.getData("text/plain");
      if (!html && !text) return;
      e.preventDefault();
      e.stopPropagation();

      // Resolve drop point → Quill index.
      let insertIndex = null;
      const ownerDoc = root.ownerDocument;
      try {
        let targetRange = null;
        if (ownerDoc.caretRangeFromPoint) {
          targetRange = ownerDoc.caretRangeFromPoint(e.clientX, e.clientY);
        } else if (ownerDoc.caretPositionFromPoint) {
          const pos = ownerDoc.caretPositionFromPoint(e.clientX, e.clientY);
          if (pos) {
            targetRange = ownerDoc.createRange();
            targetRange.setStart(pos.offsetNode, pos.offset);
          }
        }
        if (targetRange) {
          const blot = Quill.find(targetRange.startContainer, true);
          if (blot) insertIndex = quill.getIndex(blot) + (targetRange.startOffset || 0);
        }
      } catch (_) {}
      if (insertIndex == null) {
        const cur = quill.getSelection();
        insertIndex = cur ? cur.index : quill.getLength();
      }

      let delta;
      if (html) {
        delta = quill.clipboard.convert({ html: html });
      } else {
        delta = new Delta().insert(text);
      }
      quill.updateContents(new Delta().retain(insertIndex).concat(delta), "user");
      quill.setSelection(insertIndex + delta.length(), 0);
      quill.focus();
    });
  }

  // ============ Translator =============================================
  async function translate(text, source) {
    // MyMemory public endpoint. Free for ~5k chars/day without an email.
    const url =
      "https://api.mymemory.translated.net/get?q=" +
      encodeURIComponent(text) +
      "&langpair=" + encodeURIComponent(source || "auto") + "|en";
    const res = await fetch(url);
    if (!res.ok) throw new Error("translate http " + res.status);
    const json = await res.json();
    const best = json && json.responseData && json.responseData.translatedText;
    return best || "";
  }

  // Position the translate popover anchored to the current Quill
  // selection. Only call after a non-empty selection has been confirmed.
  function positionTranslatePopover(quill, range) {
    const pop = document.getElementById("translate-popover");
    const editor = document.querySelector(".build-pane-editor");
    if (!pop || !editor || !range) return;
    // Quill gives bounds relative to the editor root; translate to our
    // build-pane-editor coordinate system so the absolute popover lines
    // up with the highlighted text. getBounds can return null if the
    // index is out of range during a layout transition — bail quietly.
    const bounds = quill.getBounds(range.index, range.length);
    if (!bounds) { hideTranslatePopover(); return; }
    const editorRoot = quill.root;
    const editorOffset = editorRoot.getBoundingClientRect();
    const paneOffset  = editor.getBoundingClientRect();
    const top  = (editorOffset.top - paneOffset.top) + bounds.top - 44;
    const left = (editorOffset.left - paneOffset.left) + bounds.left + Math.min(bounds.width, 160);
    pop.style.top  = Math.max(4, top) + "px";
    pop.style.left = Math.max(4, left) + "px";
    pop.hidden = false;
    const result = document.getElementById("translate-result");
    if (result) {
      result.hidden = true;
      result.textContent = "";
    }
  }

  function hideTranslatePopover() {
    const pop = document.getElementById("translate-popover");
    if (pop) pop.hidden = true;
  }

  function attachTranslator(quill) {
    const btn = document.getElementById("translate-btn");
    const result = document.getElementById("translate-result");
    let currentSelectionText = "";
    let currentSelectionLang = null;

    quill.on("selection-change", function (range) {
      if (!range || range.length === 0) {
        hideTranslatePopover();
        return;
      }
      const text = quill.getText(range.index, range.length).trim();
      const lang = detectLang(text);
      if (!lang) {
        hideTranslatePopover();
        return;
      }
      currentSelectionText = text;
      currentSelectionLang = lang;
      positionTranslatePopover(quill, range);
    });

    btn.addEventListener("click", async function () {
      if (!currentSelectionText) return;
      btn.disabled = true;
      const prev = btn.textContent;
      btn.textContent = "Translating…";
      try {
        const out = await translate(currentSelectionText, currentSelectionLang);
        result.textContent = out || "(no translation returned)";
        result.hidden = false;
      } catch (err) {
        result.textContent = "Translation failed. Try again later.";
        result.hidden = false;
      } finally {
        btn.disabled = false;
        btn.textContent = prev;
      }
    });

    // Clicking outside the editor closes the popover.
    document.addEventListener("mousedown", function (e) {
      const pop = document.getElementById("translate-popover");
      if (!pop) return;
      if (pop.contains(e.target)) return;
      // If the click is inside the editor, the selection-change handler
      // will redraw the popover — so we don't need to hide proactively.
      if (quill.root.contains(e.target)) return;
      hideTranslatePopover();
    });
  }

  // ============ State + load / save ====================================
  const state = {
    buildId: null,
    name: "",
    quill: null,
    dirty: false,
    // Idempotency guard. Keyed by the signed-in user's id so a sign-out
    // properly resets us back to the sign-in gate, and a fresh sign-in
    // re-mounts the editor once. Without this, Supabase's auth-state
    // refresh events (fired on token refresh, INITIAL_SESSION, or focus
    // regains) would wipe innerHTML and rebuild Quill every cycle —
    // which steals the user's cursor and aborts in-flight clicks.
    mountedForUserId: null,
  };

  function setStatus(text) {
    const el = document.getElementById("build-status");
    if (el) el.textContent = text || "";
  }

  // Share is only available once the build has been saved AND has no
  // unsaved changes — otherwise there'd be nothing to share (or the
  // shared snapshot would silently lag behind what the user sees).
  function updateShareButton() {
    const btn = document.getElementById("build-share");
    if (!btn) return;
    const canShare = state.buildId != null && !state.dirty;
    btn.disabled = !canShare;
    btn.title = canShare
      ? "Create a public share link"
      : state.buildId == null
        ? "Save this build first, then you can share it."
        : "You have unsaved changes. Save to update the share snapshot.";
  }

  function currentName() {
    const input = document.getElementById("build-name");
    return (input && input.value.trim()) || "";
  }

  async function saveBuild(options) {
    options = options || {};
    const quill = state.quill;
    if (!quill) return null;

    let name = currentName();
    if (!name) {
      // First save (or cleared name): prompt for one.
      const promptedName = await openModal(
        "Save build",
        '<p>Give this build a name so you can find it later.</p>' +
        '<input type="text" placeholder="e.g. \'The Zaynab affair\'" />',
        { confirmLabel: "Save" }
      );
      if (promptedName === null) return null;
      name = (promptedName || "").toString().trim() || "Untitled build";
      const input = document.getElementById("build-name");
      if (input) input.value = name;
    }

    const delta = quill.getContents();
    const html = quill.root.innerHTML;

    setStatus("Saving…");
    let row;
    if (state.buildId) {
      row = await window.AI_BUILDS.update(state.buildId, {
        name: name,
        content_delta: delta,
        content_html: html,
      });
    } else {
      row = await window.AI_BUILDS.create({
        name: name,
        content_delta: delta,
        content_html: html,
      });
      if (row && row.id) {
        state.buildId = row.id;
        // Update URL so reloads land on the same build.
        const url = new URL(location.href);
        url.searchParams.set("id", String(row.id));
        history.replaceState(null, "", url.toString());
      }
    }
    if (!row) {
      setStatus("Save failed.");
      return null;
    }
    state.name = row.name;
    state.dirty = false;
    setStatus("Saved · " + new Date(row.updated_at || row.created_at).toLocaleTimeString());
    updateShareButton();
    return row;
  }

  async function shareBuild() {
    // Precondition: the Share button is only enabled when the build has
    // been saved and has no unsaved changes. If something slipped past
    // that guard (e.g. keyboard shortcut), bail with a clear message.
    if (state.buildId == null) {
      await openModal(
        "Save first",
        "<p>Save this build before sharing it. Click <strong>Save</strong> — once it's named and stored, you can create a share link.</p>",
        { confirmLabel: "OK", cancelLabel: "" }
      );
      return;
    }
    if (state.dirty) {
      await openModal(
        "Unsaved changes",
        "<p>You have unsaved changes. Save them first so your share link reflects the latest version.</p>",
        { confirmLabel: "OK", cancelLabel: "" }
      );
      return;
    }

    const quill = state.quill;
    const share = await window.AI_BUILDS.createShare(state.buildId, {
      name: state.name || currentName(),
      content_delta: quill.getContents(),
      content_html: quill.root.innerHTML,
    });
    if (!share) {
      await openModal("Share link", '<p>Could not create share link. Try again later.</p>', { confirmLabel: "OK", cancelLabel: "" });
      return;
    }
    const url = new URL("build-shared.html", location.href);
    url.searchParams.set("id", share.id);
    const urlStr = url.toString();

    await openModal(
      "Share this build",
      '<p>Anyone with this link can read a snapshot of this build (read-only).</p>' +
      '<input type="text" readonly value="' + escapeHtml(urlStr) + '" />' +
      '<p style="margin-top:10px; color: var(--text-dim); font-size: 12px;">' +
      '  The link reflects the snapshot taken right now. Save and share again to refresh it.' +
      '</p>',
      { confirmLabel: "Copy", cancelLabel: "Close" }
    ).then(function (val) {
      if (val === null) return;
      try { navigator.clipboard.writeText(urlStr); } catch (_) {}
    });
  }

  // ============ Mount ==================================================
  async function mountEditor() {
    shell.innerHTML = buildEditorShellHtml();

    const quill = initQuill();
    state.quill = quill;

    // Source picker + search wiring.
    const sel = document.getElementById("source-select");
    const search = document.getElementById("source-search");
    sel.addEventListener("change", function () {
      setSource(sel.value, "");
    });
    const onSearch = debounce(performSearch, 220);
    search.addEventListener("input", onSearch);

    document.addEventListener("click", function (e) {
      const results = document.getElementById("source-results");
      const pane = document.querySelector(".build-pane-source");
      if (results && pane && !pane.contains(e.target)) results.hidden = true;
    });

    // Drag-drop bridge: iframe selection → Quill (with formatting).
    wireDragDropBridge(quill);

    // Translate popover on selection of non-Latin script.
    attachTranslator(quill);

    // Track dirty state.
    quill.on("text-change", function () {
      state.dirty = true;
      setStatus("Unsaved changes");
      updateShareButton();
    });
    const nameInput = document.getElementById("build-name");
    nameInput.addEventListener("input", function () {
      state.dirty = true;
      setStatus("Unsaved changes");
      updateShareButton();
    });

    // Save / Share buttons.
    document.getElementById("build-save").addEventListener("click", function () { saveBuild(); });
    document.getElementById("build-share").addEventListener("click", function () { shareBuild(); });

    // Keyboard: Ctrl/Cmd+S saves.
    document.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        saveBuild();
      }
    });

    // Warn on navigation away with unsaved changes.
    window.addEventListener("beforeunload", function (e) {
      if (!state.dirty) return;
      e.preventDefault();
      e.returnValue = "";
    });

    // Load existing build if ?id= is present.
    const params = new URLSearchParams(location.search);
    const existingId = params.get("id");
    if (existingId) {
      setStatus("Loading…");
      const row = await window.AI_BUILDS.get(existingId);
      if (!row) {
        setStatus("Build not found.");
      } else {
        state.buildId = row.id;
        state.name = row.name;
        nameInput.value = row.name || "";
        if (row.content_delta && row.content_delta.ops) {
          quill.setContents(row.content_delta, "silent");
        } else if (row.content_html) {
          quill.clipboard.dangerouslyPasteHTML(row.content_html, "silent");
        }
        state.dirty = false;
        setStatus("Opened · last saved " + new Date(row.updated_at || row.created_at).toLocaleString());
      }
    } else {
      // Fresh build — set a sensible default source.
      setSource(DEFAULT_SOURCE, "");
      setStatus("New build");
    }
    // Ensure source is set (even for loaded builds).
    if (!document.getElementById("source-frame").getAttribute("src")) {
      setSource(DEFAULT_SOURCE, "");
    }

    // Set initial Share-button state. Disabled for fresh builds (no id yet)
    // and for loaded-but-dirty builds; enabled for cleanly-loaded existing.
    updateShareButton();
  }

  // ============ Entry point ============================================
  function paint() {
    const sess = window.__session;
    const userId = sess && sess.user ? sess.user.id : null;

    if (!userId) {
      // Signed out (or never signed in). Reset the mount guard so a
      // subsequent sign-in remounts cleanly. Only re-render the gate
      // if we're not already showing it to avoid useless reflows.
      if (state.mountedForUserId !== null) {
        state.mountedForUserId = null;
      }
      if (!shell.querySelector(".auth-message")) renderSignedOut();
      return;
    }

    // Already mounted for this user — do nothing. Prevents auth-state
    // refresh events from tearing down and rebuilding the editor (which
    // would cancel clicks and kill the cursor mid-keystroke).
    if (state.mountedForUserId === userId) return;

    state.mountedForUserId = userId;
    mountEditor();
  }

  function start() {
    if (window.__authReady && typeof window.__authReady.then === "function") {
      window.__authReady.then(paint);
    } else {
      paint();
    }
    window.addEventListener("auth-state", paint);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

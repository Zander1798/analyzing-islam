/* =============================================================
   Analyzing Islam — Community editor: reference picker
   -------------------------------------------------------------
   Adds an "Add reference" button to the Quill toolbar used in
   community posts. The button opens a modal with two tabs:

     1. Catalog entry — searchable list of all 1,500 entries
        (Quran + 6 hadith collections). Picking one inserts a
        styled card that links back to the entry.
     2. Reader — source dropdown (Quran, Bukhari, Muslim, etc.)
        plus a reference input (e.g. 5:43, or 2749). Inserts a
        card that links to the Reader page anchor.

   The inserted markup is a single <a class="cf-ref-card"> block
   so it survives Quill serialisation and renders consistently
   in the post view and feed snippets.
   ============================================================= */
(function () {
  "use strict";

  if (!window.Quill) return;

  // ---- Sources we can target in the Reader tab ---------------------
  // slug → { label, anchor(ref) → string }
  const READER_SOURCES = {
    quran: {
      label: "Quran (verse, e.g. 5:43)",
      url: "read/quran.html",
      anchor: (ref) => {
        const m = String(ref).match(/^\s*(\d+)\s*[:\.]\s*(\d+)/);
        return m ? `s${m[1]}v${m[2]}` : null;
      },
      placeholder: "5:43",
      refDisplay: (ref) => `Quran ${ref}`,
    },
    bukhari:    hadithSource("bukhari",    "Sahih al-Bukhari (hadith #)"),
    muslim:     hadithSource("muslim",     "Sahih Muslim (hadith #)"),
    "abu-dawud":hadithSource("abu-dawud",  "Sunan Abi Dawud (hadith #)"),
    tirmidhi:   hadithSource("tirmidhi",   "Sunan al-Tirmidhi (hadith #)"),
    nasai:      hadithSource("nasai",      "Sunan an-Nasa'i (hadith #)"),
    "ibn-majah":hadithSource("ibn-majah",  "Sunan Ibn Majah (hadith #)"),
  };

  function hadithSource(slug, label) {
    const nice = {
      "bukhari": "Bukhari",
      "muslim": "Muslim",
      "abu-dawud": "Abu Dawud",
      "tirmidhi": "Tirmidhi",
      "nasai": "Nasa'i",
      "ibn-majah": "Ibn Majah",
    }[slug];
    return {
      label,
      url: `read/${slug}.html`,
      anchor: (ref) => {
        const m = String(ref).match(/(\d+)/);
        return m ? `h${m[1]}` : null;
      },
      placeholder: "2749",
      refDisplay: (ref) => `${nice} ${ref}`,
    };
  }

  const SOURCE_NICE = {
    quran: "Quran",
    bukhari: "Bukhari",
    muslim: "Muslim",
    "abu-dawud": "Abu Dawud",
    tirmidhi: "Tirmidhi",
    nasai: "Nasa'i",
    "ibn-majah": "Ibn Majah",
  };

  let catalogIndex = null;
  let catalogPromise = null;

  // The index is 400 KB+ so only fetch it when the picker is opened.
  async function loadCatalog(prefix) {
    if (catalogIndex) return catalogIndex;
    if (catalogPromise) return catalogPromise;
    catalogPromise = fetch(prefix + "assets/data/catalog-entries.json")
      .then((r) => (r.ok ? r.json() : []))
      .then((json) => { catalogIndex = Array.isArray(json) ? json : []; return catalogIndex; })
      .catch(() => { catalogIndex = []; return catalogIndex; });
    return catalogPromise;
  }

  // ---- Register a custom toolbar icon so the button has visible text
  const icons = Quill.import("ui/icons");
  if (!icons["cf-ref"]) {
    icons["cf-ref"] = '<span style="font-size:12px;font-weight:600;letter-spacing:0.06em;">REF</span>';
  }

  // ---- Modal markup (built once per page) --------------------------
  let modal = null;
  let onPick = null;

  function ensureModal() {
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "cf-ref-modal";
    modal.innerHTML = `
      <div class="cf-ref-modal-inner" role="dialog" aria-modal="true" aria-labelledby="cf-ref-title">
        <div class="cf-ref-modal-head">
          <h3 id="cf-ref-title">Add a reference</h3>
          <button type="button" class="cf-btn" data-close>Close</button>
        </div>
        <div class="cf-ref-tabs">
          <button type="button" class="cf-ref-tab is-active" data-tab="catalog">Catalog entry</button>
          <button type="button" class="cf-ref-tab" data-tab="reader">Verse / Hadith</button>
        </div>

        <div class="cf-ref-panel is-active" data-panel="catalog">
          <input type="text" class="cf-ref-search" placeholder="Search 1,500 entries by title, category, verse…" spellcheck="false">
          <div class="cf-ref-list" data-role="catalog-list">
            <div class="cf-ref-empty">Loading entries…</div>
          </div>
        </div>

        <div class="cf-ref-panel" data-panel="reader">
          <div class="cf-ref-form-row">
            <label for="cf-ref-source">Source</label>
            <select id="cf-ref-source">
              ${Object.entries(READER_SOURCES).map(([k, v]) =>
                `<option value="${k}">${v.label}</option>`
              ).join("")}
            </select>
          </div>
          <div class="cf-ref-form-row">
            <label for="cf-ref-ref">Reference</label>
            <input id="cf-ref-ref" type="text" placeholder="5:43" spellcheck="false">
          </div>
          <div class="cf-ref-form-row" style="justify-content:flex-end;">
            <button type="button" class="cf-btn cf-btn-primary" data-reader-insert>Insert reference</button>
          </div>
          <p class="cf-ref-empty" style="text-align:left;padding:0;">
            Links to the Reader page with the exact anchor. Example:
            <code>read/quran.html#s5v43</code>.
          </p>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) close();
      if (e.target.closest("[data-close]")) close();
    });

    modal.querySelectorAll(".cf-ref-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        modal.querySelectorAll(".cf-ref-tab").forEach((t) => t.classList.remove("is-active"));
        tab.classList.add("is-active");
        const name = tab.getAttribute("data-tab");
        modal.querySelectorAll(".cf-ref-panel").forEach((p) =>
          p.classList.toggle("is-active", p.getAttribute("data-panel") === name)
        );
      });
    });

    modal.querySelector("[data-reader-insert]").addEventListener("click", () => {
      insertFromReader();
    });
    modal.querySelector("#cf-ref-ref").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); insertFromReader(); }
    });

    // Source picker updates the placeholder of the reference input.
    const srcSel = modal.querySelector("#cf-ref-source");
    const refIn  = modal.querySelector("#cf-ref-ref");
    srcSel.addEventListener("change", () => {
      refIn.placeholder = (READER_SOURCES[srcSel.value] || {}).placeholder || "";
    });

    // Catalog search (debounced).
    const searchIn = modal.querySelector(".cf-ref-search");
    let tok = 0;
    searchIn.addEventListener("input", () => {
      const my = ++tok;
      setTimeout(() => {
        if (my !== tok) return;
        renderCatalogList(searchIn.value);
      }, 120);
    });

    return modal;
  }

  function close() {
    if (modal) modal.classList.remove("is-open");
    onPick = null;
  }

  function renderCatalogList(query) {
    const list = modal.querySelector('[data-role="catalog-list"]');
    if (!catalogIndex) {
      list.innerHTML = '<div class="cf-ref-empty">Loading entries…</div>';
      return;
    }
    const q = (query || "").trim().toLowerCase();
    let items = catalogIndex;
    if (q) {
      items = items.filter((e) =>
        e.title.toLowerCase().includes(q) ||
        (e.ref && e.ref.toLowerCase().includes(q)) ||
        e.source.includes(q) ||
        (e.categories || []).some((c) => c.includes(q)) ||
        e.id.includes(q)
      );
    }
    items = items.slice(0, 200);
    if (!items.length) {
      list.innerHTML = '<div class="cf-ref-empty">No matches.</div>';
      return;
    }
    list.innerHTML = items.map((e) => `
      <div class="cf-ref-row" data-id="${e.id}" data-source="${e.source}">
        <div class="cf-ref-row-title">${esc(e.title)}</div>
        <div class="cf-ref-row-meta">
          ${esc(SOURCE_NICE[e.source] || e.source)}${e.ref ? " · " + esc(e.ref) : ""}${e.strength ? " · " + esc(e.strength) : ""}
        </div>
      </div>
    `).join("");
    list.querySelectorAll(".cf-ref-row").forEach((row) => {
      row.addEventListener("click", () => {
        const id = row.getAttribute("data-id");
        const entry = catalogIndex.find((e) => e.id === id);
        if (!entry) return;
        const card = {
          kind: "Catalog entry",
          title: entry.title,
          meta: (SOURCE_NICE[entry.source] || entry.source) + (entry.ref ? " · " + entry.ref : ""),
          url: entry.url,
        };
        if (onPick) onPick(card);
        close();
      });
    });
  }

  function insertFromReader() {
    const srcSel = modal.querySelector("#cf-ref-source");
    const refIn  = modal.querySelector("#cf-ref-ref");
    const src = READER_SOURCES[srcSel.value];
    const ref = refIn.value.trim();
    if (!src || !ref) { refIn.focus(); return; }
    const anchor = src.anchor(ref);
    if (!anchor) {
      alert("Can't parse that reference. Try something like 5:43 for the Quran or 2749 for a hadith.");
      refIn.focus();
      return;
    }
    const card = {
      kind: "Source",
      title: src.refDisplay(ref),
      meta: srcSel.options[srcSel.selectedIndex].text,
      url: src.url + "#" + anchor,
    };
    if (onPick) onPick(card);
    close();
  }

  function assetPrefix() {
    // Used to resolve assets/data/... from either the site root or a
    // subdirectory. Community pages are all at the site root right now,
    // so the prefix is empty — but parameterise it in case that changes.
    const el = document.querySelector('link[href*="assets/"], script[src*="assets/"]');
    if (el) {
      const attr = el.getAttribute("href") || el.getAttribute("src");
      const idx = attr.indexOf("assets/");
      return attr.slice(0, idx);
    }
    return "";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  // ---- Quill HTML insertion ----------------------------------------
  function cardHtml(card) {
    return (
      '<a class="cf-ref-card" href="' + esc(card.url) + '">' +
        '<span class="cf-ref-card-kind">' + esc(card.kind) + '</span>' +
        '<div class="cf-ref-card-title">' + esc(card.title) + '</div>' +
        '<div class="cf-ref-card-meta">' + esc(card.meta) + '</div>' +
      '</a>'
    );
  }

  function insertCardIntoQuill(quill, card) {
    const range = quill.getSelection(true) || { index: quill.getLength() };
    // Quill's clipboard module can convert raw HTML to a delta that
    // Quill will accept. We insert the card, then a blank line after
    // it so the user's cursor is on a new line below the card.
    const delta = quill.clipboard.convert({ html: cardHtml(card) + "<p><br></p>" });
    quill.updateContents(
      { ops: [{ retain: range.index }, { delete: range.length || 0 }].concat(delta.ops) },
      "user"
    );
    quill.setSelection(range.index + delta.length(), 0, "user");
  }

  // ---- Public: wire up a Quill toolbar to use this picker ---------
  function attach(quill) {
    if (!quill || !quill.getModule) return;
    const toolbar = quill.getModule("toolbar");
    if (!toolbar) return;
    toolbar.addHandler("cf-ref", () => {
      openPicker((card) => insertCardIntoQuill(quill, card));
    });
  }

  function openPicker(callback) {
    ensureModal();
    onPick = callback;
    modal.classList.add("is-open");
    const prefix = assetPrefix();
    loadCatalog(prefix).then(() => renderCatalogList(""));
  }

  window.CF_EDITOR_REFS = { attach, openPicker };
})();

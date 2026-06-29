// Goat skin registry. Exposes window.GoatSkins used by goat.js and goat-page.js.
(function () {
  "use strict";

  var SKINS = [
    {
      id:    "standard",
      name:  "Standard",
      blurb: "The classic.",
      gif:   "assets/images/goat-standard.gif",
      level: null,
    },
    {
      id:    "educated",
      name:  "Educated",
      blurb: "Shirt, tie, big ideas.",
      gif:   "assets/images/goat-educated.gif",
      level: 1,
    },
    {
      id:    "hijab",
      name:  "Hijab",
      blurb: "Modest and magnificent.",
      gif:   "assets/images/goat-hijab.gif",
      level: 2,
    },
    {
      id:    "chef",
      name:  "Chef",
      blurb: "Head chef, head horns.",
      gif:   "assets/images/goat-chef.gif",
      level: 3,
    },
    {
      id:    "astronaut",
      name:  "Astronaut",
      blurb: "One small bleat for goat-kind.",
      gif:   "assets/images/goat-astronaut.gif",
      level: 4,
    },
    {
      id:    "royal",
      name:  "Royal",
      blurb: "Crown, cape, absolute power.",
      gif:   "assets/images/goat-royal.gif",
      level: 5,
    },
    {
      id:    "detective",
      name:  "Detective",
      blurb: "The case of the missing grass.",
      gif:   "assets/images/goat-detective.gif",
      level: 6,
    },
    {
      id:    "glorious",
      name:  "Glorious",
      blurb: "Halo, wings, divine grazing.",
      gif:   "assets/images/goat-glorious.gif",
      level: 7,
    },
    {
      id:    "beard",
      name:  "Beard of Glory",
      blurb: "The beard demands respect.",
      gif:   "assets/images/goat-beard.gif",
      level: 8,
    },
    {
      id:    "quran",
      name:  "Quran Goat",
      blurb: "Reads the book, eats the grass.",
      gif:   "assets/images/goat-quran.gif",
      level: 9,
    },
  ];

  var LS_SKIN     = "aig:goat-skin";
  var LS_LEVEL    = "aig:unlocked-level";
  var LS_UNLOCKED = "aig:unlocked-skins";
  var DB_TABLE    = "quiz_progress";

  // ── In-memory cache (always in sync with the source of truth) ──────────
  // Initialised to safe defaults; populated once auth + the Supabase
  // round-trip resolve. `loaded` flips true the moment we know the real
  // state (server row, migrated local progress, or confirmed signed-out)
  // so the UI can tell "still loading" from "genuinely only standard".
  var _cache = (function () {
    var lvl     = parseInt(localStorage.getItem(LS_LEVEL) || "1", 10);
    var stored  = localStorage.getItem(LS_UNLOCKED);
    var ids     = stored ? JSON.parse(stored) : [];
    if (ids.indexOf("standard") === -1) ids.push("standard");
    // Seed the selection from the localStorage mirror so the nav paints the
    // user's last-known skin immediately, instead of flashing "standard"
    // before the auth + Supabase round-trip resolves. This is only ever
    // written by setSelectedId (which requires the skin to be unlocked), and
    // loadProgress repaints to the authoritative value once it loads.
    return {
      unlockedLevel: lvl,
      unlockedSkins: new Set(ids),
      selectedSkin:  localStorage.getItem(LS_SKIN) || "standard",
      loaded:        false,
    };
  }());

  function sb()  { return window.__supabase; }
  function uid() { var s = window.__session; return s && s.user ? s.user.id : null; }

  // ── Server helpers ──────────────────────────────────────────────────────
  async function serverLoad() {
    if (!sb() || !uid()) return null;
    var result = await sb()
      .from(DB_TABLE)
      .select("unlocked_level, unlocked_skins, selected_skin")
      .eq("user_id", uid())
      .maybeSingle();
    return result.data || null;
  }

  async function serverSave() {
    if (!sb() || !uid()) return;
    await sb().from(DB_TABLE).upsert({
      user_id:         uid(),
      unlocked_level:  _cache.unlockedLevel,
      unlocked_skins:  Array.from(_cache.unlockedSkins),
      selected_skin:   _cache.selectedSkin,
      updated_at:      new Date().toISOString(),
    }, { onConflict: "user_id" });
  }

  // ── Migration: localStorage → Supabase on first sign-in ────────────────
  async function migrateLocal() {
    var lvl    = parseInt(localStorage.getItem(LS_LEVEL) || "1", 10);
    var stored = localStorage.getItem(LS_UNLOCKED);
    var ids    = stored ? JSON.parse(stored) : ["standard"];
    if (ids.indexOf("standard") === -1) ids.push("standard");

    // Carry the locally-chosen skin up too, but only if it's actually
    // unlocked — otherwise fall back to standard.
    var sel = localStorage.getItem(LS_SKIN) || "standard";
    if (ids.indexOf(sel) === -1) sel = "standard";

    _cache.unlockedLevel = lvl;
    _cache.unlockedSkins = new Set(ids);
    _cache.selectedSkin  = sel;

    // Only write a server row if the user has real progress beyond the
    // default; otherwise leave the table untouched (defaults apply).
    if (lvl <= 1 && ids.length <= 1) return;

    await sb().from(DB_TABLE).upsert({
      user_id:        uid(),
      unlocked_level: lvl,
      unlocked_skins: ids,
      selected_skin:  sel,
      updated_at:     new Date().toISOString(),
    }, { onConflict: "user_id" });

    localStorage.removeItem(LS_LEVEL);
    localStorage.removeItem(LS_UNLOCKED);
  }

  // ── Load progress and refresh the cache ────────────────────────────────
  async function loadProgress() {
    if (uid()) {
      var row = await serverLoad();
      if (row) {
        var ids = row.unlocked_skins || ["standard"];
        if (ids.indexOf("standard") === -1) ids.push("standard");
        _cache.unlockedLevel = row.unlocked_level || 1;
        _cache.unlockedSkins = new Set(ids);

        var sel = row.selected_skin || "standard";
        if (ids.indexOf(sel) === -1) sel = "standard";

        // One-time adoption of a pre-server-sync localStorage selection:
        // if the server still holds the default but localStorage names an
        // unlocked skin, adopt it and push it up so it syncs everywhere.
        var localSel = localStorage.getItem(LS_SKIN);
        if (sel === "standard" && localSel && localSel !== "standard" &&
            ids.indexOf(localSel) !== -1) {
          sel = localSel;
          _cache.selectedSkin = sel;
          serverSave();
        } else {
          _cache.selectedSkin = sel;
        }
      } else {
        // No server row yet — push any local progress (incl. selection) up.
        await migrateLocal();
      }
    } else {
      // Signed out: always use defaults — skins are locked behind auth.
      // Drop the localStorage mirror too, so the next signed-out load
      // doesn't optimistically paint a skin it'll only snap back from.
      _cache.unlockedLevel = 1;
      _cache.unlockedSkins = new Set(["standard"]);
      _cache.selectedSkin  = "standard";
      localStorage.removeItem(LS_SKIN);
    }
    _cache.loaded = true;
    window.dispatchEvent(new Event("aig:progress-loaded"));
  }

  // Reload whenever auth state changes (sign-in / sign-out)…
  window.addEventListener("auth-state", function () { loadProgress(); });
  // …and once on first load as a safety net, in case the initial
  // auth-state event fired before this listener was registered.
  (window.__authReady || Promise.resolve()).then(loadProgress);

  // ── Asset prefix helper ─────────────────────────────────────────────────
  function assetPrefix() {
    var el = document.querySelector('link[href*="assets/"], script[src*="assets/"]');
    if (el) {
      var attr = el.getAttribute("href") || el.getAttribute("src");
      var idx  = attr.indexOf("assets/");
      return attr.slice(0, idx);
    }
    return "";
  }

  function getSkin(id) {
    return SKINS.find(function (s) { return s.id === id; }) || SKINS[0];
  }

  // ── Public API ──────────────────────────────────────────────────────────
  window.GoatSkins = {
    SKINS: SKINS,

    // Skin selection — server-backed (quiz_progress.selected_skin), synced
    // across devices. Until the real state has loaded we deliberately
    // report "standard" so the UI never shows a skin the user may not have
    // unlocked on this device; callers repaint on "aig:progress-loaded".
    getSelectedId: function () {
      var id = _cache.selectedSkin || "standard";
      // Before the real state loads, optimistically honour the last-known
      // selection (seeded from localStorage) so the nav never flashes the
      // default skin first. loadProgress repaints to the authoritative
      // value — including back to "standard" if signed out or locked.
      if (!_cache.loaded) return id;
      if (!_cache.unlockedSkins.has(id)) id = "standard";
      return id;
    },
    setSelectedId: function (id) {
      if (!uid()) return;
      if (!_cache.unlockedSkins.has(id)) return;
      _cache.selectedSkin = id;
      // Mirror to localStorage so same-device tabs repaint via the
      // "storage" event; the server row remains the source of truth.
      localStorage.setItem(LS_SKIN, id);
      serverSave();
      window.dispatchEvent(new Event("aig:skin-changed"));
    },

    // Has the real (server/confirmed) state loaded yet?
    isLoaded: function () {
      return _cache.loaded;
    },

    // Progress reads — synchronous from cache.
    getProgress: function () {
      return { unlockedLevel: _cache.unlockedLevel };
    },
    getUnlockedIds: function () {
      return _cache.unlockedSkins;
    },

    // Progress write — update cache then persist (fire-and-forget).
    markLevelPassed: function (level) {
      if (level >= _cache.unlockedLevel) {
        _cache.unlockedLevel = level + 1;
      }
      var skinId = this.levelToSkinId(level);
      if (skinId) _cache.unlockedSkins.add(skinId);

      // Persist: server only (quiz is gated behind auth, so uid() must be set).
      if (uid()) {
        serverSave();
      }
    },

    levelToSkinId: function (level) {
      var skin = SKINS.find(function (s) { return s.level === level; });
      return skin ? skin.id : null;
    },

    resetProgress: function () {
      var wasSelected = _cache.selectedSkin;
      _cache.unlockedLevel = 1;
      _cache.unlockedSkins = new Set(["standard"]);
      _cache.selectedSkin  = "standard";
      if (uid()) {
        localStorage.setItem(LS_SKIN, "standard");
        if (wasSelected && wasSelected !== "standard") {
          window.dispatchEvent(new Event("aig:skin-changed"));
        }
        serverSave();
      }
      window.dispatchEvent(new Event("aig:progress-loaded"));
    },

    buildSvg: function (id) {
      var skin   = getSkin(id || this.getSelectedId());
      var prefix = assetPrefix();
      var img    = document.createElement("img");
      img.src       = prefix + skin.gif;
      img.alt       = skin.name;
      img.className = "goat-gif goat-svg";
      return img;
    },
  };
})();

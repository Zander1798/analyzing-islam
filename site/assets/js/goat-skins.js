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
  // Initialised from localStorage immediately so the page renders without
  // waiting for the Supabase round-trip. Overwritten once auth resolves.
  var _cache = (function () {
    var lvl     = parseInt(localStorage.getItem(LS_LEVEL) || "1", 10);
    var stored  = localStorage.getItem(LS_UNLOCKED);
    var ids     = stored ? JSON.parse(stored) : [];
    if (ids.indexOf("standard") === -1) ids.push("standard");
    return { unlockedLevel: lvl, unlockedSkins: new Set(ids) };
  }());

  function sb()  { return window.__supabase; }
  function uid() { var s = window.__session; return s && s.user ? s.user.id : null; }

  // ── Server helpers ──────────────────────────────────────────────────────
  async function serverLoad() {
    if (!sb() || !uid()) return null;
    var result = await sb()
      .from(DB_TABLE)
      .select("unlocked_level, unlocked_skins")
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
      updated_at:      new Date().toISOString(),
    }, { onConflict: "user_id" });
  }

  // ── Migration: localStorage → Supabase on first sign-in ────────────────
  async function migrateLocal() {
    var lvl    = parseInt(localStorage.getItem(LS_LEVEL) || "1", 10);
    var stored = localStorage.getItem(LS_UNLOCKED);
    var ids    = stored ? JSON.parse(stored) : ["standard"];
    if (ids.indexOf("standard") === -1) ids.push("standard");

    // Only migrate if the user has actual progress beyond the default.
    if (lvl <= 1 && ids.length <= 1) return;

    await sb().from(DB_TABLE).upsert({
      user_id:        uid(),
      unlocked_level: lvl,
      unlocked_skins: ids,
      updated_at:     new Date().toISOString(),
    }, { onConflict: "user_id" });

    localStorage.removeItem(LS_LEVEL);
    localStorage.removeItem(LS_UNLOCKED);

    _cache.unlockedLevel = lvl;
    _cache.unlockedSkins = new Set(ids);
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
      } else {
        // No server row yet — push any local progress up.
        await migrateLocal();
      }
    } else {
      // Signed out: read from localStorage.
      var lvl    = parseInt(localStorage.getItem(LS_LEVEL) || "1", 10);
      var stored = localStorage.getItem(LS_UNLOCKED);
      var ids    = stored ? JSON.parse(stored) : ["standard"];
      if (ids.indexOf("standard") === -1) ids.push("standard");
      _cache.unlockedLevel = lvl;
      _cache.unlockedSkins = new Set(ids);
    }
    window.dispatchEvent(new Event("aig:progress-loaded"));
  }

  // Reload whenever auth state changes (sign-in / sign-out).
  window.addEventListener("auth-state", function () { loadProgress(); });

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

    // Skin selection — always localStorage (no need to sync per-device).
    getSelectedId: function () {
      return localStorage.getItem(LS_SKIN) || "standard";
    },
    setSelectedId: function (id) {
      localStorage.setItem(LS_SKIN, id);
      window.dispatchEvent(new Event("aig:skin-changed"));
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

      // Persist: server if signed in, localStorage otherwise.
      if (uid()) {
        serverSave();
      } else {
        localStorage.setItem(LS_LEVEL, String(_cache.unlockedLevel));
        localStorage.setItem(LS_UNLOCKED, JSON.stringify(Array.from(_cache.unlockedSkins)));
      }
    },

    levelToSkinId: function (level) {
      var skin = SKINS.find(function (s) { return s.level === level; });
      return skin ? skin.id : null;
    },

    resetProgress: function () {
      _cache.unlockedLevel = 1;
      _cache.unlockedSkins = new Set(["standard"]);
      var selectedId = localStorage.getItem(LS_SKIN);
      if (selectedId && selectedId !== "standard") {
        localStorage.setItem(LS_SKIN, "standard");
        window.dispatchEvent(new Event("aig:skin-changed"));
      }
      if (uid()) {
        serverSave();
      } else {
        localStorage.setItem(LS_LEVEL, "1");
        localStorage.setItem(LS_UNLOCKED, JSON.stringify(["standard"]));
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

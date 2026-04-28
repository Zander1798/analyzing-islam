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
      level: null,
    },
    {
      id:    "hijab",
      name:  "Hijab",
      blurb: "Modest and magnificent.",
      gif:   "assets/images/goat-hijab.gif",
      level: null,
    },
  ];

  var LS_SKIN    = "aig:goat-skin";
  var LS_LEVEL   = "aig:unlocked-level";
  var LS_UNLOCKED = "aig:unlocked-skins";

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

  window.GoatSkins = {
    SKINS: SKINS,

    getSelectedId: function () {
      return localStorage.getItem(LS_SKIN) || "standard";
    },

    setSelectedId: function (id) {
      localStorage.setItem(LS_SKIN, id);
      window.dispatchEvent(new Event("aig:skin-changed"));
    },

    getProgress: function () {
      var lvl = parseInt(localStorage.getItem(LS_LEVEL) || "1", 10);
      return { unlockedLevel: lvl };
    },

    markLevelPassed: function (level) {
      var cur = this.getProgress().unlockedLevel;
      if (level >= cur) {
        localStorage.setItem(LS_LEVEL, String(level + 1));
      }
      var skinId = this.levelToSkinId(level);
      if (skinId) {
        var ids = Array.from(this.getUnlockedIds());
        if (ids.indexOf(skinId) === -1) ids.push(skinId);
        localStorage.setItem(LS_UNLOCKED, JSON.stringify(ids));
      }
    },

    getUnlockedIds: function () {
      var stored = localStorage.getItem(LS_UNLOCKED);
      var ids    = stored ? JSON.parse(stored) : [];
      if (ids.indexOf("standard") === -1) ids.push("standard");
      return new Set(ids);
    },

    levelToSkinId: function (level) {
      var skin = SKINS.find(function (s) { return s.level === level; });
      return skin ? skin.id : null;
    },

    // Returns a DOM element for the goat nav button (replaces old SVG).
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

// Nav goat button: injects the goat into the site nav. Click navigates to goat.html.
// Animations and skins will be GIF-based — old CSS animation system removed.
(function () {
  "use strict";

  function assetPrefix() {
    const el = document.querySelector('link[href*="assets/"], script[src*="assets/"]');
    if (el) {
      const attr = el.getAttribute("href") || el.getAttribute("src");
      const idx = attr.indexOf("assets/");
      return attr.slice(0, idx);
    }
    const parts = location.pathname.split("/").filter(Boolean);
    const depth = Math.max(0, parts.length - 1);
    return depth > 0 ? "../".repeat(depth) : "";
  }

  function buildNavGoatSvg() {
    if (window.GoatSkins && typeof window.GoatSkins.buildSvg === "function") {
      const id = window.GoatSkins.getSelectedId();
      return window.GoatSkins.buildSvg(id, { withGrass: true });
    }
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("class", "goat-svg");
    svg.setAttribute("viewBox", "0 0 24 20");
    return svg;
  }

  function repaintNavGoat(btn) {
    const old = btn.querySelector(".goat-svg");
    const next = buildNavGoatSvg();
    if (old) old.replaceWith(next);
    else btn.insertBefore(next, btn.firstChild);
  }

  function init() {
    const navInner = document.querySelector(".site-nav-inner");
    if (!navInner) return;
    if (navInner.querySelector(".goat-scream")) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "goat-scream";
    btn.setAttribute("aria-label", "Goat page");
    btn.title = "Click me for the Goat page";
    btn.appendChild(buildNavGoatSvg());
    navInner.appendChild(btn);

    btn.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      var session = window.__session;
      if (!session || !session.user) return;
      e.preventDefault();
      window.location.href = (assetPrefix() || "") + "goat.html";
    });

    window.addEventListener("aig:skin-changed", function () { repaintNavGoat(btn); });
    window.addEventListener("storage", function (e) {
      if (e.key === "aig:goat-skin") repaintNavGoat(btn);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // --- Nav auto-hide: slide nav off-screen on scroll-down, back on scroll-up ---
  function initNavAutoHide() {
    const nav = document.querySelector(".site-nav");
    if (!nav) return;
    let lastY = window.scrollY;
    let ticking = false;
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        const y = window.scrollY;
        if (y <= 60) {
          // Always show nav near the top of the page.
          nav.classList.remove("is-hidden");
        } else if (y > lastY) {
          // Scrolling down: hide nav.
          nav.classList.add("is-hidden");
        } else if (window.innerWidth > 900) {
          // Scrolling up on desktop: reveal nav.
          nav.classList.remove("is-hidden");
        }
        // Scrolling up on mobile while past the top: nav stays hidden.
        lastY = y;
        ticking = false;
      });
    }, { passive: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNavAutoHide);
  } else {
    initNavAutoHide();
  }

  // --- Embed mode (for iframes on the Compare page) ---------------------
  function applyEmbedMode() {
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.get("embed") === "1") {
        document.documentElement.classList.add("embed-mode");
        document.body && document.body.classList.add("embed-mode");
      }
    } catch (_) {}
  }
  applyEmbedMode();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyEmbedMode);
  }

  // --- Footer: random catalog fact -------------------------------------------
  var FOOTER_FACTS = [
    "Muhammad married Aisha when she was 6 years old and consummated the marriage when she was 9. (Bukhari 5134)",
    "The Quran permits husbands to beat disobedient wives. (Quran 4:34)",
    "Islamic law prescribes amputation of the hand for theft. (Quran 5:38)",
    "A woman inherits half of what a man inherits under Quranic law. (Quran 4:11)",
    "A woman's testimony counts as half a man's in Islamic courts. (Quran 2:282)",
    "The Quran permits men to have sex with female captives and slaves. (Quran 4:24)",
    "Paradise in the Quran includes rivers of wine for believers. (Quran 47:15)",
    "Male believers in paradise are promised eternal virgin companions called houris. (Quran 44:54)",
    "Muhammad claimed the sun physically sets each night in a muddy spring. (Quran 18:86)",
    "The Quran says human semen is produced between the backbone and the ribs. (Quran 86:6-7)",
    "Muhammad said a fly carries disease on one wing and its cure on the other. (Bukhari 3320)",
    "Leaving Islam is punishable by death in Islamic jurisprudence. (Bukhari 6922)",
    "The Quran prescribes crucifixion and cross-amputation for spreading corruption. (Quran 5:33)",
    "Muhammad had at least 13 wives, while the Quran limits other men to 4. (Quran 33:50)",
    "The Quran claims Allah split the moon in two as proof of Muhammad's prophethood. (Quran 54:1)",
    "Stars are described in the Quran as missiles fired at eavesdropping demons. (Quran 67:5)",
    "The Quran instructs Muslims not to take Jews or Christians as close allies. (Quran 5:51)",
    "Muhammad reportedly said the black seed cures every disease except death. (Bukhari 5687)",
    "Jinn are described in the Quran as beings made from smokeless fire. (Quran 55:15)",
    "The Quran endorses slavery and gives detailed rules for the treatment of slaves. (Quran 4:36)",
    "Muhammad declared that most people in hell are women. (Bukhari 304)",
    "The Quran says disbelievers will drink boiling water and wear garments of fire in hell. (Quran 22:19-20)",
    "Dogs are considered ritually impure in Islamic law, requiring purification after contact. (Muslim 279)",
    "Muhammad ordered the killing of those who leave Islam, even if they later convert back. (Bukhari 6922)",
    "The Quran says Allah cursed and transformed some Jews into apes and pigs. (Quran 5:60)",
  ];

  function initFooterFact() {
    var footer = document.querySelector(".site-footer");
    if (!footer) return;
    var fact = FOOTER_FACTS[Math.floor(Math.random() * FOOTER_FACTS.length)];
    footer.innerHTML = '<span class="cf-footer-fact">' + fact + "</span>";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFooterFact);
  } else {
    initFooterFact();
  }
})();

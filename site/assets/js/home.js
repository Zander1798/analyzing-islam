// home.js — Analyzing Islam homepage (Direction B) interactions.
// Self-contained IIFE. Does NOT define or overwrite any shared global
// (__session, __profile, __supabase, __authReady, AI_AUTH, GoatSkins).
// Only touches homepage-only elements + toggles a `.scrolled` class on the nav.
(function () {
  "use strict";
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  try {

  // ---- category filmstrip (links to the real category pages) ----
  var cats = [
    ["Prophetic Character", 235, "category/prophet.html"],
    ["Women", 278, "category/women.html"],
    ["Contradictions", 185, "category/contradiction.html"],
    ["Moral Problems", 183, "category/morality.html"],
    ["Science", 163, "category/science.html"],
    ["Strange / Obscure", 152, "category/strange.html"],
    ["Logical Inconsistency", 147, "category/logic.html"],
    ["Ritual Absurdities", 138, "category/ritual.html"],
    ["Eschatology", 127, "category/eschatology.html"],
    ["Warfare & Jihad", 120, "category/warfare.html"],
    ["Magic & Occult", 105, "category/magic.html"],
    ["Pre-Islamic Borrowings", 96, "category/preislamic.html"],
    ["Sexual Issues", 95, "category/sexual.html"],
    ["Slavery & Captives", 85, "category/slavery.html"],
    ["Hudud", 83, "category/hudud.html"],
    ["Governance", 81, "category/governance.html"],
    ["Disbelievers", 71, "category/disbelievers.html"],
    ["Allah's Character", 62, "category/allah.html"],
    ["Antisemitism", 58, "category/antisemitism.html"],
    ["Paradise", 55, "category/paradise.html"],
    ["Hell", 51, "category/hell.html"],
    ["Animals", 51, "category/animals.html"],
    ["Jesus / Christology", 46, "category/jesus.html"],
    ["Abrogation", 44, "category/abrogation.html"],
    ["Scripture Integrity", 42, "category/scripture.html"],
    ["Apostasy & Blasphemy", 41, "category/apostasy.html"],
    ["Prophetic Privileges", 38, "category/privileges.html"],
    ["Child Marriage", 22, "category/childmarriage.html"],
    ["LGBTQ / Gender", 22, "category/lgbtq.html"],
    ["Gross / Vile", 18, "category/gross-vile.html"],
    ["Incest", 11, "category/incest.html"]
  ];
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function tile(c) {
    return '<a class="tile" href="' + c[2] + '"><span class="tn">' + esc(c[0]) +
           '</span><span class="tc">' + c[1] + ' entries</span></a>';
  }
  var strip = document.querySelector("[data-strip]");
  if (strip) strip.innerHTML = cats.map(tile).join("").repeat(2);

  // ---- Today's arguments: deterministic daily shuffle of 3 from a pool ----
  var pool = [
    ["Logic", "The Islamic Dilemma", "The Quran affirms the previous scriptures, contradicts them, and claims Allah's words cannot be changed. Every escape route breaks at least one."],
    ["Child Marriage", "Aisha at six and nine", "The canonical collections place the contract at six and consummation at nine — reported approvingly, in the sources Sunni jurisprudence treats as authoritative."],
    ["Scripture", "Uthman's variant-burning", "The caliph standardised one reading and burned the rest — awkward for a claim of perfect, untouched preservation."],
    ["Jesus", "Denial of the crucifixion", "The Quran denies the crucifixion. Every contemporary source — Christian, Jewish, Roman, pagan — affirms it. No serious historian disputes it."],
    ["Warfare", "The Sword Verse (9:5)", "“Kill the polytheists wherever you find them.” Classical commentators hold it abrogates over 100 conciliatory verses."],
    ["Prophet", "The Zaynab affair (33:37)", "A revelation authorises Muhammad's marriage to his adopted son's divorced wife — after he had admired her."],
    ["Contradiction", "“No contradiction” (4:82)", "The Quran claims its lack of contradictions proves divine origin. The book contains dozens. The self-test fails by its own terms."],
    ["Abrogation", "The Abrogation Verse (2:106)", "Allah replaces verses with “better” ones — but an omniscient author's first draft should already be optimal."],
    ["Women", "“Deficient in intellect”", "A sound hadith has the Prophet call women deficient in intelligence and religion — cited to justify a woman's half-testimony."],
    ["Science", "The sun prostrates", "A sound hadith has the sun travel each night to prostrate beneath the Throne before being permitted to rise again."]
  ];
  var stageEl = document.querySelector("[data-daily]");
  if (stageEl) {
    var day = Math.floor(Date.now() / 864e5), n = pool.length, offs = [0, 4, 7], html = "";
    for (var k = 0; k < 3; k++) {
      var p = pool[((day * 3) + offs[k]) % n];
      html += '<div class="slide' + (k === 0 ? ' active' : '') + '"><span class="k">Today · ' +
              esc(p[0]) + '</span><h3>' + esc(p[1]) + '</h3><p>' + esc(p[2]) + '</p></div>';
    }
    stageEl.innerHTML = html;
  }

  // ---- count-up ----
  function countUp(el) {
    var to = parseInt(el.getAttribute("data-to"), 10);
    if (reduce) { el.textContent = to.toLocaleString(); return; }
    var s = null;
    requestAnimationFrame(function step(t) {
      if (!s) s = t;
      var pr = Math.min((t - s) / 1600, 1);
      el.textContent = Math.round(to * (1 - Math.pow(1 - pr, 3))).toLocaleString();
      if (pr < 1) requestAnimationFrame(step);
    });
  }

  // ---- reveal + counters via IntersectionObserver ----
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          var num = e.target.querySelector && e.target.querySelector(".n[data-to]");
          if (num && !num._d) { num._d = 1; countUp(num); }
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.2 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
    document.querySelectorAll(".n[data-to]").forEach(function (el) { el.textContent = parseInt(el.getAttribute("data-to"), 10).toLocaleString(); });
  }

  // ---- Today's arguments carousel ----
  document.querySelectorAll("[data-stage]").forEach(function (stage) {
    var dots = stage.parentNode.querySelector("[data-dots]");
    var slides = [].slice.call(stage.querySelectorAll(".slide"));
    if (!dots || !slides.length) return;
    slides.forEach(function () {
      var b = document.createElement("button");
      b.innerHTML = '<span class="fill"></span>';
      dots.appendChild(b);
    });
    var btns = [].slice.call(dots.children), cur = 0, timer = null;
    function paint() {
      slides.forEach(function (s, i) { s.classList.toggle("active", i === cur); });
      btns.forEach(function (b, i) { b.classList.remove("on"); if (i === cur && !reduce) { void b.offsetWidth; b.classList.add("on"); } });
    }
    function go(i) { cur = (i + slides.length) % slides.length; paint(); restart(); }
    function restart() { if (timer) clearInterval(timer); if (!reduce) timer = setInterval(function () { cur = (cur + 1) % slides.length; paint(); }, 6000); }
    btns.forEach(function (b, i) { b.onclick = function () { go(i); }; });
    paint(); restart();
  });

  // ---- nav: transparent over the hero, solid once scrolled past it ----
  var nav = document.querySelector(".site-nav");
  if (nav) {
    var onScroll = function () { nav.classList.toggle("scrolled", window.scrollY > window.innerHeight * 0.7); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  } catch (e) {
    // Failsafe: if anything above throws, reveal all content so nothing is
    // ever left invisible (animation is lost, content is not).
    if (window.console) console.error("[home] init failed", e);
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
    document.querySelectorAll(".n[data-to]").forEach(function (el) {
      el.textContent = parseInt(el.getAttribute("data-to"), 10).toLocaleString();
    });
  }
})();

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
  // [category, title, description, entry URL] — each links to the specific catalog entry.
  var pool = [
    ["Logic", "The Islamic Dilemma", "The Quran affirms the previous scriptures, contradicts them, and claims Allah's words cannot be changed. Every escape route breaks at least one.", "catalog/quran.html#the-islamic-dilemma-the-quran-traps-itself-between-the-bible-12cdc43a"],
    ["Child Marriage", "Aisha at six and nine", "The canonical collections place the contract at six and consummation at nine — reported approvingly, in the sources Sunni jurisprudence treats as authoritative.", "catalog/abu-dawud.html#aisha-s-consummation-at-nine-the-swing-the-preparation-the-h-3c215117"],
    ["Scripture", "Uthman's variant-burning", "The caliph standardised one reading and burned the rest — awkward for a claim of perfect, untouched preservation.", "catalog/bukhari.html#uthman-burned-all-quran-manuscripts-except-his-standardized-368135b4"],
    ["Jesus", "Denial of the crucifixion", "The Quran denies the crucifixion. Every contemporary source — Christian, Jewish, Roman, pagan — affirms it. No serious historian disputes it.", "catalog/quran.html#jesus-was-not-crucified-someone-else-was-substituted-e7011545"],
    ["Warfare", "The Sword Verse (9:5)", "“Kill the polytheists wherever you find them.” Classical commentators hold it abrogates over 100 conciliatory verses.", "catalog/quran.html#the-sword-verse-kill-the-polytheists-wherever-you-find-them-8b577325"],
    ["Prophet", "The Zaynab affair (33:37)", "A revelation authorises Muhammad's marriage to his adopted son's divorced wife — after he had admired her.", "catalog/quran.html#zaynab-affair-allah-engineers-muhammad-s-marriage-to-his-ado-d1a100b2"],
    ["Contradiction", "“No contradiction” (4:82)", "The Quran claims its lack of contradictions proves divine origin. The book contains dozens. The self-test fails by its own terms.", "catalog/quran.html#no-contradiction-the-verse-that-sets-the-test-then-fails-it-09fb0e2d"],
    ["Abrogation", "The Abrogation Verse (2:106)", "Allah replaces verses with “better” ones — but an omniscient author's first draft should already be optimal.", "catalog/quran.html#q2-106-the-abrogation-verse-creates-cascading-problems-for-a-d34ebf0a"],
    ["Women", "“Deficient in intellect”", "A sound hadith has the Prophet call women deficient in intelligence and religion — cited to justify a woman's half-testimony.", "catalog/bukhari.html#women-are-deficient-in-intelligence-and-religion-most-of-hel-480b1975"],
    ["Science", "The sun prostrates", "A sound hadith has the sun travel each night to prostrate beneath the Throne before being permitted to rise again.", "catalog/bukhari.html#the-sun-prostrates-beneath-allah-s-throne-nightly-dfb0bdf8"]
  ];
  var stageEl = document.querySelector("[data-daily]");
  if (stageEl) {
    var day = Math.floor(Date.now() / 864e5), n = pool.length, offs = [0, 4, 7], html = "";
    for (var k = 0; k < 3; k++) {
      var p = pool[((day * 3) + offs[k]) % n];
      html += '<a class="slide' + (k === 0 ? ' active' : '') + '" href="' + p[3] + '">' +
              '<span class="k">Today · ' + esc(p[0]) + '</span><h3>' + esc(p[1]) + '</h3><p>' + esc(p[2]) +
              '</p><span class="slide-go">Read this argument →</span></a>';
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

    // Publish the nav's real height so the mobile hero can sit directly under
    // it (see the max-width:768px block in home.css). The nav is fixed and its
    // links wrap onto a variable number of rows, so this has to be measured —
    // and re-measured whenever the auth control changes the nav's contents.
    var heroInner = document.querySelector(".hero .inner");
    var cta = document.querySelector(".hero .cta");
    var setNavH = function () {
      var h = nav.offsetHeight;
      if (h) document.documentElement.style.setProperty("--nav-h", h + "px");
      if (!heroInner || !cta) return;
      // Decide whether the hero needs the compact treatment. Always measure the
      // *untightened* layout (class off first) so the result can't oscillate
      // between the two states on successive passes.
      document.body.classList.remove("hero-tight");
      void heroInner.offsetHeight; // force reflow before measuring
      if (cta.getBoundingClientRect().bottom > window.innerHeight - 8) {
        document.body.classList.add("hero-tight");
      }
    };
    setNavH();
    window.addEventListener("resize", setNavH);
    window.addEventListener("orientationchange", setNavH);
    // auth-ui.js injects the Sign in / account control asynchronously (after
    // the first session check), which can add a nav row. A ResizeObserver
    // catches that, plus font swaps and username changes, without polling.
    if (window.ResizeObserver) {
      new ResizeObserver(setNavH).observe(nav);
    } else {
      window.addEventListener("auth-state", function () { setTimeout(setNavH, 0); });
      window.addEventListener("profile-state", function () { setTimeout(setNavH, 0); });
    }
  }

  // ---- background videos: never show iOS's play glyph ----
  // The <video> tags already carry autoplay/muted/loop/playsinline, but iOS
  // Safari still refuses to autoplay under Low Power Mode, Low Data Mode
  // (cellular) or Settings > Safari > Auto-Play = off, and then paints a
  // large play button over the paused first frame. So: (1) kick play()
  // explicitly, (2) retry on the first user gesture, which unlocks playback
  // in every one of those modes, and (3) if it still refuses, hide the video
  // so the glyph is never drawn — the gradient/vignette layers stay put.
  var bgVideos = Array.prototype.slice.call(document.querySelectorAll(".hero video, .featbg video"));
  if (bgVideos.length) {
    bgVideos.forEach(function (v) { v.muted = true; v.defaultMuted = true; });
    var tryPlay = function () {
      bgVideos.forEach(function (v) {
        if (!v.paused && !v.ended) return;
        var p = v.play();
        if (p && p.catch) p.catch(function () { v.classList.add("bg-video-blocked"); });
      });
    };
    var onGesture = function () {
      tryPlay();
      bgVideos.forEach(function (v) {
        v.addEventListener("playing", function () { v.classList.remove("bg-video-blocked"); }, { once: true });
      });
    };
    tryPlay();
    // Mark as blocked if nothing has started within a moment, so the glyph
    // is hidden even in modes where play() never settles.
    setTimeout(function () {
      bgVideos.forEach(function (v) { if (v.paused) v.classList.add("bg-video-blocked"); });
    }, 1500);
    ["touchstart", "pointerdown", "scroll", "keydown"].forEach(function (ev) {
      window.addEventListener(ev, onGesture, { once: true, passive: true });
    });
    bgVideos.forEach(function (v) {
      v.addEventListener("playing", function () { v.classList.remove("bg-video-blocked"); });
    });
    document.addEventListener("visibilitychange", function () { if (!document.hidden) tryPlay(); });
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

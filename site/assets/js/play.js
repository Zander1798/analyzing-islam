// Drives /play.html: levels grid, quiz runner, fail/pass modals, unlock flow.
//
// Persistence: localStorage via window.GoatSkins (goat-skins.js).
//   - GoatSkins.getProgress().unlockedLevel = highest level number currently
//     playable. Level 1 always playable; level N+1 unlocks after passing N.
//   - GoatSkins.markLevelPassed(level) bumps the unlocked level and unlocks
//     the corresponding skin.
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }
  function $(sel) { return document.querySelector(sel); }

  const state = {
    levels: null,
    currentLevel: null, // 1..9
    currentQ: 0,        // 0..6
    questions: [],
  };

  // --- Levels grid ---------------------------------------------------------
  function renderLevelsGrid() {
    const grid = $("#levels-grid");
    if (!grid || !state.levels) return;
    grid.innerHTML = "";
    const progress = window.GoatSkins.getProgress();
    const unlocked = window.GoatSkins.getUnlockedIds();
    state.levels.forEach(function (lvl) {
      const isUnlocked = lvl.level <= progress.unlockedLevel;
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = "level-tile" + (isUnlocked ? "" : " is-locked");
      tile.disabled = !isUnlocked;

      const skinId = window.GoatSkins.levelToSkinId(lvl.level);
      const isCleared = skinId && unlocked.has(skinId);

      tile.innerHTML = ''
        + '<div class="level-num">Level ' + lvl.level + '</div>'
        + '<div class="level-title">' + escapeHtml(lvl.title) + '</div>'
        + '<div class="level-blurb">' + escapeHtml(lvl.blurb) + '</div>'
        + '<div class="level-foot">'
        + (isUnlocked
            ? (isCleared
                ? '<span class="level-tag is-cleared">Cleared</span>'
                : '<span class="level-tag is-ready">Ready</span>')
            : '<span class="level-tag is-locked">Locked \u{1F512}</span>')
        + '</div>';

      if (isUnlocked) {
        tile.addEventListener("click", function () { startLevel(lvl.level); });
      }
      grid.appendChild(tile);
    });
  }

  // --- Quiz runner ---------------------------------------------------------
  function startLevel(level) {
    const lvl = state.levels.find(function (l) { return l.level === level; });
    if (!lvl) return;
    state.currentLevel = level;
    state.currentQ = 0;
    state.questions = shuffle(lvl.questions.slice()).slice(0, 7);
    $("#levels-view").hidden = true;
    $("#quiz-view").hidden = false;
    $("#quiz-title").textContent = "Level " + lvl.level + " — " + lvl.title;
    renderQuestion();
  }

  function renderQuestion() {
    const i = state.currentQ;
    const total = state.questions.length;
    const q = state.questions[i];
    $("#quiz-progress-label").textContent = "Question " + (i + 1) + " / " + total;
    $("#quiz-progress-fill").style.width = ((i / total) * 100) + "%";
    $("#quiz-question").textContent = q.q;
    const refEl = $("#quiz-ref");
    if (refEl) refEl.textContent = q.ref || "";
    const choicesEl = $("#quiz-choices");
    choicesEl.innerHTML = "";
    [["a", q.a], ["b", q.b], ["c", q.c]].forEach(function (pair) {
      const key = pair[0], text = pair[1];
      if (text == null) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quiz-choice";
      btn.dataset.key = key;
      btn.innerHTML = '<span class="quiz-choice-letter">' + key.toUpperCase() + '</span>'
                    + '<span class="quiz-choice-text">' + escapeHtml(text) + '</span>';
      btn.addEventListener("click", function () { submitAnswer(key); });
      choicesEl.appendChild(btn);
    });
    const link = $("#quiz-source-link");
    link.href = q.source || "read.html";
    link.textContent = "Read source ↗";
    const link2 = $("#quiz-source-link-2");
    if (link2) {
      if (q.source2) {
        link2.href = q.source2;
        link2.hidden = false;
      } else {
        link2.hidden = true;
      }
    }
  }

  function submitAnswer(key) {
    const q = state.questions[state.currentQ];
    if (key !== q.answer) {
      // Wrong: instant fail, never reveal correct answer.
      showFailModal();
      return;
    }
    state.currentQ++;
    if (state.currentQ >= state.questions.length) {
      passLevel();
    } else {
      renderQuestion();
    }
  }

  function quitToLevels() {
    state.currentLevel = null;
    state.currentQ = 0;
    state.questions = [];
    hideModal();
    $("#quiz-view").hidden = true;
    $("#levels-view").hidden = false;
    renderLevelsGrid();
  }

  // --- Result modals -------------------------------------------------------
  function showFailModal() {
    const modal = $("#result-modal");
    const title = $("#result-title");
    const body = $("#result-body");
    const actions = $("#result-actions");
    title.textContent = "LEVEL FAILED";
    title.className = "result-title is-fail";
    body.textContent = "One wrong answer ends the level. Don't worry — the source is open in a tab if you want to study before retrying.";
    actions.innerHTML = "";
    const tryAgain = button("Try again", "btn btn-primary", function () {
      hideModal();
      startLevel(state.currentLevel);
    });
    const back = button("Back to play page", "btn", quitToLevels);
    actions.appendChild(tryAgain);
    actions.appendChild(back);
    modal.hidden = false;
  }

  function showPassModal(skinId, isFirstClear) {
    const modal = $("#result-modal");
    const title = $("#result-title");
    const body = $("#result-body");
    const actions = $("#result-actions");
    title.textContent = "LEVEL PASSED";
    title.className = "result-title is-pass";
    if (isFirstClear) {
      const skin = window.GoatSkins.SKINS.find(function (s) { return s.id === skinId; });
      body.innerHTML = '<strong>New skin unlocked:</strong> ' + escapeHtml(skin ? skin.name : skinId);
    } else {
      body.textContent = "Level cleared!";
    }
    actions.innerHTML = "";
    if (isFirstClear) {
      actions.appendChild(button("See skin", "btn btn-primary", function () {
        window.location.href = "goat.html#skin-slot-" + skinId;
      }));
    }
    const nextLevel = state.currentLevel + 1;
    if (nextLevel <= 9) {
      actions.appendChild(button("Next level", "btn", function () {
        hideModal();
        startLevel(nextLevel);
      }));
    }
    actions.appendChild(button("Back to play page", "btn", quitToLevels));
    modal.hidden = false;
  }

  function hideModal() {
    $("#result-modal").hidden = true;
  }

  function passLevel() {
    const skinId = window.GoatSkins.levelToSkinId(state.currentLevel);
    const wasUnlocked = window.GoatSkins.getUnlockedIds().has(skinId);
    window.GoatSkins.markLevelPassed(state.currentLevel);
    showPassModal(skinId, !wasUnlocked);
  }

  // --- Helpers -------------------------------------------------------------
  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
    }
    return arr;
  }
  function button(text, cls, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.textContent = text;
    b.addEventListener("click", onClick);
    return b;
  }
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // --- Auth gate -----------------------------------------------------------
  function isSignedIn() {
    return !!(window.__session && window.__session.user);
  }

  function renderAuthGate() {
    const view = $("#levels-view");
    if (!view) return;
    view.innerHTML =
      '<div class="play-page-back"><a href="index.html" class="btn">← Home</a></div>' +
      '<h1 class="play-page-title">Quiz Levels</h1>' +
      '<div class="play-auth-gate">' +
        '<p class="play-auth-message">Sign in to play and save your progress across all your devices.</p>' +
        '<a href="login.html" class="btn btn-primary">Sign in</a>' +
      '</div>';
  }

  function initPlay() {
    if (!window.GoatSkins) return;

    if (!isSignedIn()) {
      renderAuthGate();
      return;
    }

    // Restore the levels-view HTML if we previously showed the auth gate.
    const view = $("#levels-view");
    if (view && view.querySelector(".play-auth-gate")) {
      view.innerHTML =
        '<div class="play-page-back">' +
          '<a href="index.html" class="btn">← Home</a>' +
          '<a href="goat.html" class="btn">Goat →</a>' +
        '</div>' +
        '<h1 class="play-page-title">Quiz Levels</h1>' +
        '<p class="play-page-tagline">One wrong answer ends the level. Pass each level to unlock a new goat skin. 7 questions drawn from a pool of 12 — the order changes every run.</p>' +
        '<div class="levels-grid" id="levels-grid"><p style="color:var(--text-muted)">Loading levels…</p></div>';
    }

    if (!state.levels) {
      fetch("assets/data/quiz-levels.json", { cache: "no-cache" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          state.levels = data.levels;
          renderLevelsGrid();
        })
        .catch(function (err) {
          const grid = $("#levels-grid");
          if (grid) grid.innerHTML = '<p class="quiz-error">Could not load levels: ' + escapeHtml(String(err)) + '</p>';
        });
    } else {
      renderLevelsGrid();
    }

    if (!$("#quiz-quit")._quitBound) {
      $("#quiz-quit").addEventListener("click", quitToLevels);
      $("#quiz-quit")._quitBound = true;
    }
  }

  // --- Boot ----------------------------------------------------------------
  ready(function () {
    // Wait for the first auth check to complete before rendering so we don't
    // flash the sign-in gate for users who are already logged in.
    (window.__authReady || Promise.resolve()).then(function () { initPlay(); });

    // Re-run gate check whenever auth state changes.
    window.addEventListener("auth-state", function () { initPlay(); });

    // Re-render the levels grid when progress syncs from Supabase.
    window.addEventListener("aig:progress-loaded", function () {
      if (state.levels && !state.currentLevel) renderLevelsGrid();
    });
  });
})();

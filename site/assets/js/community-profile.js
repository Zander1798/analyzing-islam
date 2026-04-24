/* =============================================================
   Analyzing Islam — Community profile editor
   -------------------------------------------------------------
   Renders into #cf-profile-shell. Two modes:

     Edit (default): username (with availability check), bio,
                     avatar upload, banner upload. Save button
                     writes to profiles via AI_AUTH.updateProfile.

     Preview: swaps the form for the exact public user-profile
              rendering from community-profile-view.js so the
              author can see how they'll appear to others.

   The only field that pulls double-duty with the account
   profile page is username — both places hit profiles.username,
   so edits in either propagate automatically.
   ============================================================= */
(function () {
  "use strict";

  const shell = document.getElementById("cf-profile-shell");
  const USERNAME_RE = /^[a-z0-9][a-z0-9_]{2,19}$/;

  const state = {
    user: null,
    profile: null,      // current profile row
    memberships: [],    // viewer's own communities (used in Preview)
    mode: "edit",
    dirty: {},          // { username?, bio?, avatar_url?, banner_url? }
    avatarPreview: null,
    bannerPreview: null,
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  // ---------- Top-level paint ----------
  function renderSignedOut() {
    shell.innerHTML = `
      <div class="cf-form" style="text-align:center;">
        <h1>My profile</h1>
        <p>Sign in to manage your community profile.</p>
        <div style="display:flex;gap:10px;justify-content:center;margin-top:16px;">
          <a class="cf-btn cf-btn-primary" href="login.html?return=community-profile.html">Sign in</a>
          <a class="cf-btn" href="signup.html">Create account</a>
        </div>
      </div>`;
  }

  function render() {
    if (!state.user) { renderSignedOut(); return; }
    if (state.mode === "preview") { renderPreview(); return; }
    renderEdit();
  }

  // ---------- Edit mode ----------
  function renderEdit() {
    const p = state.profile || {};
    const username = (p.username || "").trim();
    const bio = p.bio || "";
    const avatarUrl = state.avatarPreview || p.avatar_url || "";
    const bannerUrl = state.bannerPreview || p.banner_url || "";

    const avatarThumb = avatarUrl
      ? `<img src="${esc(avatarUrl)}" alt="">`
      : `<span>${esc((username || state.user.email || "?")[0].toUpperCase())}</span>`;

    const bannerThumb = bannerUrl
      ? `<img src="${esc(bannerUrl)}" alt="">`
      : `<div class="cf-profile-banner-empty">No banner yet</div>`;

    shell.innerHTML = `
      <div class="cf-profile-edit">
        <div class="cf-profile-edit-head">
          <h1>My community profile</h1>
          <div class="cf-profile-mode-toggle" role="tablist">
            <button type="button" class="cf-profile-mode-btn is-active" data-mode="edit" role="tab">Edit</button>
            <button type="button" class="cf-profile-mode-btn" data-mode="preview" role="tab">Preview</button>
          </div>
        </div>
        <p class="cf-profile-edit-lede">This is how other community members see you. Username syncs with your account profile.</p>

        <div id="cf-profile-msg" class="auth-message auth-message--info" style="display:none;"></div>

        <section class="cf-profile-section">
          <h2>Banner</h2>
          <p class="cf-profile-section-lede">Wide image, shown at the top of your public profile. PNG / JPG / WebP / GIF, up to 5 MB.</p>
          <div class="cf-profile-banner-preview">${bannerThumb}</div>
          <div class="cf-profile-file-row">
            <label for="cf-profile-banner" class="btn">Choose image…</label>
            <input id="cf-profile-banner" type="file" accept="image/png,image/jpeg,image/webp,image/gif" style="display:none;">
            ${p.banner_url ? `<button type="button" class="btn btn-ghost" data-action="remove-banner">Remove banner</button>` : ""}
          </div>
        </section>

        <section class="cf-profile-section">
          <h2>Profile photo</h2>
          <p class="cf-profile-section-lede">Square image, shown in your header and next to your posts and comments.</p>
          <div class="cf-profile-avatar-row">
            <div class="cf-profile-avatar-preview">${avatarThumb}</div>
            <div class="cf-profile-file-row">
              <label for="cf-profile-avatar" class="btn">Choose image…</label>
              <input id="cf-profile-avatar" type="file" accept="image/png,image/jpeg,image/webp,image/gif" style="display:none;">
              ${p.avatar_url ? `<button type="button" class="btn btn-ghost" data-action="remove-avatar">Remove photo</button>` : ""}
            </div>
          </div>
        </section>

        <section class="cf-profile-section">
          <h2>Username</h2>
          <p class="cf-profile-section-lede">Public. 3–20 chars, lowercase letters, digits, underscore. Changes here also update your account profile.</p>
          <div class="auth-field">
            <input id="cf-profile-username" type="text"
                   value="${esc(username)}"
                   minlength="3" maxlength="20" pattern="[a-z0-9][a-z0-9_]{2,19}"
                   spellcheck="false" autocomplete="off">
            <div id="cf-profile-username-hint" class="auth-hint">${username ? 'Change your username.' : 'Pick a username.'}</div>
          </div>
        </section>

        <section class="cf-profile-section">
          <h2>Bio</h2>
          <p class="cf-profile-section-lede">A short description. Up to 500 characters.</p>
          <div class="auth-field">
            <textarea id="cf-profile-bio" maxlength="500" rows="4"
                      placeholder="Tell other users who you are or what you post about.">${esc(bio)}</textarea>
            <div id="cf-profile-bio-count" class="auth-hint">${bio.length}/500</div>
          </div>
        </section>

        <div class="cf-profile-save-row">
          <button type="button" id="cf-profile-save" class="auth-submit">Save profile</button>
          <button type="button" class="cf-btn" data-mode="preview">Preview</button>
        </div>
      </div>
    `;

    wireEdit();
  }

  function wireEdit() {
    shell.querySelectorAll("[data-mode]").forEach((b) => {
      b.addEventListener("click", () => {
        state.mode = b.getAttribute("data-mode");
        render();
      });
    });

    const msg = document.getElementById("cf-profile-msg");
    function setMsg(kind, text) {
      msg.className = "auth-message auth-message--" + kind;
      msg.textContent = text;
      msg.style.display = "block";
    }

    // Banner
    const bannerFile = document.getElementById("cf-profile-banner");
    const bannerPreview = shell.querySelector(".cf-profile-banner-preview");
    bannerFile.addEventListener("change", () => {
      const f = bannerFile.files && bannerFile.files[0];
      if (!f) return;
      if (!/^image\//i.test(f.type)) { setMsg("error", "Not an image."); return; }
      if (f.size > 5 * 1024 * 1024) { setMsg("error", "Banner too large (5 MB max)."); return; }
      const reader = new FileReader();
      reader.onload = () => {
        state.bannerPreview = reader.result;
        state.dirty.bannerFile = f;
        bannerPreview.innerHTML = `<img src="${reader.result}" alt="">`;
      };
      reader.readAsDataURL(f);
    });
    const removeBanner = shell.querySelector('[data-action="remove-banner"]');
    if (removeBanner) {
      removeBanner.addEventListener("click", () => {
        state.bannerPreview = null;
        state.dirty.banner_url = null;
        state.dirty.bannerFile = null;
        bannerPreview.innerHTML = `<div class="cf-profile-banner-empty">No banner yet</div>`;
      });
    }

    // Avatar
    const avatarFile = document.getElementById("cf-profile-avatar");
    const avatarPreview = shell.querySelector(".cf-profile-avatar-preview");
    avatarFile.addEventListener("change", () => {
      const f = avatarFile.files && avatarFile.files[0];
      if (!f) return;
      if (!/^image\//i.test(f.type)) { setMsg("error", "Not an image."); return; }
      if (f.size > 5 * 1024 * 1024) { setMsg("error", "Photo too large (5 MB max)."); return; }
      const reader = new FileReader();
      reader.onload = () => {
        state.avatarPreview = reader.result;
        state.dirty.avatarFile = f;
        avatarPreview.innerHTML = `<img src="${reader.result}" alt="">`;
      };
      reader.readAsDataURL(f);
    });
    const removeAvatar = shell.querySelector('[data-action="remove-avatar"]');
    if (removeAvatar) {
      removeAvatar.addEventListener("click", () => {
        state.avatarPreview = null;
        state.dirty.avatar_url = null;
        state.dirty.avatarFile = null;
        const seed = (state.profile && state.profile.username) || state.user.email || "?";
        avatarPreview.innerHTML = `<span>${esc(seed[0].toUpperCase())}</span>`;
      });
    }

    // Username (with availability debounce)
    const usernameIn = document.getElementById("cf-profile-username");
    const usernameHint = document.getElementById("cf-profile-username-hint");
    function setHint(kind, text) {
      usernameHint.textContent = text;
      usernameHint.className = "auth-hint auth-hint--" + kind;
    }
    let tok = 0;
    usernameIn.addEventListener("input", () => {
      const lower = usernameIn.value.toLowerCase();
      if (lower !== usernameIn.value) usernameIn.value = lower;
      const u = lower.trim();
      state.dirty.username = u || null;
      const my = ++tok;
      if (!u) { setHint("info", "Pick a username."); return; }
      if (!USERNAME_RE.test(u)) { setHint("error", "3–20 chars, lowercase letters/digits/underscore, can't start with _."); return; }
      if (state.profile && state.profile.username && u === state.profile.username) {
        setHint("info", "This is your current username.");
        return;
      }
      setHint("info", "Checking availability…");
      setTimeout(async () => {
        if (my !== tok) return;
        const { available, reason } = await window.AI_AUTH.checkUsernameAvailable(u);
        if (my !== tok) return;
        if (available) setHint("success", "“" + u + "” is available.");
        else if (reason === "taken") setHint("error", "“" + u + "” is already taken.");
        else setHint("error", "Could not check availability.");
      }, 400);
    });

    // Bio
    const bioIn = document.getElementById("cf-profile-bio");
    const bioCount = document.getElementById("cf-profile-bio-count");
    bioIn.addEventListener("input", () => {
      state.dirty.bio = bioIn.value;
      bioCount.textContent = bioIn.value.length + "/500";
    });

    // Save
    const saveBtn = document.getElementById("cf-profile-save");
    saveBtn.addEventListener("click", async () => {
      msg.style.display = "none";
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving…";

      // Format a Postgres / PostgREST error so the reason surfaces in the
      // UI instead of a vague failure. Missing bio/banner_url columns are
      // the most common foot-gun when the SQL migration hasn't been run.
      function describe(err) {
        const m = (err && (err.message || String(err))) || "Unknown error";
        const code = err && err.code;
        if (code === "42703" || /column .* does not exist/i.test(m) ||
            /could not find the .* column/i.test(m)) {
          return "Database migration missing. Paste supabase/profile-community-extensions.sql into the Supabase SQL editor and run it, then try again.";
        }
        if (code === "23505" || /duplicate/i.test(m)) {
          return "That username is already taken.";
        }
        if (code === "23514" || /profiles_username_format/.test(m)) {
          return "Invalid username format.";
        }
        if (code === "23514" || /profiles_bio_length/.test(m)) {
          return "Bio is too long (500 characters max).";
        }
        if (code === "42501" || /row-level security/i.test(m)) {
          return "Permission denied. Make sure you're signed in and the profile-extensions SQL has been applied.";
        }
        return m;
      }

      try {
        // 1) Banner upload (if a file was picked).
        if (state.dirty.bannerFile) {
          const up = await window.AI_AUTH.uploadBanner(state.dirty.bannerFile);
          if (up.error) throw up.error;
          // updateProfile inside uploadBanner already persisted the URL.
        } else if (state.dirty.banner_url === null) {
          const { error } = await window.AI_AUTH.updateProfile({ banner_url: null });
          if (error) throw error;
        }

        // 2) Avatar upload (if a file was picked).
        if (state.dirty.avatarFile) {
          const up = await window.AI_AUTH.uploadAvatar(state.dirty.avatarFile);
          if (up.error) throw up.error;
        } else if (state.dirty.avatar_url === null) {
          const { error } = await window.AI_AUTH.updateProfile({ avatar_url: null });
          if (error) throw error;
        }

        // 3) Username + bio via a single patch.
        const fields = {};
        if (typeof state.dirty.username !== "undefined" &&
            state.dirty.username !== (state.profile && state.profile.username)) {
          if (state.dirty.username && !USERNAME_RE.test(state.dirty.username)) {
            throw new Error("Username has an invalid format.");
          }
          fields.username = state.dirty.username;
        }
        if (typeof state.dirty.bio !== "undefined" &&
            (state.dirty.bio || "") !== ((state.profile && state.profile.bio) || "")) {
          fields.bio = state.dirty.bio || null;
        }
        if (Object.keys(fields).length) {
          const { error } = await window.AI_AUTH.updateProfile(fields);
          if (error) throw error;
        }

        // Refresh state from the canonical DB row.
        await window.AI_AUTH.refetchProfile();
        state.profile = window.__profile || state.profile;
        state.dirty = {};
        state.avatarPreview = null;
        state.bannerPreview = null;

        msg.className = "auth-message auth-message--success";
        msg.textContent = "Profile saved.";
        msg.style.display = "block";

        // Re-render so removed-avatar UI reflects state, etc.
        render();
      } catch (e) {
        console.error("[community-profile] save failed", e);
        msg.className = "auth-message auth-message--error";
        msg.textContent = describe(e);
        msg.style.display = "block";
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save profile";
      }
    });
  }

  // ---------- Preview mode ----------
  function renderPreview() {
    // Merge the draft on top of the saved profile so the preview shows
    // what a save-right-now would look like, including any un-uploaded
    // image selections.
    const base = state.profile || {};
    const preview = {
      id: base.id,
      username: (state.dirty.username !== undefined ? state.dirty.username : base.username) || base.username,
      avatar_url: state.avatarPreview || base.avatar_url,
      banner_url: state.bannerPreview || base.banner_url,
      bio: (state.dirty.bio !== undefined ? state.dirty.bio : base.bio) || base.bio,
      joined_at: (state.user && state.user.created_at) || null,
      post_count: 0,
      comment_count: 0,
    };

    const html = window.CF_PROFILE_VIEW.renderProfileHtml(
      preview,
      state.memberships,
      state.user ? state.user.id : null
    );

    shell.innerHTML = `
      <div class="cf-profile-preview-wrap">
        <div class="cf-profile-edit-head">
          <h1>Preview</h1>
          <div class="cf-profile-mode-toggle" role="tablist">
            <button type="button" class="cf-profile-mode-btn" data-mode="edit" role="tab">Edit</button>
            <button type="button" class="cf-profile-mode-btn is-active" data-mode="preview" role="tab">Preview</button>
          </div>
        </div>
        <p class="cf-profile-edit-lede">This is how other users see you. Post and comment counts reflect your activity.</p>
        ${html}
      </div>
    `;
    shell.querySelectorAll("[data-mode]").forEach((b) => {
      b.addEventListener("click", () => {
        state.mode = b.getAttribute("data-mode");
        render();
      });
    });
  }

  // ---------- Boot ----------
  let lastSignedIn = null;
  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    if (!user) { render(); return; }

    // Fresh fetch of own profile so the editor starts from canonical data.
    if (window.AI_AUTH && typeof window.AI_AUTH.refetchProfile === "function") {
      await window.AI_AUTH.refetchProfile();
    }
    state.profile = window.__profile || null;

    // Memberships for the Preview.
    const { data } = await COMMUNITY_API.listMyCommunities();
    state.memberships = data || [];

    render();
  }

  function onReady() {
    if (window.__authReady) window.__authReady.then(paint);
    else paint();
    window.addEventListener("auth-state", paint);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }
})();

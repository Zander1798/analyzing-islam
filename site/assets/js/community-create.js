// community-create.js — Create-community form. Renders into #cf-create-shell.
// Fields: name, slug (auto-generated from name, editable), description,
// optional icon + banner uploads, public-or-private radio. Submits via
// COMMUNITY_API.createCommunity and redirects to community-view.html?c=<slug>.
(function () {
  "use strict";

  const shell = document.getElementById("cf-create-shell");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  function slugify(name) {
    return String(name || "")
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 42);
  }

  function renderSignedOut() {
    shell.innerHTML = `
      <div class="cf-form" style="text-align:center;">
        <h1>Create a community</h1>
        <p>You need an account to create a community.</p>
        <div style="display:flex; gap:10px; justify-content:center; margin-top:16px;">
          <a class="cf-btn cf-btn-primary" href="login.html?return=community-create.html">Sign in</a>
          <a class="cf-btn" href="signup.html">Create account</a>
        </div>
      </div>
    `;
  }

  function renderForm() {
    shell.innerHTML = `
      <form class="cf-form" id="cf-create-form" autocomplete="off" novalidate>
        <h1>Create a community</h1>
        <p>Build a page around a topic. Members can post discussions and builds.</p>

        <div id="cf-form-error" class="cf-error" style="display:none;"></div>

        <label for="cf-name">Community name</label>
        <input type="text" id="cf-name" name="name" maxlength="80" required placeholder="e.g. Warfare & Jihad">
        <div class="cf-hint">2–80 characters. Shown at the top of the page.</div>

        <label for="cf-slug">URL slug</label>
        <input type="text" id="cf-slug" name="slug" maxlength="42" required placeholder="warfare-jihad" pattern="^[a-z0-9][a-z0-9-]{1,40}$">
        <div class="cf-hint">Appears in the link: <code>community-view.html?c=<span id="cf-slug-preview">your-slug</span></code>. Lowercase letters, numbers, hyphens only.</div>

        <label for="cf-desc">Description</label>
        <textarea id="cf-desc" name="description" maxlength="500" rows="3" placeholder="What's this community about?"></textarea>

        <div class="cf-upload-row">
          <div class="cf-upload-preview" id="cf-icon-preview">icon</div>
          <div style="flex:1;">
            <label>Icon (optional, square, ≤ 5MB)</label>
            <input type="file" id="cf-icon" accept="image/*">
          </div>
        </div>

        <div class="cf-upload-row">
          <div class="cf-upload-preview cf-upload-banner" id="cf-banner-preview">banner</div>
          <div style="flex:1;">
            <label>Banner (optional, wide, ≤ 5MB)</label>
            <input type="file" id="cf-banner" accept="image/*">
          </div>
        </div>

        <label>Privacy</label>
        <div class="cf-radio-group" id="cf-privacy">
          <label class="cf-radio-option is-selected">
            <input type="radio" name="privacy" value="public" checked>
            <div>
              <strong>Public</strong>
              <div class="cf-radio-desc">Anyone can see, join, and post. Best default for most communities.</div>
            </div>
          </label>
          <label class="cf-radio-option">
            <input type="radio" name="privacy" value="private">
            <div>
              <strong>Private</strong>
              <div class="cf-radio-desc">Only approved members can see posts. Other users see a request-to-join button and the admin must approve each request.</div>
            </div>
          </label>
        </div>

        <div class="cf-form-actions">
          <a class="cf-btn" href="community.html">Cancel</a>
          <button type="submit" class="cf-btn cf-btn-primary" id="cf-create-btn">Create community</button>
        </div>
      </form>
    `;

    wireForm();
  }

  function wireForm() {
    const $name = document.getElementById("cf-name");
    const $slug = document.getElementById("cf-slug");
    const $slugPreview = document.getElementById("cf-slug-preview");
    const $desc = document.getElementById("cf-desc");
    const $icon = document.getElementById("cf-icon");
    const $banner = document.getElementById("cf-banner");
    const $iconPreview = document.getElementById("cf-icon-preview");
    const $bannerPreview = document.getElementById("cf-banner-preview");
    const $privacyGroup = document.getElementById("cf-privacy");
    const $form = document.getElementById("cf-create-form");
    const $error = document.getElementById("cf-form-error");
    const $btn = document.getElementById("cf-create-btn");

    let slugManual = false;

    $name.addEventListener("input", () => {
      if (!slugManual) {
        const s = slugify($name.value);
        $slug.value = s;
        $slugPreview.textContent = s || "your-slug";
      }
    });
    $slug.addEventListener("input", () => {
      slugManual = true;
      const s = slugify($slug.value);
      if (s !== $slug.value) $slug.value = s;
      $slugPreview.textContent = s || "your-slug";
    });

    function bindImagePreview(input, preview, isBanner) {
      input.addEventListener("change", () => {
        const f = input.files && input.files[0];
        if (!f) { preview.textContent = isBanner ? "banner" : "icon"; preview.innerHTML = isBanner ? "banner" : "icon"; return; }
        if (!f.type.startsWith("image/")) { alert("Please pick an image file."); input.value = ""; return; }
        if (f.size > 5 * 1024 * 1024) { alert("Image must be 5MB or smaller."); input.value = ""; return; }
        const url = URL.createObjectURL(f);
        preview.innerHTML = `<img src="${url}" alt="">`;
      });
    }
    bindImagePreview($icon, $iconPreview, false);
    bindImagePreview($banner, $bannerPreview, true);

    $privacyGroup.querySelectorAll(".cf-radio-option input").forEach((r) => {
      r.addEventListener("change", () => {
        $privacyGroup.querySelectorAll(".cf-radio-option").forEach((o) => o.classList.remove("is-selected"));
        r.closest(".cf-radio-option").classList.add("is-selected");
      });
    });

    $form.addEventListener("submit", async (e) => {
      e.preventDefault();
      $error.style.display = "none";
      $error.textContent = "";

      const name = $name.value.trim();
      const slug = slugify($slug.value);
      const description = $desc.value.trim();
      const isPrivate = $form.querySelector('input[name="privacy"]:checked').value === "private";

      if (name.length < 2) return showError("Name must be at least 2 characters.");
      if (!/^[a-z0-9][a-z0-9-]{1,40}$/.test(slug)) return showError("Slug must be 2–41 characters, lowercase letters / digits / hyphens, and must start with a letter or digit.");

      $btn.disabled = true;
      $btn.textContent = "Creating…";

      try {
        // Upload optional images first (path prefix must be the user's id for RLS).
        let iconUrl = null, bannerUrl = null;
        const iconFile = $icon.files && $icon.files[0];
        const bannerFile = $banner.files && $banner.files[0];
        if (iconFile) {
          const up = await COMMUNITY_API.uploadImage("community-icons", iconFile);
          if (up.error) throw up.error;
          iconUrl = up.url;
        }
        if (bannerFile) {
          const up = await COMMUNITY_API.uploadImage("community-banners", bannerFile);
          if (up.error) throw up.error;
          bannerUrl = up.url;
        }

        const { data, error } = await COMMUNITY_API.createCommunity({
          slug, name, description, isPrivate, iconUrl, bannerUrl,
        });
        if (error) {
          // Friendly messages for the common errors.
          const msg = (error.message || "").toLowerCase();
          if (msg.includes("duplicate") || msg.includes("unique")) {
            throw new Error("That slug is already taken. Pick a different one.");
          }
          throw error;
        }

        // Belt-and-suspenders: the DB trigger should have already enrolled
        // us as the owner, but defensively upsert in case it didn't, so
        // comment + post rights work from the first page load.
        try {
          const u = window.AI_AUTH && window.AI_AUTH.getUser();
          if (u && window.__supabase) {
            await window.__supabase
              .from("community_members")
              .upsert(
                { community_id: data.id, user_id: u.id, role: "owner" },
                { onConflict: "community_id,user_id" }
              );
          }
        } catch (_) {
          // Non-fatal: the DB trigger almost certainly ran. Worst case the
          // user sees "Join" on their own community and clicks it once.
        }

        location.href = "community-view.html?c=" + encodeURIComponent(data.slug);
      } catch (err) {
        showError(err.message || String(err));
      } finally {
        $btn.disabled = false;
        $btn.textContent = "Create community";
      }

      function showError(text) {
        $error.textContent = text;
        $error.style.display = "";
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    });
  }

  // Track the last signed-in state so we don't repaint (and wipe the
  // form) on every auth-state event. Supabase fires auth-state on token
  // refresh too, not just sign-in / sign-out.
  let lastSignedIn = null;

  function paint() {
    const user = window.AI_AUTH && window.AI_AUTH.getUser();
    const isIn = !!user;
    if (lastSignedIn === isIn) return; // no meaningful change, keep typed input
    lastSignedIn = isIn;
    if (!user) renderSignedOut();
    else renderForm();
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

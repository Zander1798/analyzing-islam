// community-new-post.js — compose form for a new community post.
// Fields: title, rich-text body (Quill), optional "attach build" picker
// that opens a modal listing the user's saved builds. The user can edit
// the build's title + body inline before attaching it, and we save those
// edits back to the builds table so the edited version is the canonical
// one (matches the original flow of the Build editor).
//
// Usage: community-new-post.html?c=<community-slug>
(function () {
  "use strict";

  const shell = document.getElementById("cf-new-shell");
  const params = new URLSearchParams(location.search);
  const slug = (params.get("c") || "").trim();

  const state = {
    user: null,
    community: null,
    membership: null,
    bodyQuill: null,
    buildQuill: null,         // only created if editing an attached build
    attachedBuild: null,      // { id, name, content_delta, content_html }
    busy: false,
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  // ------------------------------------------------------------------
  // Paint states
  // ------------------------------------------------------------------
  function renderSignedOut() {
    shell.innerHTML = `
      <div class="cf-form" style="text-align:center;">
        <h1>Sign in to post</h1>
        <p>You need an account to post in a community.</p>
        <div style="display:flex; gap:10px; justify-content:center; margin-top:16px;">
          <a class="cf-btn cf-btn-primary" href="login.html?return=${encodeURIComponent(location.pathname + location.search)}">Sign in</a>
          <a class="cf-btn" href="signup.html">Create account</a>
        </div>
      </div>`;
  }

  function renderNotMember(c) {
    shell.innerHTML = `
      <div class="cf-form" style="text-align:center;">
        <h1>Join ${esc(c.name)} to post</h1>
        <p>You need to be a member of this community before you can post.</p>
        <div style="margin-top:16px;">
          <a class="cf-btn cf-btn-primary" href="community-view.html?c=${encodeURIComponent(c.slug)}">Go to community</a>
        </div>
      </div>`;
  }

  function renderNotFound() {
    shell.innerHTML = `
      <div class="cf-form" style="text-align:center;">
        <h1>Community not found</h1>
        <p>No community with slug "<code>${esc(slug)}</code>".</p>
        <a class="cf-btn" href="community.html">Back to community home</a>
      </div>`;
  }

  function renderForm() {
    const c = state.community;
    shell.innerHTML = `
      <form class="cf-form" id="cf-new-post-form" autocomplete="off" novalidate>
        <h1>Create a post</h1>
        <p>Posting in <a href="community-view.html?c=${encodeURIComponent(c.slug)}"><strong>${esc(c.name)}</strong></a>. Posts must not contain grotesque, violent, or sexual content — anything that violates this can be removed by the community admin.</p>

        <div id="cf-new-error" class="cf-error" style="display:none;"></div>

        <label for="cf-title">Title</label>
        <input type="text" id="cf-title" name="title" maxlength="300" required placeholder="A clear, specific title">

        <label>Body (optional)</label>
        <div class="cf-editor-wrap">
          <div id="cf-body-editor"></div>
        </div>

        <div id="cf-attached-preview"></div>

        <div class="cf-form-actions" style="justify-content:space-between;">
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button type="button" class="cf-btn" id="cf-attach-build">📎 Attach one of my builds</button>
            <button type="button" class="cf-btn" id="cf-detach-build" style="display:none;">✕ Remove attachment</button>
          </div>
          <div style="display:flex; gap:10px;">
            <a class="cf-btn" href="community-view.html?c=${encodeURIComponent(c.slug)}">Cancel</a>
            <button type="submit" class="cf-btn cf-btn-primary" id="cf-post-btn">Post</button>
          </div>
        </div>
      </form>

      <!-- Build picker modal -->
      <div class="cf-modal-backdrop" id="cf-build-modal">
        <div class="cf-modal" role="dialog" aria-modal="true">
          <div class="cf-modal-header">
            <h3>Attach a build</h3>
            <button class="cf-modal-close" data-close>✕</button>
          </div>
          <div class="cf-modal-body" id="cf-build-modal-body">
            Loading…
          </div>
          <div class="cf-modal-footer">
            <button class="cf-btn" data-close>Cancel</button>
            <button class="cf-btn cf-btn-primary" id="cf-build-pick-btn" disabled>Open for editing</button>
          </div>
        </div>
      </div>

      <!-- Build editor modal (opens after picking) -->
      <div class="cf-modal-backdrop" id="cf-build-edit-modal">
        <div class="cf-modal" role="dialog" aria-modal="true" style="max-width: 820px;">
          <div class="cf-modal-header">
            <h3>Edit before attaching</h3>
            <button class="cf-modal-close" data-close>✕</button>
          </div>
          <div class="cf-modal-body">
            <p style="font-size:13px; color:var(--text-muted); margin-top:0;">
              Any edits here are saved back to your build. This edited version is what people will see on the post.
            </p>
            <label>Build title</label>
            <input type="text" id="cf-build-name" maxlength="200" style="width:100%; background:var(--bg-elevated); border:1px solid var(--border); color:var(--text); padding:10px 12px; border-radius:4px; font-size:14px; font-family:inherit; margin-bottom:14px;">
            <label>Body</label>
            <div class="cf-editor-wrap">
              <div id="cf-build-editor"></div>
            </div>
          </div>
          <div class="cf-modal-footer">
            <button class="cf-btn" data-close>Cancel</button>
            <button class="cf-btn cf-btn-primary" id="cf-build-save-btn">Save & attach</button>
          </div>
        </div>
      </div>
    `;

    initBodyEditor();
    wireAttachFlow();
    wireSubmit();
  }

  // ------------------------------------------------------------------
  // Editor helpers
  // ------------------------------------------------------------------
  function makeQuill(target) {
    return new Quill(target, {
      theme: "snow",
      placeholder: "Write your post…",
      modules: {
        toolbar: [
          [{ header: [1, 2, 3, false] }],
          ["bold", "italic", "underline", "strike"],
          [{ color: [] }, { background: [] }],
          [{ list: "ordered" }, { list: "bullet" }],
          ["blockquote", "link", "image"],
          ["clean"],
        ],
      },
    });
  }

  function initBodyEditor() {
    state.bodyQuill = makeQuill("#cf-body-editor");

    // Intercept the toolbar's "image" button so uploads go to Supabase Storage
    // instead of being base64-embedded.
    const toolbar = state.bodyQuill.getModule("toolbar");
    toolbar.addHandler("image", () => pickAndUploadImage(state.bodyQuill));
  }

  function pickAndUploadImage(quill) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = async () => {
      const f = input.files && input.files[0];
      if (!f) return;
      const placeholderRange = quill.getSelection(true);
      quill.insertText(placeholderRange.index, "Uploading image…", "italic", true);
      const up = await COMMUNITY_API.uploadImage("community-post-images", f);
      quill.deleteText(placeholderRange.index, "Uploading image…".length);
      if (up.error) {
        alert("Image upload failed: " + (up.error.message || up.error));
        return;
      }
      quill.insertEmbed(placeholderRange.index, "image", up.url, "user");
      quill.setSelection(placeholderRange.index + 1, 0);
    };
    input.click();
  }

  // ------------------------------------------------------------------
  // Attach-a-build flow
  // ------------------------------------------------------------------
  function wireAttachFlow() {
    const pickerModal = document.getElementById("cf-build-modal");
    const editModal = document.getElementById("cf-build-edit-modal");
    const body = document.getElementById("cf-build-modal-body");
    const pickBtn = document.getElementById("cf-build-pick-btn");

    // Generic: data-close closes the nearest modal.
    [pickerModal, editModal].forEach((m) => {
      m.querySelectorAll("[data-close]").forEach((el) =>
        el.addEventListener("click", () => m.classList.remove("open"))
      );
      m.addEventListener("click", (e) => {
        if (e.target === m) m.classList.remove("open");
      });
    });

    document.getElementById("cf-attach-build").addEventListener("click", async () => {
      pickerModal.classList.add("open");
      body.innerHTML = "Loading…";
      pickBtn.disabled = true;

      const { data, error } = await COMMUNITY_API.listMyBuilds();
      if (error) {
        body.innerHTML = `<div class="cf-error">${esc(error.message || error)}</div>`;
        return;
      }
      const list = data || [];
      if (!list.length) {
        body.innerHTML = `
          <p>You don't have any saved builds yet.</p>
          <p><a class="cf-btn cf-btn-primary" href="build.html" target="_blank">Open the Build editor</a> to create one, then come back.</p>`;
        return;
      }

      body.innerHTML = `
        <p style="font-size:13px; color:var(--text-muted); margin-top:0;">
          Pick a build to attach. You'll be able to edit it before posting.
        </p>
        <div class="cf-build-list" id="cf-build-list">
          ${list.map((b) => `
            <div class="cf-build-row" data-build-id="${b.id}">
              <strong>${esc(b.name || "Untitled build")}</strong>
              <div class="cf-build-meta">Updated ${new Date(b.updated_at).toLocaleString()}</div>
              <div class="cf-build-preview">${esc(stripHtml(b.content_html).slice(0, 160))}</div>
            </div>`).join("")}
        </div>`;

      let chosenId = null;
      body.querySelectorAll(".cf-build-row").forEach((row) => {
        row.addEventListener("click", () => {
          body.querySelectorAll(".cf-build-row").forEach((r) => r.classList.remove("is-selected"));
          row.classList.add("is-selected");
          chosenId = Number(row.getAttribute("data-build-id"));
          pickBtn.disabled = false;
        });
      });

      pickBtn.onclick = () => {
        if (!chosenId) return;
        const chosen = list.find((b) => b.id === chosenId);
        pickerModal.classList.remove("open");
        openBuildEditor(chosen);
      };
    });

    document.getElementById("cf-detach-build").addEventListener("click", () => {
      state.attachedBuild = null;
      renderAttachedPreview();
    });
  }

  function openBuildEditor(build) {
    const editModal = document.getElementById("cf-build-edit-modal");
    const nameInput = document.getElementById("cf-build-name");
    nameInput.value = build.name || "Untitled build";

    editModal.classList.add("open");

    // Create Quill fresh each time so old state doesn't leak.
    document.getElementById("cf-build-editor").innerHTML = "";
    state.buildQuill = makeQuill("#cf-build-editor");
    const toolbar = state.buildQuill.getModule("toolbar");
    toolbar.addHandler("image", () => pickAndUploadImage(state.buildQuill));
    state.buildQuill.setContents(build.content_delta || { ops: [] });

    const saveBtn = document.getElementById("cf-build-save-btn");
    saveBtn.onclick = async () => {
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving…";
      try {
        const contentDelta = state.buildQuill.getContents();
        const contentHtml = state.buildQuill.root.innerHTML;
        const name = nameInput.value.trim() || "Untitled build";
        const { data, error } = await COMMUNITY_API.saveBuild({
          id: build.id,
          name,
          contentDelta,
          contentHtml,
        });
        if (error) throw error;
        state.attachedBuild = data;
        renderAttachedPreview();
        editModal.classList.remove("open");
      } catch (e) {
        alert("Save failed: " + (e.message || e));
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save & attach";
      }
    };
  }

  function renderAttachedPreview() {
    const wrap = document.getElementById("cf-attached-preview");
    const detachBtn = document.getElementById("cf-detach-build");
    if (!state.attachedBuild) {
      wrap.innerHTML = "";
      detachBtn.style.display = "none";
      return;
    }
    const b = state.attachedBuild;
    wrap.innerHTML = `
      <div class="cf-attached-build">
        <div class="cf-attached-build-header">
          <h4>Attached build</h4>
          <strong>${esc(b.name || "Untitled build")}</strong>
        </div>
        <div class="cf-attached-build-body ql-snow">
          <div class="ql-editor" style="padding:0;">${b.content_html || ""}</div>
        </div>
      </div>`;
    detachBtn.style.display = "";
  }

  // ------------------------------------------------------------------
  // Submit
  // ------------------------------------------------------------------
  function wireSubmit() {
    const form = document.getElementById("cf-new-post-form");
    const titleEl = document.getElementById("cf-title");
    const btn = document.getElementById("cf-post-btn");
    const errEl = document.getElementById("cf-new-error");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (state.busy) return;
      errEl.style.display = "none";
      errEl.textContent = "";

      const title = titleEl.value.trim();
      if (!title) return showError("Title is required.");
      if (title.length > 300) return showError("Title is too long (max 300 chars).");

      state.busy = true;
      btn.disabled = true;
      btn.textContent = "Posting…";

      try {
        const bodyDelta = state.bodyQuill.getContents();
        const bodyHtml = state.bodyQuill.root.innerHTML;
        const buildId = state.attachedBuild ? state.attachedBuild.id : null;
        const buildSnapshot = state.attachedBuild
          ? {
              name: state.attachedBuild.name,
              content_delta: state.attachedBuild.content_delta,
              content_html: state.attachedBuild.content_html,
            }
          : null;
        const { data, error } = await COMMUNITY_API.createPost({
          communityId: state.community.id,
          title,
          bodyDelta,
          bodyHtml,
          buildId,
          buildSnapshot,
        });
        if (error) throw error;
        location.href = "community-post.html?p=" + data.id;
      } catch (e) {
        showError(e.message || String(e));
      } finally {
        state.busy = false;
        btn.disabled = false;
        btn.textContent = "Post";
      }

      function showError(t) {
        errEl.textContent = t;
        errEl.style.display = "";
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    });
  }

  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return tmp.textContent || "";
  }

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  async function paint() {
    state.user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    if (!state.user) { renderSignedOut(); return; }
    if (!slug) {
      shell.innerHTML = `<div class="cf-form"><p>No community specified. <a href="community.html">Back to community home</a>.</p></div>`;
      return;
    }
    const { data: community } = await COMMUNITY_API.getCommunity(slug);
    if (!community) { renderNotFound(); return; }
    state.community = community;
    const { data: membership } = await COMMUNITY_API.getMembership(community.id);
    state.membership = membership || null;
    if (!state.membership) { renderNotMember(community); return; }
    renderForm();
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

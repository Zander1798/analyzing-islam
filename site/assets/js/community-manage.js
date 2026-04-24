// community-manage.js — admin panel for a single community.
// Only visible to owners/admins of the community. Features:
//   1. Edit details (name, description, icon, banner, private toggle)
//   2. Pending join requests → approve/deny
//   3. Member list → remove
//   4. Open reports → dismiss or action (navigates to the post/comment to delete)
(function () {
  "use strict";

  const shell = document.getElementById("cf-manage-shell");
  const params = new URLSearchParams(location.search);
  const slug = (params.get("c") || "").trim();

  const state = {
    user: null,
    community: null,
    membership: null,
    requests: [],
    members: [],
    reports: [],
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }
  function ago(ts) {
    if (!ts) return "";
    const d = new Date(ts);
    const s = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
    if (s < 60) return s + "s ago";
    if (s < 3600) return Math.floor(s / 60) + "m ago";
    if (s < 86400) return Math.floor(s / 3600) + "h ago";
    if (s < 2592000) return Math.floor(s / 86400) + "d ago";
    return d.toLocaleDateString();
  }
  function shortId(id) {
    const s = String(id || "");
    return s.length > 10 ? s.slice(0, 6) + "…" + s.slice(-4) : s;
  }

  function renderGate(msg) {
    shell.innerHTML = `
      <div class="cf-empty">
        <h2>${esc(msg || "Not allowed")}</h2>
        <p>Only admins of this community can manage it.</p>
        <a class="cf-btn" href="community-view.html?c=${encodeURIComponent(slug)}">Back to community</a>
      </div>`;
  }

  function renderNotFound() {
    shell.innerHTML = `
      <div class="cf-empty">
        <h2>Community not found</h2>
        <p>No community with slug "<code>${esc(slug)}</code>".</p>
        <a class="cf-btn" href="community.html">Back to community home</a>
      </div>`;
  }

  function renderShell() {
    const c = state.community;
    const pendingCount = (state.requests || []).length;
    const reportCount = (state.reports || []).length;

    shell.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; gap:12px; flex-wrap:wrap;">
        <div>
          <h1 style="margin:0; font-family:var(--sans); font-size:24px; font-weight:600;">Manage ${esc(c.name)}</h1>
          <p style="color:var(--text-muted); font-size:13px; margin:4px 0 0;">
            <a href="community-view.html?c=${encodeURIComponent(c.slug)}">View community ↗</a>
            · ${c.is_private ? '<span class="cf-badge cf-badge-private">Private</span>' : '<span class="cf-badge">Public</span>'}
          </p>
        </div>
      </div>

      <section class="cf-manage-section">
        <h2>Pending join requests ${pendingCount ? `(${pendingCount})` : ""}</h2>
        ${renderRequests()}
      </section>

      <section class="cf-manage-section">
        <h2>Open reports ${reportCount ? `(${reportCount})` : ""}</h2>
        ${renderReports()}
      </section>

      <section class="cf-manage-section">
        <h2>Members (${state.members.length})</h2>
        ${renderMembers()}
      </section>

      <section class="cf-manage-section">
        <h2>Community details</h2>
        <form id="cf-edit-form">
          <label>Name</label>
          <input type="text" id="cf-edit-name" maxlength="80" value="${esc(c.name)}" style="width:100%; background:var(--bg-elevated); border:1px solid var(--border); color:var(--text); padding:10px 12px; border-radius:4px; font-family:inherit; font-size:14px; margin-bottom:14px;">

          <label>Description</label>
          <textarea id="cf-edit-desc" maxlength="500" rows="3" style="width:100%; background:var(--bg-elevated); border:1px solid var(--border); color:var(--text); padding:10px 12px; border-radius:4px; font-family:inherit; font-size:14px; margin-bottom:14px; line-height:1.5;">${esc(c.description || "")}</textarea>

          <div class="cf-upload-row">
            <div class="cf-upload-preview" id="cf-edit-icon-preview">
              ${c.icon_url ? `<img src="${esc(c.icon_url)}" alt="">` : "icon"}
            </div>
            <div style="flex:1;">
              <label>Replace icon</label>
              <input type="file" id="cf-edit-icon" accept="image/*">
            </div>
          </div>

          <div class="cf-upload-row">
            <div class="cf-upload-preview cf-upload-banner" id="cf-edit-banner-preview">
              ${c.banner_url ? `<img src="${esc(c.banner_url)}" alt="">` : "banner"}
            </div>
            <div style="flex:1;">
              <label>Replace banner</label>
              <input type="file" id="cf-edit-banner" accept="image/*">
            </div>
          </div>

          <label>Privacy</label>
          <div class="cf-radio-group" id="cf-edit-privacy">
            <label class="cf-radio-option ${!c.is_private ? "is-selected" : ""}">
              <input type="radio" name="privacy" value="public" ${!c.is_private ? "checked" : ""}>
              <div><strong>Public</strong><div class="cf-radio-desc">Anyone can view and join.</div></div>
            </label>
            <label class="cf-radio-option ${c.is_private ? "is-selected" : ""}">
              <input type="radio" name="privacy" value="private" ${c.is_private ? "checked" : ""}>
              <div><strong>Private</strong><div class="cf-radio-desc">Join requests must be approved.</div></div>
            </label>
          </div>

          <div class="cf-form-actions">
            <button type="submit" class="cf-btn cf-btn-primary" id="cf-edit-save">Save changes</button>
          </div>
        </form>
      </section>

      ${state.membership && state.membership.role === "owner" ? `
      <section class="cf-manage-section" style="border-color: var(--strong);">
        <h2 style="color: var(--strong);">Danger zone</h2>
        <p style="color: var(--text-muted); font-size: 13px; margin: 0 0 14px;">
          Deleting this community removes every post, comment, member and join request attached to it. This cannot be undone.
        </p>
        <p style="color: var(--text-muted); font-size: 13px; margin: 0 0 10px;">
          Type the slug <code>${esc(c.slug)}</code> below to confirm, then click Delete.
        </p>
        <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
          <input type="text" id="cf-delete-confirm" placeholder="${esc(c.slug)}" autocomplete="off"
                 style="flex:1 1 240px; max-width:320px; background:var(--bg-elevated); border:1px solid var(--border); color:var(--text); padding:10px 12px; border-radius:4px; font-family:inherit; font-size:14px;">
          <button type="button" class="cf-btn cf-btn-danger" id="cf-delete-btn" disabled>Delete community</button>
        </div>
      </section>` : ""}
    `;

    wireRequests();
    wireReports();
    wireMembers();
    wireEditForm();
    wireDeleteCommunity();
  }

  function renderRequests() {
    if (!state.requests.length) return `<div class="cf-manage-empty">No pending requests.</div>`;
    return state.requests.map((r) => `
      <div class="cf-manage-row" data-request-id="${r.id}">
        <div class="cf-manage-row-info">
          <strong>User ${esc(shortId(r.user_id))}</strong>
          <span>Requested ${ago(r.created_at)}${r.message ? ` · "${esc(r.message)}"` : ""}</span>
        </div>
        <div class="cf-manage-actions">
          <button class="cf-btn cf-btn-primary" data-action="approve">Approve</button>
          <button class="cf-btn cf-btn-danger" data-action="deny">Deny</button>
        </div>
      </div>`).join("");
  }

  function renderReports() {
    if (!state.reports.length) return `<div class="cf-manage-empty">No open reports.</div>`;
    return state.reports.map((r) => {
      const target = r.post_id
        ? `<a href="community-post.html?p=${r.post_id}">Post #${r.post_id}</a>`
        : `<a href="community-post.html?p=${r.post_id || ""}">Comment #${r.comment_id}</a>`;
      return `
        <div class="cf-manage-row" data-report-id="${r.id}" data-post-id="${r.post_id || ""}" data-comment-id="${r.comment_id || ""}">
          <div class="cf-manage-row-info">
            <strong>${esc(r.reason)}</strong>
            <span>${target} · reported ${ago(r.created_at)}${r.detail ? ` · "${esc(r.detail)}"` : ""}</span>
          </div>
          <div class="cf-manage-actions">
            ${r.post_id ? `<button class="cf-btn cf-btn-danger" data-action="delete-post">Delete post</button>` : ""}
            ${r.comment_id ? `<button class="cf-btn cf-btn-danger" data-action="delete-comment">Delete comment</button>` : ""}
            <button class="cf-btn" data-action="dismiss">Dismiss</button>
          </div>
        </div>`;
    }).join("");
  }

  function renderMembers() {
    if (!state.members.length) return `<div class="cf-manage-empty">No members yet.</div>`;
    return state.members.map((m) => {
      const roleBadge = m.role === "owner" ? `<span class="cf-role-badge cf-role-owner">owner</span>` :
                        m.role === "admin" ? `<span class="cf-role-badge cf-role-admin">admin</span>` : "";
      const isSelf = state.user && state.user.id === m.user_id;
      const canRemove = m.role !== "owner" && !isSelf;
      return `
        <div class="cf-manage-row" data-user-id="${m.user_id}">
          <div class="cf-manage-row-info">
            <strong>User ${esc(shortId(m.user_id))}${isSelf ? " (you)" : ""} ${roleBadge}</strong>
            <span>Joined ${ago(m.joined_at)}</span>
          </div>
          <div class="cf-manage-actions">
            ${canRemove ? `<button class="cf-btn cf-btn-danger" data-action="remove">Remove</button>` : ""}
          </div>
        </div>`;
    }).join("");
  }

  // ------------------------------------------------------------------
  // Wiring
  // ------------------------------------------------------------------
  function wireRequests() {
    shell.querySelectorAll("[data-request-id]").forEach((row) => {
      const id = Number(row.getAttribute("data-request-id"));
      row.querySelector('[data-action="approve"]').addEventListener("click", async () => {
        const { error } = await COMMUNITY_API.approveRequest(id);
        if (error) { alert("Approve failed: " + (error.message || error)); return; }
        await reload();
      });
      row.querySelector('[data-action="deny"]').addEventListener("click", async () => {
        const { error } = await COMMUNITY_API.denyRequest(id);
        if (error) { alert("Deny failed: " + (error.message || error)); return; }
        await reload();
      });
    });
  }

  function wireReports() {
    shell.querySelectorAll("[data-report-id]").forEach((row) => {
      const id = Number(row.getAttribute("data-report-id"));
      const postId = row.getAttribute("data-post-id");
      const commentId = row.getAttribute("data-comment-id");

      const dismiss = row.querySelector('[data-action="dismiss"]');
      if (dismiss) dismiss.addEventListener("click", async () => {
        const { error } = await COMMUNITY_API.resolveReport(id, "dismissed");
        if (error) { alert("Dismiss failed: " + (error.message || error)); return; }
        await reload();
      });
      const delPost = row.querySelector('[data-action="delete-post"]');
      if (delPost) delPost.addEventListener("click", async () => {
        if (!confirm("Delete the reported post? This can't be undone.")) return;
        const { error } = await COMMUNITY_API.softDeletePost(Number(postId));
        if (error) { alert("Delete failed: " + (error.message || error)); return; }
        await COMMUNITY_API.resolveReport(id, "actioned");
        await reload();
      });
      const delCmt = row.querySelector('[data-action="delete-comment"]');
      if (delCmt) delCmt.addEventListener("click", async () => {
        if (!confirm("Delete the reported comment?")) return;
        const { error } = await COMMUNITY_API.softDeleteComment(Number(commentId));
        if (error) { alert("Delete failed: " + (error.message || error)); return; }
        await COMMUNITY_API.resolveReport(id, "actioned");
        await reload();
      });
    });
  }

  function wireMembers() {
    shell.querySelectorAll("[data-user-id]").forEach((row) => {
      const uid = row.getAttribute("data-user-id");
      const remove = row.querySelector('[data-action="remove"]');
      if (remove) remove.addEventListener("click", async () => {
        if (!confirm("Remove this member?")) return;
        const { error } = await COMMUNITY_API.removeMember(state.community.id, uid);
        if (error) { alert("Remove failed: " + (error.message || error)); return; }
        await reload();
      });
    });
  }

  function wireEditForm() {
    const form = document.getElementById("cf-edit-form");
    if (!form) return;

    const iconInput = document.getElementById("cf-edit-icon");
    const iconPreview = document.getElementById("cf-edit-icon-preview");
    const bannerInput = document.getElementById("cf-edit-banner");
    const bannerPreview = document.getElementById("cf-edit-banner-preview");

    function bindPreview(input, preview, fallback) {
      input.addEventListener("change", () => {
        const f = input.files && input.files[0];
        if (!f) return;
        if (!f.type.startsWith("image/")) { alert("Please pick an image."); input.value = ""; return; }
        if (f.size > 5 * 1024 * 1024) { alert("Image must be 5MB or smaller."); input.value = ""; return; }
        preview.innerHTML = `<img src="${URL.createObjectURL(f)}" alt="">`;
      });
    }
    bindPreview(iconInput, iconPreview);
    bindPreview(bannerInput, bannerPreview);

    const privacyGroup = document.getElementById("cf-edit-privacy");
    privacyGroup.querySelectorAll(".cf-radio-option input").forEach((r) => {
      r.addEventListener("change", () => {
        privacyGroup.querySelectorAll(".cf-radio-option").forEach((o) => o.classList.remove("is-selected"));
        r.closest(".cf-radio-option").classList.add("is-selected");
      });
    });

    const saveBtn = document.getElementById("cf-edit-save");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving…";
      try {
        const patch = {
          name: document.getElementById("cf-edit-name").value.trim(),
          description: document.getElementById("cf-edit-desc").value.trim(),
          is_private: form.querySelector('input[name="privacy"]:checked').value === "private",
        };
        if (iconInput.files && iconInput.files[0]) {
          const up = await COMMUNITY_API.uploadImage("community-icons", iconInput.files[0]);
          if (up.error) throw up.error;
          patch.icon_url = up.url;
        }
        if (bannerInput.files && bannerInput.files[0]) {
          const up = await COMMUNITY_API.uploadImage("community-banners", bannerInput.files[0]);
          if (up.error) throw up.error;
          patch.banner_url = up.url;
        }
        const { error } = await COMMUNITY_API.updateCommunity(state.community.id, patch);
        if (error) throw error;
        await reload();
        saveBtn.textContent = "Saved ✓";
        setTimeout(() => { saveBtn.textContent = "Save changes"; }, 1500);
      } catch (err) {
        alert("Save failed: " + (err.message || err));
        saveBtn.textContent = "Save changes";
      } finally {
        saveBtn.disabled = false;
      }
    });
  }

  function wireDeleteCommunity() {
    const input = document.getElementById("cf-delete-confirm");
    const btn = document.getElementById("cf-delete-btn");
    if (!input || !btn) return;

    const expected = state.community.slug;
    input.addEventListener("input", () => {
      btn.disabled = input.value.trim() !== expected;
    });

    btn.addEventListener("click", async () => {
      if (input.value.trim() !== expected) return;
      if (!confirm(`Really delete "${state.community.name}"? Every post, comment, and member will be removed. This is permanent.`)) return;
      btn.disabled = true;
      btn.textContent = "Deleting…";
      const { error } = await COMMUNITY_API.deleteCommunity(state.community.id);
      if (error) {
        alert("Delete failed: " + (error.message || error));
        btn.disabled = false;
        btn.textContent = "Delete community";
        return;
      }
      location.href = "community.html";
    });
  }

  // ------------------------------------------------------------------
  // Loads
  // ------------------------------------------------------------------
  async function loadAll() {
    const { data: community } = await COMMUNITY_API.getCommunity(slug);
    if (!community) { state.community = null; return; }
    state.community = community;

    const { data: membership } = await COMMUNITY_API.getMembership(community.id);
    state.membership = membership || null;

    if (!state.membership || !(state.membership.role === "owner" || state.membership.role === "admin")) {
      return;
    }

    const [reqRes, memRes, repRes] = await Promise.all([
      COMMUNITY_API.listPendingRequests(community.id),
      COMMUNITY_API.listMembers(community.id),
      COMMUNITY_API.listOpenReports(community.id),
    ]);
    state.requests = reqRes.data || [];
    state.members = memRes.data || [];
    state.reports = repRes.data || [];
  }

  async function reload() {
    await loadAll();
    renderShell();
  }

  async function paint() {
    state.user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    if (!state.user) { renderGate("Sign in to manage a community"); return; }
    if (!slug) { renderNotFound(); return; }
    await loadAll();
    if (!state.community) { renderNotFound(); return; }
    if (!state.membership || !(state.membership.role === "owner" || state.membership.role === "admin")) {
      renderGate("Not an admin of this community");
      return;
    }
    renderShell();
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

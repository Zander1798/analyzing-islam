/* =============================================================
   Analyzing Islam — Public user profile page
   -------------------------------------------------------------
   URL: user-profile.html?u=<username>    (preferred, shareable)
        user-profile.html?id=<uuid>       (fallback)
   Renders the shared public-profile block (banner, avatar, bio,
   stats, communities) + adds per-community Join buttons for any
   community the viewer isn't already in.
   ============================================================= */
(function () {
  "use strict";

  const shell = document.getElementById("cf-user-shell");
  const params = new URLSearchParams(location.search);
  const queryUsername = params.get("u");
  const queryId = params.get("id");

  const state = {
    user: null,           // current viewer
    profile: null,        // public_profiles row of the user being viewed
    memberships: [],      // their communities
    myMemberships: {},    // { communityId: role } for the viewer
  };

  async function loadProfile() {
    if (!queryUsername && !queryId) {
      state.profile = null;
      return;
    }
    const { data } = await COMMUNITY_API.getPublicProfile({
      username: queryUsername || undefined,
      id: queryId || undefined,
    });
    state.profile = data || null;
  }

  async function loadMemberships() {
    state.memberships = [];
    if (!state.profile) return;
    const { data } = await COMMUNITY_API.listCommunitiesForUser(state.profile.id);
    state.memberships = data || [];
  }

  async function loadMyMemberships() {
    state.myMemberships = {};
    if (!state.user) return;
    const { data } = await COMMUNITY_API.listMyCommunities();
    (data || []).forEach((m) => {
      if (m.communities) state.myMemberships[m.communities.id] = m.role;
    });
  }

  function render() {
    if (!queryUsername && !queryId) {
      shell.innerHTML = '<div class="cf-empty"><h2>No user specified</h2><p>Open a profile by clicking a username.</p></div>';
      return;
    }
    const viewerId = state.user ? state.user.id : null;
    shell.innerHTML = window.CF_PROFILE_VIEW.renderProfileHtml(
      state.profile,
      state.memberships,
      viewerId
    );
    wireCommunityActions();
  }

  function wireCommunityActions() {
    shell.querySelectorAll(".cf-user-community-card").forEach((card) => {
      const id = Number(card.getAttribute("data-community-id"));
      const actions = card.querySelector('[data-role="community-actions"]');
      if (!actions) return;

      // Viewer is the profile owner → no Join button needed.
      if (state.profile && state.user && state.profile.id === state.user.id) return;

      const role = state.myMemberships[id];
      if (role) {
        actions.innerHTML = `<span class="cf-user-joined">✓ ${esc(role === "owner" ? "Owner" : role === "admin" ? "Admin" : "Joined")}</span>`;
        return;
      }

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cf-btn cf-btn-primary";
      btn.textContent = "Join";
      btn.addEventListener("click", async () => {
        if (!state.user) {
          location.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search);
          return;
        }
        btn.disabled = true;
        btn.textContent = "Joining…";
        const { error } = await COMMUNITY_API.joinCommunity(id);
        if (error) {
          alert("Join failed: " + (error.message || error));
          btn.disabled = false;
          btn.textContent = "Join";
          return;
        }
        state.myMemberships[id] = "member";
        actions.innerHTML = `<span class="cf-user-joined">✓ Joined</span>`;
      });
      actions.appendChild(btn);
    });
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  let lastSignedIn = null;
  async function paint() {
    const user = (window.AI_AUTH && window.AI_AUTH.getUser()) || null;
    const isIn = !!user;
    if (lastSignedIn !== null && lastSignedIn === isIn) return;
    lastSignedIn = isIn;
    state.user = user;
    await loadProfile();
    await Promise.all([loadMemberships(), loadMyMemberships()]);
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

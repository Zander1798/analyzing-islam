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
    friendship: null,     // row from friendships table (or null)
  };

  async function loadProfile() {
    if (!queryUsername && !queryId) {
      state.profile = null;
      return;
    }
    // First fetch is just to resolve username -> id so we can resync
    // the denormalised counters before rendering. Skipped for signed-out
    // visitors (recompute_profile_counts is authenticated-only).
    let initial = null;
    {
      const { data } = await COMMUNITY_API.getPublicProfile({
        username: queryUsername || undefined,
        id: queryId || undefined,
      });
      initial = data || null;
    }
    if (initial && state.user) {
      try { await COMMUNITY_API.recomputeProfileCounts(initial.id); } catch (_) {}
      const { data } = await COMMUNITY_API.getPublicProfile({ id: initial.id });
      state.profile = data || initial;
    } else {
      state.profile = initial;
    }
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

  async function loadFriendship() {
    state.friendship = null;
    if (!state.user || !state.profile || state.user.id === state.profile.id) return;
    const { data } = await COMMUNITY_API.getFriendship(state.profile.id);
    state.friendship = data || null;
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
    renderFriendAction();
  }

  // Render the Add-friend / Request-sent / Accept / Friends button(s)
  // into the slot exposed by the shared profile renderer. Button state
  // comes from state.friendship (null = no relationship yet).
  function renderFriendAction() {
    const slot = shell.querySelector('[data-role="user-actions"]');
    if (!slot) return;
    slot.innerHTML = "";

    if (!state.profile) return;
    // Own profile: no button (handled by the community profile editor).
    if (state.user && state.profile.id === state.user.id) return;

    // Signed-out visitor: prompt to sign in to friend anyone.
    if (!state.user) {
      const a = document.createElement("a");
      a.className = "cf-btn";
      a.href = "login.html?return=" + encodeURIComponent(location.pathname + location.search);
      a.textContent = "Sign in to add friend";
      slot.appendChild(a);
      return;
    }

    const fr = state.friendship;
    const viewerIsRequester = fr && fr.requester_id === state.user.id;

    if (!fr || fr.status === "declined") {
      const btn = addActionButton(slot, "+ Add friend", "cf-btn cf-btn-primary");
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Sending…";
        // If a previously-declined row exists, clear it first so the
        // unique pair-index doesn't block a fresh request.
        if (fr && fr.status === "declined") {
          await COMMUNITY_API.removeFriendship(fr.id);
        }
        const { data, error } = await COMMUNITY_API.sendFriendRequest(state.profile.id);
        if (error) {
          alert("Couldn't send friend request: " + (error.message || error));
          btn.disabled = false;
          btn.textContent = "+ Add friend";
          return;
        }
        state.friendship = data || null;
        renderFriendAction();
      });
      return;
    }

    if (fr.status === "pending" && viewerIsRequester) {
      const btn = addActionButton(slot, "Request sent · Cancel", "cf-btn");
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Cancelling…";
        const { error } = await COMMUNITY_API.removeFriendship(fr.id);
        if (error) {
          alert("Couldn't cancel: " + (error.message || error));
          btn.disabled = false;
          btn.textContent = "Request sent · Cancel";
          return;
        }
        state.friendship = null;
        renderFriendAction();
      });
      return;
    }

    if (fr.status === "pending" && !viewerIsRequester) {
      const accept = addActionButton(slot, "Accept friend request", "cf-btn cf-btn-primary");
      const decline = addActionButton(slot, "Decline", "cf-btn");
      accept.addEventListener("click", async () => {
        accept.disabled = true; decline.disabled = true;
        accept.textContent = "Accepting…";
        const { data, error } = await COMMUNITY_API.acceptFriendRequest(fr.id);
        if (error) {
          alert("Couldn't accept: " + (error.message || error));
          accept.disabled = false; decline.disabled = false;
          accept.textContent = "Accept friend request";
          return;
        }
        state.friendship = data || { ...fr, status: "accepted" };
        if (state.profile) {
          state.profile.friend_count = (state.profile.friend_count || 0) + 1;
        }
        render();
      });
      decline.addEventListener("click", async () => {
        accept.disabled = true; decline.disabled = true;
        decline.textContent = "Declining…";
        const { error } = await COMMUNITY_API.declineFriendRequest(fr.id);
        if (error) {
          alert("Couldn't decline: " + (error.message || error));
          accept.disabled = false; decline.disabled = false;
          decline.textContent = "Decline";
          return;
        }
        state.friendship = { ...fr, status: "declined" };
        renderFriendAction();
      });
      return;
    }

    if (fr.status === "accepted") {
      const btn = addActionButton(slot, "✓ Friends", "cf-btn cf-btn-joined");
      btn.title = "Click to unfriend";
      btn.addEventListener("click", async () => {
        if (!confirm("Remove " + (state.profile.username ? "@" + state.profile.username : "this user") + " from your friends?")) return;
        btn.disabled = true;
        btn.textContent = "Removing…";
        const { error } = await COMMUNITY_API.removeFriendship(fr.id);
        if (error) {
          alert("Couldn't unfriend: " + (error.message || error));
          btn.disabled = false;
          btn.textContent = "✓ Friends";
          return;
        }
        state.friendship = null;
        if (state.profile) {
          state.profile.friend_count = Math.max(0, (state.profile.friend_count || 0) - 1);
        }
        render();
      });
    }
  }

  function addActionButton(slot, label, cls) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.textContent = label;
    slot.appendChild(b);
    return b;
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
    await Promise.all([loadMemberships(), loadMyMemberships(), loadFriendship()]);
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

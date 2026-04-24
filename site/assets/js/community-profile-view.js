/* =============================================================
   Analyzing Islam — Shared public-profile renderer
   -------------------------------------------------------------
   Single source of truth for how a user's public profile
   renders. Used by user-profile.html (when someone else is
   viewing the profile) and by the Preview toggle in the
   community profile editor.
   ============================================================= */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  function fmtDate(ts) {
    if (!ts) return "unknown";
    try {
      return new Date(ts).toLocaleDateString(undefined, {
        year: "numeric", month: "short", day: "numeric",
      });
    } catch (_) { return "unknown"; }
  }

  function fmtInt(n) {
    const v = Number(n || 0);
    if (v < 1000) return String(v);
    if (v < 1e6) return (v / 1000).toFixed(v < 10000 ? 1 : 0) + "k";
    return (v / 1e6).toFixed(1) + "M";
  }

  // Render the public-profile HTML block. memberships is the raw list
  // of community_members rows with embedded community(*). viewerId is
  // the current user's UUID (or null) — used to show Join / View
  // actions on community cards.
  function renderProfileHtml(profile, memberships, viewerId) {
    if (!profile) {
      return (
        '<div class="cf-user-profile cf-user-profile--empty">' +
        '<h2>User not found</h2>' +
        '<p>This username doesn\'t match any profile.</p>' +
        '</div>'
      );
    }

    const banner = profile.banner_url
      ? `<img class="cf-user-banner-img" src="${esc(profile.banner_url)}" alt="">`
      : '<div class="cf-user-banner-placeholder" aria-hidden="true"></div>';

    const avatarLetter = (profile.username || "?")[0].toUpperCase();
    const avatar = profile.avatar_url
      ? `<img class="cf-user-avatar-img" src="${esc(profile.avatar_url)}" alt="">`
      : `<span class="cf-user-avatar-initial">${esc(avatarLetter)}</span>`;

    const bio = profile.bio
      ? `<p class="cf-user-bio">${esc(profile.bio)}</p>`
      : '<p class="cf-user-bio cf-user-bio--empty">No bio yet.</p>';

    const communitiesHtml = renderCommunityList(memberships || [], viewerId);

    return `
      <article class="cf-user-profile">
        <div class="cf-user-banner">
          ${banner}
        </div>
        <div class="cf-user-head">
          <div class="cf-user-avatar">${avatar}</div>
          <div class="cf-user-head-text">
            <h1 class="cf-user-name">@${esc(profile.username || "user")}</h1>
            <div class="cf-user-meta">Joined ${fmtDate(profile.joined_at)}</div>
          </div>
          <div class="cf-user-head-actions" data-role="user-actions"></div>
        </div>
        ${bio}
        <div class="cf-user-stats">
          <div class="cf-user-stat">
            <strong>${fmtInt(profile.post_count)}</strong>
            <span>${profile.post_count === 1 ? "Post" : "Posts"}</span>
          </div>
          <div class="cf-user-stat">
            <strong>${fmtInt(profile.comment_count)}</strong>
            <span>${profile.comment_count === 1 ? "Comment" : "Comments"}</span>
          </div>
          <div class="cf-user-stat" data-stat="friends">
            <strong>${fmtInt(profile.friend_count || 0)}</strong>
            <span>${(profile.friend_count || 0) === 1 ? "Friend" : "Friends"}</span>
          </div>
          <div class="cf-user-stat">
            <strong>${fmtInt((memberships || []).length)}</strong>
            <span>${(memberships || []).length === 1 ? "Community" : "Communities"}</span>
          </div>
        </div>
        <section class="cf-user-communities">
          <h3>Communities</h3>
          ${communitiesHtml}
        </section>
      </article>
    `;
  }

  function renderCommunityList(memberships, viewerId) {
    if (!memberships.length) {
      return '<p class="cf-user-empty">Not a member of any communities yet.</p>';
    }
    // Stable sort by community name.
    const rows = memberships
      .filter((m) => m.communities)
      .slice()
      .sort((a, b) => (a.communities.name || "").localeCompare(b.communities.name || ""));

    return (
      '<div class="cf-user-community-grid">' +
      rows.map((m) => {
        const c = m.communities;
        const iconBlock = c.icon_url
          ? `<img class="cf-user-community-icon" src="${esc(c.icon_url)}" alt="">`
          : `<span class="cf-user-community-icon cf-user-community-icon--placeholder">${esc((c.name || "?")[0].toUpperCase())}</span>`;
        const roleBadge = m.role === "owner"
          ? `<span class="cf-role-badge cf-role-owner">Owner</span>`
          : m.role === "admin"
            ? `<span class="cf-role-badge cf-role-admin">Admin</span>`
            : "";
        return `
          <div class="cf-user-community-card" data-community-id="${c.id}" data-slug="${esc(c.slug)}">
            <a class="cf-user-community-link" href="community-view.html?c=${encodeURIComponent(c.slug)}">
              ${iconBlock}
              <div class="cf-user-community-meta">
                <div class="cf-user-community-name">${esc(c.name)} ${roleBadge}</div>
                <div class="cf-user-community-members">${fmtInt(c.member_count)} members</div>
              </div>
            </a>
            <div class="cf-user-community-actions" data-role="community-actions">
              <!-- "Join" button gets wired up client-side based on viewer's own membership -->
            </div>
          </div>`;
      }).join("") +
      '</div>'
    );
  }

  window.CF_PROFILE_VIEW = { renderProfileHtml, renderCommunityList };
})();

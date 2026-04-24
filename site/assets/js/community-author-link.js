/* =============================================================
   Analyzing Islam — Community: author link helpers
   -------------------------------------------------------------
   Tiny shared helpers for rendering a post or comment author as
   a clickable @username + optional avatar chip. Used by
   community-home, community-view, community-post (and the
   public user-profile page for "also commented in").
   ============================================================= */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  // Plain "@username" link. Falls back to a greyed-out "@deleted" label
  // when the author row is missing or the username wasn't set.
  function authorLink(author) {
    if (!author || !author.username) {
      return '<span class="cf-author-link cf-author-link--missing">@user</span>';
    }
    const u = author.username;
    return (
      '<a class="cf-author-link" href="user-profile.html?u=' +
      encodeURIComponent(u) +
      '">@' + esc(u) + "</a>"
    );
  }

  // Avatar + @username for comment/post headers. Same fallback as
  // authorLink.
  function authorChip(author) {
    if (!author || !author.username) {
      return (
        '<span class="cf-author-chip cf-author-chip--missing">' +
          '<span class="cf-author-chip-avatar">?</span>' +
          '<span class="cf-author-chip-name">@user</span>' +
        '</span>'
      );
    }
    const u = author.username;
    const url = "user-profile.html?u=" + encodeURIComponent(u);
    const avatar = author.avatar_url
      ? '<img class="cf-author-chip-avatar" src="' + esc(author.avatar_url) + '" alt="">'
      : '<span class="cf-author-chip-avatar">' + esc(u[0].toUpperCase()) + '</span>';
    return (
      '<a class="cf-author-chip" href="' + url + '">' +
        avatar +
        '<span class="cf-author-chip-name">@' + esc(u) + '</span>' +
      '</a>'
    );
  }

  // Make available everywhere. Each page script reads from window.
  window.authorLink = authorLink;
  window.authorChip = authorChip;
})();

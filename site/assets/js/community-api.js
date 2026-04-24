// Community forum — thin wrapper over Supabase for every community operation.
//
// Load order (same as other pages):
//   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
//   <script src="{prefix}assets/js/config.js"></script>
//   <script src="{prefix}assets/js/auth.js" defer></script>
//   <script src="{prefix}assets/js/auth-ui.js" defer></script>
//   <script src="{prefix}assets/js/community-api.js" defer></script>
//
// After load, reachable as `window.COMMUNITY_API`. All methods return either
// Supabase's `{ data, error }` envelope or, for storage uploads, `{ url, path, error }`.
(function () {
  "use strict";

  function client() {
    if (!window.__supabase) throw new Error("Supabase client not ready");
    return window.__supabase;
  }

  function currentUser() {
    return window.AI_AUTH ? window.AI_AUTH.getUser() : null;
  }

  function requireUser() {
    const u = currentUser();
    if (!u) throw new Error("Must be signed in");
    return u;
  }

  // ------------------------------------------------------------------
  // Communities
  // ------------------------------------------------------------------
  async function listCommunities(opts = {}) {
    const { orderBy = "member_count", orderDir = "desc", limit = 50, search = "" } = opts;
    let q = client().from("communities").select("*");
    if (search && search.trim()) {
      const like = `%${search.trim()}%`;
      q = q.or(`name.ilike.${like},slug.ilike.${like},description.ilike.${like}`);
    }
    return await q.order(orderBy, { ascending: orderDir === "asc" }).limit(limit);
  }

  async function getCommunity(slug) {
    return await client()
      .from("communities")
      .select("*")
      .eq("slug", slug)
      .maybeSingle();
  }

  async function createCommunity({ slug, name, description = "", isPrivate = false, iconUrl = null, bannerUrl = null }) {
    const u = requireUser();
    return await client()
      .from("communities")
      .insert({
        slug,
        name,
        description,
        is_private: isPrivate,
        icon_url: iconUrl,
        banner_url: bannerUrl,
        owner_id: u.id,
      })
      .select()
      .single();
  }

  async function updateCommunity(communityId, patch) {
    return await client().from("communities").update(patch).eq("id", communityId).select().single();
  }

  async function deleteCommunity(communityId) {
    return await client().from("communities").delete().eq("id", communityId);
  }

  // ------------------------------------------------------------------
  // Membership
  // ------------------------------------------------------------------
  async function listMyCommunities() {
    const u = currentUser();
    if (!u) return { data: [], error: null };
    return await client()
      .from("community_members")
      .select("role, joined_at, communities(*)")
      .eq("user_id", u.id);
  }

  async function getMembership(communityId) {
    const u = currentUser();
    if (!u) return { data: null, error: null };
    return await client()
      .from("community_members")
      .select("role, joined_at")
      .eq("community_id", communityId)
      .eq("user_id", u.id)
      .maybeSingle();
  }

  // Public community: direct join. For a private community this will fail RLS —
  // call requestToJoin() instead.
  async function joinCommunity(communityId) {
    const u = requireUser();
    return await client()
      .from("community_members")
      .insert({ community_id: communityId, user_id: u.id, role: "member" });
  }

  async function leaveCommunity(communityId) {
    const u = requireUser();
    return await client()
      .from("community_members")
      .delete()
      .eq("community_id", communityId)
      .eq("user_id", u.id);
  }

  async function requestToJoin(communityId, message = "") {
    const u = requireUser();
    return await client()
      .from("community_join_requests")
      .insert({ community_id: communityId, user_id: u.id, message });
  }

  async function getMyJoinRequest(communityId) {
    const u = currentUser();
    if (!u) return { data: null, error: null };
    return await client()
      .from("community_join_requests")
      .select("*")
      .eq("community_id", communityId)
      .eq("user_id", u.id)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();
  }

  async function listPendingRequests(communityId) {
    return await client()
      .from("community_join_requests")
      .select("*")
      .eq("community_id", communityId)
      .eq("status", "pending")
      .order("created_at", { ascending: true });
  }

  async function approveRequest(requestId) {
    const u = requireUser();
    return await client()
      .from("community_join_requests")
      .update({ status: "approved", decided_by: u.id })
      .eq("id", requestId);
  }

  async function denyRequest(requestId) {
    const u = requireUser();
    return await client()
      .from("community_join_requests")
      .update({ status: "denied", decided_by: u.id })
      .eq("id", requestId);
  }

  async function listMembers(communityId) {
    return await client()
      .from("community_members")
      .select("user_id, role, joined_at")
      .eq("community_id", communityId)
      .order("joined_at", { ascending: true });
  }

  async function removeMember(communityId, userId) {
    return await client()
      .from("community_members")
      .delete()
      .eq("community_id", communityId)
      .eq("user_id", userId);
  }

  // ------------------------------------------------------------------
  // Posts
  // ------------------------------------------------------------------
  async function listPosts(communityId, opts = {}) {
    const { sort = "new", limit = 25, offset = 0 } = opts;
    const column = sort === "top" ? "score" : "created_at";
    return await client()
      .from("community_posts")
      .select("*, communities(slug, name, icon_url)")
      .eq("community_id", communityId)
      .eq("is_deleted", false)
      .order(column, { ascending: false })
      .range(offset, offset + limit - 1);
  }

  // Merged home feed: posts from every community the current user has joined.
  async function listFeed(opts = {}) {
    const u = requireUser();
    const { sort = "new", limit = 25, offset = 0 } = opts;
    const column = sort === "top" ? "score" : "created_at";

    const { data: memberships, error: mErr } = await client()
      .from("community_members")
      .select("community_id")
      .eq("user_id", u.id);
    if (mErr) return { data: null, error: mErr };
    const ids = (memberships || []).map((m) => m.community_id);
    if (!ids.length) return { data: [], error: null };

    return await client()
      .from("community_posts")
      .select("*, communities(slug, name, icon_url, is_private)")
      .in("community_id", ids)
      .eq("is_deleted", false)
      .order(column, { ascending: false })
      .range(offset, offset + limit - 1);
  }

  async function getPost(postId) {
    return await client()
      .from("community_posts")
      .select("*, communities(slug, name, icon_url, is_private)")
      .eq("id", postId)
      .single();
  }

  async function createPost({ communityId, title, bodyDelta, bodyHtml, buildId = null, buildSnapshot = null }) {
    const u = requireUser();
    return await client()
      .from("community_posts")
      .insert({
        community_id: communityId,
        author_id: u.id,
        title,
        body_delta: bodyDelta || { ops: [] },
        body_html: bodyHtml || "",
        build_id: buildId,
        build_snapshot: buildSnapshot,
      })
      .select()
      .single();
  }

  async function updatePost(postId, patch) {
    return await client().from("community_posts").update(patch).eq("id", postId).select().single();
  }

  async function softDeletePost(postId) {
    return await client().from("community_posts").update({ is_deleted: true }).eq("id", postId);
  }

  // ------------------------------------------------------------------
  // Votes — value: +1 upvote, -1 downvote, 0 to clear
  // ------------------------------------------------------------------
  async function votePost(postId, value) {
    const u = requireUser();
    if (value === 0) {
      return await client()
        .from("post_votes")
        .delete()
        .eq("post_id", postId)
        .eq("user_id", u.id);
    }
    return await client()
      .from("post_votes")
      .upsert({ post_id: postId, user_id: u.id, value }, { onConflict: "post_id,user_id" });
  }

  async function getMyPostVote(postId) {
    const u = currentUser();
    if (!u) return 0;
    const { data } = await client()
      .from("post_votes")
      .select("value")
      .eq("post_id", postId)
      .eq("user_id", u.id)
      .maybeSingle();
    return data ? data.value : 0;
  }

  async function getMyPostVotes(postIds) {
    const u = currentUser();
    if (!u || !postIds.length) return {};
    const { data } = await client()
      .from("post_votes")
      .select("post_id, value")
      .in("post_id", postIds)
      .eq("user_id", u.id);
    const out = {};
    (data || []).forEach((r) => (out[r.post_id] = r.value));
    return out;
  }

  async function voteComment(commentId, value) {
    const u = requireUser();
    if (value === 0) {
      return await client()
        .from("comment_votes")
        .delete()
        .eq("comment_id", commentId)
        .eq("user_id", u.id);
    }
    return await client()
      .from("comment_votes")
      .upsert({ comment_id: commentId, user_id: u.id, value }, { onConflict: "comment_id,user_id" });
  }

  async function getMyCommentVotes(commentIds) {
    const u = currentUser();
    if (!u || !commentIds.length) return {};
    const { data } = await client()
      .from("comment_votes")
      .select("comment_id, value")
      .in("comment_id", commentIds)
      .eq("user_id", u.id);
    const out = {};
    (data || []).forEach((r) => (out[r.comment_id] = r.value));
    return out;
  }

  // ------------------------------------------------------------------
  // Comments
  // ------------------------------------------------------------------
  async function listComments(postId) {
    return await client()
      .from("post_comments")
      .select("*")
      .eq("post_id", postId)
      .eq("is_deleted", false)
      .order("created_at", { ascending: true });
  }

  async function createComment({ postId, parentCommentId = null, body }) {
    const u = requireUser();
    return await client()
      .from("post_comments")
      .insert({
        post_id: postId,
        parent_comment_id: parentCommentId,
        author_id: u.id,
        body,
      })
      .select()
      .single();
  }

  async function softDeleteComment(commentId) {
    return await client().from("post_comments").update({ is_deleted: true }).eq("id", commentId);
  }

  // ------------------------------------------------------------------
  // Lenient search — trigram similarity RPC
  // ------------------------------------------------------------------
  async function search(q, limit = 20) {
    if (!q || !q.trim()) return { data: [], error: null };
    return await client().rpc("search_all", { q: q.trim(), lim: limit });
  }

  // ------------------------------------------------------------------
  // Reports
  // ------------------------------------------------------------------
  async function reportPost(postId, reason = "other", detail = "") {
    const u = requireUser();
    const { data: post, error } = await client()
      .from("community_posts")
      .select("community_id")
      .eq("id", postId)
      .single();
    if (error) return { error };
    return await client().from("community_reports").insert({
      community_id: post.community_id,
      reporter_id: u.id,
      post_id: postId,
      reason,
      detail,
    });
  }

  async function reportComment(commentId, reason = "other", detail = "") {
    const u = requireUser();
    const { data: comment, error: e1 } = await client()
      .from("post_comments")
      .select("post_id")
      .eq("id", commentId)
      .single();
    if (e1) return { error: e1 };
    const { data: post, error: e2 } = await client()
      .from("community_posts")
      .select("community_id")
      .eq("id", comment.post_id)
      .single();
    if (e2) return { error: e2 };
    return await client().from("community_reports").insert({
      community_id: post.community_id,
      reporter_id: u.id,
      comment_id: commentId,
      reason,
      detail,
    });
  }

  async function listOpenReports(communityId) {
    return await client()
      .from("community_reports")
      .select("*")
      .eq("community_id", communityId)
      .eq("status", "open")
      .order("created_at", { ascending: true });
  }

  async function resolveReport(reportId, status = "dismissed") {
    return await client()
      .from("community_reports")
      .update({ status })
      .eq("id", reportId);
  }

  // ------------------------------------------------------------------
  // Storage — upload images for icons / banners / inline post images.
  // Path layout: `<user_id>/<timestamp>-<rand>.<ext>`  (enforced by RLS).
  // ------------------------------------------------------------------
  async function uploadImage(bucket, file) {
    const u = requireUser();
    const okBuckets = ["community-icons", "community-banners", "community-post-images"];
    if (!okBuckets.includes(bucket)) throw new Error(`Bad bucket: ${bucket}`);
    const MAX_BYTES = 5 * 1024 * 1024;
    if (file.size > MAX_BYTES) return { error: new Error("Image must be 5MB or smaller") };
    if (!file.type.startsWith("image/")) return { error: new Error("File must be an image") };

    const ext = (file.name.split(".").pop() || "png").toLowerCase().replace(/[^a-z0-9]/g, "") || "png";
    const rand = Math.random().toString(36).slice(2, 8);
    const path = `${u.id}/${Date.now()}-${rand}.${ext}`;
    const { error } = await client().storage.from(bucket).upload(path, file, {
      contentType: file.type,
      upsert: false,
    });
    if (error) return { error };
    const {
      data: { publicUrl },
    } = client().storage.from(bucket).getPublicUrl(path);
    return { url: publicUrl, path };
  }

  // ------------------------------------------------------------------
  // Builds integration (reused in the "Post a build" flow)
  // ------------------------------------------------------------------
  async function listMyBuilds() {
    const u = requireUser();
    return await client()
      .from("builds")
      .select("id, name, updated_at, content_delta, content_html")
      .eq("user_id", u.id)
      .order("updated_at", { ascending: false });
  }

  async function saveBuild({ id = null, name, contentDelta, contentHtml }) {
    const u = requireUser();
    if (id) {
      return await client()
        .from("builds")
        .update({ name, content_delta: contentDelta, content_html: contentHtml })
        .eq("id", id)
        .eq("user_id", u.id)
        .select()
        .single();
    }
    return await client()
      .from("builds")
      .insert({
        user_id: u.id,
        name,
        content_delta: contentDelta,
        content_html: contentHtml,
      })
      .select()
      .single();
  }

  window.COMMUNITY_API = {
    listCommunities,
    getCommunity,
    createCommunity,
    updateCommunity,
    deleteCommunity,
    listMyCommunities,
    getMembership,
    joinCommunity,
    leaveCommunity,
    requestToJoin,
    getMyJoinRequest,
    listPendingRequests,
    approveRequest,
    denyRequest,
    listMembers,
    removeMember,
    listPosts,
    listFeed,
    getPost,
    createPost,
    updatePost,
    softDeletePost,
    votePost,
    getMyPostVote,
    getMyPostVotes,
    voteComment,
    getMyCommentVotes,
    listComments,
    createComment,
    softDeleteComment,
    search,
    reportPost,
    reportComment,
    listOpenReports,
    resolveReport,
    uploadImage,
    listMyBuilds,
    saveBuild,
  };
})();

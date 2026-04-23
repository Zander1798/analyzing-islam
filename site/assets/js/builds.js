// Builds API — thin wrapper over Supabase.
// Waits for auth.js to have initialised the supabase client + session.
//
// Exposes window.AI_BUILDS with:
//   list()                               — returns Promise<Array<BuildRow>>
//   get(id)                              — returns Promise<BuildRow | null>
//   create({name, content_delta, content_html})  — returns Promise<BuildRow | null>
//   update(id, {name?, content_delta?, content_html?}) — returns Promise<BuildRow | null>
//   remove(id)                           — returns Promise<boolean>
//   getActiveShare(buildId)              — returns existing share row for a build, or null
//   createShare(buildId, snapshot)       — snapshot = {name, content_delta, content_html}; returns share row
//   revokeShare(shareId)                 — returns boolean
//   getSharedPublic(shareId)             — anon read for the shared viewer
//
// Dispatches "builds-changed" on window when anything is modified.
(function () {
  "use strict";

  function sb() { return window.__supabase; }
  function uid() {
    const s = window.__session;
    return s && s.user ? s.user.id : null;
  }

  function randomToken() {
    if (window.crypto && window.crypto.randomUUID) {
      return window.crypto.randomUUID().replace(/-/g, "");
    }
    const bytes = new Uint8Array(16);
    (window.crypto || {}).getRandomValues(bytes);
    let s = "";
    for (let i = 0; i < bytes.length; i++) s += bytes[i].toString(16).padStart(2, "0");
    return s;
  }

  async function list() {
    if (!uid()) return [];
    const { data, error } = await sb()
      .from("builds")
      .select("id, name, content_html, created_at, updated_at")
      .eq("user_id", uid())
      .order("updated_at", { ascending: false });
    if (error) {
      console.error("[builds] list failed", error);
      // Re-throw so the UI can surface the real cause (missing table,
      // RLS misconfig, network failure, …) instead of silently
      // pretending the user has no builds.
      const wrapped = new Error(error.message || "List failed");
      wrapped.cause = error;
      wrapped.code = error.code;
      wrapped.hint = error.hint;
      throw wrapped;
    }
    return data || [];
  }

  async function get(id) {
    if (!uid()) return null;
    const { data, error } = await sb()
      .from("builds")
      .select("*")
      .eq("user_id", uid())
      .eq("id", id)
      .maybeSingle();
    if (error) {
      console.error("[builds] get failed", error);
      return null;
    }
    return data || null;
  }

  async function create(payload) {
    if (!uid()) return null;
    const row = {
      user_id: uid(),
      name: (payload && payload.name) || "Untitled build",
      content_delta: (payload && payload.content_delta) || { ops: [] },
      content_html: (payload && payload.content_html) || "",
    };
    const { data, error } = await sb()
      .from("builds")
      .insert(row)
      .select("*")
      .single();
    if (error) {
      console.error("[builds] create failed", error);
      return null;
    }
    window.dispatchEvent(new CustomEvent("builds-changed", { detail: { id: data.id, action: "created" } }));
    return data;
  }

  async function update(id, patch) {
    if (!uid()) return null;
    const { data, error } = await sb()
      .from("builds")
      .update(patch || {})
      .eq("user_id", uid())
      .eq("id", id)
      .select("*")
      .single();
    if (error) {
      console.error("[builds] update failed", error);
      return null;
    }
    window.dispatchEvent(new CustomEvent("builds-changed", { detail: { id, action: "updated" } }));
    return data;
  }

  async function remove(id) {
    if (!uid()) return false;
    const { error } = await sb()
      .from("builds")
      .delete()
      .eq("user_id", uid())
      .eq("id", id);
    if (error) {
      console.error("[builds] remove failed", error);
      return false;
    }
    window.dispatchEvent(new CustomEvent("builds-changed", { detail: { id, action: "removed" } }));
    return true;
  }

  // ---------- Shares ----------

  async function getActiveShare(buildId) {
    if (!uid()) return null;
    const { data, error } = await sb()
      .from("shared_builds")
      .select("id, build_id, created_at")
      .eq("user_id", uid())
      .eq("build_id", buildId)
      .maybeSingle();
    if (error) {
      console.error("[builds] getActiveShare failed", error);
      return null;
    }
    return data || null;
  }

  async function createShare(buildId, snapshot) {
    if (!uid()) return null;
    // One active share per build: revoke any prior share first.
    const existing = await getActiveShare(buildId);
    if (existing) await revokeShare(existing.id);

    const token = randomToken();
    const { data, error } = await sb()
      .from("shared_builds")
      .insert({
        id: token,
        user_id: uid(),
        build_id: buildId,
        name: (snapshot && snapshot.name) || null,
        content_delta: (snapshot && snapshot.content_delta) || null,
        content_html: (snapshot && snapshot.content_html) || null,
      })
      .select("id, build_id, created_at")
      .single();
    if (error) {
      console.error("[builds] createShare failed", error);
      return null;
    }
    window.dispatchEvent(new CustomEvent("builds-changed", { detail: { id: buildId, action: "shared" } }));
    return data;
  }

  async function revokeShare(shareId) {
    if (!uid()) return false;
    const { error } = await sb()
      .from("shared_builds")
      .delete()
      .eq("user_id", uid())
      .eq("id", shareId);
    if (error) {
      console.error("[builds] revokeShare failed", error);
      return false;
    }
    return true;
  }

  async function getSharedPublic(shareId) {
    const { data, error } = await sb()
      .from("shared_builds")
      .select("id, name, content_delta, content_html, created_at")
      .eq("id", shareId)
      .maybeSingle();
    if (error) {
      console.error("[builds] getSharedPublic failed", error);
      return null;
    }
    return data || null;
  }

  window.AI_BUILDS = {
    list,
    get,
    create,
    update,
    remove,
    getActiveShare,
    createShare,
    revokeShare,
    getSharedPublic,
  };
})();

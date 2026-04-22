// Bookmarks API — thin wrapper over Supabase.
// Waits for auth.js to have initialised the supabase client + session.
//
// Exposes window.AI_BOOKMARKS with:
//   loadSet()            — returns Promise<Set<string>> of entry_ids the
//                          current user has bookmarked. Null if not signed in.
//   toggle(entry)        — add or remove a bookmark for the given entry object.
//                          Returns "added" | "removed" | "error".
//   list(filters)        — return array of bookmark rows matching filters
//                          { source?, strength?, category?, search? }
//   getNote(entry_id)    — returns Promise<{content, updated_at} | null>
//   saveNote(entry_id, content) — upsert; returns Promise<{content, updated_at}>
//   deleteNote(entry_id) — delete; returns Promise<void>
//
// Dispatches "bookmarks-changed" on window when anything is modified.
(function () {
  "use strict";

  function sb() { return window.__supabase; }
  function uid() {
    const s = window.__session;
    return s && s.user ? s.user.id : null;
  }

  let cachedSet = null;
  let cachedUserId = null;

  function invalidateCache() {
    cachedSet = null;
    cachedUserId = null;
  }

  window.addEventListener("auth-state", invalidateCache);

  async function loadSet(force) {
    if (!uid()) return null;
    if (!force && cachedSet && cachedUserId === uid()) return cachedSet;

    const { data, error } = await sb()
      .from("bookmarks")
      .select("entry_id")
      .eq("user_id", uid());

    if (error) {
      console.error("[bookmarks] loadSet failed", error);
      return new Set();
    }

    cachedSet = new Set((data || []).map((r) => r.entry_id));
    cachedUserId = uid();
    return cachedSet;
  }

  async function toggle(entry) {
    if (!uid()) return "error";
    const set = await loadSet();
    if (!set) return "error";

    if (set.has(entry.entry_id)) {
      const { error } = await sb()
        .from("bookmarks")
        .delete()
        .eq("user_id", uid())
        .eq("entry_id", entry.entry_id);
      if (error) {
        console.error("[bookmarks] remove failed", error);
        return "error";
      }
      set.delete(entry.entry_id);
      window.dispatchEvent(new CustomEvent("bookmarks-changed", { detail: { entry_id: entry.entry_id, action: "removed" } }));
      return "removed";
    }

    const row = {
      user_id: uid(),
      entry_id: entry.entry_id,
      entry_title: entry.entry_title || null,
      entry_ref: entry.entry_ref || null,
      entry_url: entry.entry_url || null,
      source: entry.source || null,
      strength: entry.strength || null,
      categories: entry.categories || [],
    };
    const { error } = await sb().from("bookmarks").insert(row);
    if (error) {
      console.error("[bookmarks] add failed", error);
      return "error";
    }
    set.add(entry.entry_id);
    window.dispatchEvent(new CustomEvent("bookmarks-changed", { detail: { entry_id: entry.entry_id, action: "added" } }));
    return "added";
  }

  async function list(filters) {
    if (!uid()) return [];
    filters = filters || {};

    // Bookmarks and notes are independent tables joined only through
    // (user_id, entry_id) — no FK between them, so we fetch bookmarks
    // on their own and pull notes lazily per row via getNote().
    let q = sb()
      .from("bookmarks")
      .select("*")
      .eq("user_id", uid())
      .order("created_at", { ascending: false });

    if (filters.source) q = q.eq("source", filters.source);
    if (filters.strength) q = q.eq("strength", filters.strength);
    if (filters.category) q = q.contains("categories", [filters.category]);

    const { data, error } = await q;
    if (error) {
      console.error("[bookmarks] list failed", error);
      return [];
    }

    let rows = data || [];
    // Text filter in-browser (Supabase fulltext would be nicer but not
    // strictly needed for the scale we expect).
    if (filters.search) {
      const needle = String(filters.search).toLowerCase();
      rows = rows.filter(
        (r) =>
          (r.entry_title && r.entry_title.toLowerCase().includes(needle)) ||
          (r.entry_ref && r.entry_ref.toLowerCase().includes(needle))
      );
    }
    return rows;
  }

  async function getNote(entry_id) {
    if (!uid()) return null;
    const { data, error } = await sb()
      .from("notes")
      .select("content, updated_at")
      .eq("user_id", uid())
      .eq("entry_id", entry_id)
      .maybeSingle();
    if (error) {
      console.error("[bookmarks] getNote failed", error);
      return null;
    }
    return data || null;
  }

  async function saveNote(entry_id, content) {
    if (!uid()) return null;
    const { data, error } = await sb()
      .from("notes")
      .upsert(
        { user_id: uid(), entry_id, content },
        { onConflict: "user_id,entry_id" }
      )
      .select("content, updated_at")
      .single();
    if (error) {
      console.error("[bookmarks] saveNote failed", error);
      return null;
    }
    window.dispatchEvent(new CustomEvent("bookmarks-changed", { detail: { entry_id, action: "note-saved" } }));
    return data;
  }

  async function deleteNote(entry_id) {
    if (!uid()) return;
    const { error } = await sb()
      .from("notes")
      .delete()
      .eq("user_id", uid())
      .eq("entry_id", entry_id);
    if (error) console.error("[bookmarks] deleteNote failed", error);
    window.dispatchEvent(new CustomEvent("bookmarks-changed", { detail: { entry_id, action: "note-deleted" } }));
  }

  window.AI_BOOKMARKS = {
    loadSet,
    toggle,
    list,
    getNote,
    saveNote,
    deleteNote,
  };
})();

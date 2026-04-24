// Supabase auth shell: initialises the client, tracks session state, exposes
// a tiny API for the rest of the site to use.
//
// Expected load order on every page:
//   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
//   <script src="{prefix}assets/js/config.js"></script>
//   <script src="{prefix}assets/js/auth.js" defer></script>
//   <script src="{prefix}assets/js/auth-ui.js" defer></script>
//
// After init, the rest of the site can reach:
//   window.__supabase        — the Supabase client
//   window.__session         — current session (or null)
//   window.__authReady       — Promise that resolves once the first session
//                              check has completed (used by auth-ui to render
//                              the correct nav button before paint).
//   window.addEventListener("auth-state", (e) => ...)
//       — custom event fired whenever the session changes.
(function init() {
  "use strict";

  if (!window.supabase || !window.SUPABASE_CONFIG) {
    // Retry on next tick — config.js is loaded synchronously but the Supabase
    // CDN script might not have evaluated yet depending on browser caching.
    console.warn("[auth] supabase-js or config.js not loaded yet; retrying…");
    setTimeout(init, 50);
    return;
  }

  const { createClient } = window.supabase;
  const client = createClient(
    window.SUPABASE_CONFIG.url,
    window.SUPABASE_CONFIG.anonKey,
    {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true, // picks up magic-link / email-verification returns
        storage: window.localStorage,
        storageKey: "analyzing-islam-auth",
      },
    }
  );

  window.__supabase = client;
  window.__session = null;

  let resolveReady;
  window.__authReady = new Promise((r) => {
    resolveReady = r;
  });

  function setSession(session) {
    window.__session = session || null;
    window.dispatchEvent(
      new CustomEvent("auth-state", { detail: { session: window.__session } })
    );
  }

  // Initial session check.
  client.auth.getSession().then(({ data }) => {
    setSession(data && data.session);
    resolveReady();
  });

  // Listen for future changes (sign-in, sign-out, token refresh).
  client.auth.onAuthStateChange((_event, session) => {
    setSession(session);
  });

  // Profile cache: refetched on sign-in / profile update so callers (the
  // auth-ui nav widget, profile page, share rendering, etc.) don't hammer
  // the database. window.__profile is null when signed out.
  window.__profile = null;
  let profilePromise = null;

  async function refetchProfile() {
    const uid = window.__session && window.__session.user && window.__session.user.id;
    if (!uid) {
      window.__profile = null;
      window.dispatchEvent(new CustomEvent("profile-state", { detail: null }));
      return null;
    }
    const { data, error } = await client
      .from("profiles")
      .select("id,email,username,avatar_url,banner_url,bio,display_name,created_at")
      .eq("id", uid)
      .maybeSingle();
    if (error) {
      console.warn("[auth] profile fetch failed", error);
      window.__profile = null;
    } else {
      window.__profile = data || null;
    }
    window.dispatchEvent(
      new CustomEvent("profile-state", { detail: window.__profile })
    );
    return window.__profile;
  }

  // Refresh the profile cache whenever the session changes.
  window.addEventListener("auth-state", () => {
    profilePromise = refetchProfile();
  });
  // And do an initial fetch once the first session check has resolved.
  window.__authReady.then(() => {
    profilePromise = refetchProfile();
  });

  // USERNAME_RE is duplicated in the DB constraint (profiles_username_format).
  // Keep in sync: lowercase, 3-20 chars, letters/digits/underscore, not
  // starting with underscore.
  const USERNAME_RE = /^[a-z0-9][a-z0-9_]{2,19}$/;

  // Minimal helper API — just wrappers so the login/signup pages don't have
  // to reach into the Supabase client directly.
  window.AI_AUTH = {
    client,
    USERNAME_RE,

    signUp: async (email, password, username) => {
      const cleanUsername = (username || "").trim().toLowerCase() || null;
      const options = {
        emailRedirectTo: new URL("index.html", location.origin + location.pathname).toString(),
      };
      if (cleanUsername) {
        options.data = { username: cleanUsername };
      }
      const { data, error } = await client.auth.signUp({
        email,
        password,
        options,
      });
      return { data, error };
    },

    signIn: async (email, password) => {
      const { data, error } = await client.auth.signInWithPassword({
        email,
        password,
      });
      return { data, error };
    },

    signOut: async () => {
      const { error } = await client.auth.signOut();
      return { error };
    },

    resetPassword: async (email) => {
      const { data, error } = await client.auth.resetPasswordForEmail(email, {
        redirectTo: new URL("reset-password.html", location.origin + location.pathname).toString(),
      });
      return { data, error };
    },

    updatePassword: async (newPassword) => {
      const { data, error } = await client.auth.updateUser({ password: newPassword });
      return { data, error };
    },

    getUser: () => {
      return window.__session && window.__session.user ? window.__session.user : null;
    },

    // ---------- Profile ----------

    // Returns the cached profile (or fetches it if not yet loaded).
    getProfile: async () => {
      if (window.__profile) return window.__profile;
      if (!profilePromise) profilePromise = refetchProfile();
      return profilePromise;
    },

    refetchProfile,

    // Check whether a username is available. Returns { available, reason }.
    // reason ∈ {"format", "taken", "error", null}. We lowercase before
    // comparing. Logs the real PostgREST error when the lookup fails so
    // missing-column or missing-RLS-policy issues surface in the console.
    checkUsernameAvailable: async (username) => {
      const u = (username || "").trim().toLowerCase();
      if (!USERNAME_RE.test(u)) {
        return { available: false, reason: "format" };
      }
      const me = window.__session && window.__session.user && window.__session.user.id;
      const { data, error } = await client
        .from("profiles")
        .select("id")
        .ilike("username", u)
        .limit(1);
      if (error) {
        console.error("[auth] checkUsernameAvailable failed", error);
        return { available: false, reason: "error", error };
      }
      const hit = data && data[0];
      if (!hit) return { available: true, reason: null };
      if (me && hit.id === me) return { available: true, reason: null };
      return { available: false, reason: "taken" };
    },

    // Patch profile columns. Pass { username, avatar_url, display_name }.
    // Uses upsert so a missing profile row gets created, and maybeSingle +
    // a follow-up refetch so an RLS policy that blocks reading our own row
    // back immediately after the write doesn't crash the save.
    updateProfile: async (fields) => {
      const sess = window.__session;
      const uid = sess && sess.user && sess.user.id;
      if (!uid) return { error: { message: "not signed in" } };
      const patch = { id: uid };
      if (sess.user.email) patch.email = sess.user.email;
      if (typeof fields.username !== "undefined") {
        patch.username = fields.username
          ? String(fields.username).trim().toLowerCase()
          : null;
      }
      if (typeof fields.avatar_url !== "undefined") patch.avatar_url = fields.avatar_url;
      if (typeof fields.banner_url !== "undefined") patch.banner_url = fields.banner_url;
      if (typeof fields.bio !== "undefined") {
        const b = fields.bio == null ? null : String(fields.bio);
        patch.bio = b && b.length ? b : null;
      }
      if (typeof fields.display_name !== "undefined") patch.display_name = fields.display_name;

      const { data, error } = await client
        .from("profiles")
        .upsert(patch, { onConflict: "id" })
        .select()
        .maybeSingle();

      if (error) {
        console.error("[auth] updateProfile failed", error, patch);
        return { data: null, error };
      }

      // If RLS allowed the write but blocked reading it back, refetch
      // explicitly so the UI has the canonical row.
      const next = data || (await refetchProfile());
      window.__profile = next;
      window.dispatchEvent(new CustomEvent("profile-state", { detail: next }));
      return { data: next, error: null };
    },

    // Upload a banner image to Storage under avatars/<user_id>/banner-*.<ext>
    // and save the resulting public URL to profiles.banner_url.
    uploadBanner: async (file) => {
      const uid = window.__session && window.__session.user && window.__session.user.id;
      if (!uid) return { error: { message: "not signed in" } };
      if (!file) return { error: { message: "no file" } };
      if (!/^image\//i.test(file.type)) return { error: { message: "Not an image file." } };
      if (file.size > 5 * 1024 * 1024) return { error: { message: "Image too large (5 MB max)." } };

      let ext = (file.name.match(/\.([A-Za-z0-9]+)$/) || [])[1] || "jpg";
      ext = ext.toLowerCase();
      const path = uid + "/banner-" + Date.now() + "." + ext;

      const { error: upErr } = await client.storage
        .from("avatars")
        .upload(path, file, {
          cacheControl: "3600",
          upsert: true,
          contentType: file.type,
        });
      if (upErr) return { error: upErr };

      const { data: pub } = client.storage.from("avatars").getPublicUrl(path);
      const url = pub && pub.publicUrl;
      if (!url) return { error: { message: "Could not resolve banner URL." } };

      const { data, error } = await window.AI_AUTH.updateProfile({ banner_url: url });
      return { data, error, url };
    },

    // Upload an avatar image to Storage under avatars/<user_id>/avatar.<ext>
    // and save the resulting public URL to profiles.avatar_url.
    uploadAvatar: async (file) => {
      const uid = window.__session && window.__session.user && window.__session.user.id;
      if (!uid) return { error: { message: "not signed in" } };
      if (!file) return { error: { message: "no file" } };
      if (!/^image\//i.test(file.type)) {
        return { error: { message: "Not an image file." } };
      }
      if (file.size > 5 * 1024 * 1024) {
        return { error: { message: "Image too large (5 MB max)." } };
      }
      // File extension — fallback to jpg if browser didn't give one.
      let ext = (file.name.match(/\.([A-Za-z0-9]+)$/) || [])[1] || "jpg";
      ext = ext.toLowerCase();
      const path = uid + "/avatar-" + Date.now() + "." + ext;

      const { error: upErr } = await client.storage
        .from("avatars")
        .upload(path, file, {
          cacheControl: "3600",
          upsert: true,
          contentType: file.type,
        });
      if (upErr) return { error: upErr };

      const { data: pub } = client.storage.from("avatars").getPublicUrl(path);
      const url = pub && pub.publicUrl;
      if (!url) return { error: { message: "Could not resolve avatar URL." } };

      const { data, error } = await window.AI_AUTH.updateProfile({ avatar_url: url });
      return { data, error, url };
    },

    // Permanently delete the current account (removes auth.users row; ON
    // DELETE CASCADE wipes profile, bookmarks, notes, builds, shares).
    deleteAccount: async () => {
      const { error } = await client.rpc("delete_current_user");
      if (error) return { error };
      // Server side the row is gone; client should forget the session.
      try {
        await client.auth.signOut();
      } catch (_) {}
      return { error: null };
    },
  };
})();

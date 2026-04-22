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

  // Minimal helper API — just wrappers so the login/signup pages don't have
  // to reach into the Supabase client directly.
  window.AI_AUTH = {
    client,
    signUp: async (email, password) => {
      const { data, error } = await client.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: new URL("index.html", location.origin + location.pathname).toString(),
        },
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
  };
})();

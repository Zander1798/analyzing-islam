// Supabase public configuration — safe to ship in browser JS.
// The publishable (anon) key is gated by Row-Level Security at the database
// level; privileged operations require the service_role key which is NOT here
// and never will be (server-side only).
window.SUPABASE_CONFIG = {
  url: "https://cndmksrilytnpgstvmxb.supabase.co",
  anonKey: "sb_publishable_9rJKQFSBSA12YijYfGtD5g_7h4WD8wa",
};

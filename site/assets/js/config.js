// Supabase public configuration — safe to ship in browser JS.
// The anon key is gated by Row-Level Security at the database level; privileged
// operations require the service_role key which is NOT here (server-side only).
//
// SELF-HOSTED (VPS). Until Stage 12 this file deliberately diverged from the
// server's copy — the repo pointed at Supabase Cloud so GitHub Pages stayed
// usable as the rollback target, and the deploy rsync carried an
// --exclude for this path to stop a content deploy clobbering the server.
// That divergence is now closed: repo and server agree, and the exclude is
// gone. Change this file and it deploys like any other.
window.SUPABASE_CONFIG = {
  url: "https://api.analyzingislam.com",
  anonKey: "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJyb2xlIjogImFub24iLCAiaXNzIjogInN1cGFiYXNlIiwgImlhdCI6IDE3ODUxODIxMDQsICJleHAiOiAyMTAwNTQyMTA0fQ.O3qaKLoiiSAdM7EKCzlwPWpWLkN4ccNCjABUX6uhdsA",
};

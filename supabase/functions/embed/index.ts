// ============================================================
// Analyzing Islam — chatbot embedding endpoint (Phase 1, Task 2).
//
// Wraps the runtime's built-in `gte-small` model: 384 dimensions, English
// only, truncates at 512 tokens. There is deliberately no local Python path
// to this model — every embedding in the system comes through here, so the
// query vector and the stored document vectors can never drift apart.
//
// VERIFIED ON THE SELF-HOSTED RUNTIME (supabase/edge-runtime:v1.74.0, VPS
// 72.60.17.245, 2026-07-27). `Supabase.ai.Session` is not a Cloud-only API:
// it returned 384 real dimensions self-hosted, and an end-to-end store +
// retrieve ranked a semantically-matching document (cosine 0.176) above two
// unrelated ones (0.238, 0.239) for a query sharing none of its keywords.
// That was the open question blocking Phase 1 behind the migration.
//
// Auth: service_role only, enforced BELOW. The runtime's own verify_jwt only
// checks that the token is validly signed — it does not care which role it
// carries, so the anon key (which ships in the public site's config.js)
// reaches this endpoint with a 200 unless the role claim is checked here.
// Measured on the VPS before this guard existed. Embedding is real CPU on a
// 2-vCPU box; leaving it open to the anon key is a free DoS.
// ============================================================

const session = new Supabase.ai.Session("gte-small");

function roleOf(req: Request): string | null {
  // The runtime has already verified the signature; we only need the claim.
  const raw = req.headers.get("Authorization")?.replace(/^Bearer\s+/i, "");
  if (!raw) return null;
  try {
    const p = raw.split(".")[1];
    const pad = p.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(pad + "=".repeat((4 - (pad.length % 4)) % 4))).role ?? null;
  } catch {
    return null;
  }
}

Deno.serve(async (req: Request): Promise<Response> => {
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });

  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  if (roleOf(req) !== "service_role") return json({ error: "forbidden" }, 403);

  let input: unknown;
  try {
    ({ input } = await req.json());
  } catch {
    return json({ error: "body must be JSON" }, 400);
  }

  // Accept one string or a batch; always answer in the shape asked for.
  const batch = Array.isArray(input) ? input : [input];
  if (batch.length === 0) return json({ error: "input is empty" }, 400);
  if (batch.some((t) => typeof t !== "string" || t.trim() === "")) {
    return json({ error: "input must be a non-empty string or array of them" }, 400);
  }

  try {
    const out: number[][] = [];
    for (const text of batch as string[]) {
      const v = await session.run(text, { mean_pool: true, normalize: true });
      const arr = v as number[];
      // A wrong-width vector must fail here, not silently poison kb_docs —
      // pgvector would reject it anyway, but far from the cause.
      if (arr.length !== 384) {
        return json({ error: `expected 384 dims, model returned ${arr.length}` }, 500);
      }
      out.push(arr);
    }
    return Array.isArray(input)
      ? json({ embeddings: out })
      : json({ embedding: out[0] });
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});

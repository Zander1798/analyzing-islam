# Stage 12 — executor checklist

Written 2026-08-27 from the primary Windows checkout, which has **no SSH access
to the VPS** (`deploy@72.60.17.245` → `Permission denied (publickey)`; the `vps`
alias in `~/.ssh/config` is a different box, `72.61.197.178`). Everything below
needs the authorized Linux workstation, GitHub admin, or the Supabase dashboard.

Read `docs/migration/EXECUTION-PLAN.md` Stage 12 and the runbook's Stage 12
section first. This file does not replace them; it records what is already done
and what each remaining step actually requires.

---

## The rollback path is already gone — verified before starting

Stage 12's whole purpose is the deliberate abandonment of the rollback path.
As of 2026-08-27 that path is not intact, so the decision has largely been made
by circumstance rather than by anyone choosing it.

**Supabase Cloud does not resolve.** Four independent lookups:

```
cndmksrilytnpgstvmxb.supabase.co
  local resolver → NXDOMAIN
  8.8.8.8        → NXDOMAIN
  1.1.1.1        → NXDOMAIN
  DoH JSON       → {"Status":3}          (3 = NXDOMAIN)
supabase.co      → 76.76.21.21           (control — resolves normally)
```

A *paused* Supabase project normally still resolves. NXDOMAIN is what a
*deleted* project looks like. **Nothing in `EXECUTION-PLAN.md`, either
untracked handoff, or any commit since the cutover records pausing or deleting
it.** Whether the data is still restorable is unknown from outside.

**GitHub Pages TLS is broken for the apex.** `gh api repos/Zander1798/analyzing-islam/pages`:

```json
"https_certificate": { "state": "bad_authz",
  "description": "The ACME authorization is in a bad state. We need to start over." }
```

Expected — the apex A records moved to the VPS on 2026-07-28, so Let's Encrypt
can no longer validate for Pages. A DNS rollback today lands on a host that
cannot serve valid HTTPS until a fresh certificate issues.

> **Do this before anything else below:** open the Supabase dashboard and
> establish whether that project is *paused* or *deleted*, and confirm the
> Stage 1 backup still exists. If the project was deleted, that backup is the
> only remaining copy of the pre-migration state. Keep it permanently.

---

## Gate status at the time of writing

| Gate | State | Evidence |
|---|---|---|
| Backups running + one test-restored | ✅ | cleared 2026-07-27, `scripts/vps/test-restore.sh` — 55 tables, 1245 rows, 546 schema objects identical |
| Two weeks clean on the VPS | ⚠️ **verify on the box** | 30 days elapsed since the 2026-07-28 cutover; live endpoints healthy from outside, but container/uptime history was not visible from this machine |
| `fix/session-continuity-guard` merged | ✅ | `git merge-base --is-ancestor` confirms `b4ea2768` is an ancestor of `origin/main` |

External health at the time of writing — all from `72.60.17.245`:

```
/                    200      /about               200
/catalog.html        200      /assets/js/config.js 200
api…/auth/v1/.well-known/jwks.json   200
```

> Probe `jwks.json`, **not** `/auth/v1/health` — the latter returns 401 on this
> stack. Correction #10. Stage 11b's text and this workflow's older comments
> still name the health endpoint; they are stale on that point.

---

## Done — repo side, branch `stage12/repo-side`

- [x] **`site/assets/js/config.js` committed with the self-hosted values**,
      both lines. Verified byte-identical to the live server copy before
      committing. The anon key was decoded first to confirm it is
      `{"role":"anon"}`, expiring 2036 — a public RLS-gated browser key that
      the live site already serves at
      `https://analyzingislam.com/assets/js/config.js`. It is not one of the
      secrets `CLAUDE.md` prohibits committing.
- [x] **`--exclude='assets/js/config.js'` removed** from
      `.github/workflows-staged/deploy-vps.yml`, in the same commit, per the
      runbook's requirement that these two move together. Do not re-add it:
      repo and server now agree, so it would only stop future `config.js`
      changes from ever deploying.
- [x] **`site/CNAME` removed.**

## To do — needs access this checkout does not have

Order matters. Step 2 gates steps 3 and 4.

- [ ] **2. Add the three repository secrets.** `gh secret list` currently
      returns **empty** — none of them exist:

      VPS_SSH_KEY   private key for deploy@VPS   (on the authorized workstation)
      VPS_HOST      72.60.17.245
      VPS_USER      deploy

      > **Do not do steps 3–4 before this.** Retiring `pages.yml` while the
      > secrets are missing leaves every `site/**` push deploying nowhere:
      > Pages gone, and the VPS workflow failing on a missing key. The static
      > site keeps serving from the VPS, so nothing looks broken — the deploy
      > pipeline is simply dead and silent. That is the failure shape this
      > migration's traps keep taking.

- [ ] **3. Enable the replacement workflow.**

      ```bash
      gh auth refresh -s workflow      # the current token has only gist, read:org, repo
      git mv .github/workflows-staged/deploy-vps.yml .github/workflows/
      ```

      Without the `workflow` scope the push is rejected outright.

- [ ] **4. `git rm .github/workflows/pages.yml`.**

- [ ] **6b. Disable GitHub Pages.** Repo settings, or:

      ```bash
      gh api -X DELETE repos/Zander1798/analyzing-islam/pages
      ```

- [ ] **7. First post-Stage-12 deploy — re-check `config.js` on the live site.**
      The workflow's "Verify the deploy actually landed" step asserts both
      `/about` 200 and `config.js` naming the self-hosted API while *not*
      naming `cndmksrilytnpgstvmxb`. This is the last chance for trap 3 to bite.

- [ ] **Final absolute-URL sweep — must return 0.** Against the **live
      self-hosted** database, not Cloud:

      ```sql
      select count(*) from public.profiles
      where avatar_url  like '%cndmksrilytnpgstvmxb%'
         or banner_url  like '%cndmksrilytnpgstvmxb%';
      ```

      This catches anyone who uploaded an avatar between the Stage 10a sync and
      the client being repointed. Zero is what makes losing the old project
      safe. Note this is now partly retrospective: the Cloud host already does
      not resolve, so any row still pointing at it is **already** a broken
      image on the live site, not a future risk. Fix any hits rather than just
      recording the count.

      Use `docker exec -i` — without `-i`, `psql` can receive no SQL from a
      heredoc and still exit 0.

- [ ] **Supabase Cloud.** Nothing to pause if it is already deleted. Record
      which it was, and keep the Stage 1 backup permanently either way.

---

## Still outstanding from the cutover notes

1. **Rotate the Supabase Cloud database password** — it was pasted into a chat
   window. No record of this having been done. If the project is gone this is
   moot; confirm which.
2. **Do NOT revoke the Cloudflare API token** — correction #16. The apex
   certificate renews via DNS-01 against
   `/home/deploy/secrets/cloudflare.ini`. Revoking it breaks renewal without
   touching the currently valid certificate, so the failure surfaces weeks
   later. Switch to and verify a replacement authenticator first.

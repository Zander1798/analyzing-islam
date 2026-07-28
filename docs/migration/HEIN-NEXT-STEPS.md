# Hein — start here (2026-07-28)

**The Cloudflare blocker is gone. Stage 9a is done. You are unblocked on 9b, 9e and 10.**

Context lives in `EXECUTION-PLAN.md` (stage detail, the 15 corrections, the execution
log). This file is only: what changed today, what to do with the token, and your next
commands in order.

`git pull` first — `main` is at `77dd80d0` or later.

---

## 1. What changed today, from Zander's Windows PC

Nothing was touched on the VPS, the live site, or Supabase Cloud. The only writes were
two new DNS records.

**The old Cloudflare token was the wrong account** — 11 zones, none of them this domain.
Zander minted a new one on the correct account and it is verified working:

- Scope: **Zone → DNS → Edit** *and* **Zone → Zone → Read**
- Zone resources: **Include → Specific zone → `analyzingislam.com`** only
- No client-IP filter, **no expiry** (deliberate — see §3 on renewals)
- Verified: `/user/tokens/verify` → `active`; zone resolves to
  `7136f649b2c92b633c6bcf805721116f` with nameservers `dell.ns.cloudflare.com` /
  `zahir.ns.cloudflare.com`, matching the recorded pair

**Stage 9a executed** over the Cloudflare REST API:

| Record | Value | ID |
|---|---|---|
| `new.analyzingislam.com` | A → 72.60.17.245, TTL 300, DNS-only | `803059386b884197f8809daed0b15563` |
| `api.analyzingislam.com` | A → 72.60.17.245, TTL 300, DNS-only | `837954585e39adb39985bd2afa228484` |

**Verified after the write — the live site was not touched:**

```
total records: 7   (was 5, +2)
A      analyzingislam.com       185.199.108/109/110/111.153   ttl auto   proxied false
A      api.analyzingislam.com   72.60.17.245                  ttl 300    proxied false
A      new.analyzingislam.com   72.60.17.245                  ttl 300    proxied false
CNAME  www.analyzingislam.com   zander1798.github.io          ttl auto   proxied false
APEX UNCHANGED: True     WWW UNCHANGED: True     MX: still none
```

`https://analyzingislam.com/` → **HTTP 200 from 185.199.108.153**, still GitHub Pages.

Both new names resolve on 1.1.1.1 and 8.8.8.8. `api.` was briefly NXDOMAIN on 1.1.1.1
from a stale negative cache (zone SOA default TTL **1800s**); it has since cleared.
**Re-confirm before 9b anyway:**

```bash
dig +short new.analyzingislam.com @1.1.1.1   # 72.60.17.245
dig +short api.analyzingislam.com @1.1.1.1   # 72.60.17.245
```

---

## 2. The token — where it goes, and where it does NOT

Zander will give you the token value directly. It is **not** in this repo and must never
be committed; the repo is public.

**It belongs on the VPS**, because that is where certbot and nginx run:

```bash
ssh deploy@72.60.17.245
mkdir -p ~/secrets && chmod 700 ~/secrets
printf 'dns_cloudflare_api_token = %s\n' 'PASTE_TOKEN' > ~/secrets/cloudflare.ini
chmod 600 ~/secrets/cloudflare.ini
```

One line, no quotes around the value. **`chmod 600` is not optional** — certbot refuses
a credentials file that is group- or world-readable.

Also overwrite the stale workstation copy at `~/secrets/analyzingislam/cloudflare.ini`
(same one-line format, mode 600) so nobody trips over the wrong-account token again.

**You do not need the token for Stage 9b** — see below. It is only required for 9e.

---

## 3. Your commands, in order

### 9b — staging certs. No token needed.

`--nginx` is the **HTTP-01** authenticator: it proves control by serving a file on port
80. Both names already point at the VPS and 80 is open, so this works right now.

```bash
sudo certbot --nginx -d new.analyzingislam.com -d api.analyzingislam.com
```

certbot 2.9.0, `python3-certbot-nginx` and `python3-certbot-dns-cloudflare` are already
installed; `certbot.timer` is enabled and active; no certificates exist yet, so this
starts from a clean slate. The self-signed rig used for the 9d testing was fully
removed — the VPS currently has **no 443 block and no 80→443 redirect at all**, and
`certbot --nginx` writes the staging ones itself.

**Verify:**
```bash
curl -sI https://new.analyzingislam.com/about        # 200, valid public cert
curl -s https://new.analyzingislam.com/assets/js/config.js | grep -o 'url: "[^"]*"'
# must print https://api.analyzingislam.com — if it prints cndmksri…, the rsync
# --exclude was lost and the site is writing to the OLD database
curl -s -o /dev/null -w '%{http_code}\n' \
  https://api.analyzingislam.com/auth/v1/.well-known/jwks.json   # 200
```

Then re-run the 9d matrix against the **real** hostnames over public TLS. It passed
104/104 twice behind an `/etc/hosts` + self-signed rig; this is the same suite with the
rig removed, so it should be a formality — but it is the first time real DNS and a real
CA are in the path.

### 9e — pre-issue the LIVE certificate. Token required here.

This is why the token exists. It issues a cert for the apex and `www` **while those
names still point at GitHub Pages**, so HTTP-01 is impossible (it would validate against
Pages). DNS-01 writes a TXT record instead.

```bash
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/secrets/cloudflare.ini \
  -d analyzingislam.com -d www.analyzingislam.com
```

Add the 443 server block for apex + www (same root and `try_files $uri $uri.html $uri/
=404;` as the staging block — 989 pages depend on extensionless URLs — plus the 80→443
redirect), then `sudo nginx -t && sudo systemctl reload nginx`.

**Verify without touching DNS** — this is the whole point of the stage:
```bash
curl --resolve analyzingislam.com:443:72.60.17.245 -sI https://analyzingislam.com/about
# 200 with a valid cert: the live vhost is proven BEFORE cutover
```

> **Renewal caveat.** Issuing with `--dns-cloudflare` records that authenticator in
> `/etc/letsencrypt/renewal/analyzingislam.com.conf`, so **every 60-day renewal re-runs
> DNS-01 and needs this token still valid on the box.** That is why the token has no
> expiry. After cutover, switch the renewal authenticator to `--nginx` (HTTP-01 works
> once DNS points here and needs no credential at all) and the dependency goes away.
> Do that as a Stage 11 follow-up, then `sudo certbot renew --dry-run`.

### 10 — cutover. Zander's call, not a mechanical step.

```bash
./scripts/stage10a-final-sync.sh          # dump → ship → restore → repair → verify
```
Rehearsed 4× end to end, 29–31s on the VPS, under three minutes total, idempotent,
exits non-zero rather than half-finishing. **Do not perform this sequence by hand** —
corrections #11, #12 and #13 are all defects in the documented manual version, and two
of them produce a stack that is broken for users while every row count looks perfect.

The DNS flip (10b) can be driven from Zander's PC with the same token, or by you from
the VPS. Rollback is restoring the four `185.199.*` A records and pointing `www` back at
`zander1798.github.io` — live again in ~5 minutes, since TTL is already 300s.

---

## 4. Two things that are still human decisions

1. **`fix/session-continuity-guard` must be resolved BEFORE cutover, not after.**
   Correction #14: a returning user holding a *non-expired* Cloud ES256 token gets a UI
   that says signed-in while nothing loads, for up to an hour. Merging deploys to the
   live GitHub Pages site, so it is Zander's call. It is a no-op on the live site today.

   > ⚠ Until it is merged, `site/assets/js/auth.js` is the **only** file where the VPS
   > and the repo differ, and any Stage 8a rsync silently reverts it. After every rsync:
   > ```bash
   > ssh deploy@72.60.17.245 'grep -c reconcileForeignSession /var/www/analyzingislam/assets/js/auth.js'
   > # must print 1
   > ```

2. **Rotate the Supabase Cloud database password** after the Stage 10a final sync — it
   was pasted into a chat window.

---

## 5. Standing constraints — unchanged

- **Do not flip the apex `A` records or the `www` CNAME** without Zander's explicit go.
  The live site serves from GitHub Pages until then, and Pages is the rollback target.
- **Do not write to Supabase Cloud.** Read-only: dumps and queries.
- **Never commit secrets.** The repo is public. No `.env`, no dumps (6 users' password
  hashes, refresh tokens, private messages), no keys.
- **`docker exec` without `-i` silently discards stdin and exits 0.** Always `-i` for
  SQL, and always re-query to confirm a write landed.
- Evidence before claims. Nothing is "done" without command output proving it.

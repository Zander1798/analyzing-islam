# Cloudflare API token for the analyzingislam.com migration

> ## ✅ DONE — token minted 2026-07-28, Stage 9a executed
>
> Zander created a correctly-scoped token (Zone→DNS→Edit + Zone→Zone→Read, single
> zone, no IP filter, no expiry) and the staging DNS records are live:
> `new.` and `api.analyzingislam.com` both resolve to 72.60.17.245, while the apex
> and `www` are byte-for-byte unchanged on GitHub Pages. See EXECUTION-PLAN.md
> Stage 9a for record ids and the post-write verification.
>
> **Part 1 below is kept as the record of what was asked, and as the instructions
> to re-issue the token if it is ever lost or revoked.** Do not re-send it as a
> live request.
>
> **Part 2 is still live**: the token has to be copied onto the workstation (and,
> for Stage 9e, the VPS). `~/secrets/analyzingislam/cloudflare.ini` on this machine
> still holds the *wrong* account.

Everything for the migration to the new server is built and tested. The last piece
is DNS, and the domain's DNS lives in **Zander's Cloudflare account** — so Zander
needs to issue a narrow API token.

This document has two halves: **Part 1 is for Zander** (forward it as-is), and
**Part 2 is for Hein**, to verify and store the token once it arrives.

Why a token rather than "just send me the login": a token is scoped to one domain,
does one job, is revocable in a single click, and never gives access to the account,
billing, or any other site. It is the safer option for both sides.

---

## Part 1 — For Zander

**Time: about two minutes.**

### What you're creating

An API token that can edit DNS records for `analyzingislam.com` **and nothing else**.

**What it CAN do**
- Add, change and remove DNS records for `analyzingislam.com`

**What it CANNOT do**
- Log in to your account, or see your dashboard
- Touch billing, payment details, or your account settings
- Access any other domain you own
- Transfer, delete, or change ownership of the domain
- Read your email or anything outside Cloudflare DNS

You can revoke it instantly at any time from the same page you created it on, and
it stops working immediately. Nothing is permanent.

### Steps

1. Go to **dash.cloudflare.com** and log in.
2. Click your **profile icon** (top right) → **My Profile**.
3. In the left sidebar, click **API Tokens**.
   *(If your dashboard shows API Tokens under "Manage Account" instead, either
   place works — the user-level one under My Profile is fine.)*
4. Click **Create Token**.
5. Find the template called **"Edit zone DNS"** and click **Use template**.
   **Please use this template rather than building one by hand** — it includes a
   second permission (`Zone → Zone → Read`) that the certificate tool needs to look
   the domain up. A token with only DNS edit rights fails in a confusing way.
6. Scroll to **Zone Resources**. Set the three dropdowns to:

   > **Include** — **Specific zone** — **analyzingislam.com**

   This is the important step. Do **not** leave it on "All zones".
7. Leave **Client IP Address Filtering** and **TTL** empty.
   *(A TTL would expire the token mid-migration; we will ask you to revoke it
   manually instead, which is cleaner.)*
8. Click **Continue to summary**. It should read roughly:

   > `analyzingislam.com` — DNS:Edit, Zone:Read

9. Click **Create Token**.
10. **Copy the token now.** Cloudflare shows it exactly once and you cannot get it
    back — if you lose it, just delete that token and make another.

### Sending it

Send it to Hein over **WhatsApp or Signal** — a direct message, not email, not a
shared doc, not a group chat. Delete the message once Hein confirms it works.

### Afterwards

Please **leave the token in place for now**. It is what renews the site's HTTPS
certificate automatically every 60 days, so deleting it would eventually take the
site's padlock away. Hein will tell you when it is safe to remove, after switching
the renewal over to a method that does not need it.

### One thing to be aware of

`analyzingislam.com` is registered *at* Cloudflare, not just hosted there. Nothing
in this process changes that, and the domain stays entirely yours — the token only
edits DNS records inside it.

---

## Part 2 — For Hein: verify and store

### Verify before telling Zander it worked

Read-only. Confirms the token sees the right zone and has the right permissions,
and changes nothing:

```bash
read -rsp 'CF token: ' T; echo
curl -s -H "Authorization: Bearer $T" \
  https://api.cloudflare.com/client/v4/user/tokens/verify | python3 -m json.tool
curl -s -H "Authorization: Bearer $T" \
  "https://api.cloudflare.com/client/v4/zones?name=analyzingislam.com" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin);
print("zone visible:", [z["name"] for z in d["result"]] or "NONE — wrong scope")'
```

Expect `"status": "active"` from the first call and `['analyzingislam.com']` from
the second. If the second prints `NONE`, Zander left Zone Resources on the wrong
setting — ask him to edit the token rather than make a new one.

### Store it

```bash
install -d -m 700 ~/secrets/analyzingislam
# The existing cloudflare.ini holds the velocityfibre GLOBAL key in
# email + api_key form. certbot errors if both credential styles are present,
# so move it aside — it still controls the other 11 zones and is worth keeping.
mv ~/secrets/analyzingislam/cloudflare.ini \
   ~/secrets/analyzingislam/cloudflare-velocityfibre.ini 2>/dev/null
printf 'dns_cloudflare_api_token = %s\n' "$T" > ~/secrets/analyzingislam/cloudflare.ini
chmod 600 ~/secrets/analyzingislam/cloudflare.ini
unset T
```

`read -rsp` keeps the token off the screen and out of the shell transcript. **Never
commit it — this repo is public.**

### Where the token has to live

Both machines, because the two stages that need it run in different places:

| Stage | Runs on | Method | Needs the token? |
|---|---|---|---|
| 9a staging DNS records | workstation | Cloudflare API | yes |
| 9b staging certs | VPS | `certbot --nginx` (HTTP-01) | **no** — the A records are enough |
| 9e pre-issue the live cert | VPS | `certbot --dns-cloudflare` (DNS-01) | **yes, on the VPS** |
| 10b the cutover flip | workstation | Cloudflare API | yes |

9e is the one that forces the token onto the VPS: it proves the apex certificate
*before* DNS points at the new server, which is what removes the several-minute
TLS-mismatch window the original runbook had. It lives at `/home/deploy/secrets/cloudflare.ini` (mode 600) on the VPS.

> **Do NOT delete it after Stage 10.** certbot binds the apex certificate's
> renewal to that exact path (`authenticator = dns-cloudflare`), so removing it
> breaks renewal silently — the first symptom is an expired certificate on the
> live site ~60 days later. See EXECUTION-PLAN correction #16 for the
> switch-to-HTTP-01-then-revoke order if you want it gone.

### What happens the moment it lands

Stages **9a → 9b → 9e** run straight through, then everything stops before the flip.
Stage 10 (cutover) stays a separate, deliberate, human-approved step.

---

## If Zander would rather not issue a token

Two alternatives, in order of preference:

1. **Add Hein as a member of the Cloudflare account** (Manage Account → Members →
   Invite, with a DNS role scoped to this domain). Hein then creates and owns the
   token, and can rotate it without asking. Better long term if Hein is going to
   run this domain's infrastructure.
2. **Zander makes each DNS change manually.** This is the plan's documented
   fallback and needs no credential to change hands. The cost is that cutover
   becomes a scheduled live call rather than a command, and the Stage 9e
   pre-issued certificate becomes awkward — DNS-01 requires a token, so we would
   fall back to issuing the apex certificate *after* the flip, reintroducing a
   few minutes where visitors get a certificate warning.

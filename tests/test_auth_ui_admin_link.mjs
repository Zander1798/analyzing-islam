// tests/test_auth_ui_admin_link.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../site/assets/js/auth-ui.js", import.meta.url), "utf8");
// The menu must contain an admin Dashboard item that is gated behind an is_creator rpc.
assert.ok(/admin\.html/.test(src), "auth-ui must link to admin.html");
assert.ok(/is_creator/.test(src), "auth-ui must check is_creator via rpc before showing the link");
assert.ok(/auth-menu-admin/.test(src), "admin link should carry a stable class for show/hide");

// The Dashboard link is rendered with the `hidden` attribute so it stays
// invisible until explicitly revealed.
assert.ok(
  /auth-menu-admin[^>]*hidden/.test(src),
  "admin link must be rendered hidden by default"
);

// It must be pinned to the owner account: reveal requires BOTH the owner email
// and is_creator === true, so no other signed-in account can ever see it.
assert.ok(/OWNER_EMAIL\s*=\s*["']zandervv0610@icloud\.com["']/.test(src),
  "auth-ui must define the owner email");
assert.ok(/isOwnerEmail\s*&&\s*res\s*&&\s*res\.data\s*===\s*true/.test(src),
  "admin link must require owner email AND is_creator before un-hiding");

// The `hidden` attribute only wins if CSS does not force `display` on menu
// items — otherwise the card shows for everyone. Guard the CSS rule too.
const css = readFileSync(new URL("../site/assets/css/style.css", import.meta.url), "utf8");
assert.ok(/\.auth-menu-item\[hidden\]\s*\{\s*display:\s*none/.test(css),
  "style.css must set .auth-menu-item[hidden] { display: none } so `hidden` wins over display:block");

console.log("auth-ui admin link wiring present (hidden default + owner-email gate + CSS guard)");

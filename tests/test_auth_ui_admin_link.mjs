// tests/test_auth_ui_admin_link.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../site/assets/js/auth-ui.js", import.meta.url), "utf8");
// The menu must contain an admin Dashboard item that is gated behind an is_creator rpc.
assert.ok(/admin\.html/.test(src), "auth-ui must link to admin.html");
assert.ok(/is_creator/.test(src), "auth-ui must check is_creator via rpc before showing the link");
assert.ok(/auth-menu-admin/.test(src), "admin link should carry a stable class for show/hide");
console.log("auth-ui admin link wiring present");

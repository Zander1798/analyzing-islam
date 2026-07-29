import assert from "node:assert";
import {
  copyFileSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const root = mkdtempSync(join(tmpdir(), "mirror-agents-md-"));

try {
  mkdirSync(join(root, "scripts"));
  copyFileSync(
    new URL("../scripts/mirror-agents-md.mjs", import.meta.url),
    join(root, "scripts", "mirror-agents-md.mjs"),
  );
  writeFileSync(join(root, "CLAUDE.md"), "# Rules\n\nCanonical text.\n", "utf8");

  const write = spawnSync("node", ["scripts/mirror-agents-md.mjs"], {
    cwd: root,
    encoding: "utf8",
  });
  assert.equal(write.status, 0, write.stderr || write.stdout);

  const mirror = join(root, "AGENTS.md");
  writeFileSync(
    mirror,
    readFileSync(mirror, "utf8").replace(/\n/g, "\r\n"),
    "utf8",
  );

  const check = spawnSync(
    "node",
    ["scripts/mirror-agents-md.mjs", "--check"],
    { cwd: root, encoding: "utf8" },
  );
  assert.equal(
    check.status,
    0,
    `CRLF-only differences must not report STALE:\n${check.stderr}${check.stdout}`,
  );
} finally {
  rmSync(root, { recursive: true, force: true });
}

console.log("mirror line-ending test passed");

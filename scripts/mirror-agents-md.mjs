#!/usr/bin/env node
/**
 * Mirror the Claude-facing docs into Codex-facing `AGENTS.md` siblings.
 * Plain ESM — runs on bare `node`, no tsx / TypeScript / dependencies.
 *
 *   node scripts/mirror-agents-md.mjs             # write
 *   node scripts/mirror-agents-md.mjs --dry-run   # preview
 *   node scripts/mirror-agents-md.mjs --check     # exit 1 if STALE or MISSING
 *
 * `--check` compares rendered content to disk rather than using `git diff`:
 * git cannot see an untracked file, so a diff-based gate passes silently when a
 * sibling that SHOULD exist was never committed at all.
 */

import {
  readdirSync,
  readFileSync,
  writeFileSync,
  existsSync,
} from "node:fs";
import { dirname, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

/** Codex stops reading at 32 KB; warn well before we get there. */
const CODEX_LIMIT_BYTES = 32 * 1024;
const WARN_BYTES = 28 * 1024;

/** N-rule: don't port a stub, or a doc for a module too small to need one. */
const MIN_SOURCE_FILES = 4;
const MIN_DOC_LINES = 10;

/**
 * Directories to search for nested `.claude.md`.
 *
 * Set for THIS repository: the maintained source and documentation trees only.
 *
 * Deliberately excluded, and why:
 *   site/            generated HTML — build output, not source
 *   quran-json/, hadith-json/, arguments-data/           data fixtures
 *   book-design/, mockups/, e2e_screenshots/             artifacts and drafts
 *   video/public/, video/out/, video/capture/             media/build artifacts
 *
 * The 165 Python files live at the repository root, which is not scanned: the root
 * `CLAUDE.md` already covers them and is emitted unconditionally below.
 */
const SCAN_ROOTS = [
  "scripts",
  "supabase",
  "tests",
  "docs",
  "kb-doctrine",
  "video/src",
];

const SOURCE_EXT = /\.(ts|tsx|js|jsx|mjs|cjs|py|go|rb|rs|java|kt|php)$/;

function listClaudeMd(dir, acc = []) {
  if (!existsSync(dir)) return acc;

  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === ".next") continue;

    const full = resolve(dir, entry.name);

    if (entry.isDirectory()) {
      listClaudeMd(full, acc);
    } else if (entry.name === ".claude.md") {
      acc.push(full);
    }
  }

  return acc;
}

/**
 * Deliberately non-recursive: a module doc describes the code beside it.
 *
 * A module organised mostly through subdirectories could read as "small" and
 * be skipped. Revisit the heuristic if that shape appears rather than
 * recursing blindly into fixtures and generated output.
 */
function countSourceFiles(dir) {
  let n = 0;

  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isFile() && SOURCE_EXT.test(entry.name)) n++;
  }

  return n;
}

function banner(canonical) {
  return [
    `<!-- GENERATED — do not edit. Canonical source: ${canonical} -->`,
    `<!-- Regenerate: node scripts/mirror-agents-md.mjs -->`,
    `<!-- You are reading the AGENTS.md view of the Claude-facing docs. Prose`,
    `     below may refer to ".claude.md" when describing the canonical side;`,
    `     that is accurate — only PATH references are rewritten to AGENTS.md. -->`,
    ``,
  ].join("\n");
}

/**
 * Rewrite only backtick-quoted PATH references, for example a nested canonical
 * path ending in `.claude.md` becomes the sibling path ending in `AGENTS.md`.
 *
 * The `/` in the pattern is load-bearing.
 *
 * A blanket `.claude.md` -> `AGENTS.md` replacement also rewrites prose ABOUT
 * the mirroring system. An earlier implementation produced false output such
 * as "the only transform is `AGENTS.md` -> `AGENTS.md`" and claimed the path
 * gate scans generated files when it actually scans canonical files.
 *
 * A path has a directory in front of it; a concept does not.
 */
function render(source, canonical) {
  const body = readFileSync(source, "utf8").replace(
    /`([^`\s]*\/)\.claude\.md`/g,
    "`$1AGENTS.md`",
  );

  return banner(canonical) + body;
}

function targets() {
  const emit = [];
  const skipped = [];

  emit.push({
    out: resolve(ROOT, "AGENTS.md"),
    source: resolve(ROOT, "CLAUDE.md"),
    canonical: "CLAUDE.md",
  });

  const nested = [];

  for (const root of SCAN_ROOTS) {
    listClaudeMd(resolve(ROOT, root), nested);
  }

  for (const doc of nested) {
    const dir = dirname(doc);
    const rel = relative(ROOT, doc);
    const files = countSourceFiles(dir);
    const lines = readFileSync(doc, "utf8").split("\n").length;

    if (files < MIN_SOURCE_FILES) {
      skipped.push(`${rel} — small-module (${files} source files)`);
      continue;
    }

    if (lines < MIN_DOC_LINES) {
      skipped.push(`${rel} — stub (${lines} lines)`);
      continue;
    }

    emit.push({
      out: resolve(dir, "AGENTS.md"),
      source: doc,
      canonical: "./.claude.md",
    });
  }

  return { emit, skipped };
}

const argv = process.argv.slice(2);
const CHECK = argv.includes("--check");
const DRY = argv.includes("--dry-run");

if (!existsSync(resolve(ROOT, "CLAUDE.md"))) {
  console.error(
    "[agents] FAIL — no CLAUDE.md at the repo root. Write it first; mirroring an absent file helps nobody.",
  );
  process.exit(1);
}

const { emit, skipped } = targets();
const stale = [];
const missing = [];
const written = [];

for (const target of emit) {
  const content = render(target.source, target.canonical);
  const rel = relative(ROOT, target.out);
  const bytes = Buffer.byteLength(content, "utf8");

  if (bytes > CODEX_LIMIT_BYTES) {
    console.error(
      `[agents] FAIL — ${rel} is ${(bytes / 1024).toFixed(1)} KB, over Codex's 32 KB cut-off.`,
    );
    process.exit(1);
  }

  if (bytes > WARN_BYTES) {
    console.warn(
      `[agents] warn — ${rel} is ${(bytes / 1024).toFixed(1)} KB, approaching the 32 KB cut-off.`,
    );
  }

  if (CHECK) {
    if (!existsSync(target.out)) {
      missing.push(rel);
    } else if (readFileSync(target.out, "utf8") !== content) {
      stale.push(rel);
    }

    continue;
  }

  // Only touch a file whose content changed, so --dry-run is a truthful
  // preview and the printed count means something.
  if (existsSync(target.out) && readFileSync(target.out, "utf8") === content) {
    continue;
  }

  if (!DRY) {
    writeFileSync(target.out, content, "utf8");
  }

  written.push(rel);
}

if (CHECK) {
  if (missing.length === 0 && stale.length === 0) {
    console.log(
      `[agents:check] OK — ${emit.length} AGENTS.md mirror(s) match their canonical source.`,
    );
    process.exit(0);
  }

  console.error("[agents:check] FAIL — AGENTS.md is out of sync with CLAUDE.md:\n");

  for (const file of missing) {
    console.error(`  MISSING  ${file}`);
  }

  for (const file of stale) {
    console.error(`  STALE    ${file}`);
  }

  console.error("\nFix: node scripts/mirror-agents-md.mjs");
  process.exit(1);
}

console.log(
  DRY
    ? `[agents] dry-run — ${written.length} file(s) would be written.`
    : `[agents] wrote ${written.length} file(s).`,
);

for (const file of written) {
  console.log(`  ${file}`);
}

for (const reason of skipped) {
  console.log(`  [skip] ${reason}`);
}

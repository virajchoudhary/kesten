import { spawn } from "node:child_process";
import { setTimeout } from "node:timers/promises";
import { cpSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  assertSameTerminalSource,
  terminalSourceReceipt,
} from "./terminal-source.mjs";

const before = terminalSourceReceipt();
if (process.env.TERMINAL_EVIDENCE_DIR) {
  mkdirSync(process.env.TERMINAL_EVIDENCE_DIR, { recursive: true });
  writeFileSync(
    join(process.env.TERMINAL_EVIDENCE_DIR, "source-before.json"),
    JSON.stringify(before, null, 2),
  );
}

const suites = [
  "accounts",
  "markets",
  "research-quality",
  "research",
  "terminal",
  "terminal-depth",
];
for (const [index, suite] of suites.entries()) {
  if (index > 0) {
    process.stdout.write(
      "Waiting 60 seconds for the configured API throttle window.\n",
    );
    await setTimeout(60_000);
  }
  const status = await new Promise((resolve, reject) => {
    const child = spawn(
      process.execPath,
      [
        "node_modules/@playwright/test/cli.js",
        "test",
        "--workers=1",
        `e2e/${suite}.spec.ts`,
      ],
      {
        stdio: "inherit",
        env: process.env,
      },
    );
    child.on("error", reject);
    child.on("exit", (code) => resolve(code ?? 1));
  });
  if (process.env.TERMINAL_EVIDENCE_DIR) {
    mkdirSync(process.env.TERMINAL_EVIDENCE_DIR, { recursive: true });
    cpSync("test-results", join(process.env.TERMINAL_EVIDENCE_DIR, suite), {
      recursive: true,
    });
  }
  if (status !== 0) process.exit(status);
}
const after = terminalSourceReceipt();
if (process.env.TERMINAL_EVIDENCE_DIR)
  writeFileSync(
    join(process.env.TERMINAL_EVIDENCE_DIR, "source-after.json"),
    JSON.stringify(after, null, 2),
  );
assertSameTerminalSource(before, after);
process.stdout.write(
  "All terminal browser suites passed with API limits unchanged.\n",
);

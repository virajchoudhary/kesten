import { spawn } from "node:child_process";
import { setTimeout } from "node:timers/promises";

const suites = [
  "accounts",
  "markets",
  "research-quality",
  "research",
  "terminal",
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
  if (status !== 0) process.exit(status);
}
process.stdout.write(
  "All terminal browser suites passed with API limits unchanged.\n",
);

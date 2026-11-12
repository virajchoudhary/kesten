import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
export function assertSameTerminalSource(before, after) {
  if (before.source_sha256 !== after.source_sha256)
    throw new Error(
      "Terminal source changed during browser acceptance. Run the affected checks again.",
    );
}
export function terminalSourceReceipt() {
  const files = [];
  function collect(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) collect(path);
      else if (entry.isFile()) files.push(path);
    }
  }
  for (const directory of ["src", "e2e", "scripts"])
    collect(join(root, directory));
  for (const file of [
    "package.json",
    "package-lock.json",
    "next.config.ts",
    "playwright.config.ts",
    "tsconfig.json",
  ])
    files.push(join(root, file));
  const entries = files.sort().map((path) => ({
    path: relative(root, path).replaceAll("\\", "/"),
    sha256: createHash("sha256").update(readFileSync(path)).digest("hex"),
  }));
  return {
    recorded_at: new Date().toISOString(),
    scope:
      "web/src, web/e2e, web/scripts and frontend package/configuration files; no runtime data or credentials",
    source_sha256: createHash("sha256")
      .update(JSON.stringify(entries))
      .digest("hex"),
    files: entries,
  };
}

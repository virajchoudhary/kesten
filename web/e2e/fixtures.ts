import { existsSync } from "node:fs";
import { basename, resolve } from "node:path";
import { test } from "@playwright/test";

export function fixturePath(name: string): string {
  const directory = process.env.CADRISYN_E2E_FIXTURE_DIR ?? resolve(process.cwd(), "../.local");
  const accounts = resolve(directory, "browser-spec-accounts");
  if (name === "credentials.json" && existsSync(accounts)) {
    const credentials = resolve(accounts, basename(test.info().file, ".ts"), name);
    if (!existsSync(credentials)) throw new Error("Prepare the private account for this browser spec first.");
    return credentials;
  }
  return resolve(directory, name);
}

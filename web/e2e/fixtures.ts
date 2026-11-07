import { resolve } from "node:path";

export function fixturePath(name: string): string {
  return resolve(process.env.CADRISYN_E2E_FIXTURE_DIR ?? resolve(process.cwd(), "../.local"), name);
}

import { createHash, X509Certificate } from "node:crypto";
import { readFileSync } from "node:fs";

import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "https://localhost:8443";
const origin = new URL(baseURL);
if (origin.protocol !== "https:" || !["localhost", "127.0.0.1"].includes(origin.hostname) || origin.port !== "8443" || origin.pathname !== "/" || origin.username || origin.password || origin.search || origin.hash) {
  throw new Error("Release rehearsal requires the loopback HTTPS gateway on port 8443.");
}
const certificatePath = process.env.CADRISYN_REHEARSAL_CERT;
if (!certificatePath) throw new Error("Specify the exact local rehearsal certificate.");
const certificate = new X509Certificate(readFileSync(certificatePath));
const fingerprint = createHash("sha256").update(certificate.publicKey.export({ type: "spki", format: "der" })).digest("base64");

export default defineConfig({
  testDir: "./e2e-release",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  expect: { timeout: 10_000 },
  timeout: 120_000,
  reporter: "list",
  use: {
    baseURL,
    trace: "off",
    screenshot: "only-on-failure",
    launchOptions: { args: ["--ignore-certificate-errors-spki-list=" + fingerprint] },
  },
  projects: [{ name: "chromium-local-tls", use: { ...devices["Desktop Chrome"] } }],
});

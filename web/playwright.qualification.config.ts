import { createHash, X509Certificate } from "node:crypto";
import { readFileSync } from "node:fs";

import { defineConfig, devices } from "@playwright/test";

const origin = new URL(process.env.PLAYWRIGHT_BASE_URL ?? "https://localhost:8452");
if (origin.protocol !== "https:" || !["localhost", "127.0.0.1"].includes(origin.hostname) || !origin.port || origin.pathname !== "/" || origin.username || origin.password || origin.search || origin.hash) {
  throw new Error("Qualification requires an explicit loopback HTTPS origin.");
}
const certificatePath = process.env.CADRISYN_REHEARSAL_CERT;
if (!certificatePath) throw new Error("Supply the exact isolated rehearsal certificate.");
const certificate = new X509Certificate(readFileSync(certificatePath));
const fingerprint = createHash("sha256").update(certificate.publicKey.export({ type: "spki", format: "der" })).digest("base64");

export default defineConfig({
  testDir: "./e2e-production",
  outputDir: process.env.KERQUANT_BROWSER_OUTPUT ?? "../.local/production-browser-results",
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: "list",
  use: {
    baseURL: origin.origin,
    trace: "off",
    screenshot: "only-on-failure",
    launchOptions: { args: ["--ignore-certificate-errors-spki-list=" + fingerprint] },
  },
  projects: [{ name: "chromium-production-profile", use: { ...devices["Desktop Chrome"] } }],
});

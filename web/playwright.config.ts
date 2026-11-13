import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const production = process.env.PLAYWRIGHT_PRODUCTION === "1";
const external = process.env.PLAYWRIGHT_EXTERNAL_SERVER === "1";
const origin = new URL(baseURL);
if (
  !["http:", "https:"].includes(origin.protocol) ||
  !["127.0.0.1", "localhost", "[::1]"].includes(origin.hostname) ||
  origin.username || origin.password || origin.pathname !== "/" || origin.search || origin.hash
) {
  throw new Error("Browser acceptance requires a loopback HTTP(S) origin without credentials or a path.");
}

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL,
    trace: "off",
    actionTimeout: 15_000,
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: external ? undefined : {
    command: production ? "npm start" : "npm run dev -- --hostname 127.0.0.1",
    env: { HOSTNAME: "127.0.0.1", PORT: "3000", NEXT_TELEMETRY_DISABLED: "1" },
    url: baseURL,
    reuseExistingServer: !process.env.CI && !production,
    timeout: 120_000,
  },
});

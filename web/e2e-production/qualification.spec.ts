import { readFileSync } from "node:fs";

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { z } from "zod";

import { ResearchRunListSchema } from "../src/features/research/research-schemas";

const credentialsPath = process.env.CADRISYN_RELEASE_CREDENTIALS;
if (!credentialsPath) throw new Error("Supply credentials for the new isolated qualification accounts.");
const account = z.strictObject({ username: z.string().min(1), password: z.string().min(12) });
const [owner] = z.tuple([account, account]).parse(JSON.parse(readFileSync(credentialsPath, "utf8")));

test.beforeEach(async ({ page }) => {
  await page.goto("/sign-in/");
  await page.getByLabel("Username").fill(owner.username);
  await page.getByLabel("Password").fill(owner.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
});

test("production chart, provenance and responsive themes use the real API", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto("/app/markets/?instrument=xnas-aapl");
    await expect(page.getByTestId("price-chart").locator("canvas").first()).toBeVisible();
    await page.getByRole("button", { name: "Data evidence", exact: true }).click();
    await expect(page.getByRole("dialog", { name: "Market data evidence" })).toContainText("Synthetic demonstration dataset");
    await page.keyboard.press("Escape");
    for (const theme of ["light", "dark"]) {
      await page.evaluate(value => {
        localStorage.setItem("cadrisyn-theme", value);
      }, theme);
      await page.reload();
      await expect(page.locator("html")).toHaveClass(new RegExp(theme));
      await expect(page.getByTestId("price-chart").locator("canvas").first()).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
      await page.screenshot({ path: testInfo.outputPath(`production-markets-${viewport.width}-${theme}.png`) });
    }
  }
  expect((await page.context().cookies()).find(cookie => cookie.name === "cadrisyn_session")).toMatchObject({ secure: true, httpOnly: true, sameSite: "Lax" });
  expect(errors).toEqual([]);
});

test("saved synthetic research preserves identity and exact replay in production", async ({ page }, testInfo) => {
  // Use the browser transport pinned to this rehearsal certificate, including its private cookie jar.
  const runs = ResearchRunListSchema.parse(await page.evaluate(async () => {
    const response = await fetch("/api/v1/research/runs/");
    if (!response.ok) throw new Error("The private research list is unavailable.");
    return response.json();
  }));
  const run = runs.items.find(item => item.horizon_sessions === 5);
  if (!run) throw new Error("The isolated five-session pipeline fixture is missing.");
  expect(run.data_kind).toBe("synthetic_fixture");
  expect(run.result.empirical_performance_established).toBe(false);
  await page.goto(`/app/research/?run=${run.id}#research-results`);
  await expect(page.getByRole("heading", { name: "Synthetic pipeline fixture", exact: true })).toBeVisible();
  await expect(page.getByRole("img", { name: "Dataset history and forecast paths" })).toBeVisible();
  await expect(page.getByText("Synthetic pipeline check only. No empirical forecasting performance established.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Verify exact replay", exact: true }).click();
  await expect(page.getByLabel("Exact replay verification")).toContainText("Replay PASS");
  await expect(page).toHaveURL(new RegExp(run.id));
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`production-research-${width}.png`), fullPage: true });
  }
});

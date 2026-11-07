import { readFileSync } from "node:fs";

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { z } from "zod";

const credentialsPath = process.env.CADRISYN_RELEASE_CREDENTIALS;
if (!credentialsPath) throw new Error("Supply credentials for the isolated rehearsal account.");
const credentials = z.strictObject({ username: z.string().min(1), password: z.string().min(12) }).parse(JSON.parse(readFileSync(credentialsPath, "utf8")));

test("demo research exclusion remains readable and keyboard accessible in both themes", async ({ page }, testInfo) => {
  for (const colorScheme of ["light", "dark"] satisfies ("light" | "dark")[]) {
    await page.emulateMedia({ colorScheme });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/app/research/");
    await expect(page.getByRole("heading", { name: "Demo-only workspace" })).toBeVisible();
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Open demo markets" })).toBeFocused();
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath("demo-research-" + colorScheme + ".png") });
  }
});

test("HTTPS login sets secure private cookies and demo data remains explicit", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 960 });
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/sign-in/");
  await page.getByLabel("Username").fill(credentials.username);
  await page.getByLabel("Password").fill(credentials.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Add instrument", exact: true }).first().click();
  const search = page.getByRole("combobox", { name: "Search by symbol or company" });
  await search.fill("AAPL");
  await expect(page.getByRole("option").filter({ hasText: "AAPL" }).first()).toBeVisible();
  await search.press("ArrowDown");
  await search.press("Enter");
  await expect(page.getByText("Synthetic demonstration dataset", { exact: true }).filter({ visible: true }).first()).toBeVisible();
  await expect(page.getByTestId("price-chart").locator("canvas").first()).toBeVisible();
  const sessionCookie = (await page.context().cookies()).find(cookie => cookie.name === "cadrisyn_session");
  expect(sessionCookie).toMatchObject({ secure: true, httpOnly: true, sameSite: "Lax" });
  const status = await page.evaluate(async () => (await fetch("/api/v1/research/datasets/")).status);
  expect(status).toBe(404);
  expect(await page.evaluate(async () => (await fetch("/api/v1/watchlist/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ instrument_id: "xnas-msft" }) })).status)).toBe(403);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("https-demo-markets.png"), fullPage: true });
  expect(errors).toEqual([]);
});

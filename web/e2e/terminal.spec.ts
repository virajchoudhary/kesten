import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { z } from "zod";
import { fixturePath } from "./fixtures";
import { MarketResponseSchema, SessionSchema } from "../src/lib/api/schemas";

test("terminal preserves provenance, chart controls and integrated research identities", async ({
  page,
}, testInfo) => {
  test.setTimeout(180_000);
  const credentials = z
    .object({ username: z.string(), password: z.string() })
    .parse(JSON.parse(readFileSync(fixturePath("credentials.json"), "utf8")));
  const anonymous = SessionSchema.parse(
    await (await page.request.get("/api/v1/session/")).json(),
  );
  const login = await page.request.post("/api/v1/session/", {
    data: credentials,
    headers: { "X-CSRFToken": anonymous.csrf_token },
  });
  expect(login.status()).toBe(200);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/app/markets");
  await expect(
    page.getByTestId("price-chart").locator("canvas").first(),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveClass(/dark/u);
  const chart = page.getByTestId("price-chart");
  const bounds = await chart.boundingBox();
  expect(bounds?.height).toBeGreaterThan(550);
  if (!bounds) throw new Error("Missing chart geometry");
  await page.mouse.move(bounds.x + bounds.width * 0.4, bounds.y + 100);
  const legend = page.getByLabel("Chart observation");
  const history = MarketResponseSchema.parse(
    await (
      await page.request.get(
        "/api/v1/instruments/xnas-aapl/bars/?range=1y&mode=demo",
      )
    ).json(),
  );
  await expect
    .poll(async () => {
      const text = await legend.innerText();
      return history.bars.slice(0, -1).some((bar) => text.includes(bar.time));
    })
    .toBe(true);
  const legendText = await legend.innerText();
  const observation = history.bars.find((bar) => legendText.includes(bar.time));
  expect(observation).toBeDefined();
  if (!observation)
    throw new Error("Crosshair did not resolve an exact observation");
  for (const value of [
    observation.open,
    observation.high,
    observation.low,
    observation.close,
  ]) {
    expect(legendText).toContain(
      new Intl.NumberFormat("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value),
    );
  }
  await page.mouse.wheel(0, -180);
  await page.getByRole("button", { name: "Reset chart view" }).click();
  await page
    .getByRole("button", { name: "Chart settings", exact: true })
    .click();
  await page.getByRole("checkbox", { name: "Show grid" }).uncheck();
  await expect(
    page.getByRole("checkbox", { name: "Show grid" }),
  ).not.toBeChecked();
  await page.getByRole("checkbox", { name: "Show grid" }).check();
  await page
    .getByRole("button", { name: "Chart settings", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Data evidence", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Market data evidence" }),
  ).toContainText("Synthetic demonstration dataset");
  await page.keyboard.press("Escape");
  await page
    .getByRole("button", { name: "Open watchlist and instrument search" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Watchlist", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Open watchlist and instrument search" })
    .click();
  await page.getByRole("button", { name: /AAPL · Search/u }).click();
  await page
    .getByRole("combobox", { name: "Search by symbol or company" })
    .fill("JPM");
  await page.getByRole("option").filter({ hasText: "JPM" }).first().click();
  await expect(
    page.getByRole("heading", { name: /JPMorgan Chase/u }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Instrument research", exact: true })
    .click();
  await expect(page).toHaveURL(/view=research.*instrument=xnys-jpm/u);
  await expect(
    page.getByRole("heading", { name: "Forecasting research", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Run evaluation", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: /JPM · Search/u }).click();
  await page
    .getByRole("combobox", { name: "Search by symbol or company" })
    .fill("NVDA");
  await page.getByRole("option").filter({ hasText: "NVDA" }).first().click();
  await expect(page).toHaveURL(/instrument=xnas-nvda/u);
  await page.goBack();
  await expect(page).toHaveURL(/instrument=xnys-jpm/u);
  await expect(
    page.getByRole("heading", { name: /JPMorgan Chase/u }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Instrument research", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Run evaluation", exact: true })
    .click();
  await expect(page).toHaveURL(/\/app\/markets\?.*run=/u);
  await expect(
    page.getByRole("heading", { name: "Evaluation results", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Verify exact replay", exact: true }),
  ).toBeVisible();
  const savedUrl = page.url();
  await page
    .getByRole("link", { name: "Instrument research", exact: true })
    .click();
  await expect(page).toHaveURL(savedUrl);
  await page.reload();
  await expect(page).toHaveURL(savedUrl);
  await expect(
    page.getByRole("heading", { name: "Evaluation results", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByText("No empirical forecasting performance established.", {
        exact: true,
      })
      .first(),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("integrated-research.png"),
    fullPage: true,
  });
  await page.getByRole("link", { name: "Chart", exact: true }).click();
  for (const theme of ["dark", "light"] as const) {
    const switchTheme = page.getByRole("button", {
      name: `Use ${theme} theme`,
      exact: true,
    });
    if (await switchTheme.count()) await switchTheme.click();
    for (const [width, height] of [
      [1440, 900],
      [1920, 1080],
      [820, 1180],
      [390, 844],
      [375, 812],
    ]) {
      await page.setViewportSize({ width, height });
      await expect(chart.locator("canvas").first()).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await expect(
        page.getByRole("link", { name: "Account", exact: true }),
      ).toBeVisible();
      const axe = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      expect(
        axe.violations.map(({ id, nodes }) => ({
          id,
          targets: nodes.map((node) => node.target),
        })),
      ).toEqual([]);
      await page.screenshot({
        path: testInfo.outputPath(`terminal-${width}-${theme}.png`),
        fullPage: true,
      });
    }
  }
  await page
    .getByRole("button", { name: "Open watchlist and instrument search" })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Watchlist and instrument search" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Close watchlist", exact: true })
    .focus();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open watchlist and instrument search" }),
  ).toBeFocused();
});

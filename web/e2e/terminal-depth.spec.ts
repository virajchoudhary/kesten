import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { SessionSchema } from "../src/lib/api/schemas";
import { ResearchRunListSchema } from "../src/features/research/research-schemas";
import { fixturePath } from "./fixtures";

test("customizes, compares and measures daily charts, then inspects an exact saved run", async ({
  page,
}, testInfo) => {
  test.setTimeout(180_000);
  const credentials = JSON.parse(
    readFileSync(fixturePath("credentials.json"), "utf8"),
  );
  const session = SessionSchema.parse(
    await (await page.request.get("/api/v1/session/")).json(),
  );
  expect(
    (
      await page.request.post("/api/v1/session/", {
        data: credentials,
        headers: { "X-CSRFToken": session.csrf_token },
      })
    ).status(),
  ).toBe(200);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/app/markets?instrument=xnas-aapl");
  const chart = page.getByTestId("price-chart");
  await expect(chart).toHaveAttribute("data-chart-state", "ready");
  for (const type of ["bars", "line", "area", "candles"]) {
    await page.getByLabel("Chart type", { exact: true }).selectOption(type);
    await expect(chart.locator("canvas").first()).toBeVisible();
  }
  await page.getByRole("button", { name: "Indicators", exact: true }).click();
  await page.getByRole("checkbox", { name: "EMA 21", exact: true }).check();
  await page.getByLabel("EMA period", { exact: true }).fill("13");
  await page
    .getByRole("checkbox", { name: "Bollinger bands", exact: true })
    .check();
  await page
    .getByRole("button", { name: "Apply parameters", exact: true })
    .click();
  await expect(page.locator(".chart-study-legend")).toContainText("EMA 13");
  await page.getByRole("checkbox", { name: "RSI 14", exact: true }).uncheck();
  await page.getByRole("checkbox", { name: "RSI 14", exact: true }).check();
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page
    .getByRole("button", { name: "Chart settings", exact: true })
    .click();
  await page.getByLabel("Price scale", { exact: true }).selectOption("percent");
  await expect(page.locator(".chart-study-legend")).toContainText("% from");
  await page.getByLabel("Crosshair", { exact: true }).selectOption("magnet");
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page
    .getByRole("button", { name: "Display layouts", exact: true })
    .click();
  await page.getByLabel("Layout name", { exact: true }).fill("Review trend");
  await page
    .getByRole("button", { name: "Save current layout", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: /Review trend.*candles/u }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page.reload();
  await expect(chart).toHaveAttribute("data-chart-state", "ready");
  await expect(page.locator(".chart-study-legend")).toContainText("EMA 13");
  await expect(page.locator(".chart-study-legend")).toContainText("% from");
  await page
    .getByRole("button", { name: "Chart settings", exact: true })
    .click();
  await page.getByLabel("Price scale", { exact: true }).selectOption("log");
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page.getByRole("button", { name: "Price levels", exact: true }).click();
  await page.getByLabel("Price level", { exact: true }).fill("125");
  await page
    .getByRole("button", { name: "Add horizontal level", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Remove level 125", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page
    .getByRole("list", { name: "Saved instruments", exact: true })
    .getByRole("button", { name: /^MSFT/u })
    .click();
  await expect(
    page.getByRole("heading", { name: /Microsoft Corporation/u }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Price levels", exact: true }).click();
  await page.getByLabel("Price level", { exact: true }).fill("300");
  await page
    .getByRole("button", { name: "Add horizontal level", exact: true })
    .click();
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page
    .getByRole("list", { name: "Saved instruments", exact: true })
    .getByRole("button", { name: /^AAPL/u })
    .click();
  await expect(page.getByRole("heading", { name: /Apple Inc/u })).toBeVisible();
  await page.getByRole("button", { name: "Price levels", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Remove level 125", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Remove level 300", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Close chart panel" }).click();
  await page
    .getByRole("button", { name: "Measure session closes", exact: true })
    .click();
  const keyboardChart = page.getByRole("group", {
    name: "AAPL daily candlestick chart",
    exact: true,
  });
  await keyboardChart.focus();
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("Enter");
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("Enter");
  await expect(page.locator(".measurement-readout")).toContainText("1 session");
  await expect(page.locator(".measurement-readout")).toContainText("USD");
  await page.getByRole("button", { name: "Compare", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Search by symbol or company" })
    .fill("MSFT");
  await page.getByRole("option").filter({ hasText: "MSFT" }).first().click();
  await expect(page.locator(".comparison-strip")).toContainText(
    "common sessions",
  );
  await expect(page.locator(".comparison-strip")).toContainText(
    "Indexed to 100",
  );
  await expect(page.locator(".comparison-strip")).toContainText("as of");
  await expect(page.locator(".comparison-strip")).toContainText("Demo");
  await expect(chart).toHaveAttribute("data-chart-state", "ready");
  const attribution = chart.locator('a[href*="tradingview.com"]');
  await expect(attribution).toBeVisible();
  const attributionBox = await attribution.boundingBox();
  const measurementBox = await page
    .locator(".measurement-readout")
    .boundingBox();
  if (!attributionBox || !measurementBox)
    throw new Error("Missing chart attribution or measurement geometry");
  expect(
    measurementBox.y + measurementBox.height <= attributionBox.y ||
      measurementBox.x >= attributionBox.x + attributionBox.width,
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("custom-analysis-1440.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.screenshot({
    path: testInfo.outputPath("custom-analysis-1920.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Remove comparison", exact: true })
    .click();
  await page.getByLabel("Filter watchlist", { exact: true }).fill("NVDA");
  await expect(
    page.getByRole("list", { name: "Saved instruments" }).getByRole("listitem"),
  ).toHaveCount(1);
  await page.getByLabel("Filter watchlist", { exact: true }).clear();
  const runs = ResearchRunListSchema.parse(
    await (await page.request.get("/api/v1/research/runs/")).json(),
  );
  const run = runs.items[0];
  expect(run).toBeDefined();
  if (!run)
    throw new Error(
      "Run the terminal suite first to create the saved synthetic evaluation.",
    );
  await page.goto(
    `/app/markets?view=research&run=${run.id}&instrument=${run.instrument_id}`,
  );
  await expect(
    page.getByRole("heading", { name: "Evaluation results", exact: true }),
  ).toBeVisible();
  await expect(chart.locator("canvas").first()).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Verify exact replay", exact: true }),
  ).toBeVisible();
  const separator = page.getByRole("separator", {
    name: "Research panel height",
    exact: true,
  });
  await separator.focus();
  await page.keyboard.press("ArrowUp");
  await expect(separator).toHaveAttribute("aria-valuenow", "420");
  await page.keyboard.press("End");
  const maximum = Number(await separator.getAttribute("aria-valuemax"));
  await expect(separator).toHaveAttribute("aria-valuenow", String(maximum));
  expect(maximum).toBeLessThanOrEqual(600);
  expect((await chart.boundingBox())?.height).toBeGreaterThanOrEqual(170);
  await page.keyboard.press("Home");
  for (let step = 0; step < 10; step++) await page.keyboard.press("ArrowUp");
  await page.screenshot({
    path: testInfo.outputPath("research-dock-1920.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Maximize research panel", exact: true })
    .click();
  await expect(chart).not.toBeVisible();
  await page.getByRole("button", { name: "Walk-forward", exact: true }).click();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  const download = await downloaded;
  expect(download.suggestedFilename()).toContain(run.id);
  const stream = await download.createReadStream();
  let csv = "";
  for await (const chunk of stream) csv += chunk.toString();
  expect(csv).toContain(run.dataset_version);
  expect(csv).toContain("synthetic_fixture");
  expect(csv).toContain("information_cutoff");
  await page.getByRole("tab", { name: "Saved runs", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Saved evaluations", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("tab", { name: "Selected run inspector", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Restore research panel", exact: true })
    .click();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(chart).not.toBeVisible();
  await expect(page.locator(".research-status")).toBeVisible();
  await expect(page.locator(".chart-status")).not.toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("research-mobile-390.png"),
    fullPage: true,
  });
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    axe.violations.map(({ id, nodes }) => ({
      id,
      targets: nodes.map((node) => node.target),
    })),
  ).toEqual([]);
  expect(errors).toEqual([]);
});

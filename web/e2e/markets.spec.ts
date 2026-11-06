import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test } from "@playwright/test";
import { z } from "zod";

import { InstrumentListSchema, MarketResponseSchema, SessionSchema } from "../src/lib/api/schemas";

const LocalCredentialsSchema = z.object({
  username: z.string().trim().min(1),
  password: z.string().min(1),
});

function loadLocalCredentials(): z.infer<typeof LocalCredentialsSchema> {
  const path = resolve(process.cwd(), "../.local/credentials.json");
  if (!existsSync(path)) {
    throw new Error("Missing ignored .local/credentials.json for the authenticated browser test.");
  }
  const source: unknown = JSON.parse(readFileSync(path, "utf8"));
  return LocalCredentialsSchema.parse(source);
}

async function waitForApi(page: import("@playwright/test").Page): Promise<void> {
  await expect
    .poll(
      async () => {
        try {
          const response = await page.request.get("http://127.0.0.1:8000/health/", {
            timeout: 3000,
          });
          return response.status() === 200;
        } catch {
          return false;
        }
      },
      { intervals: [250, 500, 1000, 2000], timeout: 60_000 },
    )
    .toBe(true);
}

function isApiResponse(
  response: import("@playwright/test").Response,
  pathname: string,
  method: string,
): boolean {
  const url = new URL(response.url());
  return url.pathname === pathname && response.request().method() === method;
}

test("signs in and completes the authenticated daily market research path", async ({
  page,
}, testInfo) => {
  test.setTimeout(180_000);
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.emulateMedia({ colorScheme: "light" });
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await waitForApi(page);

  const credentials = loadLocalCredentials();
  await page.goto("/sign-in");
  await expect(page.getByRole("heading", { name: "Sign in to your workspace" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
  await page.getByLabel("Username").fill(credentials.username);
  await page.getByLabel("Password").fill(credentials.password);

  const loginResponsePromise = page.waitForResponse((response) =>
    isApiResponse(response, "/api/v1/session/", "POST"),
  );
  const initialWatchlistResponsePromise = page.waitForResponse((response) =>
    isApiResponse(response, "/api/v1/watchlist/", "GET"),
  );
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.status()).toBe(200);
  expect(loginResponse.request().redirectedFrom()).toBeNull();
  const session = SessionSchema.parse(await loginResponse.json());
  if (!session.authenticated) {
    throw new Error("The dedicated browser-test account was not authenticated.");
  }

  await page.waitForURL(/\/app\/markets\/?$/);
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Watchlist", exact: true })).toBeVisible();

  const initialWatchlistResponse = await initialWatchlistResponsePromise;
  expect(initialWatchlistResponse.status()).toBe(200);
  const initialWatchlist = InstrumentListSchema.parse(await initialWatchlistResponse.json());
  const alreadySavedAapl = initialWatchlist.items.some((item) => item.id === "xnas-aapl");

  let shouldRemoveAapl = false;
  try {
    const searchButton = page.getByRole("button", { name: "Add instrument", exact: true }).first();
    await searchButton.click();
    const search = page.getByRole("combobox", { name: "Search by symbol or company" });
    await search.fill("AAPL");
    const appleOption = page.getByRole("option").filter({ hasText: "AAPL" }).first();
    await expect(appleOption).toBeVisible();
    await search.press("ArrowDown");
    await expect(search).toHaveAttribute("aria-activedescendant", /-option-0$/);

    const barsResponsePromise = alreadySavedAapl
      ? page.request.get("/api/v1/instruments/xnas-aapl/bars/?range=1y&mode=demo")
      : page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname === "/api/v1/instruments/xnas-aapl/bars/" &&
        url.searchParams.get("range") === "1y" &&
        url.searchParams.get("mode") === "demo"
      );
    });
    const watchlistAddPromise = page.waitForResponse((response) =>
      isApiResponse(response, "/api/v1/watchlist/", "POST"),
    );
    shouldRemoveAapl = !alreadySavedAapl;
    await search.press("Enter");

    const [barsResponse, watchlistAddResponse] = await Promise.all([
      barsResponsePromise,
      watchlistAddPromise,
    ]);
    expect(barsResponse.status()).toBe(200);
    expect(watchlistAddResponse.status()).toBeGreaterThanOrEqual(200);
    expect(watchlistAddResponse.status()).toBeLessThan(300);
    const firstRange = MarketResponseSchema.parse(await barsResponse.json());
    expect(firstRange.instrument).toMatchObject({
      id: "xnas-aapl",
      symbol: "AAPL",
      exchange: "XNAS",
      currency: "USD",
    });
    expect(firstRange.bars.length).toBeGreaterThan(100);
    expect(firstRange.indicators.sma20.length).toBeGreaterThan(0);
    expect(firstRange.indicators.sma50.length).toBeGreaterThan(0);
    expect(firstRange.indicators.rsi14.length).toBeGreaterThan(0);
    expect(firstRange.provenance).toMatchObject({
      data_mode: "demo",
      source_id: "cadrisyn-synthetic-v1",
      price_basis: "synthetic",
      delay_seconds: null,
    });
    await expect(page.getByRole("heading", { name: "Apple Inc." })).toBeVisible();
    await expect(page.getByText("Synthetic demonstration dataset", { exact: true }).filter({ visible: true }).first())
      .toBeVisible();
    await expect(page.getByTestId("price-chart").locator("canvas").first()).toBeVisible();

    const aaplWatchlistButton = page.getByRole("button", { name: /AAPL Apple Inc\./ });
    await expect(aaplWatchlistButton).toBeVisible();
    await aaplWatchlistButton.click();
    await expect(page.getByRole("heading", { name: "Apple Inc." })).toBeVisible();
    await expect(page.getByText("Loading daily history")).toHaveCount(0);

    const tableToggle = page.getByRole("button", { name: "Show data table" });
    await tableToggle.click();
    const dataTable = page.getByRole("table", { name: "AAPL daily OHLCV" });
    await expect(dataTable).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Session" })).toBeVisible();
    const latest = firstRange.bars.at(-1);
    expect(latest).toBeDefined();
    if (latest !== undefined) {
      const formattedClose = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(latest.close);
      await expect(dataTable.getByRole("row").nth(1)).toContainText(formattedClose);
    }

    const rangeReload = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname === "/api/v1/instruments/xnas-aapl/bars/" &&
        url.searchParams.get("range") === "3m" &&
        url.searchParams.get("mode") === "demo"
      );
    });
    await page.getByRole("combobox", { name: "Displayed range" }).click();
    await page.getByRole("option", { name: "3 months" }).click();
    const threeMonthResponse = await rangeReload;
    expect(threeMonthResponse.status()).toBe(200);
    const threeMonthData = MarketResponseSchema.parse(await threeMonthResponse.json());
    expect(threeMonthData.bars.length).toBeGreaterThan(30);
    await expect(page.getByText("Daily · 3 months", { exact: true })).toBeVisible();

    await page.getByRole("checkbox", { name: "SMA 20" }).uncheck();
    await page.getByRole("checkbox", { name: "RSI 14" }).uncheck();
    await expect(page.getByRole("checkbox", { name: "SMA 20" })).not.toBeChecked();
    await expect(page.getByRole("checkbox", { name: "RSI 14" })).not.toBeChecked();
    await page.getByRole("checkbox", { name: "SMA 20" }).check();
    await page.getByRole("checkbox", { name: "RSI 14" }).check();
    await page.getByRole("button", { name: "Hide data table" }).click();

    await page.getByRole("combobox", { name: "Data mode" }).click();
    const delayedDataOption = page.getByRole("option", { name: "Delayed data" });
    if (!session.market_data_enabled) {
      await expect(delayedDataOption).toBeDisabled();
    }
    await page.keyboard.press("Escape");

    await page.setViewportSize({ width: 1440, height: 960 });
    const useLightTheme = page.getByRole("button", { name: "Use light theme" });
    if (await useLightTheme.count()) {
      await useLightTheme.click();
    }
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    await page.screenshot({
      path: testInfo.outputPath("markets-light-desktop.png"),
      animations: "disabled",
      fullPage: true,
    });

    const useDarkTheme = page.getByRole("button", { name: "Use dark theme" });
    await useDarkTheme.click();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await expect.poll(async () => page.getByTestId("price-chart").locator("canvas").first().evaluate((canvas) => {
      if (!(canvas instanceof HTMLCanvasElement)) return 1000;
      const context = canvas.getContext("2d");
      if (context === null) return 1000;
      const pixel = context.getImageData(15, 15, 1, 1).data;
      return (pixel[0] ?? 255) + (pixel[1] ?? 255) + (pixel[2] ?? 255);
    })).toBeLessThan(300);
    await page.screenshot({
      path: testInfo.outputPath("markets-dark-desktop.png"),
      animations: "disabled",
      fullPage: true,
    });

    await page.setViewportSize({ width: 390, height: 844 });
    const horizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(horizontalOverflow).toBe(false);
    await expect(page.getByRole("button", { name: "Open watchlist and instrument search" }))
      .toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath("markets-dark-mobile.png"),
      animations: "disabled",
      fullPage: true,
    });

    const useLightMobileTheme = page.getByRole("button", { name: "Use light theme" });
    await useLightMobileTheme.click();
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    await page.screenshot({
      path: testInfo.outputPath("markets-light-mobile.png"),
      animations: "disabled",
      fullPage: true,
    });

    await page.getByRole("button", { name: "Open watchlist and instrument search" }).click();
    await expect(page.getByRole("dialog", { name: "Watchlist and instrument search" }))
      .toBeVisible();
    await expect(page.getByRole("button", { name: "Close watchlist" })).toBeVisible();
    const duplicateIds = await page.locator("[id]").evaluateAll((nodes) => {
      const counts = new Map<string, number>();
      for (const node of nodes) {
        const id = node.getAttribute("id");
        if (id !== null) {
          counts.set(id, (counts.get(id) ?? 0) + 1);
        }
      }
      return [...counts].filter(([, count]) => count > 1).map(([id]) => id);
    });
    expect(duplicateIds).toEqual([]);
    await expect(page.getByRole("button", { name: "Close watchlist" })).toBeInViewport();
    await page.getByRole("button", { name: "Close watchlist" }).click();
    await expect(page.getByRole("dialog", { name: "Watchlist and instrument search" }))
      .toHaveCount(0);

    for (const width of [320, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 960 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
    }

    await page.route("**/api/v1/instruments/*/bars/**", (route) => route.fulfill({
      status: 503, contentType: "application/json",
      body: JSON.stringify({code: "market_data_unavailable", message: "Data source unavailable in browser fault test.", field_errors: {}, request_id: "browser-fault-test"}),
    }));
    await page.getByRole("combobox", { name: "Displayed range" }).click();
    await page.getByRole("option", { name: "1 month", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Daily history unavailable" })).toBeVisible();
    await expect(page.getByTestId("price-chart")).toHaveCount(0);
    await page.unroute("**/api/v1/instruments/*/bars/**");
    await page.getByRole("button", { name: "Retry", exact: true }).click();
    await expect(page.getByTestId("price-chart").locator("canvas").first()).toBeVisible();

    await page.goto("/data");
    await expect(page.getByRole("heading", { name: "Market data" })).toBeVisible();
    await expect(page.getByText("not observed market prices", { exact: false })).toBeVisible();
    await page.goto("/methodology");
    await expect(page.getByRole("heading", { name: "Methodology" })).toBeVisible();
    await expect(page.getByText("does not publish an ML forecast", { exact: false })).toBeVisible();
    expect(pageErrors).toEqual([]);
  } finally {
    if (shouldRemoveAapl) {
      const cleanupResponse = await page.request.delete(
        `${testInfo.project.use.baseURL ?? "http://127.0.0.1:3000"}/api/v1/watchlist/xnas-aapl/`,
        { headers: { "X-CSRFToken": session.csrf_token } },
      );
      expect(cleanupResponse.status()).toBe(204);
    }
  }
  await page.goto("/app/markets");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sign in to your workspace" })).toBeVisible();
});

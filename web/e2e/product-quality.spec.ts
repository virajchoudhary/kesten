import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";
import { fixturePath } from "./fixtures";
import { SessionSchema } from "../src/lib/api/schemas";
import {
  ResearchRunListSchema,
  ResearchRunSchema,
  type ResearchRun,
} from "../src/features/research/research-schemas";

async function authenticate(page: Page): Promise<void> {
  const session = SessionSchema.parse(
    await (await page.request.get("/api/v1/session/")).json(),
  );
  const response = await page.request.post("/api/v1/session/", {
    data: JSON.parse(readFileSync(fixturePath("credentials.json"), "utf8")),
    headers: { "X-CSRFToken": session.csrf_token },
  });
  expect(response.status()).toBe(200);
}

test("symbol selection resets the next search", async ({ page }) => {
  await authenticate(page);
  await page.goto("/app/markets?instrument=xnas-aapl");
  await page.getByRole("button", { name: /AAPL · Search/u }).click();
  await page
    .getByRole("combobox", { name: "Search by symbol or company" })
    .fill("MSFT");
  await page.getByRole("option").filter({ hasText: "Microsoft" }).click();
  await expect(page.getByRole("heading", { name: /Microsoft/u })).toBeVisible();
  await page.getByRole("button", { name: /MSFT · Search/u }).click();
  await expect(
    page.getByRole("combobox", { name: "Search by symbol or company" }),
  ).toHaveValue("");
  await expect(page.getByRole("option")).toHaveCount(0);
});

test("mobile settings retain chart context and account navigation stays consistent", async ({
  page,
}, testInfo) => {
  await authenticate(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/markets");
  const chart = page.getByTestId("price-chart");
  await expect(chart).toHaveAttribute("data-chart-state", "ready");
  await page
    .getByRole("button", { name: "Chart settings", exact: true })
    .click();
  const panel = page.getByRole("complementary", {
    name: "Chart settings",
    exact: true,
  });
  const panelBounds = await panel.boundingBox();
  const chartBounds = await chart.boundingBox();
  if (!panelBounds || !chartBounds)
    throw new Error("Missing live chart-panel geometry");
  expect(panelBounds.height).toBeLessThan(chartBounds.height * 0.75);
  await expect(page.getByLabel("Price scale", { exact: true })).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("mobile-settings-context.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Close chart panel", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Chart settings", exact: true }),
  ).toBeFocused();
  await page.getByRole("link", { name: "Account", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Account security", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Research", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Account", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  await expect(
    page.getByRole("button", { name: "Sign out", exact: true }),
  ).toBeVisible();
  const theme = page.getByRole("button", { name: /Use (dark|light) theme/u });
  const nextTheme = await theme.getAttribute("aria-label");
  await theme.click();
  await expect(page.locator("html")).toHaveClass(
    nextTheme === "Use dark theme" ? /dark/u : /^(?!.*dark).*$/u,
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("mobile-account-navigation.png"),
    fullPage: true,
  });
});

test("mobile history opens the exact result in view", async ({
  page,
}, testInfo) => {
  await authenticate(page);
  const saved = ResearchRunListSchema.parse(
    await (await page.request.get("/api/v1/research/runs/")).json(),
  );
  expect(saved.items.length).toBeGreaterThan(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/research");
  const history = page.getByRole("region", {
    name: "Saved evaluations",
    exact: true,
  });
  const open = history.getByRole("link", { name: /^Open /u }).first();
  await expect(open).toBeVisible();
  const href = await open.getAttribute("href");
  if (!href) throw new Error("Missing saved research link");
  const id = new URL(href, "http://127.0.0.1:3000").searchParams.get("run");
  await open.click();
  await expect(page).toHaveURL(new RegExp(`run=${id}`, "u"));
  await expect(
    page.getByRole("heading", { name: "Evaluation results", exact: true }),
  ).toBeInViewport();
  await expect(
    page.getByRole("heading", { name: "Research analytics", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Research sections", exact: true })
    .getByRole("link", { name: "Saved runs", exact: true })
    .click();
  await expect(history).toBeInViewport();
  await page.screenshot({
    path: testInfo.outputPath("mobile-history-navigation.png"),
    fullPage: false,
  });
});

test("a server-accepted evaluation completes after switching dock tabs", async ({
  page,
}) => {
  await authenticate(page);
  let releaseResponse = () => {};
  const responseGate = new Promise<void>((resolve) => {
    releaseResponse = resolve;
  });
  let reportAccepted: (run: ResearchRun) => void = () => {};
  const acceptedRun = new Promise<ResearchRun>((resolve) => {
    reportAccepted = resolve;
  });
  let submissions = 0;
  const transportErrors: string[] = [];
  await page.route("**/api/v1/research/runs/", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    submissions += 1;
    const response = await route.fetch();
    expect(response.status()).toBeGreaterThanOrEqual(200);
    expect(response.status()).toBeLessThan(300);
    reportAccepted(ResearchRunSchema.parse(await response.json()));
    await responseGate;
    try {
      await route.fulfill({ response });
    } catch (error: unknown) {
      transportErrors.push(String(error));
    }
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/app/markets?view=research&instrument=xnys-jpm");
  await page.getByRole("tab", { name: "New evaluation", exact: true }).click();
  await page
    .getByRole("button", { name: "Run evaluation", exact: true })
    .click();
  const run = await acceptedRun;
  await page.getByRole("tab", { name: "Saved runs", exact: true }).click();
  releaseResponse();
  await expect(page).toHaveURL(new RegExp(`run=${run.id}`, "u"));
  await expect(
    page
      .getByRole("region", { name: "Integrated research", exact: true })
      .getByRole("heading", { name: "Evaluation results", exact: true }),
  ).toBeVisible();
  const saved = ResearchRunSchema.parse(
    await (await page.request.get(`/api/v1/research/runs/${run.id}/`)).json(),
  );
  expect(saved.id).toBe(run.id);
  expect(saved.dataset_version).toBe(run.dataset_version);
  expect(submissions).toBe(1);
  expect(transportErrors).toEqual([]);
});

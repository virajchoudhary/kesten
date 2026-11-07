import { readFileSync } from "node:fs";
import { fixturePath } from "./fixtures";

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { z } from "zod";

import {
  ResearchDatasetListResponseSchema,
  ResearchRunSchema,
  ResearchRunListSchema,
} from "../src/features/research/research-schemas";
import { SessionSchema } from "../src/lib/api/schemas";

const CredentialsSchema = z.strictObject({
  username: z.string().min(1),
  password: z.string().min(1),
});

async function authenticate(page: Page): Promise<string> {
  const credentials = CredentialsSchema.parse(
    JSON.parse(
      readFileSync(
        fixturePath("credentials.json"),
        "utf8",
      ),
    ),
  );
  const anonymous = SessionSchema.parse(
    await (await page.request.get("/api/v1/session/")).json(),
  );
  const response = await page.request.post("/api/v1/session/", {
    data: credentials,
    headers: { "X-CSRFToken": anonymous.csrf_token },
  });
  expect(response.status()).toBe(200);
  const session = SessionSchema.parse(await response.json());
  expect(session.authenticated).toBe(true);
  return session.csrf_token;
}

async function assertAccessible(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    results.violations.map(({ id, nodes }) => ({
      id,
      targets: nodes.map(({ target, failureSummary }) => ({
        target,
        failureSummary,
      })),
    })),
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}

test("public pages retain readable light and dark layouts on narrow screens", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 375, height: 812 });
  for (const colorScheme of ["light", "dark"] as const) {
    await page.emulateMedia({ colorScheme });
    for (const route of ["/", "/data", "/methodology", "/sign-in"]) {
      await page.goto(route);
      await expect(page.locator("html")).toHaveClass(
        new RegExp(`\\b${colorScheme}\\b`, "u"),
      );
      await expect(page.getByRole("main")).toBeVisible();
      await assertAccessible(page);
    }
  }
});

test("research inspection, comparison, replay and exact export use saved identities", async ({
  page,
}, testInfo) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const csrfToken = await authenticate(page);
  const datasetsResponse = await page.request.get("/api/v1/research/datasets/");
  expect(datasetsResponse.status()).toBe(200);
  const datasets = ResearchDatasetListResponseSchema.parse(
    await datasetsResponse.json(),
  );
  const dataset = datasets.items.find(
    (item) => item.data_kind === "synthetic_fixture",
  );
  if (!dataset)
    throw new Error(
      "Prepare the explicitly synthetic research browser fixture first.",
    );
  const datasetId = dataset.id;

  await page.goto("/app/research");
  await page
    .getByRole("combobox", { name: "Private research dataset" })
    .click();
  await page
    .getByRole("option", { name: new RegExp(dataset.name, "u") })
    .click();
  await page.getByRole("radio", { name: "5 next sessions" }).check();
  const created = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/v1/research/runs/" &&
      response.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Run evaluation", exact: true })
    .click();
  const response = await created;
  expect(response.status()).toBe(201);
  const run = ResearchRunSchema.parse(await response.json());
  expect(run.result.empirical_performance_established).toBe(false);
  await expect(
    page.getByRole("heading", { name: dataset.name, exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Walk-forward", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Evaluation period" })
    .selectOption("test");
  const slider = page.getByRole("slider", { name: "Inspect chart session" });
  await slider.focus();
  const before = await slider.inputValue();
  await slider.press("ArrowLeft");
  expect(await slider.inputValue()).not.toBe(before);
  await expect(slider).toHaveAttribute("aria-valuetext", /test/u);
  await page.getByRole("button", { name: "Errors", exact: true }).click();
  await expect(
    page.getByRole("img", { name: /Walk-forward forecast errors/u }),
  ).toBeVisible();
  await page.getByText("Exact evaluation values", { exact: true }).click();
  await expect(
    page.getByRole("table", { name: /Exact values in the current chart/u }),
  ).toBeVisible();
  expect(await page.locator("svg polyline").count()).toBeLessThanOrEqual(3);
  await assertAccessible(page);

  const replayResponse = page.waitForResponse(
    (item) =>
      new URL(item.url()).pathname ===
      `/api/v1/research/runs/${run.id}/replay/`,
  );
  await page
    .getByRole("button", { name: "Verify exact replay", exact: true })
    .click();
  expect((await replayResponse).status()).toBe(200);
  await expect(page.getByText("Replay PASS", { exact: true })).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download synthetic run JSON", exact: true })
    .click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain(run.id);
  const downloadedPath = await download.path();
  if (!downloadedPath) throw new Error("No browser download was produced.");
  const exported = await page.request.get(
    `/api/v1/research/runs/${run.id}/export/`,
  );
  expect(exported.status()).toBe(200);
  expect(readFileSync(downloadedPath, "utf8")).toBe(await exported.text());

  async function createReference(horizon: 1 | 5) {
    const created = await page.request.post("/api/v1/research/runs/", {
      data: {
        dataset_id: datasetId,
        horizon_sessions: horizon,
        idempotency_key: crypto.randomUUID(),
      },
      headers: { "X-CSRFToken": csrfToken },
    });
    expect(created.status()).toBe(201);
    return ResearchRunSchema.parse(await created.json());
  }
  const compatible = await createReference(5);
  await page.goto(`/app/research?run=${run.id}&compare=${compatible.id}`);
  await expect(
    page.getByText(/These runs use compatible evaluation conditions/u),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText(/These runs use compatible evaluation conditions/u),
  ).toBeVisible();
  const incompatible = await createReference(1);
  await page.goto(`/app/research?run=${run.id}&compare=${incompatible.id}`);
  await expect(
    page.getByText("These runs are not comparable.", { exact: true }),
  ).toBeVisible();

  await page.goto(`/app/research?run=${run.id}`);
  for (const colorScheme of ["light", "dark"] as const) {
    await page.emulateMedia({ colorScheme });
    await expect(page.locator("html")).toHaveClass(
      new RegExp(`\\b${colorScheme}\\b`, "u"),
    );
    for (const width of [1440, 375]) {
      await page.setViewportSize({ width, height: width === 375 ? 812 : 1000 });
      await assertAccessible(page);
      await page.screenshot({
        path: testInfo.outputPath(`research-${width}-${colorScheme}.png`),
      });
    }
  }
  for (const route of ["/app/markets", "/app/account"]) {
    await page.goto(route);
    await assertAccessible(page);
  }
  await page.goto("/app/research?instrument=xnas-aapl");
  await expect(
    page.getByText(/No private research dataset is available for xnas-aapl/u),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Run evaluation", exact: true }),
  ).toHaveCount(0);
  expect(pageErrors).toEqual([]);
});

test("account changes in another tab clear private research before a second account loads", async ({
  page,
  context,
}) => {
  const credentials = CredentialsSchema.parse(
    JSON.parse(
      readFileSync(
        fixturePath("research-e2e-isolation.json"),
        "utf8",
      ),
    ),
  );
  await authenticate(page);
  const history = ResearchRunListSchema.parse(await (
    await page.request.get("/api/v1/research/runs/")
  ).json());
  const run = ResearchRunSchema.parse(history.items[0]);
  await page.goto(`/app/research?run=${run.id}`);
  await expect(
    page.getByRole("heading", { name: run.name, exact: true }),
  ).toBeVisible();
  const otherTab = await context.newPage();
  await otherTab.goto("/app/research");
  await otherTab.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/sign-in\/?$/u);
  await expect(
    page.getByRole("heading", { name: run.name, exact: true }),
  ).toHaveCount(0);
  await otherTab.getByLabel("Username").fill(credentials.username);
  await otherTab.getByLabel("Password").fill(credentials.password);
  await otherTab.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(otherTab).toHaveURL(/\/app\/markets\/?$/u);
  await expect(page.getByText(`You are signed in as ${credentials.username}.`, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Open Markets" }).click();
  await expect(page).toHaveURL(/\/app\/markets\/?$/u);
  await page.goto(`/app/research?run=${run.id}`);
  await expect(
    page.getByRole("heading", { name: run.name, exact: true }),
  ).toHaveCount(0);
  const forbidden = await page.request.get(`/api/v1/research/runs/${run.id}/`);
  expect(forbidden.status()).toBe(404);
  const datasets = ResearchDatasetListResponseSchema.parse(
    await (await page.request.get("/api/v1/research/datasets/")).json(),
  );
  expect(datasets.items).toEqual([]);
});

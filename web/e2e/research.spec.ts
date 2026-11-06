import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test } from "@playwright/test";
import { z } from "zod";

import { SessionSchema } from "../src/lib/api/schemas";
import {
  ResearchDatasetListResponseSchema,
  ResearchRunListSchema,
  ResearchRunRequestSchema,
  ResearchRunSchema,
} from "../src/features/research/research-schemas";
import {
  formatSessionDate,
  formatUtcTimestamp,
} from "../src/features/research/research-formatters";

const LocalCredentialsSchema = z.strictObject({
  username: z.string().trim().min(1),
  password: z.string().min(1),
});

function loadLocalCredentials(): z.infer<typeof LocalCredentialsSchema> {
  const path = resolve(process.cwd(), "../.local/credentials.json");
  if (!existsSync(path)) {
    throw new Error("Missing ignored .local/credentials.json for the authenticated browser test.");
  }
  const contents: unknown = JSON.parse(readFileSync(path, "utf8"));
  return LocalCredentialsSchema.parse(contents);
}

async function waitForApi(page: import("@playwright/test").Page): Promise<void> {
  await expect
    .poll(
      async () => {
        try {
          const health = process.env.PLAYWRIGHT_EXTERNAL_SERVER === "1"
            ? new URL("/api/v1/session/", process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:8080").href
            : "http://127.0.0.1:8000/health/";
          const response = await page.request.get(health, { timeout: 3000 });
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

test("runs and reloads a private synthetic research evaluation against the real API", async ({ page }) => {
  test.setTimeout(180_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ colorScheme: "light" });
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await waitForApi(page);

  const credentials = loadLocalCredentials();
  await page.goto("/sign-in");
  await page.getByLabel("Username").fill(credentials.username);
  await page.getByLabel("Password").fill(credentials.password);

  const loginResponsePromise = page.waitForResponse((response) =>
    isApiResponse(response, "/api/v1/session/", "POST"),
  );
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.status()).toBe(200);
  const session = SessionSchema.parse(await loginResponse.json());
  if (!session.authenticated) {
    throw new Error("The dedicated browser-test account was not authenticated.");
  }
  await page.waitForURL(/\/app\/markets\/?$/u);
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  const datasetsResponsePromise = page.waitForResponse((response) =>
    isApiResponse(response, "/api/v1/research/datasets/", "GET"),
  );
  const runsResponsePromise = page.waitForResponse((response) =>
    isApiResponse(response, "/api/v1/research/runs/", "GET"),
  );
  await page.getByRole("link", { name: "Research", exact: true }).click();
  await page.waitForURL(/\/app\/research\/?$/u);
  const [datasetsResponse, runsResponse] = await Promise.all([
    datasetsResponsePromise,
    runsResponsePromise,
  ]);
  expect(datasetsResponse.status()).toBe(200);
  expect(runsResponse.status()).toBe(200);
  const datasets = ResearchDatasetListResponseSchema.parse(await datasetsResponse.json());
  const initialRuns = ResearchRunListSchema.parse(await runsResponse.json());
  const fixture = datasets.items.find((dataset) => dataset.name === "Synthetic pipeline fixture");
  expect(fixture).toBeDefined();
  expect(fixture?.data_kind).toBe("synthetic_fixture");
  expect(initialRuns.items.every((run) => run.status === "succeeded")).toBe(true);

  const datasetControl = page.getByRole("combobox", { name: "Private research dataset" });
  await datasetControl.click();
  await page.getByRole("option", { name: /Synthetic pipeline fixture/u }).click();
  await page.getByRole("radio", { name: "5 next sessions" }).check();
  await expect(page.getByText("No empirical forecasting performance established.", { exact: true }))
    .toBeVisible();
  await expect(page.getByText("SYNTHETIC FIXTURE", { exact: true }).first()).toBeVisible();

  const createResponsePromise = page.waitForResponse((response) =>
    isApiResponse(response, "/api/v1/research/runs/", "POST"),
  );
  await page.getByRole("button", { name: "Run evaluation", exact: true }).click();
  const createResponse = await createResponsePromise;
  expect(createResponse.status()).toBe(201);
  const requestPayload: unknown = createResponse.request().postDataJSON();
  const sentRequest = ResearchRunRequestSchema.parse(requestPayload);
  expect(sentRequest.dataset_id).toBe(fixture?.id);
  expect(sentRequest.horizon_sessions).toBe(5);

  const createdRun = ResearchRunSchema.parse(await createResponse.json());
  expect(createdRun.status).toBe("succeeded");
  expect(createdRun.data_kind).toBe("synthetic_fixture");
  expect(createdRun.result.empirical_performance_established).toBe(false);
  expect(createdRun.result.evidence_kind).toBe("synthetic_pipeline_check");
  expect(createdRun.completed_at).toBeTruthy();

  await page.waitForURL(new RegExp(`/app/research\\?run=${createdRun.id}$`, "u"));
  await expect(page.getByRole("heading", { name: "Synthetic pipeline fixture", exact: true }))
    .toBeVisible();
  await expect(page.getByRole("img", { name: "Dataset history and forecast paths" }))
    .toBeVisible();
  const axisLabels = await page.getByRole("region", { name: "Dataset history and forecast", exact: true })
    .locator("svg text").evaluateAll((nodes) => nodes.map((node) => {
      const bounds = node.getBoundingClientRect();
      return { text: node.textContent?.trim() ?? "", left: bounds.left, right: bounds.right, top: bounds.top, bottom: bounds.bottom };
    }));
  type LabelBounds = Omit<(typeof axisLabels)[number], "text">;
  const overlap = (a: LabelBounds, b: LabelBounds): boolean =>
    a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
  const unitsLabel = axisLabels.find((label) => label.text === "USD per initial share");
  if (!unitsLabel) throw new Error("The chart must show its price-axis units.");
  const prices = axisLabels.filter((label) => label.text.startsWith("$"));
  const dates = axisLabels.filter((label) => /^[A-Za-z]{3} \d{1,2}$/u.test(label.text));
  expect(prices).toHaveLength(4);
  expect(dates).toHaveLength(2);
  expect(prices.some((label) => overlap(label, unitsLabel))).toBe(false);
  expect(dates.some((label, index) => dates.slice(index + 1).some((other) => overlap(label, other)))).toBe(false);
  await expect(page.getByText("Dataset history", { exact: true }).first()).toBeVisible();
  await expect(
    page.getByText("Historical log mean · geometric drift path", { exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Validation and test metrics" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Direction confusion counts" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Data and run provenance" })).toBeVisible();
  await expect(page.getByText(createdRun.result.protocol.protocol_sha256)).toBeVisible();
  await expect(page.getByRole("region", { name: "Data and run provenance" }).getByText(formatSessionDate(createdRun.result.forecast.origin), { exact: false }).first())
    .toBeVisible();
  await expect(page.getByRole("region", { name: "Data and run provenance" }).getByText(formatUtcTimestamp(createdRun.completed_at), { exact: false }).first())
    .toBeVisible();
  await expect(page.getByText(fixture?.source_id ?? "", { exact: true })).toBeVisible();
  await expect(page.getByText(fixture?.license_reference ?? "", { exact: true })).toBeVisible();
  await expect(page.getByText(fixture?.availability_evidence ?? "", { exact: true })).toBeVisible();
  await expect(page.getByText(`${createdRun.result.target.units}; return convention: ${createdRun.result.target.return_convention}.`, { exact: true })).toBeVisible();
  expect(await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )).toBe(true);

  await page.reload();
  await expect(page.getByRole("heading", { name: "Synthetic pipeline fixture", exact: true }))
    .toBeVisible();
  await expect(page.getByRole("link", { name: /Synthetic pipeline fixture/u }).first())
    .toHaveAttribute("aria-current", "page");
  await expect(page.getByText("Synthetic pipeline check only. No empirical forecasting performance established.", { exact: true }))
    .toBeVisible();

  await page.setViewportSize({ width: 1440, height: 960 });
  await expect(page.getByRole("table", { name: /Validation and test metrics/u })).toBeVisible();
  expect(pageErrors).toEqual([]);
});

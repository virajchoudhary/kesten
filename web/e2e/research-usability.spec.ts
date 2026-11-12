import { readFileSync, writeFileSync } from "node:fs";

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { z } from "zod";

import { fixturePath } from "./fixtures";
import {
  ResearchDatasetListResponseSchema, ResearchDatasetProvenanceSchema, ResearchRunSchema,
} from "../src/features/research/research-schemas";
import { SessionSchema } from "../src/lib/api/schemas";

test("private dataset discovery, source inspection and baseline interpretation remain exploratory", async ({ page, browser }, testInfo) => {
  test.setTimeout(180_000);
  await page.setViewportSize({ width: 1440, height: 900 });
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const credentials = z.strictObject({ username: z.string(), password: z.string() }).parse(JSON.parse(readFileSync(fixturePath("credentials.json"), "utf8")));
  const anonymous = SessionSchema.parse(await (await page.request.get("/api/v1/session/")).json());
  const login = await page.request.post("/api/v1/session/", { data: credentials, headers: { "X-CSRFToken": anonymous.csrf_token } });
  expect(login.status()).toBe(200);
  const datasets = ResearchDatasetListResponseSchema.parse(await (await page.request.get("/api/v1/research/datasets/")).json());
  const synthetic = datasets.items.filter((item) => item.data_kind === "synthetic_fixture");
  let dataset = synthetic[0];
  if (!dataset) throw new Error("Prepare the account-private synthetic research fixture first.");
  let evidence = ResearchDatasetProvenanceSchema.parse(await (await page.request.get(`/api/v1/research/datasets/${dataset.id}/provenance/`)).json());
  for (const candidate of synthetic.slice(0, 10)) {
    const candidateEvidence = ResearchDatasetProvenanceSchema.parse(await (await page.request.get(`/api/v1/research/datasets/${candidate.id}/provenance/`)).json());
    if (candidateEvidence.intake.status === "verified") { dataset = candidate; evidence = candidateEvidence; break; }
  }
  await page.goto("/app/research");
  await expect(page.getByRole("heading", { name: "Exploratory research", exact: true })).toBeVisible();
  const search = page.getByRole("searchbox", { name: "Find a private dataset" });
  await search.fill("no-such-private-dataset");
  await expect(page.getByText("No matching datasets in the available private list.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Run evaluation", exact: true })).toBeDisabled();
  await search.fill(dataset.name);
  await page.getByRole("combobox", { name: "Private research dataset" }).click();
  await page.getByRole("option").filter({ hasText: dataset.name }).click();
  await expect(page.getByText(`${dataset.observation_count} observations · ${dataset.calendar}`, { exact: true })).toBeVisible();
  await expect(page.getByText(`Source: ${dataset.source_id}`, { exact: true })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("after-setup-desktop.png"), fullPage: true });
  await page.getByText("Inspect selected dataset provenance", { exact: true }).click();
  await expect(page.getByText(/Point-in-time qualification has not been independently verified/u)).toBeVisible();
  expect(evidence.independently_verified_source).toBe(false);
  if (evidence.intake.status === "verified") {
    await expect(page.getByText("Archived bytes match the intake receipt", { exact: true })).toBeVisible();
    await expect(page.getByText(evidence.intake.receipt_version, { exact: true })).toBeVisible();
    await expect(page.getByText("Operator-declared permissions", { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText(/No archived intake receipt/u)).toBeVisible();
  }
  await page.screenshot({ path: testInfo.outputPath("after-provenance-desktop.png"), fullPage: true });
  await page.getByText("Inspect selected dataset provenance", { exact: true }).click();
  await page.getByRole("radio", { name: "5 next sessions" }).check();
  const created = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/v1/research/runs/" && response.request().method() === "POST");
  await page.getByRole("button", { name: "Run evaluation", exact: true }).click();
  const response = await created;
  expect(response.status()).toBe(201);
  const run = ResearchRunSchema.parse(await response.json());
  expect(run.dataset_id).toBe(dataset.id);
  expect(run.dataset_version).toBe(dataset.version);
  expect(run.result.empirical_performance_established).toBe(false);
  const benchmark = page.getByRole("region", { name: "Baseline error comparison", exact: true });
  await page.getByRole("link", { name: "Compare baseline errors", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Baseline comparison", exact: true })).toBeInViewport();
  await expect(benchmark).toBeVisible();
  const row = benchmark.getByRole("row", { name: /Historical log mean/u });
  const testMetrics = run.result.evaluation.find((item) => item.model_id === "historical_log_mean" && item.partition === "test");
  if (!testMetrics) throw new Error("The saved result lacks its fixed test comparison.");
  await expect(row.locator("data").last()).toHaveAttribute("value", String(testMetrics.mae_difference_vs_last_close));
  await page.getByRole("group", { name: "Baseline comparison period" }).getByRole("button", { name: "Validation", exact: true }).click();
  await expect(benchmark.getByRole("table", { name: /validation errors by model/u })).toBeVisible();
  await page.getByText("How to read these errors", { exact: true }).click();
  await expect(page.getByText(/Five-session targets overlap/u)).toBeVisible();
  await page.getByRole("button", { name: "Verify exact replay", exact: true }).click();
  await expect(page.getByText("Replay PASS", { exact: true })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("after-results-desktop.png"), fullPage: true });
  for (const viewport of [{ width: 1920, height: 1080, name: "wide" }, { width: 768, height: 1024, name: "tablet" }]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`after-results-${viewport.name}.png`), fullPage: true });
  }
  await page.addInitScript(() => localStorage.setItem("cadrisyn-theme", "system"));
  for (const theme of ["dark", "light"] as const) {
    await page.emulateMedia({ colorScheme: theme });
    await page.setViewportSize({ width: 375, height: 812 });
    await page.reload();
    await expect(page.getByRole("heading", { name: dataset.name, exact: true })).toBeVisible();
    await expect(page.locator("html")).toHaveClass(new RegExp(`\\b${theme}\\b`, "u"));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(accessibility.violations.map(({ id, nodes }) => ({ id, targets: nodes.map((node) => node.target) }))).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`after-results-mobile-${theme}.png`), fullPage: true });
    await page.getByRole("link", { name: "Compare baseline errors", exact: true }).click();
    const baselineHeading = page.getByRole("heading", { name: "Baseline comparison", exact: true });
    await expect(baselineHeading).toBeInViewport();
    const headingBox = await baselineHeading.boundingBox();
    const navigationBox = await page.getByRole("navigation", { name: "Research sections" }).boundingBox();
    if (!headingBox || !navigationBox) throw new Error("Research navigation or baseline heading is missing.");
    expect(headingBox.y).toBeGreaterThanOrEqual(navigationBox.y + navigationBox.height);
    await page.screenshot({ path: testInfo.outputPath(`after-baselines-mobile-${theme}-viewport.png`) });
  }
  expect(pageErrors).toEqual([]);
  writeFileSync(testInfo.outputPath("research-usability.json"), JSON.stringify({
    result: "PASS", scope: "Synthetic browser qualification, not empirical research",
    browser: browser.version(), dataset_id: run.dataset_id, dataset_version: run.dataset_version,
    run_id: run.id, horizon_sessions: run.horizon_sessions, source_receipt_status: evidence.intake.status,
    independently_verified_source: evidence.independently_verified_source,
    empirical_performance_established: run.result.empirical_performance_established,
    overflow_checks: ["1920x1080", "768x1024", "375x812 dark", "375x812 light"],
    mobile_accessibility_violations: 0, page_errors: pageErrors,
  }, null, 2));
});

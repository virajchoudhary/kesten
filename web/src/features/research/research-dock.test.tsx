import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

import {
  researchWorkspaceHref,
  type ResearchWorkspaceQuery,
} from "./research-navigation";
import {
  researchDatasetFixture,
  researchExportFixture,
  researchHistoryItemFixture,
  researchRunFixture,
} from "./research-test-fixtures";
import type { ResearchRun, ResearchRunRequest } from "./research-schemas";
import { ResearchDock } from "./research-dock";

const api = vi.hoisted(() => ({
  getResearchDatasets: vi.fn(),
  getResearchRun: vi.fn(),
  getResearchHistory: vi.fn(),
  compareResearchRuns: vi.fn(),
  createResearchRun: vi.fn(),
  verifyResearchReplay: vi.fn(),
  getResearchExport: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: api.replace }),
}));

vi.mock("@/features/session/session-provider", () => ({
  useSession: () => ({ refresh: api.refresh }),
}));

vi.mock("./research-api", () => ({
  getResearchDatasets: api.getResearchDatasets,
  getResearchRun: api.getResearchRun,
  getResearchHistory: api.getResearchHistory,
  compareResearchRuns: api.compareResearchRuns,
  createResearchRun: api.createResearchRun,
  verifyResearchReplay: api.verifyResearchReplay,
  getResearchExport: api.getResearchExport,
}));

const RUN_ID = "22222222-2222-4222-8222-222222222222";
const SECOND_RUN_ID = "44444444-4444-4444-8444-444444444444";
const CREATED_RUN_ID = "66666666-6666-4666-8666-666666666666";

function query(
  overrides: Partial<ResearchWorkspaceQuery> = {},
): ResearchWorkspaceQuery {
  return {
    requestedRunId: RUN_ID,
    requestedCompareId: null,
    requestedInstrumentId: "xnas-aapl",
    focusModel: "historical_log_mean",
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  vi.clearAllMocks();
  const dataset = researchDatasetFixture();
  api.getResearchDatasets.mockResolvedValue({ items: [dataset] });
  api.getResearchRun.mockImplementation((runId: string) =>
    Promise.resolve(
      researchRunFixture({
        id: runId,
        name: runId === RUN_ID ? "Saved run" : "Compared run",
      }),
    ),
  );
  api.getResearchHistory.mockResolvedValue({
    items: [],
    total: 0,
    offset: 0,
    limit: 20,
  });
  api.compareResearchRuns.mockImplementation(
    (leftId: string, rightId: string) =>
      Promise.resolve({
        left_id: leftId,
        right_id: rightId,
        compatible: true,
        reasons: [],
      }),
  );
  api.createResearchRun.mockResolvedValue(
    researchRunFixture({ id: CREATED_RUN_ID, name: "Created run" }),
  );
  api.verifyResearchReplay.mockImplementation((runId: string) =>
    Promise.resolve({
      run_id: runId,
      result: "PASS",
      dataset_matches: true,
      engine_matches: true,
      dependency_lock_matches: true,
      runtime_versions_match: true,
      result_matches: true,
      result_sha256: "a".repeat(64),
    }),
  );
  api.getResearchExport.mockImplementation((runId: string) => {
    const exported = researchExportFixture(
      researchRunFixture({ id: runId, name: "Exported run" }),
    );
    return Promise.resolve({
      data: exported,
      source: JSON.stringify(exported),
    });
  });
});

describe("ResearchDock", () => {
  it("shows saved identity, provenance, forecast, metrics, mismatch and replay", async () => {
    const user = userEvent.setup();
    const activeInstrument = "xnas-msft";
    const comparisonId = SECOND_RUN_ID;
    render(
      <ResearchDock
        csrfToken="fixture-csrf"
        query={query({
          requestedCompareId: comparisonId,
          requestedInstrumentId: activeInstrument,
          focusModel: "last_close",
        })}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Saved run" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Evaluation results" }),
    ).toBeVisible();
    expect(
      screen
        .getAllByRole("status")
        .some(
          (element) =>
            element.textContent ===
            `Active chart: ${activeInstrument}. This saved run belongs to xnas-aapl.`,
        ),
    ).toBe(true);
    expect(
      screen.getByText(
        "Synthetic pipeline check only. No empirical forecasting performance established.",
      ),
    ).toBeVisible();
    expect(screen.getByText("Target")).toBeVisible();
    expect(screen.getByText("Origin")).toBeVisible();
    expect(screen.getByText("Information cutoff")).toBeVisible();
    expect(screen.getByText("1 next scheduled session")).toBeVisible();
    expect(
      screen.getAllByText(
        `${researchDatasetFixture().id} · ${researchDatasetFixture().version}`,
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("synthetic-fixture-v1").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByRole("heading", { name: "Run comparison" }),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Walk-forward" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Verify exact replay" }),
    ).toBeVisible();

    const fullResearchHref = researchWorkspaceHref({
      embedded: false,
      runId: RUN_ID,
      compareId: comparisonId,
      instrumentId: activeInstrument,
      focusModel: "last_close",
    });
    expect(screen.getByRole("link", { name: "Full research" })).toHaveAttribute(
      "href",
      fullResearchHref,
    );

    await user.click(
      screen.getByRole("button", { name: "Verify exact replay" }),
    );
    expect(
      await screen.findByLabelText("Exact replay verification"),
    ).toBeVisible();
    expect(api.verifyResearchReplay).toHaveBeenCalledWith(
      RUN_ID,
      "fixture-csrf",
      expect.any(AbortSignal),
    );
  });

  it("keeps compact history links inside the market route with run and compare identity", async () => {
    const user = userEvent.setup();
    const other = researchHistoryItemFixture({
      id: SECOND_RUN_ID,
      name: "Other evaluation",
    });
    api.getResearchHistory.mockResolvedValue({
      items: [
        researchHistoryItemFixture({ id: RUN_ID, name: "Saved run" }),
        other,
      ],
      total: 2,
      offset: 0,
      limit: 20,
    });

    render(
      <ResearchDock
        csrfToken="fixture-csrf"
        query={query({ focusModel: "last_close" })}
      />,
    );
    await screen.findByRole("heading", { name: "Saved run" });
    await user.click(screen.getByRole("tab", { name: "Saved runs" }));

    const openOtherHref = researchWorkspaceHref({
      embedded: true,
      runId: SECOND_RUN_ID,
      compareId: null,
      instrumentId: "xnas-aapl",
      focusModel: "last_close",
    });
    expect(
      await screen.findByRole("link", { name: /Other evaluation/u }),
    ).toHaveAttribute("href", openOtherHref);
    expect(
      screen.getByRole("link", { name: /Compare with open run/u }),
    ).toHaveAttribute(
      "href",
      researchWorkspaceHref({
        embedded: true,
        runId: RUN_ID,
        compareId: SECOND_RUN_ID,
        instrumentId: "xnas-aapl",
        focusModel: "last_close",
      }),
    );
  });

  it("places dataset and horizon controls before provenance and routes the created run", async () => {
    const user = userEvent.setup();
    render(
      <ResearchDock
        csrfToken="fixture-csrf"
        query={query({
          requestedRunId: null,
          requestedInstrumentId: "xnas-aapl",
          focusModel: "last_close",
        })}
      />,
    );
    await user.click(screen.getByRole("tab", { name: "New evaluation" }));

    const datasetSelector = await screen.findByRole("combobox", {
      name: "Private research dataset",
    });
    const horizonSelector = screen.getByRole("radio", {
      name: "1 next session",
    });
    const provenanceDisclosure = screen.getByText(
      "Dataset source and permissions",
      { exact: true },
    );
    expect(
      datasetSelector.compareDocumentPosition(provenanceDisclosure) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).not.toBe(0);
    expect(
      horizonSelector.compareDocumentPosition(provenanceDisclosure) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).not.toBe(0);

    await user.click(provenanceDisclosure);
    const provenance = await screen.findByRole("region", {
      name: "Selected dataset provenance",
    });
    expect(provenance).toHaveTextContent("Synthetic pipeline check");
    expect(provenance).toHaveTextContent("synthetic-fixture-v1");
    expect(provenance).toHaveTextContent("XNYS");
    expect(provenance).toHaveTextContent("License reference");
    const runButton = await screen.findByRole("button", {
      name: "Run evaluation",
    });
    expect(runButton).toBeVisible();

    await user.click(runButton);
    await waitFor(() => {
      expect(api.replace).toHaveBeenCalledWith(
        researchWorkspaceHref({
          embedded: true,
          runId: CREATED_RUN_ID,
          compareId: null,
          instrumentId: "xnas-aapl",
          focusModel: "last_close",
        }),
        { scroll: false },
      );
    });
    expect(api.createResearchRun).toHaveBeenCalledWith(
      expect.objectContaining({
        dataset_id: researchDatasetFixture().id,
        horizon_sessions: 1,
      }),
      "fixture-csrf",
      expect.any(AbortSignal),
    );
  });

  it("keeps a pending evaluation alive while switching dock tabs", async () => {
    const user = userEvent.setup();
    const originalUrl = window.location.href;
    window.history.replaceState(
      null,
      "",
      "/app/markets?view=research&instrument=xnas-aapl&method=last_close#analysis",
    );
    const dockUrl = window.location.href;
    let resolveCreate: ((run: ResearchRun) => void) | undefined;
    let requestSignal: AbortSignal | undefined;
    let submittedRequest: ResearchRunRequest | undefined;
    api.createResearchRun.mockImplementation(
      (
        request: ResearchRunRequest,
        _csrfToken: string,
        signal?: AbortSignal,
      ) => {
        submittedRequest = request;
        requestSignal = signal;
        return new Promise<ResearchRun>((resolve) => {
          resolveCreate = resolve;
        });
      },
    );

    try {
      render(
        <ResearchDock
          csrfToken="fixture-csrf"
          query={query({
            requestedRunId: null,
            requestedInstrumentId: "xnas-aapl",
            focusModel: "last_close",
          })}
        />,
      );
      await user.click(screen.getByRole("tab", { name: "New evaluation" }));
      await user.click(
        await screen.findByRole("button", { name: "Run evaluation" }),
      );
      await waitFor(() => {
        expect(resolveCreate).toBeDefined();
        expect(requestSignal).toBeDefined();
        expect(submittedRequest).toBeDefined();
      });

      const originalIdempotencyKey = submittedRequest?.idempotency_key;
      const savedRunsTab = screen.getByRole("tab", { name: "Saved runs" });
      await user.click(savedRunsTab);

      expect(requestSignal?.aborted).toBe(false);
      expect(api.createResearchRun).toHaveBeenCalledTimes(1);
      expect(api.replace).not.toHaveBeenCalled();
      expect(window.location.href).toBe(dockUrl);
      expect(savedRunsTab).toHaveAttribute("aria-selected", "true");

      const setupRegion = screen.getByRole("region", {
        name: "Evaluation setup",
        hidden: true,
      });
      const hiddenEvaluation = setupRegion.closest("[hidden]");
      expect(hiddenEvaluation).not.toBeNull();
      expect(hiddenEvaluation?.hasAttribute("hidden")).toBe(true);
      expect(screen.queryByRole("button", { name: "Evaluating" })).toBeNull();
      await user.tab();
      expect(screen.getByRole("link", { name: "Full research" })).toHaveFocus();
      expect(hiddenEvaluation?.contains(document.activeElement)).toBe(false);
      await user.tab();
      expect(screen.getByRole("tabpanel")).toHaveFocus();
      expect(hiddenEvaluation?.contains(document.activeElement)).toBe(false);

      await user.click(screen.getByRole("tab", { name: "New evaluation" }));
      expect(
        await screen.findByRole("button", { name: "Evaluating" }),
      ).toBeDisabled();
      expect(submittedRequest?.idempotency_key).toBe(originalIdempotencyKey);
      expect(api.createResearchRun).toHaveBeenCalledTimes(1);

      await user.click(screen.getByRole("tab", { name: "Saved runs" }));
      const savedRun = researchRunFixture({
        id: CREATED_RUN_ID,
        name: "Completed while saved runs were open",
      });
      await act(async () => {
        resolveCreate?.(savedRun);
      });

      await waitFor(() => {
        expect(api.replace).toHaveBeenCalledWith(
          researchWorkspaceHref({
            embedded: true,
            runId: CREATED_RUN_ID,
            compareId: null,
            instrumentId: "xnas-aapl",
            focusModel: "last_close",
          }),
          { scroll: false },
        );
      });
      expect(api.createResearchRun).toHaveBeenCalledTimes(1);
      expect(submittedRequest?.idempotency_key).toBe(originalIdempotencyKey);
      expect(requestSignal?.aborted).toBe(false);
      expect(window.location.href).toBe(dockUrl);
    } finally {
      window.history.replaceState(null, "", originalUrl);
    }
  });

  it.each([401, 403])(
    "refreshes the session when the private dataset request returns %i",
    async (status) => {
      const user = userEvent.setup();
      api.getResearchDatasets.mockRejectedValueOnce(
        new ApiError({
          status,
          code: "authentication_required",
          message: "Please sign in again.",
        }),
      );

      render(
        <ResearchDock
          csrfToken="fixture-csrf"
          query={query({ requestedRunId: null })}
        />,
      );
      await user.click(screen.getByRole("tab", { name: "New evaluation" }));
      expect(await screen.findByText("Please sign in again.")).toBeVisible();
      await waitFor(() => expect(api.refresh).toHaveBeenCalledTimes(1));
      expect(
        screen
          .getAllByRole("alert")
          .some((element) =>
            element.textContent?.includes("Please sign in again."),
          ),
      ).toBe(true);
    },
  );

  it("aborts stale detail requests and keeps the newest selected run", async () => {
    const earlierRun = researchRunFixture({
      id: RUN_ID,
      name: "Earlier run",
    });
    const currentRun = researchRunFixture({
      id: SECOND_RUN_ID,
      name: "Current run",
    });
    let resolveEarlier: ((run: ResearchRun) => void) | undefined;
    let earlierSignal: AbortSignal | undefined;
    api.getResearchRun.mockImplementation(
      (runId: string, signal?: AbortSignal) => {
        if (runId === RUN_ID) {
          earlierSignal = signal;
          return new Promise((resolve) => {
            resolveEarlier = resolve;
          });
        }
        return Promise.resolve(currentRun);
      },
    );
    const view = render(
      <ResearchDock
        csrfToken="fixture-csrf"
        query={query({ requestedRunId: RUN_ID })}
      />,
    );
    await waitFor(() => expect(earlierSignal).toBeDefined());

    view.rerender(
      <ResearchDock
        csrfToken="fixture-csrf"
        query={query({ requestedRunId: SECOND_RUN_ID })}
      />,
    );
    expect(
      await screen.findByRole("heading", { name: "Current run" }),
    ).toBeVisible();
    expect(earlierSignal?.aborted).toBe(true);

    await act(async () => {
      resolveEarlier?.(earlierRun);
    });
    expect(screen.getByRole("heading", { name: "Current run" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Earlier run" })).toBeNull();
  });
});

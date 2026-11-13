import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

import {
  compareResearchRuns,
  createResearchRun,
  getResearchExport,
  getResearchHistory,
  getResearchDatasetProvenance,
  verifyResearchReplay,
} from "./research-api";
import {
  researchDatasetFixture,
  researchExportFixture,
  researchHistoryItemFixture,
  researchRunFixture,
  researchProvenanceFixture,
} from "./research-test-fixtures";
import {
  ResearchHistoryQuerySchema,
  ResearchRunRequestSchema,
  type ResearchRunRequest,
} from "./research-schemas";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const request: ResearchRunRequest = {
  dataset_id: "11111111-1111-4111-8111-111111111111",
  horizon_sessions: 5,
  idempotency_key: "33333333-3333-4333-8333-333333333333",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("research API client", () => {
  it("binds provenance to the requested dataset and version without accepting a qualification claim", async () => {
    const evidence = researchProvenanceFixture();
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(evidence));
    vi.stubGlobal("fetch", fetchMock);
    const request = { datasetId: evidence.dataset.id, datasetVersion: evidence.dataset.version };
    expect(await getResearchDatasetProvenance(request)).toEqual(evidence);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(`/api/v1/research/datasets/${evidence.dataset.id}/provenance/`);
    fetchMock.mockResolvedValueOnce(jsonResponse({ ...evidence, dataset: { ...evidence.dataset, version: "c".repeat(64) } }));
    await expect(getResearchDatasetProvenance(request)).rejects.toMatchObject({ code: "research_dataset_mismatch" });
    fetchMock.mockResolvedValueOnce(jsonResponse({ ...evidence, independently_verified_source: true }));
    await expect(getResearchDatasetProvenance(request)).rejects.toBeInstanceOf(ApiError);
  });

  it("requests a bounded, filtered lightweight history page", async () => {
    const item = researchHistoryItemFixture();
    const query = ResearchHistoryQuerySchema.parse({
      q: "pipeline fixture",
      instrument_id: "xnas-aapl",
      horizon_sessions: 5,
      data_kind: "synthetic_fixture",
      offset: 20,
      limit: 20,
    });
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        jsonResponse({ items: [item], total: 21, offset: 20, limit: 20 }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const history = await getResearchHistory(query);

    expect(history.items).toEqual([item]);
    expect(history.items[0]).not.toHaveProperty("result");
    expect(history.offset).toBe(20);
    expect(history.limit).toBe(20);
    const [path, init] = fetchMock.mock.calls[0] ?? [];
    const url = new URL(String(path), "https://workspace.test");
    expect(url.pathname).toBe("/api/v1/research/history/");
    expect(url.searchParams.get("q")).toBe("pipeline fixture");
    expect(url.searchParams.get("instrument_id")).toBe("xnas-aapl");
    expect(url.searchParams.get("horizon_sessions")).toBe("5");
    expect(url.searchParams.get("data_kind")).toBe("synthetic_fixture");
    expect(url.searchParams.get("offset")).toBe("20");
    expect(url.searchParams.get("limit")).toBe("20");
    expect(init?.credentials).toBe("same-origin");
    expect(init?.cache).toBe("no-store");
  });

  it("rejects a history response for a different page", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn<typeof fetch>()
        .mockResolvedValue(
          jsonResponse({ items: [], total: 0, offset: 10, limit: 20 }),
        ),
    );

    await expect(
      getResearchHistory({ offset: 0, limit: 20 }),
    ).rejects.toMatchObject({
      code: "research_history_page_mismatch",
      status: 502,
    });
  });

  it("sends a validated request with CSRF and preserves the caller's retry key", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new TypeError("connection interrupted"))
      .mockRejectedValueOnce(new TypeError("connection interrupted"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createResearchRun(request, "fixture-csrf"),
    ).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
    await expect(
      createResearchRun(request, "fixture-csrf"),
    ).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const [path, init] of fetchMock.mock.calls) {
      expect(path).toBe("/api/v1/research/runs/");
      expect(init?.method).toBe("POST");
      expect(init?.credentials).toBe("same-origin");
      expect(init?.cache).toBe("no-store");
      expect(new Headers(init?.headers).get("X-CSRFToken")).toBe(
        "fixture-csrf",
      );
      const body: unknown = JSON.parse(
        typeof init?.body === "string" ? init.body : "{}",
      );
      expect(ResearchRunRequestSchema.parse(body)).toEqual(request);
    }
  });

  it("maps a validated API error into the shared error type with its request ID", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          code: "dataset_unavailable",
          message: "The selected private dataset is unavailable.",
          field_errors: {},
          request_id: "research-request-123",
        },
        409,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const caught = createResearchRun(request, "fixture-csrf").catch(
      (error: unknown) => error,
    );
    await expect(caught).resolves.toBeInstanceOf(ApiError);
    await expect(caught).resolves.toMatchObject({
      status: 409,
      code: "dataset_unavailable",
      requestId: "research-request-123",
    });
  });

  it("guards comparison responses against mismatched run identities", async () => {
    const leftId = "22222222-2222-4222-8222-222222222222";
    const rightId = "44444444-4444-4444-8444-444444444444";
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        left_id: rightId,
        right_id: rightId,
        compatible: true,
        reasons: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(compareResearchRuns(leftId, rightId)).rejects.toMatchObject({
      code: "research_comparison_mismatch",
      status: 502,
    });
    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
      `/api/v1/research/runs/${leftId}/compare/${rightId}/`,
    );
  });

  it("sends the exact replay request with CSRF and returns every verification flag", async () => {
    const runId = "22222222-2222-4222-8222-222222222222";
    const result = {
      run_id: runId,
      result: "FAIL",
      dataset_matches: true,
      engine_matches: true,
      dependency_lock_matches: false,
      runtime_versions_match: true,
      result_matches: false,
      result_sha256: "c".repeat(64),
    };
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(result));
    vi.stubGlobal("fetch", fetchMock);

    await expect(verifyResearchReplay(runId, "fixture-csrf")).resolves.toEqual(
      result,
    );

    const [path, init] = fetchMock.mock.calls[0] ?? [];
    expect(path).toBe(`/api/v1/research/runs/${runId}/replay/`);
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe("{}");
    expect(new Headers(init?.headers).get("X-CSRFToken")).toBe("fixture-csrf");
    expect(new Headers(init?.headers).get("Content-Type")).toBe(
      "application/json",
    );
  });

  it("returns only an identity-matched synthetic JSON export", async () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const exported = researchExportFixture(run, researchDatasetFixture());
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(exported));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getResearchExport(run.id)).resolves.toEqual({
      data: exported,
      source: JSON.stringify(exported),
    });
    expect(String(fetchMock.mock.calls[0]?.[0])).toBe(
      `/api/v1/research/runs/${run.id}/export/`,
    );

    const wrongRun = researchRunFixture({
      id: "44444444-4444-4444-8444-444444444444",
      name: "Different run",
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse({ ...exported, run: wrongRun })),
    );
    await expect(getResearchExport(run.id)).rejects.toMatchObject({
      code: "research_export_mismatch",
      status: 502,
    });
  });
});

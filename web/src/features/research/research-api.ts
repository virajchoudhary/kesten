import { ApiError, requestJson, requestJsonDocument } from "@/lib/api/client";

import {
  ResearchComparisonResponseSchema,
  ResearchDatasetListResponseSchema,
  ResearchExportResponseSchema,
  ResearchHistoryQuerySchema,
  ResearchHistoryResponseSchema,
  ResearchReplayResponseSchema,
  ResearchRunIdSchema,
  ResearchRunListSchema,
  ResearchRunRequestSchema,
  ResearchRunSchema,
  type ResearchComparisonResponse,
  type ResearchDatasetList,
  type ResearchExportResponse,
  type ResearchHistoryQuery,
  type ResearchHistoryResponse,
  type ResearchReplayResponse,
  type ResearchRun,
  type ResearchRunList,
  type ResearchRunRequest,
} from "./research-schemas";

export function getResearchDatasets(
  signal?: AbortSignal,
): Promise<ResearchDatasetList> {
  return requestJson({
    path: "/api/v1/research/datasets/",
    schema: ResearchDatasetListResponseSchema,
    signal,
  });
}

export function getResearchRuns(
  signal?: AbortSignal,
): Promise<ResearchRunList> {
  return requestJson({
    path: "/api/v1/research/runs/",
    schema: ResearchRunListSchema,
    signal,
  });
}

export async function getResearchHistory(
  query: ResearchHistoryQuery,
  signal?: AbortSignal,
): Promise<ResearchHistoryResponse> {
  const validatedQuery = ResearchHistoryQuerySchema.parse(query);
  const params = new URLSearchParams({
    offset: String(validatedQuery.offset),
    limit: String(validatedQuery.limit),
  });
  if (validatedQuery.q) {
    params.set("q", validatedQuery.q);
  }
  if (validatedQuery.instrument_id) {
    params.set("instrument_id", validatedQuery.instrument_id);
  }
  if (validatedQuery.horizon_sessions !== undefined) {
    params.set("horizon_sessions", String(validatedQuery.horizon_sessions));
  }
  if (validatedQuery.data_kind !== undefined) {
    params.set("data_kind", validatedQuery.data_kind);
  }

  const response = await requestJson({
    path: `/api/v1/research/history/?${params.toString()}`,
    schema: ResearchHistoryResponseSchema,
    signal,
  });
  if (
    response.offset !== validatedQuery.offset ||
    response.limit !== validatedQuery.limit
  ) {
    throw new ApiError({
      status: 502,
      code: "research_history_page_mismatch",
      message: "The API returned a different saved-evaluation page.",
    });
  }
  return response;
}

export async function getResearchRun(
  runId: string,
  signal?: AbortSignal,
): Promise<ResearchRun> {
  const expectedRunId = ResearchRunIdSchema.parse(runId);
  const run = await requestJson({
    path: `/api/v1/research/runs/${encodeURIComponent(expectedRunId)}/`,
    schema: ResearchRunSchema,
    signal,
  });
  if (run.id !== expectedRunId) {
    throw new ApiError({
      status: 502,
      code: "research_run_mismatch",
      message: "The API returned a different saved research run.",
    });
  }
  return run;
}

export async function compareResearchRuns(
  leftRunId: string,
  rightRunId: string,
  signal?: AbortSignal,
): Promise<ResearchComparisonResponse> {
  const expectedLeftId = ResearchRunIdSchema.parse(leftRunId);
  const expectedRightId = ResearchRunIdSchema.parse(rightRunId);
  const comparison = await requestJson({
    path: `/api/v1/research/runs/${encodeURIComponent(expectedLeftId)}/compare/${encodeURIComponent(expectedRightId)}/`,
    schema: ResearchComparisonResponseSchema,
    signal,
  });
  if (
    comparison.left_id !== expectedLeftId ||
    comparison.right_id !== expectedRightId
  ) {
    throw new ApiError({
      status: 502,
      code: "research_comparison_mismatch",
      message: "The API returned a comparison for different saved evaluations.",
    });
  }
  return comparison;
}

export async function verifyResearchReplay(
  runId: string,
  csrfToken: string,
  signal?: AbortSignal,
): Promise<ResearchReplayResponse> {
  const expectedRunId = ResearchRunIdSchema.parse(runId);
  const replay = await requestJson({
    path: `/api/v1/research/runs/${encodeURIComponent(expectedRunId)}/replay/`,
    schema: ResearchReplayResponseSchema,
    init: { method: "POST", body: JSON.stringify({}) },
    csrfToken,
    signal,
  });
  if (replay.run_id !== expectedRunId) {
    throw new ApiError({
      status: 502,
      code: "research_replay_mismatch",
      message:
        "The API returned a replay result for a different saved evaluation.",
    });
  }
  return replay;
}

export async function getResearchExport(
  runId: string,
  signal?: AbortSignal,
): Promise<{ data: ResearchExportResponse; source: string }> {
  const expectedRunId = ResearchRunIdSchema.parse(runId);
  const exported = await requestJsonDocument({
    path: `/api/v1/research/runs/${encodeURIComponent(expectedRunId)}/export/`,
    schema: ResearchExportResponseSchema,
    signal,
  });
  if (exported.data.run.id !== expectedRunId) {
    throw new ApiError({
      status: 502,
      code: "research_export_mismatch",
      message: "The API returned an export for a different saved evaluation.",
    });
  }
  return exported;
}

export function createResearchRun(
  request: ResearchRunRequest,
  csrfToken: string,
  signal?: AbortSignal,
): Promise<ResearchRun> {
  const validatedRequest = ResearchRunRequestSchema.parse(request);
  return requestJson({
    path: "/api/v1/research/runs/",
    schema: ResearchRunSchema,
    init: { method: "POST", body: JSON.stringify(validatedRequest) },
    csrfToken,
    signal,
  });
}

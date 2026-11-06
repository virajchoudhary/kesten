import { ApiError, requestJson } from "@/lib/api/client";

import {
  ResearchDatasetListResponseSchema,
  ResearchRunListSchema,
  ResearchRunRequestSchema,
  ResearchRunSchema,
  type ResearchDatasetList,
  type ResearchRun,
  type ResearchRunList,
  type ResearchRunRequest,
} from "./research-schemas";

export function getResearchDatasets(signal?: AbortSignal): Promise<ResearchDatasetList> {
  return requestJson({
    path: "/api/v1/research/datasets/",
    schema: ResearchDatasetListResponseSchema,
    signal,
  });
}

export function getResearchRuns(signal?: AbortSignal): Promise<ResearchRunList> {
  return requestJson({
    path: "/api/v1/research/runs/",
    schema: ResearchRunListSchema,
    signal,
  });
}

export async function getResearchRun(
  runId: string,
  signal?: AbortSignal,
): Promise<ResearchRun> {
  const run = await requestJson({
    path: `/api/v1/research/runs/${encodeURIComponent(runId)}/`,
    schema: ResearchRunSchema,
    signal,
  });
  if (run.id !== runId) {
    throw new ApiError({
      status: 502,
      code: "research_run_mismatch",
      message: "The API returned a different saved research run.",
    });
  }
  return run;
}

export function createResearchRun(
  request: ResearchRunRequest,
  csrfToken: string,
): Promise<ResearchRun> {
  const validatedRequest = ResearchRunRequestSchema.parse(request);
  return requestJson({
    path: "/api/v1/research/runs/",
    schema: ResearchRunSchema,
    init: { method: "POST", body: JSON.stringify(validatedRequest) },
    csrfToken,
  });
}

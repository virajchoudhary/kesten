import {
  ResearchInstrumentIdSchema,
  ResearchReferenceIdSchema,
  ResearchRunIdSchema,
  type ResearchReferenceId,
} from "./research-schemas";

export type ResearchPageSearchParams = {
  run?: string | string[] | undefined;
  compare?: string | string[] | undefined;
  instrument?: string | string[] | undefined;
  method?: string | string[] | undefined;
};

export type ResearchWorkspaceQuery = {
  requestedRunId: string | null;
  requestedCompareId: string | null;
  requestedInstrumentId: string | null;
  focusModel: ResearchReferenceId;
};

export const RESEARCH_SECTIONS = {
  setup: "research-setup-title",
  results: "research-results",
  history: "research-history",
} as const;

function singleParameter(value: string | string[] | undefined): string | null {
  return typeof value === "string" ? value : null;
}

export function parseResearchPageSearchParams(
  params: ResearchPageSearchParams,
): ResearchWorkspaceQuery {
  const runId = ResearchRunIdSchema.safeParse(singleParameter(params.run));
  const compareId = ResearchRunIdSchema.safeParse(
    singleParameter(params.compare),
  );
  const instrumentId = ResearchInstrumentIdSchema.safeParse(
    singleParameter(params.instrument),
  );
  const focusModel = ResearchReferenceIdSchema.safeParse(
    singleParameter(params.method),
  );
  const requestedRunId = runId.success ? runId.data : null;
  const requestedCompareId =
    requestedRunId !== null &&
    compareId.success &&
    compareId.data !== requestedRunId
      ? compareId.data
      : null;

  return {
    requestedRunId,
    requestedCompareId,
    requestedInstrumentId: instrumentId.success ? instrumentId.data : null,
    focusModel: focusModel.success ? focusModel.data : "historical_log_mean",
  };
}

export function researchWorkspaceHref(options: {
  runId: string | null;
  compareId: string | null;
  instrumentId: string | null;
  focusModel: ResearchReferenceId;
  embedded?: boolean;
}): string {
  const params = new URLSearchParams();
  if (options.embedded) params.set("view", "research");
  if (options.runId !== null) {
    params.set("run", options.runId);
  }
  if (
    options.runId !== null &&
    options.compareId !== null &&
    options.compareId !== options.runId
  ) {
    params.set("compare", options.compareId);
  }
  if (options.instrumentId !== null) {
    params.set("instrument", options.instrumentId);
  }
  if (options.focusModel !== "historical_log_mean") {
    params.set("method", options.focusModel);
  }
  const query = params.toString();
  const path = options.embedded ? "/app/markets" : "/app/research";
  return query ? `${path}?${query}` : path;
}

export function researchResultHref(
  options: Parameters<typeof researchWorkspaceHref>[0],
): string {
  const path = researchWorkspaceHref(options);
  return options.embedded ? path : `${path}#${RESEARCH_SECTIONS.results}`;
}

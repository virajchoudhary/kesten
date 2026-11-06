"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useRouter } from "next/navigation";
import { FlaskConical, LoaderCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSession } from "@/features/session/session-provider";
import { ApiError } from "@/lib/api/client";

import {
  createResearchRun,
  getResearchDatasets,
  getResearchRun,
  getResearchRuns,
} from "./research-api";
import { ResearchResults } from "./research-results";
import {
  ResearchHorizonSchema,
  type ResearchDataset,
  type ResearchRun,
  type ResearchRunList,
  type ResearchRunRequest,
} from "./research-schemas";
import {
  DatasetSelector,
  ErrorMessage,
  HorizonSelector,
  RunHistory,
  WorkspaceHeader,
  type LoadState,
} from "./research-workspace-parts";

type ResearchDetailState =
  | { kind: "empty" }
  | { kind: "loading" }
  | { kind: "ready"; run: ResearchRun }
  | { kind: "failed"; error: ApiError };

type CreateAttempt =
  | { kind: "idle" }
  | {
      kind: "pending";
      datasetId: string;
      horizon: ResearchRunRequest["horizon_sessions"];
      idempotencyKey: string;
    }
  | {
      kind: "failed";
      datasetId: string;
      horizon: ResearchRunRequest["horizon_sessions"];
      idempotencyKey: string;
      error: ApiError;
    };

function asResearchError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  return new ApiError({
    status: 500,
    code: "research_request_failed",
    message: "The research request could not be completed. Try again.",
  });
}

function AuthenticatedResearchWorkspace({
  requestedRunId,
  username,
  csrfToken,
  onSignOut,
  signOutPending,
  signOutError,
}: {
  requestedRunId: string | null;
  username: string;
  csrfToken: string;
  onSignOut: () => void;
  signOutPending: boolean;
  signOutError: string | null;
}): React.JSX.Element {
  const router = useRouter();
  const [datasetRefresh, setDatasetRefresh] = useState(0);
  const [runListRefresh, setRunListRefresh] = useState(0);
  const [detailRefresh, setDetailRefresh] = useState(0);
  const [datasetResult, setDatasetResult] = useState<{
    attempt: number;
    state: LoadState<ResearchDataset[]>;
  } | null>(null);
  const [runsResult, setRunsResult] = useState<{
    attempt: number;
    state: LoadState<ResearchRunList>;
  } | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [horizon, setHorizon] = useState<ResearchRunRequest["horizon_sessions"]>(1);
  const [createAttempt, setCreateAttempt] = useState<CreateAttempt>({ kind: "idle" });
  const evaluationFormRef = useRef<HTMLFormElement>(null);
  const [detailResult, setDetailResult] = useState<{
    runId: string;
    attempt: number;
    state: Exclude<ResearchDetailState, { kind: "empty" }>;
  } | null>(null);

  useEffect(() => {
    const requestAttempt = datasetRefresh;
    const controller = new AbortController();
    void getResearchDatasets(controller.signal)
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        setDatasetResult({
          attempt: requestAttempt,
          state: { kind: "ready", data: response.items },
        });
        setSelectedDatasetId((current) =>
          response.items.some((dataset) => dataset.id === current)
            ? current
            : response.items[0]?.id ?? "",
        );
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setDatasetResult({
            attempt: requestAttempt,
            state: { kind: "failed", error: asResearchError(error) },
          });
        }
      });
    return () => controller.abort();
  }, [datasetRefresh]);

  useEffect(() => {
    const requestAttempt = runListRefresh;
    const controller = new AbortController();
    void getResearchRuns(controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setRunsResult({
            attempt: requestAttempt,
            state: { kind: "ready", data: response },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setRunsResult({
            attempt: requestAttempt,
            state: { kind: "failed", error: asResearchError(error) },
          });
        }
      });
    return () => controller.abort();
  }, [runListRefresh]);

  useEffect(() => {
    if (requestedRunId === null) {
      return;
    }
    const requestAttempt = detailRefresh;
    const runId = requestedRunId;
    const controller = new AbortController();
    void getResearchRun(runId, controller.signal)
      .then((run) => {
        if (!controller.signal.aborted) {
          setDetailResult({
            runId,
            attempt: requestAttempt,
            state: { kind: "ready", run },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setDetailResult({
            runId,
            attempt: requestAttempt,
            state: { kind: "failed", error: asResearchError(error) },
          });
        }
      });
    return () => controller.abort();
  }, [detailRefresh, requestedRunId]);

  const datasetsState: LoadState<ResearchDataset[]> =
    datasetResult?.attempt === datasetRefresh ? datasetResult.state : { kind: "loading" };
  const runsState: LoadState<ResearchRunList> =
    runsResult?.attempt === runListRefresh ? runsResult.state : { kind: "loading" };
  const detailState: ResearchDetailState =
    requestedRunId === null
      ? { kind: "empty" }
      : detailResult?.runId === requestedRunId && detailResult.attempt === detailRefresh
        ? detailResult.state
        : { kind: "loading" };

  const datasets = datasetsState.kind === "ready" ? datasetsState.data : [];
  const selectedDataset = datasets.find((dataset) => dataset.id === selectedDatasetId) ?? null;
  const createPending = createAttempt.kind === "pending";
  const canReuseKey =
    createAttempt.kind === "failed" &&
    createAttempt.datasetId === selectedDatasetId &&
    createAttempt.horizon === horizon;
  const createError =
    canReuseKey && createAttempt.kind === "failed" ? createAttempt.error : null;

  async function submitEvaluation(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (selectedDataset === null || createPending) {
      return;
    }
    const idempotencyKey = canReuseKey && createAttempt.kind === "failed"
      ? createAttempt.idempotencyKey
      : crypto.randomUUID();
    const request: ResearchRunRequest = {
      dataset_id: selectedDataset.id,
      horizon_sessions: horizon,
      idempotency_key: idempotencyKey,
    };
    setCreateAttempt({
      kind: "pending",
      datasetId: selectedDataset.id,
      horizon,
      idempotencyKey,
    });

    try {
      const run = await createResearchRun(request, csrfToken);
      setCreateAttempt({ kind: "idle" });
      setRunListRefresh((current) => current + 1);
      router.push(`/app/research?run=${encodeURIComponent(run.id)}`, { scroll: false });
    } catch (error: unknown) {
      setCreateAttempt({
        kind: "failed",
        datasetId: selectedDataset.id,
        horizon,
        idempotencyKey,
        error: asResearchError(error),
      });
    }
  }

  function handleDatasetChange(value: string): void {
    if (!datasets.some((dataset) => dataset.id === value)) {
      return;
    }
    setSelectedDatasetId(value);
    setCreateAttempt({ kind: "idle" });
  }

  function handleHorizonChange(value: ResearchRunRequest["horizon_sessions"]): void {
    const parsed = ResearchHorizonSchema.safeParse(value);
    if (!parsed.success) {
      return;
    }
    setHorizon(parsed.data);
    setCreateAttempt({ kind: "idle" });
  }

  return (
    <div className="min-h-dvh bg-canvas text-foreground">
      <a className="skip-link" href="#main-content">Skip to research workspace</a>
      <WorkspaceHeader
        onSignOut={onSignOut}
        signOutPending={signOutPending}
        username={username}
      />
      {signOutError && (
        <div className="border-b border-negative/40 bg-negative/10 px-4 py-2 text-sm text-negative" role="alert">
          {signOutError}
        </div>
      )}

      <main className="mx-auto min-w-0 max-w-[1600px]" id="main-content" tabIndex={-1}>
        <div className="flex min-h-12 flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-4 py-2">
          <h1 className="text-base font-semibold">Forecasting research</h1>
          <div className="flex items-center gap-2 text-xs text-secondary">
            <FlaskConical aria-hidden="true" className="text-accent" size={15} />
            Private research
          </div>
        </div>

        <section aria-labelledby="research-setup-title" className="border-b border-border-subtle">
          <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
            <h2 className="text-sm font-semibold" id="research-setup-title">Evaluation setup</h2>
          </div>

          {datasetsState.kind === "loading" && (
            <p className="flex items-center gap-2 px-4 py-5 text-sm text-secondary" role="status">
              <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
              Loading private datasets
            </p>
          )}

          {datasetsState.kind === "failed" && (
            <ErrorMessage
              error={datasetsState.error}
              onRetry={() => setDatasetRefresh((current) => current + 1)}
              retryLabel="Retry dataset list"
            />
          )}

          {datasetsState.kind === "ready" && datasets.length === 0 && (
            <div className="space-y-2 border-y border-border-subtle px-4 py-5">
              <h3 className="text-sm font-semibold">No private datasets are available</h3>
              <p className="max-w-3xl text-sm text-secondary">
                An operator must import an attested historical dataset through the research CLI before
                it can be selected here. Dataset uploads are not available in this workspace.
              </p>
              <p className="max-w-3xl text-xs text-secondary">
                A synthetic fixture will appear here after an operator seeds it for this account.
              </p>
            </div>
          )}

          {datasetsState.kind === "ready" && datasets.length > 0 && (
            <>
              <form
                className="flex flex-wrap items-end gap-4 px-4 py-4"
                onSubmit={(event) => void submitEvaluation(event)}
                ref={evaluationFormRef}
              >
                <DatasetSelector
                  datasets={datasets}
                  disabled={createPending}
                  onChange={handleDatasetChange}
                  selectedDatasetId={selectedDatasetId}
                />
                <HorizonSelector
                  disabled={createPending}
                  onChange={handleHorizonChange}
                  value={horizon}
                />
                <Button
                  className="min-h-11 min-w-44 min-[768px]:min-h-9"
                  disabled={createPending || selectedDataset === null}
                  type="submit"
                  variant="primary"
                >
                  {createPending ? (
                    <>
                      <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
                      Evaluating
                    </>
                  ) : (
                    "Run evaluation"
                  )}
                </Button>
              </form>

              {selectedDataset !== null && (
                <div className="flex flex-wrap items-center gap-2 border-t border-border-subtle px-4 py-3">
                  {selectedDataset.data_kind === "synthetic_fixture" ? (
                    <>
                      <Badge variant="demo">SYNTHETIC FIXTURE</Badge>
                      <p className="text-xs text-warning">
                        No empirical forecasting performance established.
                      </p>
                    </>
                  ) : (
                    <Badge variant="neutral">Historical dataset</Badge>
                  )}
                </div>
              )}
            </>
          )}

          {createError && (
            <ErrorMessage
              error={createError}
              onRetry={() => evaluationFormRef.current?.requestSubmit()}
              retryLabel="Retry evaluation"
            />
          )}
          {createAttempt.kind === "failed" && createError === null && (
            <div className="border-t border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative" role="alert">
              {createAttempt.error.message} Select the same dataset and horizon to retry this request.
            </div>
          )}
        </section>

        <section aria-labelledby="research-history-title" className="border-b border-border-subtle">
          <div className="flex min-h-11 items-center justify-between gap-3 border-b border-border-subtle px-4">
            <h2 className="text-sm font-semibold" id="research-history-title">Saved evaluations</h2>
            <Button
              aria-label="Reload saved evaluations"
              disabled={runsState.kind === "loading"}
              onClick={() => setRunListRefresh((current) => current + 1)}
              size="sm"
              variant="ghost"
            >
              {runsState.kind === "loading" ? (
                <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
              ) : (
                "Reload"
              )}
            </Button>
          </div>
          <RunHistory
            datasets={datasets}
            onRetry={() => setRunListRefresh((current) => current + 1)}
            selectedRunId={requestedRunId}
            state={runsState}
          />
        </section>

        <section aria-labelledby="research-detail-title" className="min-w-0">
          <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
            <h2 className="text-sm font-semibold" id="research-detail-title">Evaluation detail</h2>
          </div>

          {detailState.kind === "empty" && (
            <p className="px-4 py-5 text-sm text-secondary">
              Select a saved evaluation to view its forecast, metrics, and provenance.
            </p>
          )}
          {detailState.kind === "loading" && (
            <p className="flex items-center gap-2 px-4 py-5 text-sm text-secondary" role="status">
              <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
              Loading saved evaluation
            </p>
          )}
          {detailState.kind === "failed" && (
            <ErrorMessage
              error={detailState.error}
              onRetry={() => setDetailRefresh((current) => current + 1)}
              retryLabel="Retry evaluation detail"
            />
          )}
          {detailState.kind === "ready" && (
            <ResearchResults
              dataset={
                datasets.find(
                  (dataset) =>
                    dataset.id === detailState.run.dataset_id &&
                    dataset.version === detailState.run.dataset_version,
                ) ?? null
              }
              datasetState={datasetsState.kind}
              run={detailState.run}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export function ResearchWorkspace({
  requestedRunId,
}: {
  requestedRunId: string | null;
}): React.JSX.Element {
  const { state, refresh, signOut } = useSession();
  const router = useRouter();
  const [signOutPending, setSignOutPending] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);

  useEffect(() => {
    if (state.kind === "anonymous") {
      router.replace("/sign-in");
    }
  }, [router, state.kind]);

  async function handleSignOut(): Promise<void> {
    setSignOutPending(true);
    setSignOutError(null);
    try {
      await signOut();
    } catch (error: unknown) {
      setSignOutError(asResearchError(error).message);
    } finally {
      setSignOutPending(false);
    }
  }

  if (state.kind === "checking") {
    return (
      <main className="flex min-h-dvh items-center justify-center gap-2 bg-canvas text-sm text-secondary" role="status">
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Checking session
      </main>
    );
  }

  if (state.kind === "failed") {
    return (
      <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-3 px-5">
        <h1 className="text-lg font-semibold">Research workspace unavailable</h1>
        <p className="text-sm text-secondary">{state.error.message}</p>
        <Button className="w-fit" onClick={() => refresh()} variant="outline">
          Retry
        </Button>
      </main>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-canvas text-sm text-secondary" role="status">
        Sign-in required
      </main>
    );
  }

  return (
    <AuthenticatedResearchWorkspace
      csrfToken={state.session.csrf_token}
      onSignOut={() => void handleSignOut()}
      requestedRunId={requestedRunId}
      signOutError={signOutError}
      signOutPending={signOutPending}
      username={state.session.user.username}
    />
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FlaskConical, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useSession } from "@/features/session/session-provider";
import { ApiError } from "@/lib/api/client";

import { asResearchError } from "./research-errors";
import { ResearchEvaluationSetup } from "./research-evaluation-setup";
import { ResearchHistory } from "./research-history";
import { researchWorkspaceHref } from "./research-navigation";
import { getResearchDatasets, getResearchRun } from "./research-api";
import { ResearchResults } from "./research-results";
import {
  type ResearchDataset,
  type ResearchReferenceId,
  type ResearchRun,
  type ResearchRunRequest,
} from "./research-schemas";
import {
  ErrorMessage,
  WorkspaceHeader,
  type LoadState,
} from "./research-workspace-parts";

type ResearchDetailState =
  | { kind: "empty" }
  | { kind: "loading" }
  | { kind: "ready"; run: ResearchRun }
  | { kind: "failed"; error: ApiError };

function AuthenticatedResearchWorkspace({
  requestedRunId,
  requestedCompareId,
  requestedInstrumentId,
  focusModel,
  username,
  csrfToken,
  onSignOut,
  signOutPending,
  signOutError,
}: {
  requestedRunId: string | null;
  requestedCompareId: string | null;
  requestedInstrumentId: string | null;
  focusModel: ResearchReferenceId;
  username: string;
  csrfToken: string;
  onSignOut: () => void;
  signOutPending: boolean;
  signOutError: string | null;
}): React.JSX.Element {
  const router = useRouter();
  const [datasetRefresh, setDatasetRefresh] = useState(0);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [detailRefresh, setDetailRefresh] = useState(0);
  const [datasetResult, setDatasetResult] = useState<{
    attempt: number;
    state: LoadState<ResearchDataset[]>;
  } | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [horizon, setHorizon] =
    useState<ResearchRunRequest["horizon_sessions"]>(1);
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
        setSelectedDatasetId((current) => {
          const available =
            requestedInstrumentId === null
              ? response.items
              : response.items.filter(
                  (dataset) => dataset.instrument_id === requestedInstrumentId,
                );
          return available.some((dataset) => dataset.id === current)
            ? current
            : (available[0]?.id ?? "");
        });
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
  }, [datasetRefresh, requestedInstrumentId]);

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
    datasetResult?.attempt === datasetRefresh
      ? datasetResult.state
      : { kind: "loading" };
  const detailState: ResearchDetailState =
    requestedRunId === null
      ? { kind: "empty" }
      : detailResult?.runId === requestedRunId &&
          detailResult.attempt === detailRefresh
        ? detailResult.state
        : { kind: "loading" };

  function handleDatasetChange(value: string): void {
    setSelectedDatasetId(value);
  }

  function handleHorizonChange(
    value: ResearchRunRequest["horizon_sessions"],
  ): void {
    setHorizon(value);
  }

  function handleCreatedRun(run: ResearchRun): void {
    setHistoryRefresh((current) => current + 1);
    router.push(
      researchWorkspaceHref({
        runId: run.id,
        compareId: null,
        instrumentId: requestedInstrumentId,
        focusModel,
      }),
      { scroll: false },
    );
  }

  function handleFocusModelChange(nextFocusModel: ResearchReferenceId): void {
    router.replace(
      researchWorkspaceHref({
        runId: requestedRunId,
        compareId: requestedCompareId,
        instrumentId: requestedInstrumentId,
        focusModel: nextFocusModel,
      }),
      { scroll: false },
    );
  }

  function handleClearComparison(): void {
    router.replace(
      researchWorkspaceHref({
        runId: requestedRunId,
        compareId: null,
        instrumentId: requestedInstrumentId,
        focusModel,
      }),
      { scroll: false },
    );
  }

  return (
    <div className="min-h-dvh bg-canvas text-foreground">
      <a className="skip-link" href="#main-content">
        Skip to research workspace
      </a>
      <WorkspaceHeader
        onSignOut={onSignOut}
        signOutPending={signOutPending}
        username={username}
      />
      {signOutError && (
        <div
          className="border-b border-negative/40 bg-negative/10 px-4 py-2 text-sm text-negative"
          role="alert"
        >
          {signOutError}
        </div>
      )}

      <main
        className="mx-auto min-w-0 max-w-[1600px]"
        id="main-content"
        tabIndex={-1}
      >
        <div className="flex min-h-12 flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-4 py-2">
          <h1 className="text-base font-semibold">Forecasting research</h1>
          <div className="flex items-center gap-2 text-xs text-secondary">
            <FlaskConical
              aria-hidden="true"
              className="text-accent"
              size={15}
            />
            Private research
          </div>
        </div>

        <div className="grid min-w-0 grid-cols-1 lg:grid-cols-[minmax(18rem,24rem)_minmax(0,1fr)] lg:grid-rows-[auto_minmax(0,1fr)]">
          <ResearchEvaluationSetup
            key={`${requestedRunId}:${requestedCompareId}:${requestedInstrumentId}:${focusModel}`}
            csrfToken={csrfToken}
            datasetsState={datasetsState}
            horizon={horizon}
            onCreated={handleCreatedRun}
            onDatasetChange={handleDatasetChange}
            onHorizonChange={handleHorizonChange}
            onRetryDatasets={() => setDatasetRefresh((current) => current + 1)}
            requestedInstrumentId={requestedInstrumentId}
            selectedDatasetId={selectedDatasetId}
          />

          <section
            aria-labelledby="research-detail-title"
            className="min-w-0 border-b border-border-subtle lg:col-start-2 lg:row-span-2 lg:row-start-1"
          >
            <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
              <h2 className="text-sm font-semibold" id="research-detail-title">
                Evaluation results
              </h2>
            </div>

            {detailState.kind === "empty" && (
              <p className="px-4 py-5 text-sm text-secondary">
                Select a saved evaluation to inspect its chart, metrics, and
                provenance.
              </p>
            )}
            {detailState.kind === "loading" && (
              <p
                className="flex items-center gap-2 px-4 py-5 text-sm text-secondary"
                role="status"
              >
                <LoaderCircle
                  aria-hidden="true"
                  className="animate-spin"
                  size={15}
                />
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
                  datasetsState.kind === "ready"
                    ? (datasetsState.data.find(
                        (dataset) =>
                          dataset.id === detailState.run.dataset_id &&
                          dataset.version === detailState.run.dataset_version,
                      ) ?? null)
                    : null
                }
                datasetState={datasetsState.kind}
                csrfToken={csrfToken}
                focusModel={focusModel}
                comparisonRunId={requestedCompareId}
                onClearComparison={handleClearComparison}
                onFocusModelChange={handleFocusModelChange}
                run={detailState.run}
              />
            )}
          </section>

          <ResearchHistory
            key={requestedInstrumentId ?? "all-instruments"}
            className="border-b lg:col-start-1 lg:row-start-2 lg:border-r"
            focusModel={focusModel}
            instrumentContext={requestedInstrumentId}
            refreshToken={historyRefresh}
            selectedCompareId={requestedCompareId}
            selectedRunId={requestedRunId}
          />
        </div>
      </main>
    </div>
  );
}

export function ResearchWorkspace({
  requestedRunId,
  requestedCompareId = null,
  requestedInstrumentId = null,
  focusModel = "historical_log_mean",
}: {
  requestedRunId: string | null;
  requestedCompareId?: string | null;
  requestedInstrumentId?: string | null;
  focusModel?: ResearchReferenceId;
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
      <main
        className="flex min-h-dvh items-center justify-center gap-2 bg-canvas text-sm text-secondary"
        role="status"
      >
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Checking session
      </main>
    );
  }

  if (state.kind === "failed") {
    return (
      <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-3 px-5">
        <h1 className="text-lg font-semibold">
          Research workspace unavailable
        </h1>
        <p className="text-sm text-secondary">{state.error.message}</p>
        <Button className="w-fit" onClick={() => refresh()} variant="outline">
          Retry
        </Button>
      </main>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <main
        className="flex min-h-dvh items-center justify-center bg-canvas text-sm text-secondary"
        role="status"
      >
        Sign-in required
      </main>
    );
  }

  return (
    <AuthenticatedResearchWorkspace
      key={state.session.user.username}
      csrfToken={state.session.csrf_token}
      focusModel={focusModel}
      onSignOut={() => void handleSignOut()}
      requestedCompareId={requestedCompareId}
      requestedInstrumentId={requestedInstrumentId}
      requestedRunId={requestedRunId}
      signOutError={signOutError}
      signOutPending={signOutPending}
      username={state.session.user.username}
    />
  );
}

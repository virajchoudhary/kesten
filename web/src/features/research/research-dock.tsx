"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  Clock3,
  FlaskConical,
  LoaderCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { useSession } from "@/features/session/session-provider";
import { ApiError } from "@/lib/api/client";

import { asResearchError } from "./research-errors";
import { ResearchEvaluationSetup } from "./research-evaluation-setup";
import { ResearchHistory } from "./research-history";
import {
  ResearchDockDatasetFacts,
  ResearchDockInspector,
} from "./research-dock-inspector";
import {
  researchWorkspaceHref,
  type ResearchWorkspaceQuery,
} from "./research-navigation";
import { getResearchDatasets, getResearchRun } from "./research-api";
import {
  ResearchReferenceIdSchema,
  type ResearchDataset,
  type ResearchRun,
  type ResearchRunRequest,
} from "./research-schemas";
import { ErrorMessage, type LoadState } from "./research-workspace-parts";

const DOCK_TABS = [
  {
    id: "inspector",
    label: "Selected",
    accessibleLabel: "Selected run inspector",
    icon: Activity,
  },
  {
    id: "saved",
    label: "Saved runs",
    accessibleLabel: "Saved runs",
    icon: Clock3,
  },
  {
    id: "evaluate",
    label: "New eval",
    accessibleLabel: "New evaluation",
    icon: FlaskConical,
  },
] as const;

type DockTab = (typeof DOCK_TABS)[number]["id"];
type DetailState =
  | { kind: "empty" }
  | { kind: "loading" }
  | { kind: "ready"; run: ResearchRun }
  | { kind: "failed"; error: ApiError };

export function ResearchDock({
  query,
  csrfToken,
}: {
  query: ResearchWorkspaceQuery;
  csrfToken: string;
}): React.JSX.Element {
  const router = useRouter();
  const { refresh } = useSession();
  const dockId = useId();
  const tabButtons = useRef(new Map<DockTab, HTMLButtonElement>());
  const [tabSelection, setTabSelection] = useState<{
    runId: string | null;
    tab: DockTab;
  }>({ runId: query.requestedRunId, tab: "inspector" });
  const [datasetRefresh, setDatasetRefresh] = useState(0);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [detailRefresh, setDetailRefresh] = useState(0);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [horizon, setHorizon] =
    useState<ResearchRunRequest["horizon_sessions"]>(1);
  const [datasetResult, setDatasetResult] = useState<{
    attempt: number;
    state: LoadState<ResearchDataset[]>;
  } | null>(null);
  const [detailResult, setDetailResult] = useState<{
    key: string;
    state: Exclude<DetailState, { kind: "empty" }>;
  } | null>(null);

  useEffect(() => {
    const attempt = datasetRefresh;
    const controller = new AbortController();
    void getResearchDatasets(controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setDatasetResult({
            attempt,
            state: { kind: "ready", data: response.items },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          const normalized = asResearchError(error);
          if (normalized.status === 401 || normalized.status === 403) {
            refresh();
          }
          setDatasetResult({
            attempt,
            state: { kind: "failed", error: normalized },
          });
        }
      });
    return () => controller.abort();
  }, [datasetRefresh, refresh]);

  const datasetState: LoadState<ResearchDataset[]> =
    datasetResult?.attempt === datasetRefresh
      ? datasetResult.state
      : { kind: "loading" };
  const availableDatasets =
    datasetState.kind !== "ready"
      ? []
      : query.requestedInstrumentId === null
        ? datasetState.data
        : datasetState.data.filter(
            (dataset) => dataset.instrument_id === query.requestedInstrumentId,
          );
  const selectedDataset =
    availableDatasets.find((dataset) => dataset.id === selectedDatasetId) ??
    availableDatasets[0] ??
    null;

  const detailKey = `${query.requestedRunId ?? "none"}:${detailRefresh}`;
  useEffect(() => {
    if (query.requestedRunId === null) {
      return;
    }
    const runId = query.requestedRunId;
    const requestKey = `${runId}:${detailRefresh}`;
    const controller = new AbortController();
    void getResearchRun(runId, controller.signal)
      .then((run) => {
        if (!controller.signal.aborted) {
          setDetailResult({
            key: requestKey,
            state: { kind: "ready", run },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          const normalized = asResearchError(error);
          if (normalized.status === 401 || normalized.status === 403) {
            refresh();
          }
          setDetailResult({
            key: requestKey,
            state: { kind: "failed", error: normalized },
          });
        }
      });
    return () => controller.abort();
  }, [detailRefresh, query.requestedRunId, refresh]);

  const detailState: DetailState =
    query.requestedRunId === null
      ? { kind: "empty" }
      : detailResult?.key === detailKey
        ? detailResult.state
        : { kind: "loading" };
  const activeTab =
    query.requestedRunId !== null && tabSelection.runId !== query.requestedRunId
      ? "inspector"
      : tabSelection.tab;
  const standaloneHref = researchWorkspaceHref({
    embedded: false,
    runId: query.requestedRunId,
    compareId: query.requestedCompareId,
    instrumentId: query.requestedInstrumentId,
    focusModel: query.focusModel,
  });

  function selectTab(tab: DockTab): void {
    setTabSelection({ runId: query.requestedRunId, tab });
  }

  function handleTabKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    currentIndex: number,
  ): void {
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight") {
      nextIndex = (currentIndex + 1) % DOCK_TABS.length;
    } else if (event.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + DOCK_TABS.length) % DOCK_TABS.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = DOCK_TABS.length - 1;
    }
    if (nextIndex === null) return;
    const nextTab = DOCK_TABS[nextIndex];
    if (nextTab) {
      event.preventDefault();
      selectTab(nextTab.id);
      tabButtons.current.get(nextTab.id)?.focus();
    }
  }

  function handleCreatedRun(run: ResearchRun): void {
    setHistoryRefresh((current) => current + 1);
    selectTab("inspector");
    router.replace(
      researchWorkspaceHref({
        embedded: true,
        runId: run.id,
        compareId: null,
        instrumentId: query.requestedInstrumentId,
        focusModel: query.focusModel,
      }),
      { scroll: false },
    );
  }

  function handleFocusModelChange(value: string): void {
    const parsed = ResearchReferenceIdSchema.safeParse(value);
    if (
      !parsed.success ||
      detailState.kind !== "ready" ||
      !detailState.run.result.models.some((model) => model.id === parsed.data)
    ) {
      return;
    }
    router.replace(
      researchWorkspaceHref({
        embedded: true,
        runId: detailState.run.id,
        compareId: query.requestedCompareId,
        instrumentId: query.requestedInstrumentId,
        focusModel: parsed.data,
      }),
      { scroll: false },
    );
  }

  function handleClearComparison(): void {
    router.replace(
      researchWorkspaceHref({
        embedded: true,
        runId: query.requestedRunId,
        compareId: null,
        instrumentId: query.requestedInstrumentId,
        focusModel: query.focusModel,
      }),
      { scroll: false },
    );
  }

  return (
    <section
      aria-label="Research dock"
      className="research-dock research-polish min-w-0"
    >
      <header className="research-dock-tabs flex min-w-0 flex-wrap items-center justify-between gap-2 border-b border-border-subtle px-3 py-2">
        <div
          aria-label="Research dock views"
          className="flex min-w-0 items-center gap-1"
          role="tablist"
        >
          {DOCK_TABS.map((tab, index) => {
            const Icon = tab.icon;
            const selected = activeTab === tab.id;
            return (
              <button
                aria-controls={`${dockId}-panel`}
                aria-label={tab.accessibleLabel}
                aria-selected={selected}
                className={`inline-flex min-h-9 items-center gap-1.5 border-b-2 px-2.5 text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
                  selected
                    ? "border-accent text-foreground"
                    : "border-transparent text-secondary hover:bg-raised hover:text-foreground"
                }`}
                id={`${dockId}-tab-${tab.id}`}
                key={tab.id}
                onClick={() => selectTab(tab.id)}
                onKeyDown={(event) => handleTabKeyDown(event, index)}
                ref={(node) => {
                  if (node) tabButtons.current.set(tab.id, node);
                  else tabButtons.current.delete(tab.id);
                }}
                role="tab"
                tabIndex={selected ? 0 : -1}
                type="button"
              >
                <Icon aria-hidden="true" size={14} />
                {tab.label}
              </button>
            );
          })}
        </div>
        <Link
          className="inline-flex min-h-9 items-center gap-1 rounded-control px-2 text-xs font-medium text-secondary hover:bg-raised hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          href={standaloneHref}
          scroll={false}
        >
          <ArrowUpRight aria-hidden="true" size={14} />
          <span>Full research</span>
        </Link>
      </header>

      <div
        aria-labelledby={`${dockId}-tab-${activeTab}`}
        className="research-dock-body min-w-0"
        id={`${dockId}-panel`}
        role="tabpanel"
        tabIndex={0}
      >
        {activeTab === "inspector" &&
          (detailState.kind === "empty" ? (
            <div className="dock-inspector flex min-h-36 flex-col items-start justify-center gap-2 px-4 py-5">
              <h2 className="text-sm font-semibold">No saved run selected</h2>
              <p className="max-w-xl text-xs text-secondary">
                Open a saved run from the history tab or configure a new
                evaluation.
              </p>
              <Button
                className="mt-1 min-h-9"
                onClick={() => selectTab("evaluate")}
                size="sm"
                variant="outline"
              >
                Configure evaluation
              </Button>
            </div>
          ) : detailState.kind === "loading" ? (
            <p
              className="flex min-h-28 items-center gap-2 px-4 py-4 text-sm text-secondary"
              role="status"
            >
              <LoaderCircle
                aria-hidden="true"
                className="animate-spin"
                size={15}
              />
              Loading saved run
            </p>
          ) : detailState.kind === "failed" ? (
            <ErrorMessage
              error={detailState.error}
              onRetry={() => setDetailRefresh((current) => current + 1)}
              retryLabel="Retry saved run"
            />
          ) : (
            <ResearchDockInspector
              activeInstrumentId={query.requestedInstrumentId}
              comparisonRunId={query.requestedCompareId}
              csrfToken={csrfToken}
              dataset={
                datasetState.kind === "ready"
                  ? (datasetState.data.find(
                      (dataset) =>
                        dataset.id === detailState.run.dataset_id &&
                        dataset.version === detailState.run.dataset_version,
                    ) ?? null)
                  : null
              }
              datasetState={datasetState}
              focusModel={query.focusModel}
              onClearComparison={handleClearComparison}
              onFocusModelChange={handleFocusModelChange}
              run={detailState.run}
            />
          ))}

        {activeTab === "saved" && (
          <ResearchHistory
            compact
            embedded
            focusModel={query.focusModel}
            instrumentContext={query.requestedInstrumentId}
            key={query.requestedInstrumentId ?? "all-instruments"}
            refreshToken={historyRefresh}
            selectedCompareId={query.requestedCompareId}
            selectedRunId={query.requestedRunId}
          />
        )}

        <div
          className="research-polish-evaluation min-w-0"
          hidden={activeTab !== "evaluate"}
        >
          <ResearchEvaluationSetup
            csrfToken={csrfToken}
            datasetsState={datasetState}
            horizon={horizon}
            key={`${query.requestedInstrumentId ?? "all"}:${query.focusModel}`}
            onCreated={handleCreatedRun}
            onDatasetChange={setSelectedDatasetId}
            onHorizonChange={setHorizon}
            onRetryDatasets={() => setDatasetRefresh((current) => current + 1)}
            requestedInstrumentId={query.requestedInstrumentId}
            selectedDatasetId={selectedDataset?.id ?? ""}
          />
          <details className="dock-setup-provenance">
            <summary>Dataset source and permissions</summary>
            <ResearchDockDatasetFacts
              dataset={selectedDataset}
              state={datasetState}
              title="Selected dataset provenance"
            />
          </details>
        </div>
      </div>
    </section>
  );
}

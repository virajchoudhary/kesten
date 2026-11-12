"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { LoaderCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createResearchRun } from "./research-api";
import { ResearchDatasetEvidence } from "./research-dataset-evidence";
import { formatSessionDate } from "./research-formatters";
import { asResearchError } from "./research-errors";
import {
  ResearchHorizonSchema,
  type ResearchDataset,
  type ResearchRun,
  type ResearchRunRequest,
} from "./research-schemas";
import {
  DatasetSelector,
  ErrorMessage,
  HorizonSelector,
  type LoadState,
} from "./research-workspace-parts";

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
      error: ReturnType<typeof asResearchError>;
    };

export function ResearchEvaluationSetup({
  datasetsState,
  requestedInstrumentId,
  selectedDatasetId,
  horizon,
  csrfToken,
  onDatasetChange,
  onHorizonChange,
  onRetryDatasets,
  onCreated,
}: {
  datasetsState: LoadState<ResearchDataset[]>;
  requestedInstrumentId: string | null;
  selectedDatasetId: string;
  horizon: ResearchRunRequest["horizon_sessions"];
  csrfToken: string;
  onDatasetChange: (value: string) => void;
  onHorizonChange: (value: ResearchRunRequest["horizon_sessions"]) => void;
  onRetryDatasets: () => void;
  onCreated: (run: ResearchRun) => void;
}): React.JSX.Element {
  const [createAttempt, setCreateAttempt] = useState<CreateAttempt>({
    kind: "idle",
  });
  const [datasetQuery, setDatasetQuery] = useState("");
  const evaluationFormRef = useRef<HTMLFormElement>(null);
  const requestController = useRef<AbortController | null>(null);
  useEffect(() => () => requestController.current?.abort(), []);
  const allDatasets = datasetsState.kind === "ready" ? datasetsState.data : [];
  const scopedDatasets =
    requestedInstrumentId === null
      ? allDatasets
      : allDatasets.filter(
          (dataset) => dataset.instrument_id === requestedInstrumentId,
        );
  const query = datasetQuery.trim().toLocaleLowerCase();
  const datasets = scopedDatasets.filter((dataset) => [dataset.name, dataset.instrument_id, dataset.source_id, dataset.data_kind].join(" ").toLocaleLowerCase().includes(query));
  const selectedDataset =
    datasets.find((dataset) => dataset.id === selectedDatasetId) ?? null;
  const createPending = createAttempt.kind === "pending";
  const canReuseKey =
    createAttempt.kind === "failed" &&
    createAttempt.datasetId === selectedDatasetId &&
    createAttempt.horizon === horizon;
  const createError =
    canReuseKey && createAttempt.kind === "failed" ? createAttempt.error : null;

  async function submitEvaluation(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    if (selectedDataset === null || createPending) {
      return;
    }
    const idempotencyKey =
      canReuseKey && createAttempt.kind === "failed"
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
    const controller = new AbortController();
    requestController.current = controller;

    try {
      const run = await createResearchRun(
        request,
        csrfToken,
        controller.signal,
      );
      if (controller.signal.aborted) return;
      setCreateAttempt({ kind: "idle" });
      onCreated(run);
    } catch (error: unknown) {
      if (controller.signal.aborted) return;
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
    if (datasets.some((dataset) => dataset.id === value)) {
      onDatasetChange(value);
      setCreateAttempt({ kind: "idle" });
    }
  }

  function handleHorizonChange(
    value: ResearchRunRequest["horizon_sessions"],
  ): void {
    const parsed = ResearchHorizonSchema.safeParse(value);
    if (parsed.success) {
      onHorizonChange(parsed.data);
      setCreateAttempt({ kind: "idle" });
    }
  }

  return (
    <section
      aria-labelledby="research-setup-title"
      className="min-w-0 border-b border-border-subtle lg:border-r"
    >
      <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
        <h2
          className="text-sm font-semibold"
          id="research-setup-title"
          tabIndex={-1}
        >
          New evaluation setup
        </h2>
      </div>

      {datasetsState.kind === "loading" && (
        <p
          className="flex items-center gap-2 px-4 py-5 text-sm text-secondary"
          role="status"
        >
          <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
          Loading private datasets
        </p>
      )}

      {datasetsState.kind === "failed" && (
        <ErrorMessage
          error={datasetsState.error}
          onRetry={onRetryDatasets}
          retryLabel="Retry dataset list"
        />
      )}

      {datasetsState.kind === "ready" && allDatasets.length === 0 && (
        <div className="space-y-2 border-y border-border-subtle px-4 py-5">
          <h3 className="text-sm font-semibold">
            No private datasets are available
          </h3>
          <p className="max-w-3xl text-sm text-secondary">
            An operator must import an attested historical dataset through the
            research CLI before it can be selected here. Dataset uploads are not
            available in this workspace.
          </p>
          <p className="max-w-3xl text-xs text-secondary">
            A synthetic fixture will appear here after an operator seeds it for
            this account.
          </p>
        </div>
      )}

      {datasetsState.kind === "ready" &&
        allDatasets.length > 0 &&
        scopedDatasets.length === 0 && (
          <p className="px-4 py-5 text-sm text-secondary" role="status">
            No dataset for {requestedInstrumentId} is present in the current picker list. Older saved runs retain access to their exact dataset provenance.
          </p>
        )}

      {datasetsState.kind === "ready" && scopedDatasets.length > 0 && (
        <>
          <form
            className="grid min-w-0 grid-cols-1 gap-4 px-4 py-4"
            onSubmit={(event) => void submitEvaluation(event)}
            ref={evaluationFormRef}
          >
            <div className="grid min-w-0 grid-cols-1 gap-4">
              <label className="grid gap-1.5 text-xs font-medium">
                Find a private dataset
                <input type="search" placeholder="Name, instrument or source" value={datasetQuery} disabled={createPending}
                  onChange={(event) => { setDatasetQuery(event.currentTarget.value); setCreateAttempt({ kind: "idle" }); }}
                  className="min-h-10 min-w-0 rounded-control border border-control bg-surface px-3 font-normal outline-none focus-visible:ring-2 focus-visible:ring-focus" />
              </label>
              <DatasetSelector
                datasets={datasets}
                disabled={createPending}
                onChange={handleDatasetChange}
                selectedDatasetId={selectedDataset?.id ?? ""}
              />
              <p role="status" className="text-xs text-secondary">{datasets.length === 0 ? "No matching datasets in the available private list." : `${datasets.length} available ${datasets.length === 1 ? "dataset" : "datasets"}`}</p>
              {allDatasets.length >= 100 && <p role="note" className="text-xs text-secondary">The picker searches the 100 newest private datasets. Open older saved runs to inspect other dataset versions.</p>}
              {selectedDataset !== null && <div className="min-w-0 space-y-1 text-xs">
                <p className="break-words font-medium">{selectedDataset.name}</p>
                <p className="text-secondary">{selectedDataset.observation_count} observations · {selectedDataset.calendar}</p>
                <p className="text-secondary">{formatSessionDate(selectedDataset.first_session)} – {formatSessionDate(selectedDataset.last_session)}</p>
                <p className="break-words text-secondary">Source: {selectedDataset.source_id}</p>
              </div>}
              <HorizonSelector
                disabled={createPending}
                onChange={handleHorizonChange}
                value={horizon}
              />
            </div>
            <Button
              className="min-h-11 w-full"
              disabled={createPending || selectedDataset === null}
              type="submit"
              variant="primary"
            >
              {createPending ? (
                <>
                  <LoaderCircle
                    aria-hidden="true"
                    className="animate-spin"
                    size={15}
                  />
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
                <><Badge variant="neutral">Exploratory historical data</Badge><p className="text-xs text-warning">Point-in-time qualification is not independently verified.</p></>
              )}
            </div>
          )}
          {selectedDataset !== null && <ResearchDatasetEvidence datasetId={selectedDataset.id} datasetVersion={selectedDataset.version} label="Inspect selected dataset provenance" />}
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
        <div
          className="border-t border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative"
          role="alert"
        >
          {createAttempt.error.message} Select the same dataset and horizon to
          retry this request.
        </div>
      )}
    </section>
  );
}

"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { LoaderCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createResearchRun } from "./research-api";
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
  const evaluationFormRef = useRef<HTMLFormElement>(null);
  const requestController = useRef<AbortController | null>(null);
  useEffect(() => () => requestController.current?.abort(), []);
  const allDatasets = datasetsState.kind === "ready" ? datasetsState.data : [];
  const datasets =
    requestedInstrumentId === null
      ? allDatasets
      : allDatasets.filter(
          (dataset) => dataset.instrument_id === requestedInstrumentId,
        );
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
          Evaluation setup
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
        datasets.length === 0 && (
          <p className="px-4 py-5 text-sm text-secondary" role="status">
            No private research dataset is available for {requestedInstrumentId}
            . Choose an instrument with an imported dataset to run an
            evaluation.
          </p>
        )}

      {datasetsState.kind === "ready" && datasets.length > 0 && (
        <>
          <form
            className="grid min-w-0 grid-cols-1 gap-4 px-4 py-4"
            onSubmit={(event) => void submitEvaluation(event)}
            ref={evaluationFormRef}
          >
            <div className="grid min-w-0 grid-cols-1 gap-4">
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

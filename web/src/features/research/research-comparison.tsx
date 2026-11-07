"use client";

import { useEffect, useState } from "react";
import { LoaderCircle, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { compareResearchRuns, getResearchRun } from "./research-api";
import { asResearchError } from "./research-errors";
import {
  formatBasisPoints,
  formatPercentage,
  formatSessionDate,
  formatUsd,
} from "./research-formatters";
import type {
  ResearchComparisonResponse,
  ResearchRun,
} from "./research-schemas";
import { ErrorMessage } from "./research-workspace-parts";

type ComparisonLoadState =
  | { kind: "loading" }
  | {
      kind: "ready";
      comparison: ResearchComparisonResponse;
      rightRun: ResearchRun;
    }
  | { kind: "failed"; error: ReturnType<typeof asResearchError> };

type MetricId =
  | "mae"
  | "rmse"
  | "return_mae"
  | "return_rmse"
  | "directional_accuracy";
type MetricFormat = "usd" | "basis-points" | "percentage";

const METRICS: ReadonlyArray<{
  id: MetricId;
  label: string;
  format: MetricFormat;
}> = [
  { id: "mae", label: "MAE · USD per share", format: "usd" },
  { id: "rmse", label: "RMSE · USD per share", format: "usd" },
  { id: "return_mae", label: "Return MAE · bps", format: "basis-points" },
  { id: "return_rmse", label: "Return RMSE · bps", format: "basis-points" },
  {
    id: "directional_accuracy",
    label: "Directional accuracy",
    format: "percentage",
  },
];

function formatMetric(value: number, format: MetricFormat): string {
  switch (format) {
    case "usd":
      return formatUsd(value);
    case "basis-points":
      return formatBasisPoints(value);
    case "percentage":
      return formatPercentage(value);
    default: {
      const exhaustive: never = format;
      return exhaustive;
    }
  }
}

function IdentityPanel({
  title,
  run,
}: {
  title: string;
  run: ResearchRun;
}): React.JSX.Element {
  const dependencies = Object.entries(run.runtime.dependencies)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, version]) => `${name} ${version}`)
    .join(", ");
  const models = run.result.models
    .map((model) => `${model.label} (${model.id}, v${model.version})`)
    .join("; ");
  const values = [
    { label: "Run ID", value: run.id, mono: true },
    { label: "Dataset", value: `${run.name} · ${run.data_kind}` },
    {
      label: "Dataset identity",
      value: `${run.dataset_id} · ${run.dataset_version}`,
      mono: true,
    },
    { label: "Instrument", value: run.instrument_id, mono: true },
    {
      label: "Horizon",
      value: `${run.horizon_sessions} next scheduled ${run.horizon_sessions === 1 ? "session" : "sessions"}`,
    },
    {
      label: "Target",
      value: `${run.result.target.name} · ${run.result.target.units} · ${run.result.target.return_convention}`,
    },
    {
      label: "Walk-forward windows",
      value: `Train ${formatSessionDate(run.result.protocol.train_start)}–${formatSessionDate(run.result.protocol.train_end)}; validation ${formatSessionDate(run.result.protocol.validation_start)}–${formatSessionDate(run.result.protocol.validation_end)}; test ${formatSessionDate(run.result.protocol.test_start)}–${formatSessionDate(run.result.protocol.test_end)}`,
    },
    {
      label: "Protocol",
      value: `${run.result.protocol.id} · ${run.result.protocol.configuration_trials} configuration trial · ${run.result.protocol.issue_lag_minutes} minute issue lag`,
      mono: true,
    },
    {
      label: "Protocol SHA-256",
      value: run.result.protocol.protocol_sha256,
      mono: true,
    },
    {
      label: "Engine",
      value: `${run.result.engine_version} · ${run.runtime.engine_source_sha256}`,
      mono: true,
    },
    { label: "References evaluated", value: models },
    {
      label: "Runtime",
      value: `Python ${run.runtime.python}; dependency lock ${run.runtime.dependency_lock_sha256}; ${dependencies}`,
      mono: true,
    },
    {
      label: "Evaluation rows",
      value: run.result.evaluation_rows.length.toLocaleString("en-US"),
    },
  ];

  return (
    <section
      aria-label={title}
      className="min-w-0 border-b border-border-subtle p-4"
    >
      <h4 className="text-sm font-semibold">{title}</h4>
      <dl className="mt-3 grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
        {values.map(({ label, value, mono }) => (
          <div className="min-w-0" key={label}>
            <dt className="text-xs text-secondary">{label}</dt>
            <dd
              className={`mt-1 break-words text-xs ${mono ? "font-mono" : ""}`}
            >
              {value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function MetricChanges({
  leftRun,
  rightRun,
}: {
  leftRun: ResearchRun;
  rightRun: ResearchRun;
}): React.JSX.Element {
  const rightSummaries = new Map(
    rightRun.result.evaluation.map((summary) => [
      `${summary.model_id}:${summary.partition}`,
      summary,
    ]),
  );
  const rows = leftRun.result.evaluation.flatMap((left) => {
    const right = rightSummaries.get(`${left.model_id}:${left.partition}`);
    if (!right) {
      return [];
    }
    return METRICS.map((metric) => ({
      key: `${left.model_id}:${left.partition}:${metric.id}`,
      model: leftRun.result.models.find((item) => item.id === left.model_id),
      partition: left.partition,
      metric,
      left: left[metric.id],
      right: right[metric.id],
    }));
  });

  return (
    <section
      aria-labelledby="research-comparison-deltas-title"
      className="min-w-0 px-4 py-4"
    >
      <h4
        className="text-sm font-semibold"
        id="research-comparison-deltas-title"
      >
        Descriptive metric changes
      </h4>
      <p className="mt-1 text-xs text-secondary">
        Values show the compared run minus the current run. They describe these
        saved evaluations and do not establish forecasting performance.
      </p>
      {rows.length === 0 ? (
        <p className="mt-3 text-sm text-secondary" role="status">
          No aligned metric summaries are available.
        </p>
      ) : (
        <div
          aria-label="Compatible run metric changes"
          className="mt-3 max-w-full overflow-x-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          role="region"
          tabIndex={0}
        >
          <table className="w-full min-w-[760px] border-collapse text-left text-xs">
            <caption className="sr-only">
              Descriptive metric changes for compatible runs, calculated as
              compared run minus current run.
            </caption>
            <thead className="border-b border-border-subtle text-secondary">
              <tr>
                <th className="px-3 py-2 font-medium" scope="col">
                  Reference
                </th>
                <th className="px-3 py-2 font-medium" scope="col">
                  Partition
                </th>
                <th className="px-3 py-2 font-medium" scope="col">
                  Metric
                </th>
                <th className="px-3 py-2 text-right font-medium" scope="col">
                  Current run
                </th>
                <th className="px-3 py-2 text-right font-medium" scope="col">
                  Compared run
                </th>
                <th className="px-3 py-2 text-right font-medium" scope="col">
                  Change
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {rows.map(({ key, model, partition, metric, left, right }) => (
                <tr key={key}>
                  <th className="px-3 py-2.5 font-medium" scope="row">
                    {model?.label ?? key.split(":")[0]}
                  </th>
                  <td className="px-3 py-2.5 capitalize">{partition}</td>
                  <td className="px-3 py-2.5">{metric.label}</td>
                  <td className="px-3 py-2.5 text-right font-mono">
                    {formatMetric(left, metric.format)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono">
                    {formatMetric(right, metric.format)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono">
                    {formatMetric(right - left, metric.format)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function ResearchComparison({
  currentRun,
  comparisonRunId,
  onClear,
}: {
  currentRun: ResearchRun;
  comparisonRunId: string;
  onClear: () => void;
}): React.JSX.Element {
  const [retryCount, setRetryCount] = useState(0);
  const [loadResult, setLoadResult] = useState<{
    key: string;
    state: ComparisonLoadState;
  } | null>(null);
  const requestKey = `${currentRun.id}:${comparisonRunId}:${retryCount}`;
  const sameRun = currentRun.id === comparisonRunId;

  useEffect(() => {
    if (sameRun) {
      return;
    }
    const controller = new AbortController();
    void Promise.all([
      getResearchRun(comparisonRunId, controller.signal),
      compareResearchRuns(currentRun.id, comparisonRunId, controller.signal),
    ])
      .then(([rightRun, comparison]) => {
        if (!controller.signal.aborted) {
          setLoadResult({
            key: requestKey,
            state: { kind: "ready", rightRun, comparison },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setLoadResult({
            key: requestKey,
            state: { kind: "failed", error: asResearchError(error) },
          });
        }
      });
    return () => controller.abort();
  }, [comparisonRunId, currentRun.id, requestKey, sameRun]);

  const state = sameRun
    ? null
    : loadResult?.key === requestKey
      ? loadResult.state
      : { kind: "loading" as const };

  return (
    <section
      aria-labelledby="research-comparison-title"
      className="border-y border-border-subtle"
    >
      <div className="flex min-h-11 flex-wrap items-center justify-between gap-2 border-b border-border-subtle px-4 py-2">
        <h3 className="text-sm font-semibold" id="research-comparison-title">
          Run comparison
        </h3>
        <Button
          aria-label="Remove run comparison"
          className="min-h-10"
          onClick={onClear}
          size="sm"
          variant="ghost"
        >
          <X aria-hidden="true" size={14} />
          Close comparison
        </Button>
      </div>

      {sameRun ? (
        <p className="px-4 py-4 text-sm text-secondary" role="alert">
          Choose a different saved evaluation to compare.
        </p>
      ) : state?.kind === "loading" ? (
        <p
          className="flex items-center gap-2 px-4 py-4 text-sm text-secondary"
          role="status"
        >
          <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
          Loading comparison identities
        </p>
      ) : state?.kind === "failed" ? (
        <ErrorMessage
          error={state.error}
          onRetry={() => setRetryCount((current) => current + 1)}
          retryLabel="Retry comparison"
        />
      ) : state?.kind === "ready" ? (
        <>
          <div
            aria-live="polite"
            className="border-b border-border-subtle px-4 py-3"
          >
            {state.comparison.compatible ? (
              <p className="text-sm text-secondary">
                These runs use compatible evaluation conditions. Metric changes
                are shown as descriptive right-minus-left values.
              </p>
            ) : (
              <div role="status">
                <p className="text-sm font-medium">
                  These runs are not comparable.
                </p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-secondary">
                  {state.comparison.reasons.map((reason, index) => (
                    <li key={`${index}-${reason}`}>{reason}</li>
                  ))}
                </ul>
                <p className="mt-2 text-xs text-secondary">
                  Metric changes are hidden because the evaluation conditions
                  differ.
                </p>
              </div>
            )}
          </div>
          <div className="grid min-w-0 grid-cols-1 divide-y divide-border-subtle md:grid-cols-2 md:divide-x md:divide-y-0">
            <IdentityPanel run={currentRun} title="Current run · left" />
            <IdentityPanel run={state.rightRun} title="Compared run · right" />
          </div>
          {state.comparison.compatible && (
            <MetricChanges leftRun={currentRun} rightRun={state.rightRun} />
          )}
        </>
      ) : null}
    </section>
  );
}

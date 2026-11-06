import { Badge } from "@/components/ui/badge";
import {
  formatBasisPoints,
  formatPercentage,
  formatSessionDate,
  formatUsd,
  formatUtcTimestamp,
} from "./research-formatters";
import { ResearchForecastChart } from "./research-forecast-chart";
import type {
  ResearchDataset,
  ResearchRun,
} from "./research-schemas";

const DIRECTIONS: readonly string[] = ["Down", "Tie", "Up"];

function MetricTable({ run }: { run: ResearchRun }): React.JSX.Element {
  const modelLabels = new Map(run.result.models.map((model) => [model.id, `${model.label} · v${model.version}`]));

  return (
    <div
      aria-label="Validation and test metric comparison"
      className="max-w-full overflow-x-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
      role="region"
      tabIndex={0}
    >
      <table className="w-full min-w-[820px] border-collapse text-left text-xs">
        <caption className="sr-only">
          Validation and test metrics for each baseline model. Price errors are USD per initial share;
          return errors are basis points.
        </caption>
        <thead className="border-b border-border-subtle text-secondary">
          <tr>
            <th className="px-3 py-2 font-medium" scope="col">Model</th>
            <th className="px-3 py-2 font-medium" scope="col">Partition</th>
            <th className="px-3 py-2 text-right font-medium" scope="col">Rows</th>
            <th className="px-3 py-2 text-right font-medium" scope="col">MAE · USD</th>
            <th className="px-3 py-2 text-right font-medium" scope="col">RMSE · USD</th>
            <th className="px-3 py-2 text-right font-medium" scope="col">Return MAE</th>
            <th className="px-3 py-2 text-right font-medium" scope="col">Return RMSE</th>
            <th className="px-3 py-2 text-right font-medium" scope="col">Directional accuracy</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {run.result.evaluation.map((summary) => (
            <tr key={`${summary.model_id}-${summary.partition}`}>
              <th className="px-3 py-2.5 font-medium" scope="row">
                {modelLabels.get(summary.model_id) ?? summary.model_id}
              </th>
              <td className="px-3 py-2.5 capitalize">{summary.partition}</td>
              <td className="px-3 py-2.5 text-right font-mono">{summary.n.toLocaleString("en-US")}</td>
              <td className="px-3 py-2.5 text-right font-mono">{formatUsd(summary.mae)}</td>
              <td className="px-3 py-2.5 text-right font-mono">{formatUsd(summary.rmse)}</td>
              <td className="px-3 py-2.5 text-right font-mono">{formatBasisPoints(summary.return_mae)}</td>
              <td className="px-3 py-2.5 text-right font-mono">{formatBasisPoints(summary.return_rmse)}</td>
              <td className="px-3 py-2.5 text-right font-mono">{formatPercentage(summary.directional_accuracy)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DirectionConfusionTable({ run }: { run: ResearchRun }): React.JSX.Element {
  const modelLabels = new Map(run.result.models.map((model) => [model.id, `${model.label} · v${model.version}`]));

  return (
    <div
      aria-label="Directional confusion counts; rows are predicted direction and columns are actual direction"
      className="max-w-full overflow-x-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
      role="region"
      tabIndex={0}
    >
      <table className="w-full min-w-[620px] border-collapse text-left text-xs">
        <caption className="sr-only">
          Direction confusion counts by model and partition. Rows are predicted direction; columns
          are actual direction. Tie is a separate class.
        </caption>
        <thead className="border-b border-border-subtle text-secondary">
          <tr>
            <th className="px-3 py-2 font-medium" scope="col">Model</th>
            <th className="px-3 py-2 font-medium" scope="col">Partition · predicted</th>
            {DIRECTIONS.map((direction) => (
              <th className="px-3 py-2 text-right font-medium" key={direction} scope="col">
                Actual {direction}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {run.result.evaluation.flatMap((summary) =>
            summary.direction_confusion.map((counts, predictedIndex) => (
              <tr key={`${summary.model_id}-${summary.partition}-${predictedIndex}`}>
                {predictedIndex === 0 && (
                  <th
                    className="px-3 py-2 font-medium"
                    rowSpan={DIRECTIONS.length}
                    scope="rowgroup"
                  >
                    {modelLabels.get(summary.model_id) ?? summary.model_id}
                  </th>
                )}
                <th className="px-3 py-2 font-medium" scope="row">
                  {summary.partition} · {DIRECTIONS[predictedIndex]}
                </th>
                {counts.map((count, actualIndex) => (
                  <td
                    className="px-3 py-2 text-right font-mono"
                    key={`${summary.model_id}-${summary.partition}-${predictedIndex}-${actualIndex}`}
                  >
                    {count.toLocaleString("en-US")}
                  </td>
                ))}
              </tr>
            )),
          )}
        </tbody>
      </table>
    </div>
  );
}

function EvidenceDefinitionList({
  run,
  dataset,
  datasetState,
}: {
  run: ResearchRun;
  dataset: ResearchDataset | null;
  datasetState: "loading" | "ready" | "failed";
}): React.JSX.Element {
  const values = [
    { label: "Forecast origin", value: formatSessionDate(run.result.forecast.origin) },
    { label: "Information cutoff", value: formatUtcTimestamp(run.result.forecast.information_cutoff) },
    { label: "Generated", value: formatUtcTimestamp(run.completed_at) },
    { label: "Horizon", value: `${run.horizon_sessions} next scheduled ${run.horizon_sessions === 1 ? "session" : "sessions"}` },
    { label: "Dataset", value: run.name },
    { label: "Dataset version", value: run.dataset_version },
    { label: "Source", value: dataset?.source_id ?? "Not present in the current private dataset list" },
    { label: "License reference", value: dataset?.license_reference ?? "Not present in the current private dataset list" },
    { label: "Availability evidence", value: dataset?.availability_evidence ?? "Not present in the current private dataset list" },
    { label: "Exchange calendar", value: dataset?.calendar ?? "Not present in the current private dataset list" },
    { label: "Adjustment basis", value: dataset?.adjustment_basis ?? "Not present in the current private dataset list" },
  ];

  return (
    <div>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-3 px-4 py-4 sm:grid-cols-2 xl:grid-cols-3">
        {values.map(({ label, value }) => (
          <div className="min-w-0" key={label}>
            <dt className="text-xs text-secondary">{label}</dt>
            <dd className="mt-1 break-words text-sm">{value}</dd>
          </div>
        ))}
      </dl>
      {datasetState === "loading" && (
        <p className="border-t border-border-subtle px-4 py-2 text-xs text-secondary" role="status">
          Loading dataset provenance
        </p>
      )}
      {datasetState === "failed" && (
        <p className="border-t border-border-subtle px-4 py-2 text-xs text-negative" role="alert">
          Source, license, and availability evidence could not be loaded. Retry the private dataset list above.
        </p>
      )}
      {dataset === null && datasetState === "ready" && (
        <p className="border-t border-border-subtle px-4 py-2 text-xs text-secondary">
          This saved dataset version is not present in the current private dataset list, so its source,
          license, and availability evidence are unavailable here.
        </p>
      )}
    </div>
  );
}

export function ResearchResults({
  run,
  dataset,
  datasetState,
}: {
  run: ResearchRun;
  dataset: ResearchDataset | null;
  datasetState: "loading" | "ready" | "failed";
}): React.JSX.Element {
  const synthetic = run.data_kind === "synthetic_fixture";

  return (
    <article aria-labelledby="research-run-title" className="min-w-0">
      <section className="border-b border-border-subtle px-4 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-base font-semibold" id="research-run-title">
              {run.name}
            </h2>
            <p className="mt-1 text-xs text-secondary">
              {run.instrument_id} · {run.horizon_sessions} next scheduled{" "}
              {run.horizon_sessions === 1 ? "session" : "sessions"} · Run {run.id}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            {synthetic && <Badge variant="demo">SYNTHETIC FIXTURE</Badge>}
            <Badge variant="neutral">Succeeded</Badge>
          </div>
        </div>
        <p className="mt-3 text-sm text-warning">
          {synthetic
            ? "Synthetic pipeline check only. No empirical forecasting performance established."
            : "Historical results are descriptive. No empirical forecasting performance established."}
        </p>
        <p className="mt-2 text-xs text-secondary">
          Price basis: split-neutral close in initial-share units; cash dividends are excluded.
        </p>
      </section>

      <section aria-labelledby="research-provenance-title" className="border-b border-border-subtle">
        <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
          <h3 className="text-sm font-semibold" id="research-provenance-title">Data and run provenance</h3>
        </div>
        <EvidenceDefinitionList dataset={dataset} datasetState={datasetState} run={run} />
        <div className="border-t border-border-subtle px-4 py-3 text-xs text-secondary">
          <p>
            {run.result.target.units}; return convention: {run.result.target.return_convention}.
          </p>
          <p className="mt-1">
            {run.result.protocol.id} · protocol SHA-256{" "}
            <code className="break-all font-mono">{run.result.protocol.protocol_sha256}</code>
          </p>
        </div>
      </section>

      <section aria-labelledby="research-forecast-title" className="border-b border-border-subtle">
        <div className="flex min-h-11 flex-wrap items-center justify-between gap-2 border-b border-border-subtle px-4 py-2">
          <h3 className="text-sm font-semibold" id="research-forecast-title">Dataset history and forecast</h3>
          <span className="text-xs text-secondary">No prediction intervals</span>
        </div>
        <ResearchForecastChart
          forecast={run.result.forecast}
          models={run.result.models}
        />
      </section>

      <section aria-labelledby="research-metrics-title" className="border-b border-border-subtle">
        <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
          <h3 className="text-sm font-semibold" id="research-metrics-title">Validation and test metrics</h3>
        </div>
        <p className="px-4 py-3 text-xs text-secondary">
          Each metric is reported by model and partition. Return errors are simple price-return errors
          converted to basis points.
        </p>
        <MetricTable run={run} />
      </section>

      <section aria-labelledby="research-direction-title" className="border-b border-border-subtle">
        <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
          <h3 className="text-sm font-semibold" id="research-direction-title">
            Direction confusion counts
          </h3>
        </div>
        <p className="px-4 py-3 text-xs text-secondary">
          Rows are predicted directions and columns are actual directions. Ties are a separate class.
          Counts follow: {run.result.protocol.directional_policy}
        </p>
        <DirectionConfusionTable run={run} />
      </section>

      <section aria-labelledby="research-protocol-title" className="border-b border-border-subtle">
        <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
          <h3 className="text-sm font-semibold" id="research-protocol-title">Walk-forward protocol</h3>
        </div>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 px-4 py-4 sm:grid-cols-2 xl:grid-cols-3">
          <div>
            <dt className="text-xs text-secondary">Train</dt>
            <dd className="mt-1 text-sm">
              {formatSessionDate(run.result.protocol.train_start)} – {formatSessionDate(run.result.protocol.train_end)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Validation</dt>
            <dd className="mt-1 text-sm">
              {formatSessionDate(run.result.protocol.validation_start)} – {formatSessionDate(run.result.protocol.validation_end)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Test</dt>
            <dd className="mt-1 text-sm">
              {formatSessionDate(run.result.protocol.test_start)} – {formatSessionDate(run.result.protocol.test_end)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Training policy</dt>
            <dd className="mt-1 break-words text-sm">{run.result.protocol.training_policy}</dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Configuration trials</dt>
            <dd className="mt-1 text-sm">{run.result.protocol.configuration_trials}</dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Issue lag</dt>
            <dd className="mt-1 text-sm">{run.result.protocol.issue_lag_minutes} minutes</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="research-limitations-title" className="border-b border-border-subtle">
        <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
          <h3 className="text-sm font-semibold" id="research-limitations-title">Limitations</h3>
        </div>
        <ul className="list-disc space-y-2 px-9 py-4 text-sm text-secondary">
          {run.result.limitations.map((limitation, index) => (
            <li key={`${index}-${limitation}`}>{limitation}</li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="research-runtime-title">
        <div className="flex min-h-11 items-center border-b border-border-subtle px-4">
          <h3 className="text-sm font-semibold" id="research-runtime-title">Runtime evidence</h3>
        </div>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 px-4 py-4 sm:grid-cols-2 xl:grid-cols-3">
          <div>
            <dt className="text-xs text-secondary">Engine</dt>
            <dd className="mt-1 text-sm">{run.result.engine_version}</dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Python</dt>
            <dd className="mt-1 text-sm">{run.runtime.python}</dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Exchange calendar package</dt>
            <dd className="mt-1 text-sm">{run.runtime.dependencies.exchange_calendars}</dd>
          </div>
          <div className="min-w-0">
            <dt className="text-xs text-secondary">Engine source SHA-256</dt>
            <dd className="mt-1 break-all font-mono text-xs">{run.runtime.engine_source_sha256}</dd>
          </div>
          <div className="min-w-0">
            <dt className="text-xs text-secondary">Dependency lock SHA-256</dt>
            <dd className="mt-1 break-all font-mono text-xs">{run.runtime.dependency_lock_sha256}</dd>
          </div>
          <div>
            <dt className="text-xs text-secondary">Execution</dt>
            <dd className="mt-1 text-sm">
              Deterministic · {run.attempts} attempt · random seed not applicable
            </dd>
          </div>
        </dl>
      </section>
    </article>
  );
}

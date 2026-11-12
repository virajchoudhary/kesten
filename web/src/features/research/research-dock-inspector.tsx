import { Badge } from "@/components/ui/badge";

import { formatSessionDate, formatUtcTimestamp } from "./research-formatters";
import type {
  ResearchDataKind,
  ResearchDataset,
  ResearchReferenceId,
  ResearchRun,
} from "./research-schemas";
import type { LoadState } from "./research-workspace-parts";
import { ResearchAnalytics } from "./research-analytics";
import { ResearchBaselineSummary } from "./research-baseline-summary";
import { ResearchDatasetEvidence } from "./research-dataset-evidence";
import { ResearchRunActions } from "./research-run-actions";
import { ResearchComparison } from "./research-comparison";
import { ResearchReferenceIdSchema } from "./research-schemas";

function categoryLabel(dataKind: ResearchDataKind): string {
  return dataKind === "synthetic_fixture"
    ? "Synthetic pipeline check"
    : "Exploratory historical research";
}

type Fact = { label: string; value: string; mono?: boolean };

function FactGrid({ facts }: { facts: Fact[] }): React.JSX.Element {
  return (
    <dl className="mt-3 grid min-w-0 grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2 xl:grid-cols-3">
      {facts.map(({ label, value, mono }) => (
        <div className="min-w-0" key={label}>
          <dt className="text-[11px] text-secondary">{label}</dt>
          <dd
            className={`mt-0.5 break-words text-xs ${mono ? "font-mono" : ""}`}
          >
            {value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function ResearchDockDatasetFacts({
  dataset,
  state,
  title,
  includeIdentity = true,
}: {
  dataset: ResearchDataset | null;
  state: LoadState<ResearchDataset[]>;
  title: string;
  includeIdentity?: boolean;
}): React.JSX.Element {
  if (dataset === null) {
    const message =
      state.kind === "loading"
        ? "Loading dataset provenance."
        : state.kind === "failed"
          ? "Source, license, and availability evidence could not be loaded."
          : "This exact dataset version is not present in the current private dataset list.";
    return (
      <section
        aria-label={title}
        className="dock-dataset-facts border-y border-border-subtle px-3 py-3"
      >
        <h3 className="text-xs font-semibold">{title}</h3>
        <p className="mt-2 text-xs text-secondary" role="status">
          {message}
        </p>
      </section>
    );
  }

  const facts: Fact[] = [
    ...(includeIdentity
      ? [
          { label: "Dataset ID", value: dataset.id, mono: true },
          { label: "Dataset version", value: dataset.version, mono: true },
        ]
      : []),
    { label: "Source", value: dataset.source_id },
    { label: "Calendar", value: dataset.calendar },
    { label: "Adjustment basis", value: dataset.adjustment_basis },
    {
      label: "Observations",
      value: dataset.observation_count.toLocaleString("en-US"),
    },
    {
      label: "Date coverage",
      value: `${dataset.first_session} to ${dataset.last_session}`,
    },
    { label: "License reference", value: dataset.license_reference },
    { label: "Availability evidence", value: dataset.availability_evidence },
  ];

  return (
    <section
      aria-label={title}
      className="dock-dataset-facts min-w-0 border-y border-border-subtle px-3 py-3"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <h3 className="text-xs font-semibold">{title}</h3>
        <Badge
          variant={
            dataset.data_kind === "synthetic_fixture" ? "demo" : "neutral"
          }
        >
          {categoryLabel(dataset.data_kind)}
        </Badge>
      </div>
      <p className="mt-1 break-words text-xs text-secondary">{dataset.name}</p>
      <FactGrid facts={facts} />
    </section>
  );
}

export function ResearchDockInspector({
  run,
  dataset,
  datasetState,
  activeInstrumentId,
  focusModel,
  csrfToken,
  onFocusModelChange,
  onClearComparison,
  comparisonRunId,
}: {
  run: ResearchRun;
  dataset: ResearchDataset | null;
  datasetState: LoadState<ResearchDataset[]>;
  activeInstrumentId: string | null;
  focusModel: ResearchReferenceId;
  csrfToken: string;
  onFocusModelChange: (model: ResearchReferenceId) => void;
  onClearComparison: () => void;
  comparisonRunId: string | null;
}): React.JSX.Element {
  return (
    <article className="dock-inspector min-w-0">
      {activeInstrumentId !== null &&
        activeInstrumentId !== run.instrument_id && (
          <p
            className="border-b border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning"
            role="status"
          >
            Active chart:{" "}
            <span className="font-mono">{activeInstrumentId}</span>. This saved
            run belongs to{" "}
            <span className="font-mono">{run.instrument_id}</span>.
          </p>
        )}
      <header className="dock-run-header">
        <div>
          <h2>Evaluation results</h2>
          <h3>{run.name}</h3>
        </div>
        <Badge
          variant={run.data_kind === "synthetic_fixture" ? "demo" : "neutral"}
        >
          {categoryLabel(run.data_kind)}
        </Badge>
      </header>
      <div className="dock-run-grid">
        <aside className="dock-run-context" aria-label="Selected run summary">
          <p className="dock-integrity">
            {run.data_kind === "synthetic_fixture"
              ? "Synthetic pipeline check only. No empirical forecasting performance established."
              : "Historical results are descriptive. No empirical forecasting performance established."}
          </p>
          <dl className="dock-run-facts">
            <div>
              <dt>Target</dt>
              <dd>
                {run.horizon_sessions} next scheduled{" "}
                {run.horizon_sessions === 1 ? "session" : "sessions"}
              </dd>
            </div>
            <div>
              <dt>Origin</dt>
              <dd>{formatSessionDate(run.result.forecast.origin)}</dd>
            </div>
            <div>
              <dt>Information cutoff</dt>
              <dd>
                {formatUtcTimestamp(run.result.forecast.information_cutoff)}
              </dd>
            </div>
          </dl>
          <div className="dock-run-controls">
            <label className="dock-run-reference-label">
              Reference focus
              <select
                aria-label="Reference focus"
                className="dock-run-reference"
                value={focusModel}
                onChange={(event) => {
                  const parsed = ResearchReferenceIdSchema.safeParse(
                    event.currentTarget.value,
                  );
                  if (parsed.success) onFocusModelChange(parsed.data);
                }}
              >
                {run.result.models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label} · v{model.version}
                  </option>
                ))}
              </select>
            </label>
            <ResearchRunActions key={run.id} run={run} csrfToken={csrfToken} />
          </div>
          <details className="dock-run-identities">
            <summary>Dataset and run identities</summary>
            <FactGrid
              facts={[
                {
                  label: "Dataset identity",
                  value: `${run.dataset_id} · ${run.dataset_version}`,
                  mono: true,
                },
                { label: "Run ID", value: run.id, mono: true },
                {
                  label: "Model versions",
                  value: run.result.models
                    .map((model) => `${model.id} · v${model.version}`)
                    .join("; "),
                },
              ]}
            />
            <ResearchDockDatasetFacts
              dataset={dataset}
              includeIdentity={false}
              state={datasetState}
              title="Immutable dataset provenance"
            />
            <ResearchDatasetEvidence datasetId={run.dataset_id} datasetVersion={run.dataset_version} label="Inspect run dataset provenance" />
          </details>
        </aside>
        <div className="dock-analytics">
          <ResearchAnalytics compact run={run} focusModel={focusModel} />
          <ResearchBaselineSummary key={run.id} run={run} />
          {comparisonRunId && (
            <ResearchComparison
              currentRun={run}
              comparisonRunId={comparisonRunId}
              onClear={onClearComparison}
            />
          )}
        </div>
      </div>
    </article>
  );
}

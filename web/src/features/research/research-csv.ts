import type { ResearchRun } from "./research-schemas";
import type { ReferenceId } from "./research-series";
import { researchRowIdentity } from "./research-row-identity";

export type ResearchCsvView = "Walk-forward" | "Errors";
export type ResearchCsvPartition = "all" | "validation" | "test";

export const HISTORICAL_CSV_EXPORT_DISABLED_REASON =
  "CSV export is disabled for historical datasets because redistribution rights are not configured.";

type ResearchCsvOptions = {
  run: ResearchRun;
  focusModel: ReferenceId;
  view: ResearchCsvView;
  partition: ResearchCsvPartition;
};

type CsvCell = string | number | boolean | null;

function csvCell(value: CsvCell): string {
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (value === null) {
    return "";
  }

  const safeValue =
    /^[\s\u0000-\u0020]*[=+\-@]/u.test(value) || /^[\t\r\n]/u.test(value)
      ? `'${value}`
      : value;
  return `"${safeValue.replaceAll('"', '""')}"`;
}

export function researchEvaluationCsv({
  run,
  focusModel,
  view,
  partition,
}: ResearchCsvOptions): string {
  if (run.data_kind !== "synthetic_fixture") {
    throw new Error(HISTORICAL_CSV_EXPORT_DISABLED_REASON);
  }
  const isSynthetic = run.data_kind === "synthetic_fixture";

  const model = run.result.models.find(({ id }) => id === focusModel);
  const baselineModel = run.result.models.find(({ id }) => id === "last_close");
  const baselineRows = new Map(
    run.result.evaluation_rows
      .filter((row) => row.model_id === "last_close")
      .map((row) => [researchRowIdentity(row), row]),
  );
  const selectedRows = run.result.evaluation_rows
    .filter(
      (row) =>
        row.model_id === focusModel &&
        (partition === "all" || row.partition === partition),
    )
    .sort((left, right) => left.target.localeCompare(right.target));

  const headers = [
    "format",
    "view",
    "partition_filter",
    "run_id",
    "run_name",
    "dataset_id",
    "dataset_version",
    "data_kind",
    "is_synthetic",
    "empirical_performance_established",
    "evidence_kind",
    "instrument_id",
    "engine_version",
    "engine_source_sha256",
    "dependency_lock_sha256",
    "python_version",
    "protocol_id",
    "protocol_sha256",
    "deterministic",
    "random_seed",
    "model_id",
    "model_version",
    "baseline_model_id",
    "baseline_model_version",
    "target_name",
    "horizon_sessions",
    "units",
    "target_date",
    "origin",
    "information_cutoff",
    "origin_value",
    "input_sha256",
    "period",
    "actual",
    "chart_actual",
    "selected",
    "baseline",
    "error",
    "baseline_error",
    "selected_evaluation_row_json",
    "baseline_evaluation_row_json",
  ];
  const disclosure =
    "Synthetic pipeline check only. No empirical forecasting performance established.";
  const units =
    view === "Errors"
      ? `${run.result.target.units}; forecast error is predicted minus actual`
      : run.result.target.units;
  const rows = selectedRows.map((selectedRow) => {
    const baselineRow = baselineRows.get(researchRowIdentity(selectedRow));
    const error = selectedRow.predicted - selectedRow.actual;
    const baselineError = baselineRow
      ? baselineRow.predicted - selectedRow.actual
      : null;
    return [
      "cadrisyn-research-view-v1",
      view,
      partition,
      run.id,
      run.name,
      run.dataset_id,
      run.dataset_version,
      run.data_kind,
      isSynthetic,
      run.result.empirical_performance_established,
      `${run.result.evidence_kind}. ${disclosure}`,
      run.instrument_id,
      run.result.engine_version,
      run.runtime.engine_source_sha256,
      run.runtime.dependency_lock_sha256,
      run.runtime.python,
      run.result.protocol.id,
      run.result.protocol.protocol_sha256,
      run.runtime.deterministic,
      run.runtime.random_seed,
      focusModel,
      model?.version ?? "",
      "last_close",
      baselineModel?.version ?? "",
      run.result.target.name,
      run.horizon_sessions,
      units,
      selectedRow.target,
      selectedRow.origin,
      selectedRow.information_cutoff,
      selectedRow.origin_value,
      selectedRow.input_sha256,
      selectedRow.partition,
      selectedRow.actual,
      view === "Errors" ? 0 : selectedRow.actual,
      view === "Errors" ? error : selectedRow.predicted,
      view === "Errors" ? baselineError : (baselineRow?.predicted ?? null),
      error,
      baselineError,
      JSON.stringify(selectedRow),
      baselineRow ? JSON.stringify(baselineRow) : null,
    ] satisfies CsvCell[];
  });

  return [headers, ...rows]
    .map((row) => row.map(csvCell).join(","))
    .join("\r\n")
    .concat("\r\n");
}

export function downloadResearchEvaluationCsv(
  options: ResearchCsvOptions,
): void {
  const source = researchEvaluationCsv(options);
  const blob = new Blob([source], { type: "text/csv;charset=utf-8" });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `research-${options.run.id}-${options.view.toLowerCase()}-${options.partition}.csv`;
  anchor.hidden = true;
  document.body.append(anchor);
  try {
    anchor.click();
  } finally {
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
  }
}

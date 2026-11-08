"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ResearchForecastChart } from "./research-forecast-chart";
import {
  downloadResearchEvaluationCsv,
  HISTORICAL_CSV_EXPORT_DISABLED_REASON,
} from "./research-csv";
import { ResearchLineChart } from "./research-line-chart";
import { evaluationSeries, type ReferenceId } from "./research-series";
import type { ResearchRun } from "./research-schemas";
import { formatSessionDate } from "./research-formatters";

const VIEWS = ["Forecast", "Walk-forward", "Errors"] as const;

export function ResearchAnalytics({
  run,
  focusModel = "historical_log_mean",
  compact = false,
}: {
  run: ResearchRun;
  focusModel?: ReferenceId;
  compact?: boolean;
}): React.JSX.Element {
  const [view, setView] = useState<(typeof VIEWS)[number]>("Forecast");
  const [partition, setPartition] = useState<"all" | "validation" | "test">(
    "all",
  );
  const points = useMemo(
    () =>
      evaluationSeries(run, focusModel, view === "Errors").filter(
        (p) => partition === "all" || p.period === partition,
      ),
    [run, focusModel, partition, view],
  );
  const label =
    run.result.models.find((m) => m.id === focusModel)?.label ?? focusModel;
  const csvExportAllowed = run.data_kind === "synthetic_fixture";
  const protocol = run.result.protocol;
  return (
    <div
      className={`research-analytics min-w-0 ${compact ? "is-compact" : ""}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-4 py-3">
        <div
          className="research-view-switcher flex gap-1"
          role="group"
          aria-label="Evaluation chart view"
        >
          {VIEWS.map((name) => (
            <button
              className={`research-view-option min-h-10 rounded-control px-3 text-xs font-medium focus-visible:ring-2 focus-visible:ring-focus ${view === name ? "bg-action text-on-action" : "text-secondary hover:bg-raised"}`}
              aria-pressed={view === name}
              key={name}
              type="button"
              onClick={() => setView(name)}
            >
              {name}
            </button>
          ))}
        </div>
        {view !== "Forecast" && (
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-xs text-secondary">
              Evaluation period{" "}
              <select
                aria-label="Evaluation period"
                className="ml-2 min-h-10 rounded-control border border-control bg-surface px-2 text-foreground"
                value={partition}
                onChange={(e) => {
                  if (
                    e.target.value === "all" ||
                    e.target.value === "test" ||
                    e.target.value === "validation"
                  )
                    setPartition(e.target.value);
                }}
              >
                <option value="all">Validation and test</option>
                <option value="validation">Validation</option>
                <option value="test">Test</option>
              </select>
            </label>
            {csvExportAllowed ? (
              <Button
                className="min-h-10"
                onClick={() =>
                  downloadResearchEvaluationCsv({
                    run,
                    focusModel,
                    view,
                    partition,
                  })
                }
                size="sm"
                variant="outline"
              >
                <Download aria-hidden="true" size={15} />
                Download CSV
              </Button>
            ) : (
              <p className="max-w-xs text-xs text-secondary" role="note">
                {HISTORICAL_CSV_EXPORT_DISABLED_REASON}
              </p>
            )}
          </div>
        )}
      </div>
      <div
        className={`evaluation-periods ${compact ? "compact-periods" : ""} grid grid-cols-1 gap-2 border-b border-border-subtle px-4 py-3 text-xs sm:grid-cols-3`}
      >
        {[
          {
            name: "Training",
            start: protocol.train_start,
            end: protocol.train_end,
          },
          {
            name: "Validation",
            start: protocol.validation_start,
            end: protocol.validation_end,
          },
          { name: "Test", start: protocol.test_start, end: protocol.test_end },
        ].map((p) => (
          <div key={p.name}>
            <span className="font-medium">{p.name}</span>
            <p className="mt-1 text-secondary">
              {formatSessionDate(p.start)} – {formatSessionDate(p.end)}
            </p>
          </div>
        ))}
      </div>
      {view === "Forecast" ? (
        <ResearchForecastChart
          forecast={run.result.forecast}
          models={run.result.models}
          focusModel={focusModel}
          compact={compact}
        />
      ) : (
        <>
          <p className="px-4 pt-3 text-xs text-secondary">
            Each point is a saved out-of-sample target from its own forecast
            origin.{" "}
            {view === "Errors"
              ? "Signed errors are predicted minus actual, not trading returns."
              : "Shading separates validation and test targets."}{" "}
            Five-session targets overlap. No significance or calibrated
            uncertainty is claimed.
          </p>
          <ResearchLineChart
            key={`${run.id}-${partition}-${view}`}
            points={points}
            title={
              view === "Errors"
                ? "Walk-forward forecast errors"
                : "Walk-forward dataset values and predictions"
            }
            focusLabel={label}
            errors={view === "Errors"}
            compact={compact}
          />
          <details className="border-t border-border-subtle px-4 py-3 text-xs">
            <summary className="cursor-pointer font-medium">
              Exact evaluation values
            </summary>
            <EvaluationRows points={points} label={label} />
          </details>
        </>
      )}
    </div>
  );
}

function EvaluationRows({
  points,
  label,
}: {
  points: ReturnType<typeof evaluationSeries>;
  label: string;
}): React.JSX.Element {
  const [page, setPage] = useState(0);
  const start = Math.min(
    page * 20,
    Math.max(0, Math.ceil(points.length / 20) - 1) * 20,
  );
  return (
    <>
      <div className="my-3 flex items-center justify-between gap-2">
        <span>
          {start + 1}–{Math.min(start + 20, points.length)} of {points.length}{" "}
          targets
        </span>
        <div className="flex gap-2">
          <button
            className="min-h-10 rounded-control border border-control px-3 disabled:opacity-40"
            disabled={start === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            type="button"
          >
            Previous rows
          </button>
          <button
            className="min-h-10 rounded-control border border-control px-3 disabled:opacity-40"
            disabled={start + 20 >= points.length}
            onClick={() => setPage((p) => p + 1)}
            type="button"
          >
            Next rows
          </button>
        </div>
      </div>
      <div
        className="overflow-x-auto focus-visible:ring-2 focus-visible:ring-focus"
        tabIndex={0}
        role="region"
        aria-label="Exact evaluation values"
      >
        <table className="w-full min-w-[580px] text-left">
          <caption className="sr-only">
            Exact values in the current chart view; error view contains signed
            errors.
          </caption>
          <thead>
            <tr>
              {[
                "Target",
                "Origin",
                "Period",
                "Dataset / zero",
                label,
                "Last close",
              ].map((h) => (
                <th className="p-2" key={h} scope="col">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {points.slice(start, start + 20).map((p) => (
              <tr
                className="border-t border-border-subtle"
                key={`${p.period}-${p.time}`}
              >
                <td className="p-2">{p.time}</td>
                <td className="p-2">{p.origin}</td>
                <td className="p-2">{p.period}</td>
                {[p.actual, p.selected, p.baseline].map((v, i) => (
                  <td className="p-2 font-mono" key={i}>
                    {v === null ? "Unavailable" : String(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
